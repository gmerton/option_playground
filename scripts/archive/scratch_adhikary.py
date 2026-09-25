"""Adhikary_Options.csv analysis: per row, sweep all strikes that traded on the
entry date, enter at the Tradier open, exit at intrinsic value on expiration.
Underlying price at expiration is derived from the expiry-day chain via put-call
parity (split-proof, self-consistent with the contract's strike scale)."""
import os, asyncio, sys, traceback, datetime as dt, random
from collections import Counter
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.athena_lib import athena

OUT = "data/studies/Adhikary/Adhikary_results.csv"

# (number, entry_date, csv_ticker, athena_ticker, occ_root, expiry, cp)
ROWS = [
 (1, "2024-01-08","NVDA","NVDA","NVDA","2024-01-19","C"),
 (2, "2024-01-19","SMCI","SMCI","SMCI","2024-01-26","C"),
 (3, "2024-02-08","MSTR","MSTR","MSTR","2024-02-16","C"),
 (4, "2024-02-08","ARM","ARM","ARM","2024-02-16","C"),
 (5, "2024-02-09","COIN","COIN","COIN","2024-03-15","C"),
 (6, "2024-02-16","SMCI","SMCI","SMCI","2024-02-16","P"),
 (7, "2024-03-01","GLD","GLD","GLD","2024-04-19","C"),
 (8, "2024-03-08","NVDA","NVDA","NVDA","2024-03-08","P"),
 (9, "2024-06-11","AAPL","AAPL","AAPL","2024-06-21","C"),
 (10,"2024-07-11","BRKB","BRK","BRKB","2024-08-16","C"),
 (11,"2024-07-11","IWM","IWM","IWM","2024-07-19","C"),
 (12,"2024-08-29","GEV","GEV","GEV","2024-09-20","C"),
 (13,"2024-09-11","APP","APP","APP","2024-09-20","C"),
 (14,"2024-09-19","BABA","BABA","BABA","2024-10-18","C"),
 (15,"2024-10-11","MSTR","MSTR","MSTR","2024-10-18","C"),
 (16,"2024-10-22","DJT","DJT","DJT","2024-11-22","C"),
 (17,"2024-11-05","PLTR","PLTR","PLTR","2024-12-20","C"),
 (18,"2024-11-05","TSLA","TSLA","TSLA","2024-11-22","C"),
 (20,"2024-11-08","COST","COST","COST","2024-11-15","C"),
]


def occ_symbol(root, expiry, cp, strike):
    yymmdd = dt.date.fromisoformat(expiry).strftime("%y%m%d")
    return f"{root}{yymmdd}{cp}{int(round(strike*1000)):08d}"


def get_entry_candidates():
    conds = " OR ".join(
        f"(ticker='{at}' AND cp='{cp}' AND expiry=DATE '{e}' AND trade_date=DATE '{ed}')"
        for (_n, ed, _ct, at, _r, e, cp) in ROWS)
    sql = f"""
      SELECT ticker AS athena_ticker, cp, CAST(expiry AS DATE) AS expiry,
             CAST(trade_date AS DATE) AS entry_date, strike,
             ROUND(AVG(delta),4) AS delta_entry
      FROM silver.options_daily_v3
      WHERE ({conds}) AND volume > 0
      GROUP BY ticker, cp, expiry, trade_date, strike
    """
    df = athena(sql)
    for c in ("expiry", "entry_date"):
        df[c] = df[c].astype(str)
    df["strike"] = df["strike"].astype(float)
    return df


# 10:1 splits in 2024; expirations BEFORE the split-adjusted trading date need x10
# to convert Tradier's (present-day, split-adjusted) close back to contract scale.
SPLITS = {"NVDA": ("2024-06-10", 10), "SMCI": ("2024-10-01", 10), "MSTR": ("2024-08-08", 10)}


def split_factor(csv_ticker, expiry):
    if csv_ticker in SPLITS:
        sdate, ratio = SPLITS[csv_ticker]
        if expiry < sdate:
            return ratio
    return 1


def underlying_symbol(csv_ticker):
    return "BRK.B" if csv_ticker == "BRKB" else csv_ticker


def parity_cross_check():
    """Sanity cross-check: S = median(K + C_last - P_last) using last-trade prices
    (last ~= intrinsic at expiration, works for any moneyness, no overlap problem)."""
    pairs = sorted({(at, e) for (_n, _ed, _ct, at, _r, e, _cp) in ROWS})
    conds = " OR ".join(f"(ticker='{at}' AND expiry=DATE '{e}' AND trade_date=DATE '{e}')"
                        for at, e in pairs)
    sql = f"""
      SELECT ticker AS athena_ticker, CAST(expiry AS DATE) AS expiry, strike, cp,
             ROUND(AVG(last),4) AS last
      FROM silver.options_daily_v3
      WHERE ({conds}) AND last > 0
      GROUP BY ticker, expiry, strike, cp
    """
    df = athena(sql)
    df["expiry"] = df["expiry"].astype(str)
    df["strike"] = df["strike"].astype(float)
    out = {}
    for (at, e), g in df.groupby(["athena_ticker", "expiry"]):
        piv = g.pivot_table(index="strike", columns="cp", values="last")
        if {"C", "P"}.issubset(piv.columns):
            both = piv.dropna(subset=["C", "P"])
            if len(both) >= 2:
                s_est = both.index.values + both["C"].values - both["P"].values
                out[(at, e)] = round(float(pd.Series(s_est).median()), 3)
    return out


async def fetch_underlying_close(client, sem, sym, date):
    async with sem:
        try:
            r = await client.get_json("/markets/history", {
                "symbol": sym, "interval": "daily", "start": date, "end": date})
        except Exception:
            return None
    hist = (r or {}).get("history")
    if not hist or hist == "null":
        return None
    day = hist.get("day")
    if isinstance(day, list):
        day = day[0] if day else None
    return day["close"] if day else None


async def fetch_open(client, sem, root, expiry, cp, strike, entry_date):
    sym = occ_symbol(root, expiry, cp, strike)
    for attempt in range(7):
        async with sem:
            try:
                r = await client.get_json("/markets/history", {
                    "symbol": sym, "interval": "daily",
                    "start": entry_date, "end": entry_date})
                break
            except Exception as e:
                if attempt < 6:
                    await asyncio.sleep(min(1.5*(attempt+1), 8) + random.random())
                    continue
                return strike, None, f"err:{type(e).__name__}"
    hist = (r or {}).get("history")
    if not hist or hist == "null":
        return strike, None, "no_hist"
    days = hist.get("day")
    if days is None:
        return strike, None, "no_day"
    if isinstance(days, dict):
        days = [days]
    by = {d["date"]: d for d in days}
    o = by.get(entry_date)
    return strike, (o["open"] if o else None), "ok"


async def main():
    key = os.environ["TRADIER_API_KEY"]
    print("Loading Athena entry candidates + parity cross-check...")
    cand = get_entry_candidates()
    parity = parity_cross_check()

    # delta lookup
    dmap = {(r.athena_ticker, r.cp, r.expiry, r.entry_date, r.strike): r.delta_entry
            for r in cand.itertuples()}

    sem = asyncio.Semaphore(4)
    out_rows, errs = [], Counter()
    async with TradierClient(api_key=key) as client:
        # primary underlying-at-expiration: Tradier close x split factor
        und_pairs = sorted({(ct, at, e) for (_n, _ed, ct, at, _r, e, _cp) in ROWS})
        und_res = await asyncio.gather(*[
            fetch_underlying_close(client, sem, underlying_symbol(ct), e)
            for (ct, at, e) in und_pairs])
        s_map = {}
        print("Underlying-at-expiration  (Tradier_close x split -> S | parity check):")
        for (ct, at, e), close_adj in zip(und_pairs, und_res):
            f = split_factor(ct, e)
            s_trad = round(close_adj * f, 3) if close_adj is not None else None
            s_par = parity.get((at, e))
            S = s_trad if s_trad is not None else s_par
            s_map[(at, e)] = S
            flag = ""
            if s_trad and s_par and abs(s_trad - s_par) / s_trad > 0.02:
                flag = "  <-- >2% vs parity, check"
            print(f"   {ct:5s} {e}: Tradier {close_adj}x{f}={s_trad} | parity {s_par} -> S={S}{flag}")

        for (num, ed, ct, at, root, exp, cp) in ROWS:
            sub = cand[(cand.athena_ticker == at) & (cand.cp == cp) &
                       (cand.expiry == exp) & (cand.entry_date == ed)]
            S = s_map.get((at, exp))
            tasks = [fetch_open(client, sem, root, exp, cp, float(r.strike), ed)
                     for r in sub.itertuples()]
            res = await asyncio.gather(*tasks)
            n_ok = 0
            for strike, open_px, status in res:
                if status.startswith("err"):
                    errs[status] += 1
                if open_px is None or open_px <= 0 or S is None:
                    continue
                exit_val = max(0.0, S - strike) if cp == "C" else max(0.0, strike - S)
                profit = round((exit_val - open_px) * 100, 2)
                ret = round((exit_val - open_px) / open_px * 100, 1)
                out_rows.append({
                    "number": num, "ticker": ct, "cp": cp,
                    "entry_date": ed, "expiration": exp, "strike": strike,
                    "open_entry": round(open_px, 2),
                    "delta_entry": dmap.get((at, cp, exp, ed, strike)),
                    "underlying_at_exp": S,
                    "exit_intrinsic": round(exit_val, 2),
                    "profit": profit, "return_pct": ret,
                })
                n_ok += 1
            print(f"  row {num:2d} {ct:5s} {cp} {ed}->{exp}: {n_ok}/{len(sub)} priced (S={S})")

    df = pd.DataFrame(out_rows).sort_values(["number", "strike"]).reset_index(drop=True)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {len(df)} rows to {OUT}")
    if errs:
        print("Tradier errors:", dict(errs))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
