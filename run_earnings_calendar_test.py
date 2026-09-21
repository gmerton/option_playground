#!/usr/bin/env python3
"""
The earnings CALENDAR — the vehicle the term-structure gate is actually for.

earnings_gates_2026-09-20.md tested calculator.py's `ts_slope_0_45 <= -0.00406` backwardation gate
against a short ATM STRADDLE and found it didn't sort. That pairing was wrong: backwardation is a
TERM-STRUCTURE signal -- sell the rich front, buy the cheap back -- and a front-expiry-only straddle
cannot express it. This prices the real vehicle.

Structure, entered on the last session before the print, same ATM strike K as the straddle study
(delta-selected, parity-checked):
    SHORT the front expiry (first after the print)      LONG the next expiry out
Exit at front expiry: the short settles at intrinsic, the long is MARKED FROM A REAL QUOTE on that
date -- never modelled. An event whose back leg has no quote at front expiry is DROPPED, not assumed.
That is the discipline the original calendar path study lacked: its erratum found 87% of paths with a
>3% move were truncated before the loss finished, and an earnings move IS a >3% move.

Three variants from the same legs: call calendar, put calendar, and the double (both) -- the double
is the oquants expression.

Costs: entry pays the spread on all legs (buy the back at the ask, sell the front at the bid); the
exit pays it again on the back leg (sold at the bid). The short front settles, so it costs nothing to
close. MID columns are shown alongside because every earnings result so far has died on the spread.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_earnings_calendar_test.py \
           > data/studies/earnings_calendar_2026-09-20.log
"""
from __future__ import annotations
import os, sys, uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX

BACK = int(sys.argv[sys.argv.index("--back") + 1]) if "--back" in sys.argv else 0   # 0 = next expiry
TAG = f"_b{BACK}" if BACK else ""
ENTRY_CACHE, EXIT_CACHE = f"data/cache/earn_cal_entry{TAG}.parquet", f"data/cache/earn_cal_exit{TAG}.parquet"


def tmp(df, dtype):
    _ensure_glue_db(DB)
    name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=df, path=path, dataset=True, database=DB, table=name,
                     compression="snappy", mode="overwrite", dtype=dtype)
    return name, path


DT = {"row_id": "bigint", "ticker": "string", "pre_date": "date",
      "front": "date", "back": "date", "K": "double"}


def main():
    d = pd.read_parquet("data/cache/earnings_gates.parquet")
    T = pd.read_parquet("data/cache/earnings_term_structure.parquet")
    T["expiry"] = pd.to_datetime(T.expiry)
    # back expiry = the next listed expiry after the front, from the term-structure pull
    exp = T[["row_id", "expiry"]].drop_duplicates().merge(d[["row_id", "front"]], on="row_id")
    cand = exp[exp.expiry > exp.front].copy()
    if BACK:
        # the further-out geometry oquants / tastylive use: nearest listed expiry to front + BACK days
        cand["miss"] = ((cand.expiry - cand.front).dt.days - BACK).abs()
        nxt = cand.loc[cand.groupby("row_id").miss.idxmin(), ["row_id", "expiry"]].set_index("row_id").expiry.rename("back")
    else:
        nxt = cand.groupby("row_id").expiry.min().rename("back")
    d = d.merge(nxt, on="row_id")
    d["gap_days"] = (d.back - d.front).dt.days
    lo, hi = (max(BACK - 12, 3), BACK + 12) if BACK else (3, 45)
    d = d[d.gap_days.between(lo, hi)]
    print(f"back leg: {'nearest to front+%dd' % BACK if BACK else 'next expiry'}  (accepted gap {lo}-{hi}d)")
    print(f"{len(d):,} events with a usable back expiry | median front {d.front_dte.median():.0f} DTE, "
          f"back gap {d.gap_days.median():.0f}d")

    k = d[["row_id", "ticker", "pre_date", "front", "back", "K"]].copy()
    for c in ("pre_date", "front", "back"): k[c] = pd.to_datetime(k[c]).dt.date

    if os.path.exists(ENTRY_CACHE):
        en = pd.read_parquet(ENTRY_CACHE)
    else:
        n, p = tmp(k, DT)
        try:
            en = athena(f"""SELECT t.row_id, o.expiry, o.cp, o.bid, o.ask
              FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{n}" t
                ON o.ticker=t.ticker AND o.trade_date=t.pre_date AND o.strike=t.K
               AND (o.expiry=t.front OR o.expiry=t.back)
              WHERE o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask<9999 AND o.ask>=o.bid""")
        finally: _drop_temp_targets_table(DB, n, p)
        en.to_parquet(ENTRY_CACHE, index=False)
    if os.path.exists(EXIT_CACHE):
        ex = pd.read_parquet(EXIT_CACHE)
    else:
        n, p = tmp(k, DT)
        try:
            ex = athena(f"""SELECT t.row_id, o.cp, o.bid, o.ask
              FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{n}" t
                ON o.ticker=t.ticker AND o.trade_date=t.front AND o.strike=t.K AND o.expiry=t.back
              WHERE o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask<9999 AND o.ask>=o.bid""")
        finally: _drop_temp_targets_table(DB, n, p)
        ex.to_parquet(EXIT_CACHE, index=False)
    print(f"  entry quotes {len(en):,} rows | exit marks {len(ex):,} rows")

    en["expiry"] = pd.to_datetime(en.expiry)
    en = en.merge(d[["row_id", "front", "back"]], on="row_id")
    en["leg"] = np.where(en.expiry == en.front, "F", np.where(en.expiry == en.back, "B", ""))
    E = en[en.leg != ""].pivot_table(index="row_id", columns=["leg", "cp"], values=["bid", "ask"], aggfunc="last")
    E.columns = [f"{a}_{b}{c}" for a, b, c in E.columns]
    X = ex.pivot_table(index="row_id", columns="cp", values=["bid", "ask"], aggfunc="last")
    X.columns = [f"x{a}_{b}" for a, b in X.columns]
    d = d.merge(E.reset_index(), on="row_id").merge(X.reset_index(), on="row_id")

    need = [c for c in d.columns if c.startswith(("bid_", "ask_", "xbid_", "xask_"))]
    d = d.dropna(subset=need)
    print(f"  fully quoted both legs at entry AND the back leg at front expiry: {len(d):,} events "
          f"({d.ticker.nunique()} names)\n")

    mid = lambda b, a: (d[b] + d[a]) / 2
    res = {}
    for lab, cps in (("call calendar", ["C"]), ("put calendar", ["P"]), ("DOUBLE calendar", ["C", "P"])):
        deb_mid = sum(mid(f"bid_B{c}", f"ask_B{c}") - mid(f"bid_F{c}", f"ask_F{c}") for c in cps)
        deb_real = sum(d[f"ask_B{c}"] - d[f"bid_F{c}"] for c in cps)          # pay the ask, sell the bid
        intr = {"C": np.maximum(d.S_exp_raw - d.K, 0), "P": np.maximum(d.K - d.S_exp_raw, 0)}
        # The long back leg is floored at INTRINSIC: 17.4% of call marks and 14.6% of put marks have a
        # bid BELOW intrinsic (deep-ITM, wide quotes), and nobody sells there -- you exercise. This is the
        # same convention the calendar-study erratum settled on: shorts at intrinsic, longs at the mark
        # with an intrinsic floor. Without it the "real" arm charges a loss larger than the debit, which
        # a long calendar cannot produce.
        val_mid = sum(np.maximum(mid(f"xbid_{c}", f"xask_{c}"), intr[c]) - intr[c] for c in cps)
        val_real = sum(np.maximum(d[f"xbid_{c}"], intr[c]) - intr[c] for c in cps)
        ok = deb_mid > 0.01
        res[lab] = pd.DataFrame({"mid": 100 * (val_mid - deb_mid) / d.spot_raw,
                                 "real": 100 * (val_real - deb_real) / d.spot_raw,
                                 "debit": deb_mid, "ok": ok, "yr": d.pre_date.dt.year,
                                 "slope": d.ts_slope, "ivrv": d.iv30_rv30, "vol": d.avg_volume})
    print("=" * 96); print(f"  EARNINGS CALENDAR — long the back, short the front (% of spot)  [back = {'+%dd' % BACK if BACK else 'next expiry'}]"); print("=" * 96)
    for lab, r in res.items():
        r = r[r.ok]
        print(f"\n  {lab}  (n {len(r):,}, median debit ${r.debit.median():.2f})")
        for col, cl in (("mid", "MID pricing"), ("real", "paying the spread")):
            print(f"    {cl:<20} mean {r[col].mean():+7.3f}%  median {r[col].median():+7.3f}%  "
                  f"win {100*(r[col]>0).mean():5.1f}%  worst {r[col].min():+7.2f}%")
        yr = r.groupby("yr")["real"].mean()
        print(f"    by year (real): {yr.round(2).to_dict()}  negative years {int((yr<0).sum())}/{len(yr)}")

    print("\n" + "=" * 96); print("  DOES ts_slope SORT THE CALENDAR? (the gate on its own vehicle)"); print("=" * 96)
    r = res["DOUBLE calendar"]; r = r[r.ok]
    q = pd.qcut(r.slope, 5, duplicates="drop")
    print(r.groupby(q).agg(n=("mid", "size"), MID=("mid", "mean"), REAL=("real", "mean")).round(3).to_string())
    g = r[r.slope <= -0.00406]
    print(f"\n  gate ts_slope <= -0.00406: n {len(g):,} ({100*len(g)/len(r):.0f}%)  "
          f"MID {g['mid'].mean():+.3f}  REAL {g['real'].mean():+.3f}   "
          f"vs ungated MID {r['mid'].mean():+.3f}  REAL {r['real'].mean():+.3f}")


if __name__ == "__main__":
    main()
