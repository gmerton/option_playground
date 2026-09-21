#!/usr/bin/env python3
"""
Is earnings volatility overpriced? (the oquants "sell the event" claim)

oquants writes condors / calendars into an earnings print on the view that the market overprices the
move -- selectively, not blindly. Our only prior evidence on that was the tastylive "earnings between
the expiries, +10-15%" cut, RETRACTED 2026-09-20: it came from the calendar path study whose steps
4-12 were invalidated, and whose erratum says 87% of paths with a >3% move were truncated before the
loss finished. An earnings move IS a >3% move, so that was the worst-affected slice.

So this measures the premium DIRECTLY instead of simulating a structure -- the same move that made
the VRP panel several times more powerful than P&L simulation, and it cannot be truncated:

  implied move   ATM straddle mid / spot, on the last session BEFORE the report, using the first
                 expiry AFTER it
  realised       |move| over the same window (pre-earnings close -> expiry close)
  premium        implied - realised, in points of the underlying. Positive = the seller is paid.

Settlement is at intrinsic, so the short-straddle P&L here is exact: cost - |S_exp - K|. A condor or
calendar is a capped, cheaper expression of the same short-vol bet -- if the premium is not there in
the straddle it is not there in the condor either, and if it IS there, costs decide (today's
event-spread study: friction, not structure, killed a debit spread).

"Selectively" is the second question: the script buckets the premium by IV level, implied-move size,
market cap proxy and past-surprise behaviour to see whether the premium sorts on anything observable.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_earnings_vol_premium.py \\
           > data/studies/earnings_vol_premium_2026-09-20.log
"""
from __future__ import annotations
import os, uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX

CACHE = "data/cache/earnings_vol_chains.parquet"
MAX_DTE_AFTER = 10          # first expiry within 10 days after the print


def build_events() -> pd.DataFrame:
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    C = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    idx = C.index
    E = pd.read_parquet("data/cache/earnings_yf.parquet")
    E["session"] = pd.to_datetime(E.session)
    E = E[E.ticker.isin(C.columns) & E.session.between(idx[0], idx[-1])]
    rows = []
    for r in E.itertuples(index=False):
        j = C.columns.get_loc(r.ticker)
        i0 = idx.searchsorted(r.session)
        if i0 <= 1 or i0 + 2 >= len(idx): continue
        # BMO reacts the same session, so the last clean pre-print close is the prior one
        i_pre = i0 - 1 if r.timing == "BMO" else i0
        i_rx = i0 if r.timing == "BMO" else i0 + 1
        spot = C.values[i_pre, j]
        if not np.isfinite(spot) or spot <= 5: continue
        rows.append(dict(ticker=r.ticker, earn=r.session, pre_date=idx[i_pre], rx_date=idx[i_rx],
                         spot=float(spot), rx_move=float(C.values[i_rx, j] / spot - 1),
                         surprise_pct=r.surprise_pct))
    return pd.DataFrame(rows).reset_index(drop=True).assign(row_id=lambda d: np.arange(len(d)))


def pull(ev: pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(CACHE):
        c = pd.read_parquet(CACHE); print(f"  chains from cache: {len(c):,} rows"); return c
    k = ev[["row_id", "ticker", "pre_date", "earn", "spot"]].copy()
    k["pre_date"] = k.pre_date.dt.date; k["earn"] = k.earn.dt.date
    _ensure_glue_db(DB)
    name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy",
                     mode="overwrite", dtype={"row_id": "bigint", "ticker": "string",
                                              "pre_date": "date", "earn": "date", "spot": "double"})
    try:
        c = athena(f"""
          SELECT t.row_id, o.expiry, o.strike, o.cp, o.bid, o.ask, o.delta
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
          JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
            ON o.ticker = t.ticker AND o.trade_date = t.pre_date
          WHERE o.expiry > t.earn AND date_diff('day', t.earn, o.expiry) <= {MAX_DTE_AFTER}
            AND o.delta IS NOT NULL AND abs(o.delta) BETWEEN 0.25 AND 0.75
            AND o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999 AND o.ask >= o.bid""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    c.to_parquet(CACHE, index=False); print(f"  pulled {len(c):,} rows -> {CACHE}")
    return c


def main():
    ev = build_events()
    print(f"{len(ev):,} earnings events with a pre-print close, {ev.ticker.nunique()} names")
    c = pull(ev)
    c["mid"] = (c.bid + c.ask) / 2
    c["expiry"] = pd.to_datetime(c.expiry)
    # front expiry after the print, then the strike nearest spot
    front = c.groupby("row_id").expiry.min().rename("front")
    c = c.merge(front, on="row_id"); c = c[c.expiry == c.front]
    w = c.pivot_table(index=["row_id", "strike", "front"], columns="cp", values="mid",
                      aggfunc="last").reset_index().dropna(subset=["C", "P"])
    w["cp_gap"] = (w.C - w.P).abs()
    w = w.loc[w.groupby("row_id").cp_gap.idxmin()].rename(columns={"strike": "K"})
    w["straddle"] = w.C + w.P
    w["spot_raw"] = w.K + w.C - w.P          # put-call parity: the RAW spot, on the same basis as the chain
    d = ev.merge(w, on="row_id")
    print(f"  ATM straddle priced on {len(d):,} events ({100*len(d)/len(ev):.0f}% coverage)\n")

    # realised move to the front expiry, from the panel
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    C = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    idx = C.index
    exp_px = []
    for r in d.itertuples(index=False):
        i = idx.searchsorted(r.front)
        i = min(i, len(idx) - 1)
        exp_px.append(C.values[i, C.columns.get_loc(r.ticker)])
    d["S_exp"] = exp_px
    d = d[np.isfinite(d.S_exp)]
    d["implied_pct"] = 100 * d.straddle / d.spot_raw
    d["ret_to_exp"] = d.S_exp / d.spot - 1          # panel is adjusted, but a RATIO is basis-free
    d["realised_pct"] = 100 * d.ret_to_exp.abs()
    d["S_exp_raw"] = d.spot_raw * (1 + d.ret_to_exp)
    d["rx_abs_pct"] = 100 * d.rx_move.abs()
    d["payoff"] = (d.S_exp_raw - d.K).abs()
    d["seller_pnl_pct"] = 100 * (d.straddle - d.payoff) / d.spot_raw     # short straddle, % of spot
    d["dte"] = (d.front - d.pre_date).dt.days

    print("=" * 96); print("  IS EARNINGS VOL OVERPRICED? (ATM straddle, front expiry after the print)"); print("=" * 96)
    print(f"  events {len(d):,} | names {d.ticker.nunique()} | median DTE {d.dte.median():.0f}")
    print(f"  implied move   median {d.implied_pct.median():5.2f}%   mean {d.implied_pct.mean():5.2f}%")
    print(f"  realised |move| to expiry   median {d.realised_pct.median():5.2f}%   mean {d.realised_pct.mean():5.2f}%")
    print(f"  realised |move| on the day  median {d.rx_abs_pct.median():5.2f}%   mean {d.rx_abs_pct.mean():5.2f}%")
    print(f"\n  SHORT-STRADDLE premium (cost - payoff), % of spot, MID pricing:")
    print(f"     mean {d.seller_pnl_pct.mean():+.3f}%   median {d.seller_pnl_pct.median():+.3f}%   "
          f"win {100*(d.seller_pnl_pct>0).mean():.1f}%")
    g = d.groupby(d.pre_date.dt.year).seller_pnl_pct.agg(["size", "mean"])
    print(f"\n  by year:\n{g.round(3).to_string()}")
    d.to_parquet("data/cache/earnings_vol_events.parquet", index=False)

    print("\n" + "=" * 96); print("  DOES IT SORT? (selectivity — the 'not blindly' part)"); print("=" * 96)
    for lab, col in (("implied move size", "implied_pct"), ("DTE to expiry", "dte"),
                     ("spot price (size proxy)", "spot_raw"), ("past surprise%", "surprise_pct")):
        x = d[[col, "seller_pnl_pct"]].dropna()
        if x[col].nunique() < 5: continue
        q = pd.qcut(x[col], 5, duplicates="drop")
        t = x.groupby(q).seller_pnl_pct.agg(["size", "mean"]).round(3)
        print(f"\n--- {lab} ---"); print(t.to_string())


if __name__ == "__main__":
    main()
