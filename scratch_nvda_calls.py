import os, asyncio, csv, sys, traceback, datetime as dt
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.athena_lib import athena

ENTRY_DATE = "2024-01-08"
EXIT_DATE = "2024-01-19"
NVDA_CLOSE_119_UNADJ = 594.91  # Tradier split-adj 59.491 x 10 (10:1 split Jun 2024)
OUT = "data/nvda_calls_all_expirations_exit_2024-01-19.csv"


def occ_symbol(expiry: str, strike: float) -> str:
    d = dt.date.fromisoformat(expiry)
    yymmdd = d.strftime("%y%m%d")
    millis = int(round(strike * 1000))
    return f"NVDA{yymmdd}C{millis:08d}"


def load_athena():
    # entry-side candidates (traded on 1/8) + EOD delta
    cand = athena("""
        SELECT CAST(expiry AS DATE) AS expiry, strike, ROUND(AVG(delta),4) AS delta_eod_1_8
        FROM silver.options_daily_v3
        WHERE ticker='NVDA' AND cp='C'
          AND trade_date >= TIMESTAMP '2024-01-08 00:00:00'
          AND trade_date <  TIMESTAMP '2024-01-09 00:00:00'
          AND volume > 0
        GROUP BY expiry, strike
    """)
    # exit-side marks on 1/19 (fallback close source)
    marks = athena("""
        SELECT CAST(expiry AS DATE) AS expiry, strike,
               ROUND(AVG((bid+ask)/2),3) AS mid_1_19
        FROM silver.options_daily_v3
        WHERE ticker='NVDA' AND cp='C'
          AND trade_date >= TIMESTAMP '2024-01-19 00:00:00'
          AND trade_date <  TIMESTAMP '2024-01-20 00:00:00'
          AND bid > 0 AND ask > 0
        GROUP BY expiry, strike
    """)
    cand["expiry"] = cand["expiry"].astype(str)
    marks["expiry"] = marks["expiry"].astype(str)
    cand["strike"] = cand["strike"].astype(float)
    marks["strike"] = marks["strike"].astype(float)
    mark_map = {(r.expiry, r.strike): r.mid_1_19 for r in marks.itertuples()}
    return cand, mark_map


async def fetch_one(client, sem, expiry, strike):
    sym = occ_symbol(expiry, strike)
    import random
    r = None
    for attempt in range(7):
        async with sem:
            try:
                r = await client.get_json("/markets/history", {
                    "symbol": sym, "interval": "daily",
                    "start": ENTRY_DATE, "end": EXIT_DATE,
                })
                break
            except Exception as e:
                if attempt < 6:
                    await asyncio.sleep(min(1.5 * (attempt + 1), 8) + random.random())
                    continue
                return expiry, strike, None, None, f"err:{type(e).__name__}"
    hist = (r or {}).get("history")
    if not hist or hist == "null":
        return expiry, strike, None, None, "no_history"
    days = hist.get("day")
    if days is None:
        return expiry, strike, None, None, "no_days"
    if isinstance(days, dict):
        days = [days]
    by_date = {d["date"]: d for d in days}
    o = by_date.get(ENTRY_DATE)
    x = by_date.get(EXIT_DATE)
    open_18 = o["open"] if o else None
    close_19 = x["close"] if x else None
    return expiry, strike, open_18, close_19, "ok"


async def main():
    key = os.environ["TRADIER_API_KEY"]
    cand, mark_map = load_athena()
    print(f"Candidates (traded 1/8): {len(cand)} | 1/19 Athena marks: {len(mark_map)}")

    sem = asyncio.Semaphore(4)
    async with TradierClient(api_key=key) as client:
        tasks = [fetch_one(client, sem, r.expiry, r.strike) for r in cand.itertuples()]
        results = await asyncio.gather(*tasks)

    from collections import Counter
    err_types = Counter(s for *_, s in results if s.startswith("err"))
    if err_types:
        print("Error types:", dict(err_types))

    delta_map = {(r.expiry, r.strike): r.delta_eod_1_8 for r in cand.itertuples()}

    rows, skipped = [], {"no_open": 0, "no_close": 0, "err": 0}
    src_counts = {"tradier_close": 0, "athena_mid": 0, "intrinsic": 0}
    for expiry, strike, open_18, close_19, status in results:
        if status.startswith("err"):
            skipped["err"] += 1
            continue
        if open_18 is None or open_18 <= 0:
            skipped["no_open"] += 1
            continue
        # exit mark on 1/19
        if close_19 is not None and close_19 > 0:
            close_val, src = close_19, "tradier_close"
        elif mark_map.get((expiry, strike)) is not None:
            close_val, src = mark_map[(expiry, strike)], "athena_mid"
        elif expiry == EXIT_DATE:
            close_val, src = max(0.0, NVDA_CLOSE_119_UNADJ - strike), "intrinsic"
        else:
            skipped["no_close"] += 1
            continue
        src_counts[src] += 1
        profit = round((close_val - open_18) * 100, 2)
        ret = round((close_val - open_18) / open_18 * 100, 1)
        rows.append({
            "strike": strike,
            "expiration": expiry,
            "open_1_8": round(open_18, 2),
            "delta_eod_1_8": delta_map.get((expiry, strike)),
            "close_1_19": round(close_val, 2),
            "profit": profit,
            "return_pct": ret,
        })

    df = pd.DataFrame(rows).sort_values(["expiration", "strike"]).reset_index(drop=True)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {len(df)} rows to {OUT}")
    print("Exit-price source:", src_counts)
    print("Skipped:", skipped)
    print("\nRows per expiration:")
    print(df.groupby("expiration").size().to_string())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
