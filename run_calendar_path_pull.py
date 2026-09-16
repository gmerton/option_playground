#!/usr/bin/env python3
"""
Step 1/3 of the CALENDAR path study (2026-09-15, Gabe: "a study similar to the one we did for long straddles, but
for double calendars... a good starting place is single calendars"). Mirrors run_straddle_recenter_pull.py.

Pulls, per ticker-year, every PUT row of options_daily_v3 with DTE <= MAX_DTE whose strike is within +/-K_WIN of that
day's close (temp Glue table of daily strike windows joined on ticker + trade_date), plus the daily closes. One
dataset serves entry selection AND the daily path of every leg, so re-centering / rolling variants can price the
replacement legs on the same day. bid/ask end mid-July 2026 (v3 note), so the window stops 2026-07-10.

Universe = the index ETFs + the book's calendar names. Writes data/cache/calendar_path/closes.parquet and
chain_<TICKER>_<YEAR>.parquet.
Usage: AWS_PROFILE=clarinut-gmerton TRADIER_API_KEY=... PYTHONPATH=src python run_calendar_path_pull.py [--cp C --tickers IWM SPY QQQ]
(--cp C writes chainC_<T>_<YEAR>.parquet: the CALL side; --cp PC pulls both sides in one query; --universe-file / --kwin for the stock step)
"""
from __future__ import annotations
import asyncio, os, sys, time, uuid
from datetime import date, timedelta
from pathlib import Path
import pandas as pd, awswrangler as wr
sys.path.insert(0, "src")
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

TICKERS = ["SPY", "QQQ", "IWM", "XLU", "XLV", "XLP", "XLE", "XLF", "GLD", "TLT"]
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--cp", default="P", choices=["P", "C", "PC"]); _ap.add_argument("--tickers", nargs="*", default=None)
_ap.add_argument("--universe-file", default=None); _ap.add_argument("--kwin", type=float, default=None)
_ap.add_argument("--mode", default="window", choices=["window", "delta"])   # delta = |delta| 0.05..0.95, no price window (split-proof)
_ap.add_argument("--max-dte", type=int, default=40); _ap.add_argument("--outdir", default="data/cache/calendar_path")   # long-dated study: --max-dte 85 --outdir data/cache/calendar_path_long
_A = _ap.parse_args(); CP = _A.cp
if _A.tickers: TICKERS = [t.upper() for t in _A.tickers]
if _A.universe_file: TICKERS = [l.strip().upper() for l in open(_A.universe_file) if l.strip()]
START, END = date(2018, 11, 1), date(2026, 7, 10)
K_WIN, MAX_DTE = 0.06, _A.max_dte
ALIASES = {"META": ["FB", "META"]}          # ticker renames inside the window
MODE = _A.mode
if _A.kwin: K_WIN = _A.kwin
OUT = Path(_A.outdir); OUT.mkdir(parents=True, exist_ok=True)
_MAIN = Path("data/cache/calendar_path")
if OUT != _MAIN:      # a second cache (longer DTE) reuses the main cache's closes / earnings
    import shutil
    for _f in ("closes.parquet", "earnings.parquet"):
        if (_MAIN / _f).exists() and not (OUT / _f).exists(): shutil.copy(_MAIN / _f, OUT / _f)


async def closes(only: list[str] | None = None) -> pd.DataFrame:
    frames = []
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        for t in (only if only is not None else TICKERS):
            y = START.year
            while y <= END.year:
                d = await get_daily_history(t, max(START, date(y, 1, 1)), min(END, date(y, 12, 31)), client=c)
                if d is not None and len(d):
                    d = d.reset_index() if "date" not in d.columns else d
                    d = d.rename(columns={"index": "date"})[["date", "close"]].assign(ticker=t); frames.append(d)
                y += 1
    df = pd.concat(frames, ignore_index=True); df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.drop_duplicates(["ticker", "date"]).sort_values(["ticker", "date"])


def main() -> int:
    cp = OUT / "closes.parquet"
    C = pd.read_parquet(cp) if cp.exists() else pd.DataFrame(columns=["date", "close", "ticker"])
    missing = [t for t in TICKERS if t not in set(C.ticker)]
    if missing:                                   # the closes file only had the first universe; fetch the rest
        C = pd.concat([C, asyncio.run(closes(missing))], ignore_index=True).drop_duplicates(["ticker", "date"]); C.to_parquet(cp, index=False)
    C["date"] = pd.to_datetime(C.date).dt.date
    print(f"closes: {len(C):,} rows, {C.ticker.nunique()} tickers, {C.date.min()} -> {C.date.max()}", flush=True)
    _ensure_glue_db(DB)
    C["k_lo"], C["k_hi"] = C.close * (1 - K_WIN), C.close * (1 + K_WIN); C["yr"] = pd.to_datetime(C.date).dt.year
    for t in TICKERS:
        years = sorted(C[C.ticker == t].yr.unique()) if MODE == "window" else list(range(START.year, END.year + 1))
        for yr in years:
            w = C[(C.ticker == t) & (C.yr == yr)] if MODE == "window" else None
            out = OUT / (f"chain_{t}_{yr}.parquet" if CP in ("P", "PC") else f"chainC_{t}_{yr}.parquet")   # PC: puts -> chain_, calls -> chainC_
            outC = OUT / f"chainC_{t}_{yr}.parquet"
            if CP == "PC" and out.exists() and outC.exists(): continue
            if CP != "PC" and out.exists(): continue
            t0 = time.time(); name = f"tmp_calwin_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
            names = ALIASES.get(t, [t]); tick_sql = "o.ticker IN (" + ",".join(f"'{x}'" for x in names) + ")"
            cp_sql = "IN ('P','C')" if CP == "PC" else f"= '{CP}'"
            if MODE == "delta":          # split-proof: the table's strikes are UNADJUSTED (NVDA 2020 ~314, 2023 ~363, 2025 ~108)
                d = athena(f"""
                SELECT o.trade_date, o.expiry, o.strike, o.cp, o.bid, o.ask, o.delta, o.bid_iv, o.ask_iv, o.open_interest
                FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
                WHERE {tick_sql} AND o.cp {cp_sql} AND o.trade_date BETWEEN DATE '{yr}-01-01' AND DATE '{yr}-12-31'
                  AND date_diff('day', o.trade_date, o.expiry) BETWEEN 0 AND {MAX_DTE} AND abs(o.delta) BETWEEN 0.05 AND 0.95""")
            else:
                tw = w[["ticker", "date", "k_lo", "k_hi"]].rename(columns={"date": "trade_date"})
                wr.s3.to_parquet(df=tw, path=path, dataset=True, database=DB, table=name, compression="snappy", mode="overwrite",
                                 dtype={"ticker": "string", "trade_date": "date", "k_lo": "double", "k_hi": "double"})
                try:
                    d = athena(f"""
                    SELECT o.trade_date, o.expiry, o.strike, o.cp, o.bid, o.ask, o.delta, o.bid_iv, o.ask_iv, o.open_interest
                    FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" w
                      ON o.ticker = w.ticker AND o.trade_date = w.trade_date AND o.strike BETWEEN w.k_lo AND w.k_hi
                    WHERE o.ticker = '{t}' AND o.cp {cp_sql} AND o.trade_date BETWEEN DATE '{yr}-01-01' AND DATE '{yr}-12-31'
                      AND date_diff('day', o.trade_date, o.expiry) BETWEEN 0 AND {MAX_DTE}""")
                finally:
                    _drop_temp_targets_table(DB, name, path)
            d.insert(0, "ticker", t)
            if CP == "PC":
                d[d.cp == "P"].drop(columns="cp").to_parquet(out, index=False); d[d.cp == "C"].drop(columns="cp").to_parquet(outC, index=False)
            else:
                d.drop(columns="cp").to_parquet(out, index=False)
            print(f"{t} {yr}: {len(d):,} rows, {time.time() - t0:.0f}s", flush=True)
    if MODE == "delta":
        # spot on the chain's own basis: S = K + C - P at the strike with the smallest |C - P| on the nearest expiry 5..40 DTE
        rows = []
        for t in TICKERS:
            for yr in range(START.year, END.year + 1):
                fp, fc = OUT / f"chain_{t}_{yr}.parquet", OUT / f"chainC_{t}_{yr}.parquet"
                if not (fp.exists() and fc.exists()): continue
                P_, C_ = pd.read_parquet(fp), pd.read_parquet(fc)
                for df_ in (P_, C_):
                    df_["mid"] = (df_.bid + df_.ask) / 2
                m = P_.merge(C_, on=["trade_date", "expiry", "strike"], suffixes=("_p", "_c"))
                m = m[(m.bid_p > 0) & (m.bid_c > 0)]
                m["dte"] = (pd.to_datetime(m.expiry) - pd.to_datetime(m.trade_date)).dt.days; m = m[(m.dte >= 5) & (m.dte <= 40)]
                if m.empty: continue
                m["gap"] = (m.mid_c - m.mid_p).abs()
                idx = m.groupby("trade_date").apply(lambda g: g.sort_values(["dte", "gap"]).index[0], include_groups=False)
                best = m.loc[idx.values]
                rows.append(pd.DataFrame({"ticker": t, "date": pd.to_datetime(best.trade_date).dt.date, "close": (best.strike + best.mid_c - best.mid_p).values}))
        if rows:
            S_ = pd.concat(rows, ignore_index=True).drop_duplicates(["ticker", "date"]).sort_values(["ticker", "date"])
            S_.to_parquet(OUT / "spot_chain.parquet", index=False); print(f"spot_chain: {len(S_):,} rows for {S_.ticker.nunique()} tickers", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
