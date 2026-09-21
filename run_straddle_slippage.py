#!/usr/bin/env python3
"""
Measure the long straddle's ENTRY SLIPPAGE -- the largest remaining unknown in the book's best strategy.

Every number in long_straddle_playbook.md prices at MID with zero slippage, and the doc says so:
"Entry costs are not modelled anywhere in this document. Sensitivity: -0.95pp per 1% paid over mid."
That sensitivity is a parameterised guess. This replaces it with a measurement, pulling real
bid/ask for both legs of every entry from options_daily_v3 and repricing arm 4.

Cost is ONE-SIDED: the straddle is held to expiry and settles at intrinsic, so you only cross the
spread on the way in.

Arm 4 ("full pool + both gates", no ticker qualification) is the honest configuration -- arms 1-2 are
contaminated by selecting and scoring the published list on the same years. Gates and folds are
imported from run_straddle_rebuild_wf so they cannot drift from the published rebuild.

Fill fractions f: entry = mid + f x (ask - mid). f=0 is the published mid, f=1 pays the full ask.

Usage: AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. \\
           .venv/bin/python3 run_straddle_slippage.py > data/studies/straddle_slippage_2026-09-20.log
"""
from __future__ import annotations
import uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
from run_straddle_rebuild_wf import load, STOP, FOLDS

FILLS = [0.0, 0.10, 0.25, 0.50, 1.0]
CACHE = "data/cache/straddle_entry_quotes.parquet"


def pull_quotes(d: pd.DataFrame) -> pd.DataFrame:
    import os
    if os.path.exists(CACHE):
        q = pd.read_parquet(CACHE); print(f"  quotes from cache: {len(q):,} legs"); return q
    k = d[["row_id", "ticker", "expiry", "entry_date", "strike"]].copy()
    k["expiry"] = pd.to_datetime(k.expiry).dt.date
    k["entry_date"] = pd.to_datetime(k.entry_date).dt.date
    _ensure_glue_db(DB)
    name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy",
                     mode="overwrite", dtype={"row_id": "bigint", "ticker": "string",
                                              "expiry": "date", "entry_date": "date", "strike": "double"})
    try:
        q = athena(f"""
          SELECT t.row_id, o.cp, o.bid, o.ask, o.last
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
          JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
            ON o.ticker = t.ticker AND o.expiry = t.expiry
           AND o.trade_date = t.entry_date AND o.strike = t.strike
          WHERE o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999 AND o.ask >= o.bid""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    q.to_parquet(CACHE, index=False); print(f"  pulled {len(q):,} legs -> {CACHE}")
    return q


def main():
    print("loading the published pool + gates (imported from run_straddle_rebuild_wf)")
    d = load().reset_index(drop=True)
    d["row_id"] = np.arange(len(d), dtype=np.int64)
    print(f"  {len(d):,} gated-universe trades, {d.ticker.nunique()} tickers")

    q = pull_quotes(d)
    w = q.pivot_table(index="row_id", columns="cp", values=["bid", "ask"], aggfunc="last")
    w.columns = [f"{a}_{b.lower()}" for a, b in w.columns]
    d = d.merge(w.reset_index(), on="row_id", how="left")
    have = d[["bid_c", "ask_c", "bid_p", "ask_p"]].notna().all(axis=1)
    print(f"  both legs quoted: {have.sum():,} of {len(d):,} ({100*have.mean():.1f}%)")
    d = d[have].copy()

    d["mid_q"] = (d.bid_c + d.ask_c) / 2 + (d.bid_p + d.ask_p) / 2
    d["ask_q"] = d.ask_c + d.ask_p
    d["sprd_pct"] = 100 * (d.ask_q - (d.bid_c + d.bid_p)) / d.mid_q
    # payout is fixed: the position settles at expiry regardless of what you paid to get in
    d["payout"] = d.entry_premium * (1 + d.ret_pct_long / 100.0)
    print(f"\n  measured entry spread: median {d.sprd_pct.median():.1f}% of mid, "
          f"mean {d.sprd_pct.mean():.1f}%, p90 {d.sprd_pct.quantile(.9):.1f}%")
    print(f"  CSV mid ${d.entry_premium.mean():.2f} vs quoted mid ${d.mid_q.mean():.2f} "
          f"(agreement check)")

    a4 = d[d.pass_both & d.yr.isin(FOLDS)]
    print(f"\n  arm 4 (full pool + both gates), folds {FOLDS[0]}-{FOLDS[-1]}: {len(a4):,} trades\n")
    print("=" * 96)
    print("  ARM 4 vs ENTRY FILL  (f = fraction of the half-spread paid; f=0 is the published number)")
    print("=" * 96)
    rows = []
    for f in FILLS:
        cost = d.mid_q + f * (d.ask_q - d.mid_q)
        roc = (d.payout / cost - 1) * 100
        g = d.pass_both & d.yr.isin(FOLDS)
        raw, clipped = roc[g], roc[g].clip(lower=STOP)
        per_fold = [roc[g & (d.yr == y)].clip(lower=STOP).mean() for y in FOLDS]
        rows.append(dict(f=f, pct_over_mid=100 * f * (d.ask_q - d.mid_q).mean() / d.mid_q.mean(),
                         mean_nostop=raw.mean(), mean_stop50=clipped.mean(),
                         median=raw.median(), win_pct=100 * (raw > 0).mean(),
                         **{str(y): v for y, v in zip(FOLDS, per_fold)}))
    t = pd.DataFrame(rows)
    print(t.round(2).to_string(index=False))
    base = t.loc[t.f == 0, "mean_stop50"].iloc[0]
    print(f"\n  published (f=0, stop -50%): {base:+.2f}%")
    for f in FILLS[1:]:
        v = t.loc[t.f == f, "mean_stop50"].iloc[0]
        over = t.loc[t.f == f, "pct_over_mid"].iloc[0]
        print(f"  f={f:<5} ({over:.1f}% over mid): {v:+.2f}%   ({v-base:+.2f}pp)")
    d0, d1 = t.loc[t.f == 0], t.loc[t.f == 0.5]
    slope = (d1.mean_stop50.iloc[0] - d0.mean_stop50.iloc[0]) / max(d1.pct_over_mid.iloc[0], 1e-9)
    print(f"\n  MEASURED sensitivity: {slope:+.2f}pp of ROC per 1% paid over mid "
          f"(playbook's parameterised guess was -0.95)")
    print(f"\n  no-stop floor at f=0.5: {t.loc[t.f==0.5,'mean_nostop'].iloc[0]:+.2f}%  "
          f"(the -50% clip is an assumption, not a path sim)")


if __name__ == "__main__":
    main()
