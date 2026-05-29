"""DTE-ladder study for the Adhikary CALL setups, mirroring the NVDA multi-
expiration study: per setup, fix the window entry_date -> exit (the old
'Expiration' column), and sweep contracts across ALL expirations >= exit that
traded on the entry date. Enter at the Tradier open; mark at the exit-date close.

Output columns separate `exit` (fixed close date) from `expiration` (the
contract's own expiry, which varies = the DTE ladder).
"""
import os, asyncio, csv, sys, traceback, datetime as dt, random
from collections import Counter
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.athena_lib import athena

OUT = "data/studies/Adhikary/Adhikary_dte_ladder.csv"
COLS = ["number","ticker","cp","entry","exit","expiration","dte","hold_days",
        "strike","open_entry","delta_entry","value_at_exit","exit_src",
        "profit","return_pct"]

# (number, entry, athena_ticker, occ_root, exit_date)  -- calls only
ROWS = [
 (1, "2024-01-08","NVDA","NVDA","2024-01-19"),
 (2, "2024-01-19","SMCI","SMCI","2024-01-26"),
 (3, "2024-02-08","MSTR","MSTR","2024-02-16"),
 (4, "2024-02-08","ARM","ARM","2024-02-16"),
 (5, "2024-02-09","COIN","COIN","2024-03-15"),
 (7, "2024-03-01","GLD","GLD","2024-04-19"),
 (9, "2024-06-11","AAPL","AAPL","2024-06-21"),
 (10,"2024-07-11","BRK","BRKB","2024-08-16"),
 (11,"2024-07-11","IWM","IWM","2024-07-19"),
 (12,"2024-08-29","GEV","GEV","2024-09-20"),
 (13,"2024-09-11","APP","APP","2024-09-20"),
 (14,"2024-09-19","BABA","BABA","2024-10-18"),
 (15,"2024-10-11","MSTR","MSTR","2024-10-18"),
 (16,"2024-10-22","DJT","DJT","2024-11-22"),
 (17,"2024-11-05","PLTR","PLTR","2024-12-20"),
 (18,"2024-11-05","TSLA","TSLA","2024-11-22"),
 (20,"2024-11-08","COST","COST","2024-11-15"),
]


def occ_symbol(root, expiry, strike):
    yymmdd = dt.date.fromisoformat(expiry).strftime("%y%m%d")
    return f"{root}{yymmdd}C{int(round(strike*1000)):08d}"


def days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def load_entry_candidates():
    conds = " OR ".join(
        f"(ticker='{at}' AND trade_date=DATE '{ed}' AND expiry>=DATE '{xd}')"
        for (_n, ed, at, _r, xd) in ROWS)
    df = athena(f"""
      SELECT ticker AS athtkr, CAST(trade_date AS DATE) AS entry,
             CAST(expiry AS DATE) AS expiration, strike, ROUND(AVG(delta),4) AS delta_entry
      FROM silver.options_daily_v3
      WHERE cp='C' AND volume>0 AND ({conds})
      GROUP BY ticker, trade_date, expiry, strike
    """)
    for c in ("entry", "expiration"):
        df[c] = df[c].astype(str)
    df["strike"] = df["strike"].astype(float)
    return df


def load_exit_marks():
    conds = " OR ".join(
        f"(ticker='{at}' AND trade_date=DATE '{xd}')" for (_n, _ed, at, _r, xd) in ROWS)
    df = athena(f"""
      SELECT ticker AS athtkr, CAST(trade_date AS DATE) AS exitd,
             CAST(expiry AS DATE) AS expiration, strike,
             ROUND(AVG((bid+ask)/2),3) AS mid
      FROM silver.options_daily_v3
      WHERE cp='C' AND bid>0 AND ask>0 AND ({conds})
      GROUP BY ticker, trade_date, expiry, strike
    """)
    for c in ("exitd", "expiration"):
        df[c] = df[c].astype(str)
    df["strike"] = df["strike"].astype(float)
    return {(r.athtkr, r.exitd, r.expiration, r.strike): r.mid for r in df.itertuples()}


async def fetch_oc(client, sem, root, expiration, strike, entry, exitd):
    sym = occ_symbol(root, expiration, strike)
    for attempt in range(7):
        async with sem:
            try:
                r = await client.get_json("/markets/history", {
                    "symbol": sym, "interval": "daily", "start": entry, "end": exitd})
                break
            except Exception as e:
                if attempt < 6:
                    await asyncio.sleep(min(1.5*(attempt+1), 8) + random.random())
                    continue
                return strike, expiration, None, None, f"err:{type(e).__name__}"
    hist = (r or {}).get("history")
    if not hist or hist == "null":
        return strike, expiration, None, None, "no_hist"
    d = hist.get("day")
    if d is None:
        return strike, expiration, None, None, "no_day"
    if isinstance(d, dict):
        d = [d]
    by = {x["date"]: x for x in d}
    o = by.get(entry)
    x = by.get(exitd)
    return strike, expiration, (o["open"] if o else None), (x["close"] if x else None), "ok"


async def main():
    key = os.environ["TRADIER_API_KEY"]
    print("Loading Athena entry candidates + exit marks...", flush=True)
    cand = load_entry_candidates()
    marks = load_exit_marks()
    dmap = {(r.athtkr, r.entry, r.expiration, r.strike): r.delta_entry for r in cand.itertuples()}
    print(f"Entry candidates: {len(cand)} | exit marks: {len(marks)}", flush=True)

    with open(OUT, "w", newline="") as f:
        csv.DictWriter(f, fieldnames=COLS).writeheader()

    sem = asyncio.Semaphore(4)
    grand, errs = 0, Counter()
    async with TradierClient(api_key=key) as client:
        for (num, ed, at, root, xd) in ROWS:
            sub = cand[(cand["athtkr"] == at) & (cand["entry"] == ed)]
            res = await asyncio.gather(*[
                fetch_oc(client, sem, root, r.expiration, float(r.strike), ed, xd)
                for r in sub.itertuples()])
            out_rows = []
            for strike, expiration, open_px, close_px, status in res:
                if status.startswith("err"):
                    errs[status] += 1
                if open_px is None or open_px <= 0:
                    continue
                if close_px is not None and close_px > 0:
                    val, src = close_px, "tradier_close"
                elif marks.get((at, xd, expiration, strike)) is not None:
                    val, src = marks[(at, xd, expiration, strike)], "athena_mid"
                else:
                    continue
                out_rows.append({
                    "number": num, "ticker": (root if root != "BRKB" else "BRKB"),
                    "cp": "C", "entry": ed, "exit": xd, "expiration": expiration,
                    "dte": days(ed, expiration), "hold_days": days(ed, xd),
                    "strike": strike, "open_entry": round(open_px, 2),
                    "delta_entry": dmap.get((at, ed, expiration, strike)),
                    "value_at_exit": round(val, 2), "exit_src": src,
                    "profit": round((val - open_px) * 100, 2),
                    "return_pct": round((val - open_px) / open_px * 100, 1),
                })
            with open(OUT, "a", newline="") as f:
                csv.DictWriter(f, fieldnames=COLS).writerows(out_rows)
            grand += len(out_rows)
            nexp = sub["expiration"].nunique()
            print(f"  row {num:2d} {root:5s} {ed}->{xd}: {len(out_rows):4d} priced "
                  f"across {nexp} expirations  (running total {grand})", flush=True)

    print(f"\nDONE. Wrote {grand} rows to {OUT}", flush=True)
    if errs:
        print("Tradier errors:", dict(errs), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
