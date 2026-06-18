"""QA pass on Adhikary_Options.csv: verify each trade was directionally profitable.

No strikes in the source CSV, so we check the UNDERLYING move over the holding
window (entry date -> expiration). For a directional swing trade expressed via
long ATM/slightly-OTM options:
  - Call profits if the underlying rises; Put profits if it falls.
We report entry close, expiration close, and the MAX FAVORABLE EXCURSION (MFE)
during the hold (highest high for calls / lowest low for puts) -- what a swing
trader who exits into strength actually captures. Entry and exp prices both come
from the same Tradier (split-adjusted) daily series, so splits cancel.
"""
import os, asyncio, csv, datetime as dt
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient

SRC = "data/studies/Adhikary/Adhikary_Options.csv"
OUT = "data/studies/Adhikary/Adhikary_qa_summary.csv"

# csv ticker -> Tradier underlying symbol
# csv ticker -> Tradier underlying symbol.
#  BRKB: Tradier wants the slash form.
#  BTC:  Adhikary's "BTC" = a bullish Bitcoin bet. Tradier's "BTC" ticker is the
#        Grayscale Bitcoin Mini Trust ETF whose historical series is unreliable
#        (6.76->44 in 2wks), so we proxy Bitcoin direction via IBIT (iShares spot BTC).
SYMAP = {"BRKB": "BRK/B", "BTC": "IBIT"}


def parse_date(s):
    return dt.datetime.strptime(s, "%m/%d/%y").date().isoformat()


def load_rows():
    rows = []
    with open(SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "number": int(r["Number"]),
                "ticker": r["Ticker"].strip(),
                "entry": parse_date(r["Entry Date"]),
                "expiry": parse_date(r["Expiration"]),
                "cp": r["Call / Put"].strip(),
            })
    return rows


async def fetch_hist(client, sem, sym, start, end):
    async with sem:
        try:
            r = await client.get_json("/markets/history", {
                "symbol": sym, "interval": "daily", "start": start, "end": end})
        except Exception as e:
            return None, f"err:{type(e).__name__}"
    hist = (r or {}).get("history")
    if not hist or hist == "null":
        return None, "no_hist"
    days = hist.get("day")
    if isinstance(days, dict):
        days = [days]
    if not days:
        return None, "empty"
    return days, "ok"


async def main():
    key = os.environ["TRADIER_API_KEY"]
    rows = load_rows()
    sem = asyncio.Semaphore(4)
    out = []
    async with TradierClient(api_key=key) as client:
        tasks = []
        for row in rows:
            sym = SYMAP.get(row["ticker"], row["ticker"])
            # same-day entry/expiry trades (e.g. 0DTE) still need a >=1 day window
            end = row["expiry"]
            tasks.append(fetch_hist(client, sem, sym, row["entry"], end))
        results = await asyncio.gather(*tasks)

    for row, (days, status) in zip(rows, results):
        rec = {**row, "status": status}
        if status != "ok":
            out.append(rec)
            print(f"  row {row['number']:2d} {row['ticker']:5s} {row['cp']}: {status}")
            continue
        by = {d["date"]: d for d in days}
        entry_day = by.get(row["entry"]) or days[0]
        exp_day = by.get(row["expiry"]) or days[-1]
        entry_close = float(entry_day["close"])
        exp_close = float(exp_day["close"])
        highs = [float(d["high"]) for d in days]
        lows = [float(d["low"]) for d in days]
        if row["cp"] == "C":
            mfe_px = max(highs)
            dir_close = (exp_close - entry_close) / entry_close * 100
            dir_mfe = (mfe_px - entry_close) / entry_close * 100
        else:  # Put
            mfe_px = min(lows)
            dir_close = (entry_close - exp_close) / entry_close * 100
            dir_mfe = (entry_close - mfe_px) / entry_close * 100
        rec.update({
            "entry_close": round(entry_close, 2),
            "exp_close": round(exp_close, 2),
            "mfe_px": round(mfe_px, 2),
            "und_move_to_exp_%": round(dir_close, 1),
            "und_mfe_%": round(dir_mfe, 1),
            "bars": len(days),
            "profitable_dir": dir_mfe > 0 and dir_close > -100,  # had favorable excursion
        })
        out.append(rec)
        print(f"  row {row['number']:2d} {row['ticker']:5s} {row['cp']} "
              f"{row['entry']}->{row['expiry']}: "
              f"entry {entry_close:.2f} exp {exp_close:.2f} "
              f"| toExp {dir_close:+.1f}%  MFE {dir_mfe:+.1f}%")

    df = pd.DataFrame(out)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {len(df)} rows to {OUT}")
    ok = df[df["status"] == "ok"]
    if len(ok):
        fav = (ok["und_mfe_%"] > 0).sum()
        toexp_pos = (ok["und_move_to_exp_%"] > 0).sum()
        print(f"\nDirectional QA ({len(ok)} priced trades):")
        print(f"  Favorable excursion at some point (MFE>0): {fav}/{len(ok)}")
        print(f"  Still favorable at expiration (toExp>0):   {toexp_pos}/{len(ok)}")
        print(f"  Median MFE move:    {ok['und_mfe_%'].median():+.1f}%")
        print(f"  Median toExp move:  {ok['und_move_to_exp_%'].median():+.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
