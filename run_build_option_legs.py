#!/usr/bin/env python3
"""
Build (or refresh) the option_legs_settled Glue table from options_daily_v3.

For each ticker and Friday entry date with an expiry ~10 DTE, stores all liquid
near-ATM option legs (|delta| 0.02–0.55) with both the entry mid price and the
settlement price at expiry. This enables any short-expiry strategy (iron butterfly,
iron condor, straddle, spread) to be assembled locally in pandas.

Output schema (Glue table: silver.option_legs_settled)
------------------------------------------------------
  ticker        string   } partition cols
  year          int      }
  entry_date    date       (Friday, ~10 DTE before expiry)
  expiry        date
  dte           int
  cp            string     ('C' or 'P')
  strike        double
  delta         double     (at entry)
  mid_entry     double
  last_expiry   double     (0 if OTM/untradeable at expiry)

Coverage
--------
  ~10 DTE Fridays, |delta| 0.02–0.55, bid>0/ask>0/OI>0, B/A ≤ 35% of mid
  Estimated ~8M rows / ~200MB compressed for the 987-ticker universe (2018–2026)

Usage
-----
  # Full backfill, default 987-ticker universe:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_option_legs.py --mode full

  # Incremental (only dates after last record in table):
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_option_legs.py

  # Specific tickers:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_option_legs.py --tickers SPY QQQ TLT

  # Specific date range:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_option_legs.py \\
      --mode full --start 2024-01-01 --end 2024-12-31 --tickers SPY

  # Load tickers from file (one per line):
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_option_legs.py \\
      --ticker-file /tmp/tickers.txt --mode full

Requires: AWS_PROFILE=clarinut-gmerton
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import awswrangler as wr

from lib.studies.option_legs_study import (
    LEGS_DB,
    LEGS_TABLE,
    fetch_option_legs_batch,
    write_option_legs,
)

# ── Default ticker universe ───────────────────────────────────────────────────
# 987-ticker study universe. To regenerate from MySQL:
#   MYSQL_PASSWORD=cthekb23 python3 -c "
#   from lib.mysql_lib import _get_engine; import pandas as pd
#   pd.read_sql('SELECT DISTINCT ticker FROM study_summary WHERE study_id=12', _get_engine()
#   )['ticker'].to_csv('/tmp/tickers.txt', index=False, header=False)"

DEFAULT_TICKERS: list[str] = [
    "A", "AA", "AABA", "AAL", "AAXJ", "ABBV", "ABT", "ACGL", "ACM", "ACN",
    "ACP", "ADBE", "ADI", "ADM", "ADP", "ADSK", "AEE", "AEP", "AES", "AFL",
    "AGCO", "AIG", "AINV", "AIZ", "AJG", "AKAM", "ALB", "ALGN", "ALK", "ALL",
    "ALNY", "AMAT", "AMCR", "AMD", "AMGN", "AMP", "AMT", "AMZN", "AN", "ANET",
    "ANF", "ANSS", "AON", "AOS", "APA", "APD", "APH", "APTV", "ARC", "ARE",
    "ARKG", "ARKK", "ARKQ", "ARKW", "ARW", "ASHR", "ASO", "ATGE", "AVB", "AVGO",
    "AVY", "AWK", "AXP", "AZO", "BA", "BAC", "BAX", "BBBY", "BBY", "BDX",
    "BEN", "BIDU", "BIIB", "BJ", "BKLN", "BKNG", "BKR", "BLK", "BMY", "BND",
    "BNDX", "BRK.B", "BSX", "BURL", "BWA", "C", "CAG", "CAH", "CAT", "CB",
    "CBOE", "CBRE", "CDAY", "CDW", "CE", "CF", "CFG", "CHD", "CHRW", "CHTR",
    "CI", "CINF", "CL", "CLR", "CLS", "CMC", "CME", "CMG", "CMI", "CMS",
    "CNC", "CNP", "COF", "COO", "COP", "COST", "CPB", "CPRT", "CPT", "CRL",
    "CRM", "CRWD", "CSCO", "CSX", "CTAS", "CTLT", "CTRA", "CTSH", "CTVA", "CVS",
    "CVX", "CZR", "DAL", "DE", "DDOG", "DFS", "DG", "DGX", "DHI", "DHR",
    "DIS", "DISH", "DLTR", "DNB", "DOV", "DXCM", "DXJ", "EA", "EBAY", "EDC",
    "EDR", "EDZ", "EEM", "EFA", "EFV", "EFX", "EIX", "EL", "EMN", "EMR",
    "ENPH", "EOG", "EPAM", "EQH", "EQR", "EQT", "ES", "ESS", "ETN", "ETR",
    "ETSY", "EVBG", "EW", "EXC", "EXPD", "EXPE", "EXR", "F", "FANG", "FAST",
    "FBHS", "FCX", "FDS", "FDX", "FE", "FFIV", "FHN", "FIS", "FISV", "FITB",
    "FLT", "FMC", "FOX", "FOXA", "FRC", "FSLR", "FTNT", "FTV", "GD", "GE",
    "GEV", "GILD", "GIS", "GL", "GLD", "GLW", "GM", "GNRC", "GOOGL", "GPC",
    "GPN", "GRMN", "GS", "GWW", "HAL", "HAS", "HBAN", "HD", "HES", "HIG",
    "HII", "HLT", "HON", "HPE", "HPQ", "HRL", "HSIC", "HST", "HSY", "HUBB",
    "HUM", "HWM", "HXL", "IBM", "ICE", "IDXX", "IEF", "IEO", "IEZ", "IFF",
    "IGT", "ILMN", "INDA", "INFY", "INTC", "INTU", "IP", "IQV", "IR", "IRM",
    "ISRG", "IT", "ITW", "IVZ", "J", "JBHT", "JBL", "JCI", "JKHY", "JNJ",
    "JNPR", "JPM", "K", "KDP", "KEY", "KEYS", "KHC", "KIM", "KLAC", "KMB",
    "KMI", "KO", "KR", "L", "LB", "LDOS", "LEN", "LH", "LHX", "LIN",
    "LKQ", "LLY", "LMT", "LNC", "LOW", "LRCX", "LULU", "LUV", "LVS", "LYB",
    "LYV", "MA", "MAA", "MAR", "MAS", "MCD", "MCHP", "MCK", "MCO", "MDLZ",
    "MDT", "MET", "META", "MGM", "MHK", "MKC", "MKTX", "MLM", "MMC", "MMM",
    "MNST", "MO", "MOH", "MOS", "MPC", "MPWR", "MRK", "MRNA", "MS", "MSCI",
    "MSFT", "MSI", "MTB", "MTD", "MU", "NCLH", "NEM", "NEE", "NI", "NKE",
    "NKTR", "NLOK", "NLY", "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE",
    "NVDA", "NVR", "NWL", "NWS", "NXPI", "O", "ODFL", "OGN", "OKE", "OMC",
    "ON", "ORCL", "ORLY", "OXY", "PANW", "PAYC", "PAYX", "PCAR", "PCG", "PEG",
    "PEP", "PFE", "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PKI", "PLD",
    "PM", "PNC", "PNR", "PNW", "POOL", "PPG", "PPL", "PRU", "PSA", "PSX",
    "PTC", "PTCT", "PVH", "PWR", "PXD", "PYPL", "QCOM", "QQQ", "QRTEA", "R",
    "RCL", "RE", "REG", "REGN", "RF", "RHI", "RJF", "RL", "RMD", "ROK",
    "ROL", "ROP", "ROST", "RRC", "RSG", "RTX", "SBAC", "SBUX", "SHW", "SJM",
    "SLB", "SLGN", "SMH", "SNOW", "SNPS", "SO", "SOXX", "SPG", "SPLK", "SPY",
    "SQQQ", "SRE", "STE", "STLD", "STT", "STX", "STZ", "SWK", "SWKS", "SYF",
    "SYK", "SYY", "T", "TAP", "TDG", "TDY", "TECH", "TEL", "TER", "TFC",
    "TFX", "TGT", "TJX", "TLT", "TMF", "TMO", "TMUS", "TPR", "TROW", "TRV",
    "TSCO", "TSLA", "TSN", "TT", "TTWO", "TXN", "TXT", "TYL", "UAL", "UDR",
    "UHS", "ULTA", "UNH", "UNP", "UPS", "UPST", "UUP", "UVXY", "V", "VFC",
    "VICI", "VLO", "VMC", "VNQ", "VRSK", "VRSN", "VRTX", "VTR", "VZ", "WAB",
    "WAT", "WBA", "WDC", "WELL", "WFC", "WM", "WMB", "WMT", "WRB", "WST",
    "WTW", "WY", "XEL", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE",
    "XLU", "XLV", "XLY", "XOM", "XOP", "XRT", "XSOE", "YUM", "ZBH", "ZBRA",
    "ZION", "ZTS",
    # ETFs with liquid weekly options
    "DIA", "EWJ", "EWZ", "FXI", "GDX", "GDXJ", "GLD", "HYG", "IWM", "IYR",
    "KWEB", "LQD", "MCHI", "MSOS", "OIH", "QQQ", "SLV", "SMH", "SPY", "TBT",
    "TLT", "TNA", "TZA", "USO", "VXX", "XBI",
]

# deduplicate while preserving order
_seen: set[str] = set()
DEFAULT_TICKERS = [t for t in DEFAULT_TICKERS if not (_seen.add(t) or t in _seen)]  # type: ignore[misc]

DEFAULT_START = date(2018, 1, 1)
BATCH_SIZE    = 8   # tickers per Athena query (settlement JOIN makes queries heavier)


# ── Incremental helper ────────────────────────────────────────────────────────

def _get_table_max_date() -> Optional[date]:
    """Return the latest entry_date in silver.option_legs_settled, or None."""
    try:
        df = wr.athena.read_sql_query(
            sql=f'SELECT MAX(entry_date) AS max_td FROM "{LEGS_DB}"."{LEGS_TABLE}"',
            database=LEGS_DB,
            workgroup="dev-v3",
            s3_output="s3://athena-919061006621/",
        )
        val = df.iloc[0, 0] if not df.empty else None
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return pd.to_datetime(val).date()
    except Exception:
        return None


# ── Main run loop ─────────────────────────────────────────────────────────────

def run(
    tickers: list[str],
    start: date,
    end: date,
    batch_size: int = BATCH_SIZE,
    write_mode: str = "append",
) -> int:
    """Process tickers in batches; return total rows written."""
    total_rows = 0

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        batch_num   = i // batch_size + 1
        total_batches = (len(tickers) + batch_size - 1) // batch_size
        print(f"\n[batch {batch_num}/{total_batches}] {batch}  ({start} → {end})")

        df = fetch_option_legs_batch(batch, start, end)
        if df.empty:
            print("  → no data returned")
            continue

        n_calls = (df["cp"] == "C").sum()
        n_puts  = (df["cp"] == "P").sum()
        n_exp   = (df["expiry"] <= end).sum()
        n_no_settle = (df["last_expiry"] == 0).sum()
        print(f"  → {len(df):,} legs  "
              f"({n_calls:,} calls, {n_puts:,} puts)  "
              f"| {n_no_settle:,} expired worthless / no last price")

        write_option_legs(df, mode=write_mode)
        total_rows += len(df)

    return total_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build/refresh silver.option_legs_settled (~10 DTE option legs with settlement)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Tickers to process (default: full 987-ticker universe)",
    )
    parser.add_argument(
        "--ticker-file", type=str, default=None,
        help="Path to file with one ticker per line (overrides --tickers and default list)",
    )
    parser.add_argument(
        "--start", type=str, default=None,
        help="Start date YYYY-MM-DD (default: 2018-01-01 for full; table max+1d for incremental)",
    )
    parser.add_argument(
        "--end", type=str, default=None,
        help="End date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--mode", choices=["full", "incremental"], default="incremental",
        help=(
            "full = backfill from --start (overwrites matching partitions); "
            "incremental = only dates after table max_date (default)"
        ),
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help=f"Tickers per Athena query (default: {BATCH_SIZE})",
    )
    args = parser.parse_args()

    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [line.strip() for line in f if line.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        tickers = DEFAULT_TICKERS

    end = date.fromisoformat(args.end) if args.end else date.today()

    if args.mode == "incremental" and args.start is None:
        max_date = _get_table_max_date()
        if max_date is not None:
            start = max_date + timedelta(days=1)
            print(f"[incremental] resuming from {start}  (table max_date = {max_date})")
        else:
            start = DEFAULT_START
            print(f"[incremental] table empty/missing — full backfill from {start}")
    else:
        start = date.fromisoformat(args.start) if args.start else DEFAULT_START

    if start > end:
        print(f"Nothing to do: start {start} > end {end}")
        return

    write_mode = "overwrite_partitions" if args.mode == "full" else "append"

    print(f"\nOption legs settled build")
    print(f"  tickers   : {len(tickers)} tickers")
    print(f"  date range: {start} → {end}")
    print(f"  mode      : {args.mode}  (write_mode={write_mode})")
    print(f"  batch size: {args.batch_size}")

    total = run(tickers, start, end, batch_size=args.batch_size, write_mode=write_mode)
    print(f"\nDone. Total rows written: {total:,}")


if __name__ == "__main__":
    main()
