"""
IBKR Flex Web Service client.

Two-step process:
  1. SendRequest  — submits the query, returns a ReferenceCode
  2. GetStatement — poll with ReferenceCode until the statement is ready

Usage:
    xml_text = fetch_flex_query(from_date="20260101", to_date="20260224")
    dfs      = parse_flex_xml(xml_text)   # dict of { element_name -> DataFrame }

Run as script for a quick test:
    IBKR_FLEX_TOKEN=<token> PYTHONPATH=src python -m lib.ibkr.flex_client
"""

import os
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "src" / "lib" / "output" / "ibkr"

# ── Endpoints ────────────────────────────────────────────────────────────────
SEND_URL = (
    "https://ndcdyn.interactivebrokers.com"
    "/AccountManagement/FlexWebService/SendRequest"
)
GET_URL = (
    "https://gdcdyn.interactivebrokers.com"
    "/Universal/servlet/FlexStatementService.GetStatement"
)

QUERY_ID      = "1415008"
VERSION       = "3"
POLL_INTERVAL = 5    # seconds between polls
MAX_POLLS     = 36   # give up after 3 minutes

HEADERS = {"User-Agent": "python-requests/2.0"}


# ── Internal helpers ─────────────────────────────────────────────────────────

def _send_request(token: str, from_date: str, to_date: str) -> str:
    """Kick off the Flex query. Returns the ReferenceCode string."""
    resp = requests.get(
        SEND_URL,
        params={"t": token, "q": QUERY_ID, "fd": from_date, "td": to_date, "v": VERSION},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    status = root.findtext("Status")
    if status != "Success":
        err = root.findtext("ErrorMessage") or resp.text[:200]
        raise RuntimeError(f"SendRequest failed — status={status}: {err}")

    ref_code = root.findtext("ReferenceCode")
    if not ref_code:
        raise RuntimeError(f"SendRequest returned no ReferenceCode. Response: {resp.text[:200]}")

    return ref_code


def _get_statement(token: str, ref_code: str, request_ts: datetime) -> tuple[str, float]:
    """Poll the GetStatement endpoint until the statement XML is ready.

    Returns:
        (xml_text, lag_seconds) where lag_seconds is time from SendRequest to
        first successful GetStatement response.
    """
    for attempt in range(1, MAX_POLLS + 1):
        poll_ts = datetime.now()
        resp = requests.get(
            GET_URL,
            params={"q": ref_code, "t": token, "v": VERSION},
            headers=HEADERS,
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.text.strip()

        # Still generating — wait and retry
        if "Statement generation in progress" in text or "<Status>Processing</Status>" in text:
            elapsed = (poll_ts - request_ts).total_seconds()
            print(f"  [{attempt}/{MAX_POLLS}] Generating... ({elapsed:.1f}s elapsed) retrying in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)
            continue

        # Explicit failure
        if "<Status>Fail</Status>" in text or "ErrorCode" in text:
            raise RuntimeError(f"GetStatement returned an error:\n{text[:500]}")

        lag = (datetime.now() - request_ts).total_seconds()
        return text, lag

    raise RuntimeError(f"GetStatement timed out after {MAX_POLLS} polls ({MAX_POLLS * POLL_INTERVAL}s)")


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_flex_query(
    from_date: str | None = None,
    to_date: str | None = None,
    token: str | None = None,
) -> str:
    """
    Fetch IBKR Flex query results as a raw XML string.

    Args:
        from_date: Start date in YYYYMMDD format. Defaults to today.
        to_date:   End date in YYYYMMDD format. Defaults to today.
        token:     Flex token. Defaults to IBKR_FLEX_TOKEN env var.

    Returns:
        Raw XML string of the Flex statement.
    """
    token = token or os.environ.get("IBKR_FLEX_TOKEN")
    if not token:
        raise RuntimeError("IBKR_FLEX_TOKEN environment variable is not set")

    today = date.today().strftime("%Y%m%d")
    from_date = from_date or today
    to_date   = to_date   or today

    print(f"Submitting Flex query {QUERY_ID}  {from_date} → {to_date} ...")
    request_ts = datetime.now()
    ref_code = _send_request(token, from_date, to_date)
    print(f"  ReferenceCode: {ref_code}  (submitted at {request_ts.strftime('%H:%M:%S')})")

    print("Retrieving statement ...")
    xml_text, lag = _get_statement(token, ref_code, request_ts)
    retrieved_ts = datetime.now()
    print(f"  Done.  Lag: {lag:.1f}s  (retrieved at {retrieved_ts.strftime('%H:%M:%S')})")

    return xml_text


def parse_flex_xml(xml_text: str) -> dict[str, pd.DataFrame]:
    """
    Parse a Flex statement XML string into a dict of DataFrames.

    Each distinct child element tag within <FlexStatement> becomes a key,
    and all elements of that tag are collected into a DataFrame (attributes
    become columns).

    Example keys: 'Trade', 'OpenPosition', 'CashTransaction', etc.

    Returns:
        { element_tag: pd.DataFrame }
    """
    root = ET.fromstring(xml_text)

    # Flex XML structure:
    #   <FlexQueryResponse>
    #     <FlexStatements count="N">
    #       <FlexStatement accountId="..." ...>
    #         <Trades> <Trade .../> ... </Trades>
    #         <OpenPositions> <OpenPosition .../> </OpenPositions>
    #         ...
    #       </FlexStatement>
    #     </FlexStatements>
    #   </FlexQueryResponse>

    records: dict[str, list[dict]] = {}

    for stmt in root.iter("FlexStatement"):
        for section in stmt:
            for element in section:
                tag = element.tag
                if tag not in records:
                    records[tag] = []
                records[tag].append(element.attrib)

    return {tag: pd.DataFrame(rows) for tag, rows in records.items() if rows}


def save_flex_results(dfs: dict[str, pd.DataFrame], xml_text: str, from_date: str, to_date: str) -> Path:
    """
    Save parsed DataFrames as CSVs and raw XML to src/lib/output/ibkr/.
    Files are timestamped so repeated runs don't overwrite each other.
    Returns the output directory for this run.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"flex_{from_date}_{to_date}_{ts}"
    run_dir.mkdir()

    # Save raw XML
    xml_path = run_dir / "raw.xml"
    xml_path.write_text(xml_text, encoding="utf-8")
    print(f"  Raw XML → {xml_path}")

    # Save each DataFrame as CSV
    for name, df in dfs.items():
        csv_path = run_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  {name:30s} {len(df):>6} rows → {csv_path.name}")

    return run_dir


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    from_date = sys.argv[1] if len(sys.argv) > 1 else None
    to_date   = sys.argv[2] if len(sys.argv) > 2 else None

    xml_text = fetch_flex_query(from_date=from_date, to_date=to_date)

    dfs = parse_flex_xml(xml_text)
    if not dfs:
        print("No data returned.")
        sys.exit(0)

    print(f"\nParsed {len(dfs)} section(s):")
    for name, df in dfs.items():
        print(f"  {name:30s} {len(df):>6} rows  {len(df.columns)} columns")

    print("\nSaving output ...")
    run_dir = save_flex_results(dfs, xml_text, from_date or "today", to_date or "today")
    print(f"\nAll files saved to: {run_dir}")
