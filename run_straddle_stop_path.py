#!/usr/bin/env python3
"""
Replace the straddle's -50% stop ASSUMPTION with a path simulation.

long_straddle_playbook.md models the stop as a loss clip, max(roc, -50). After the 2026-09-20
correction that clip contributes +6.69pp -- 43% of arm 4's headline -- by rescuing 29.3% of trades.
It assumes you always exit at exactly -50%. Two things make that optimistic, and both are measured here:

  1. You exit at whatever the mark is on the day it breaches, which is usually WORSE than -50%
     (7-DTE straddles gap; the position does not glide through the level).
  2. Stopping out means SELLING, so you cross the spread a SECOND time. The entry-slippage study
     could treat cost as one-sided only because the held-to-expiry case settles at intrinsic. A
     stopped trade does not -- it pays the spread on the way out too.

Marks are daily closes from options_daily_v3 (bid/ask per leg). A real intraday stop would trigger
more often and at worse prices, so everything here is still an upper bound on the stop's value.

Arms: no stop | clip (the published assumption) | path at mid | path selling the bid, and each
crossed with the measured entry fill.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_straddle_stop_path.py \\
           > data/studies/straddle_stop_path_2026-09-20.log
"""
from __future__ import annotations
import os, uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
from run_straddle_rebuild_wf import load, STOP, FOLDS

CACHE = "data/cache/straddle_stop_paths.parquet"
STOP_LEVEL = 0.50          # exit when the position is worth <= 50% of what it cost
ENTRY_FILL = 0.50          # measured-realistic entry: half the spread


def pull_paths(k: pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(CACHE):
        p = pd.read_parquet(CACHE); print(f"  paths from cache: {len(p):,} leg-days"); return p
    _ensure_glue_db(DB)
    name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy",
                     mode="overwrite", dtype={"row_id": "bigint", "ticker": "string", "expiry": "date",
                                              "entry_date": "date", "strike": "double"})
    try:
        p = athena(f"""
          SELECT t.row_id, o.trade_date, o.cp, o.bid, o.ask
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
          JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
            ON o.ticker = t.ticker AND o.expiry = t.expiry AND o.strike = t.strike
          WHERE o.trade_date > t.entry_date AND o.trade_date <= t.expiry
            AND o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999 AND o.ask >= o.bid""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    p.to_parquet(CACHE, index=False); print(f"  pulled {len(p):,} leg-days -> {CACHE}")
    return p


def main():
    d = load().reset_index(drop=True); d["row_id"] = np.arange(len(d), dtype=np.int64)
    q = pd.read_parquet("data/cache/straddle_entry_quotes.parquet")
    w = q.pivot_table(index="row_id", columns="cp", values=["bid", "ask"], aggfunc="last")
    w.columns = [f"{a}_{b.lower()}" for a, b in w.columns]
    d = d.merge(w.reset_index(), on="row_id", how="left")
    d = d[d[["bid_c", "ask_c", "bid_p", "ask_p"]].notna().all(axis=1)].copy()
    d["mid_q"] = (d.bid_c + d.ask_c) / 2 + (d.bid_p + d.ask_p) / 2
    d["ask_q"] = d.ask_c + d.ask_p
    d["payout"] = d.entry_premium * (1 + d.ret_pct_long / 100.0)

    a4 = d[d.pass_both & d.yr.isin(FOLDS)].copy()
    print(f"arm 4: {len(a4):,} trades, folds {FOLDS[0]}-{FOLDS[-1]}")
    k = a4[["row_id", "ticker", "expiry", "entry_date", "strike"]].copy()
    k["expiry"] = pd.to_datetime(k.expiry).dt.date; k["entry_date"] = pd.to_datetime(k.entry_date).dt.date
    P = pull_paths(k)

    # daily straddle marks: mid, and the bid side you would actually receive selling to close
    P["mid"] = (P.bid + P.ask) / 2
    g = P.groupby(["row_id", "trade_date"]).agg(n=("cp", "nunique"), mid=("mid", "sum"), bid=("bid", "sum"))
    g = g[g.n == 2].reset_index().sort_values(["row_id", "trade_date"])
    print(f"  {g.row_id.nunique():,} of {len(a4):,} trades have both legs marked on >=1 day "
          f"({100*g.row_id.nunique()/len(a4):.1f}%)")

    ent_mid = a4.set_index("row_id").mid_q
    ent_fill = (a4.mid_q + ENTRY_FILL * (a4.ask_q - a4.mid_q)); ent_fill.index = a4.row_id

    out = {}
    for lab, cost_s, exit_col in (("mid entry / sell at mid", ent_mid, "mid"),
                                  ("mid entry / sell the bid", ent_mid, "bid"),
                                  ("filled entry / sell the bid", ent_fill, "bid")):
        c = g.row_id.map(cost_s)
        breach = g[exit_col] <= STOP_LEVEL * c
        first = g[breach].groupby("row_id").first()
        res = pd.DataFrame(index=a4.row_id)
        res["cost"] = cost_s
        res["stopped"] = res.index.isin(first.index)
        res["exit_val"] = first[exit_col].reindex(res.index)
        held = a4.set_index("row_id").payout
        res["val"] = np.where(res.stopped, res.exit_val, held.reindex(res.index))
        out[lab] = ((res.val / res.cost - 1) * 100)
        out[lab + "|stopped%"] = 100 * res.stopped.mean()
        out[lab + "|exit_at"] = (res.loc[res.stopped, "exit_val"] / res.loc[res.stopped, "cost"] - 1) * 100

    print("\n" + "=" * 92)
    print("  THE -50% STOP: ASSUMPTION vs PATH")
    print("=" * 92)
    base_nostop = ((a4.set_index("row_id").payout / ent_mid) - 1) * 100
    print(f"  no stop, mid entry                       {base_nostop.mean():+7.2f}%")
    print(f"  CLIP assumption max(roc,-50), mid entry  "
          f"{base_nostop.clip(lower=STOP).mean():+7.2f}%   <- the published +15.46%")
    for lab in ("mid entry / sell at mid", "mid entry / sell the bid", "filled entry / sell the bid"):
        r = out[lab]
        print(f"  PATH: {lab:<34} {r.mean():+7.2f}%   stopped {out[lab+'|stopped%']:.1f}%  "
              f"median exit {out[lab+'|exit_at'].median():+.1f}%  mean exit {out[lab+'|exit_at'].mean():+.1f}%")
    r = out["filled entry / sell the bid"]
    print(f"\n  per fold (filled entry / sell the bid):")
    fold = a4.set_index("row_id").yr
    for y in FOLDS:
        print(f"    {y}  {r[fold == y].mean():+7.2f}%   n {int((fold==y).sum()):,}")
    clip = base_nostop.clip(lower=STOP).mean()
    print(f"\n  the clip overstates by {clip - r.mean():+.2f}pp vs the honest path "
          f"(entry filled, exit crossing the spread)")
    print("  ⚠ marks are DAILY closes; a real intraday stop triggers more often and worse, so this")
    print("     is still an upper bound on the stop's value.")


if __name__ == "__main__":
    main()
