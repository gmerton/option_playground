#!/usr/bin/env python3
"""
[A1] Retail call-buying bursts -> next-days stock returns (pre-registered 2026-09-23, before any return was computed).

Idea (Gabe's "who is forced / predisposed to buy"): a burst of short-dated OTM call buying leaves dealers short calls;
their delta hedge is mechanical stock buying -> the stock should drift up. The competing story (lottery-demand
literature): retail call frenzies mark overpricing -> the stock underperforms. So the test is TWO-SIDED.

Data: silver.options_flow_daily (built 2026-09-23 from v3) for the liquid-panel names; prices from
liquid_panel_2009.parquet (adjusted, survivorship-biased: today's liquid names). Window 2010-02 -> 2026-04 (v3 is
prints-only after ~Apr 2026). Eligibility: liquid mask (ADDV >= $50M, px >= $5) on day t.
BURST on day t (all three):
  (a) call_vol_otm30(t) >= 3 x mean(call_vol_otm30, t-20 .. t-1)   (the name's own baseline; split-safe)
  (b) call_vol_otm30(t) >= 1,000 contracts
  (c) call_vol_otm30(t) >= 2 x put_vol_otm30(t)                    (directional call buying, not a vol event)
  first burst per name in any 10-session window.
Entry: OPEN of t+1 (flow is only known after the close of t), 0.10% slippage a side. Outcome: % return from that open
  to the close of t+1, t+5, t+10 (1/5/10-session horizons).
PRIMARY: +5-session return, burst minus DATE-MATCHED control: on the same date t, eligible NON-burst names in the same
  cross-sectional quintile of day-t return AND the same ADR tercile (holds the news/momentum of day t fixed); per-date
  mean(burst - matched control mean), t clustered by date. Bar: |t| >= 3, both halves (split 2018-01-01) the same sign,
  per-year shown. Direction not assumed (two-sided).
Secondary (Sidak over 3 horizons, |t| ~ 2.39; no verdict of their own): +1 / +10 sessions; split by the prior-day SPY
  dealer-gamma sign (run_gex_regime_pin.gex_series; to 2026-02); a same-name PRE-window control (random non-burst day in
  t-60 .. t-21, same entry/exit rule).
Prior: low-moderate, direction genuinely uncertain.

Run: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_call_burst.py   (log -> data/studies/logs/call_burst.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import SLIP, load_panel

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/call_burst.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
FLOW = REPO / "data/cache/options_flow_liquid.parquet"
START, END, SPLIT = "2010-02-01", "2026-04-30", "2018-01-01"
RNG = np.random.default_rng(20260923)


def pull_flow(tickers):
    """Pull the liquid names from silver.options_flow_daily once and cache locally."""
    if FLOW.exists():
        return pd.read_parquet(FLOW)
    import awswrangler as wr
    from lib.constants import WORKGROUP, S3_OUTPUT
    lst = ",".join(f"'{t}'" for t in tickers)
    frames = []
    for y in range(2010, 2027):
        sql = (f"SELECT ticker, trade_date, call_vol, put_vol, call_vol_otm30, put_vol_otm30, call_oi_30, "
               f"call_delta_sh, put_delta_sh FROM silver.options_flow_daily WHERE year = {y} AND ticker IN ({lst})")
        df = wr.athena.read_sql_query(sql, database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog",
                                      s3_output=S3_OUTPUT, ctas_approach=False)
        print(f"  flow {y}: {len(df):,}", flush=True)
        frames.append(df)
    f = pd.concat(frames, ignore_index=True)
    f["trade_date"] = pd.to_datetime(f.trade_date)
    f.to_parquet(FLOW, index=False)
    return f


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def main():
    P = load_panel(PANEL)
    idx, cols = P.close.index, P.close.columns
    f = pull_flow(list(cols))
    otm = f.pivot(index="trade_date", columns="ticker", values="call_vol_otm30").reindex(index=idx, columns=cols)
    potm = f.pivot(index="trade_date", columns="ticker", values="put_vol_otm30").reindex(index=idx, columns=cols)
    base = otm.shift(1).rolling(20, min_periods=15).mean()
    burst = (otm >= 3 * base) & (otm >= 1000) & (otm >= 2 * potm.fillna(0)) & P.elig.fillna(False)
    burst[(burst.index < START) | (burst.index > END)] = False
    # first burst per name within any 10-session window
    bv = burst.values.copy()
    for j in range(bv.shape[1]):
        last = -99
        for i in np.flatnonzero(bv[:, j]):
            if i - last < 10:
                bv[i, j] = False
            else:
                last = i
    burst = pd.DataFrame(bv, index=idx, columns=cols)
    O, C = P.open.values, P.close.values
    n = len(idx)

    def fwd(i, j, h):
        if i + h >= n or not np.isfinite(O[i + 1, j]) or not np.isfinite(C[i + h, j]):
            return np.nan
        return 100 * (C[i + h, j] * (1 - SLIP) / (O[i + 1, j] * (1 + SLIP)) - 1)

    r1 = C / np.roll(C, 1, axis=0) - 1
    r1[0] = np.nan
    elig = P.elig.fillna(False).values & np.isfinite(r1)
    adr = P.adr.values
    # gamma sign (SPY), prior day
    try:
        import run_gex_regime_pin as G
        bars = G.daily_bars("SPY")
        _, net, _ = G.gex_series("SPY", bars)
        gsign = np.sign(net).reindex(idx).shift(1)
    except Exception as e:  # noqa: BLE001
        print("gex unavailable:", e); gsign = pd.Series(np.nan, index=idx)
    rows = []
    for i in np.flatnonzero(bv.any(axis=1)):
        e = elig[i]
        if e.sum() < 50:
            continue
        rq = pd.qcut(pd.Series(r1[i, e]), 5, labels=False, duplicates="drop").values
        aq = pd.qcut(pd.Series(adr[i, e]), 3, labels=False, duplicates="drop").values
        names = np.flatnonzero(e)
        cell = dict(zip(names, zip(rq, aq)))
        for j in np.flatnonzero(bv[i]):
            if j not in cell:
                continue
            ctl = [k for k in names if k != j and not bv[i, k] and cell[k] == cell[j]]
            if len(ctl) < 3:
                continue
            ctl = RNG.choice(ctl, size=min(20, len(ctl)), replace=False)
            rec = dict(date=idx[i], sym=cols[j], gsign=gsign.iloc[i], day_ret=100 * r1[i, j])
            for h in (1, 5, 10):
                rec[f"b{h}"] = fwd(i, j, h)
                rec[f"c{h}"] = np.nanmean([fwd(i, int(k), h) for k in ctl])
            pre = [k for k in range(max(0, i - 60), max(0, i - 20)) if not bv[k, j] and np.isfinite(O[min(k + 1, n - 1), j])]
            if pre:
                k = int(RNG.choice(pre))
                rec["pre5"] = fwd(k, j, 5)
            rows.append(rec)
    T = pd.DataFrame(rows)
    print(f"# Call-buying bursts [A1] -- {len(T):,} bursts, {T.sym.nunique()} names, {T.date.min().date()} -> {T.date.max().date()}; "
          f"median day-t return of burst names {T.day_ret.median():+.2f}%")
    for h in (5, 1, 10):
        d = (T[f"b{h}"] - T[f"c{h}"])
        dd = d.groupby(T.date).mean()
        hh = dd.index < SPLIT
        tag = "PRIMARY" if h == 5 else "secondary"
        print(f"\n## {tag} +{h} sessions: burst {T[f'b{h}'].mean():+.3f}% vs date/return/ADR-matched control "
              f"{T[f'c{h}'].mean():+.3f}% | diff {dd.mean():+.3f}pp t {tstat(dd):+.2f} (dates {len(dd)}) | halves "
              f"{dd[hh].mean():+.3f} / {dd[~hh].mean():+.3f}")
        if h == 5:
            yr = dd.groupby(dd.index.year).agg(["size", "mean"]).round(3)
            print("per year (diff, pp):\n" + yr.T.to_string())
            for s, lab in ((1.0, "SPY gamma POSITIVE (prior day)"), (-1.0, "SPY gamma NEGATIVE (prior day)")):
                m = T.gsign == s
                x = (d[m]).groupby(T.date[m]).mean()
                print(f"  {lab:32s} n {int(m.sum()):5d} | diff {x.mean():+.3f}pp t {tstat(x):+.2f}")
            p = (T.b5 - T.pre5).groupby(T.date).mean()
            print(f"  same-name PRE-window control: diff {p.mean():+.3f}pp t {tstat(p):+.2f}")
    T.to_csv(REPO / "data/studies/logs/call_burst_events.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
