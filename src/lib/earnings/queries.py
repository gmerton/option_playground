import boto3
import re
from typing import Optional, Dict, Iterable, Union
from datetime import date, datetime
import time

DATABASE="gm_equity"
ATHENA_OUTPUT_LOCATION = "s3://athena-919061006621/"


def _run_athena_query(
    sql: str,
    *,
    poll_interval: float = 0.5,
    timeout_sec: int = 120
) -> Optional[str]:
    client = boto3.client("athena", region_name='us-west-2')
    q = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_LOCATION},
        WorkGroup="primary",
    )
    qid = q["QueryExecutionId"]

    # wait for completion
    start = time.time()
    while True:
        status = client.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]["State"]
        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        if time.time() - start > timeout_sec:
            client.stop_query_execution(QueryExecutionId=qid)
            raise TimeoutError("Athena query timed out")
        time.sleep(poll_interval)

    if status != "SUCCEEDED":
        return None

    # fetch first data row, first column
    res = client.get_query_results(QueryExecutionId=qid, MaxResults=2)
    rows = res.get("ResultSet", {}).get("Rows", [])
    if len(rows) <= 1:  # only header or empty
        return None
    cells = rows[1].get("Data", [])
    return cells[0].get("VarCharValue") if cells else None

def fetch_closes_for_dates(
    dates: Iterable[Union[str, date]],
    ticker: str) -> Dict[str, float]:
    """
    For each date in `dates`, query the 16:30 bar close from Athena.
    Returns a dict mapping ISO date string -> close (float) or -1.0 if not found.
    """
    t = _safe_ticker(ticker)
    out: Dict[str, float] = {}

    for d_in in dates:
        d = _parse_date(d_in)
        iso = d.isoformat()

        # Your query template
        sql = f"""
        SELECT close
        FROM stock_5min_pp
        WHERE ticker = '{t}'
          AND year = {d.year}
          AND month = {d.month}
          AND day(ts) = {d.day}
          AND hour(ts) = 16
          AND minute(ts) = 30
        LIMIT 1
        """
        print(sql)

        val = _run_athena_query(
            sql.strip(),
          )

        if val is None:
            out[iso] = -1.0
        else:
            try:
                out[iso] = float(val)
            except ValueError:
                out[iso] = -1.0

    return out



def _parse_date(d: Union[str, date]) -> date:
    if isinstance(d, date):
        return d
    # Accept 'YYYY-MM-DD' or 'MM/DD/YYYY'
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(d, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date format: {d}")

def _safe_ticker(t: str) -> str:
    # allow letters, numbers, dot, hyphen (e.g., "BRK.B", "RDS-A")
    if not re.fullmatch(r"[A-Za-z0-9.\-]+", t):
        raise ValueError("Ticker contains illegal characters")
    return t