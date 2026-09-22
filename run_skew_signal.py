#!/usr/bin/env python3
"""
Is SPY option SKEW a directional / timing signal? (2026-09-22, pre-registered here before the first run.)

Prompted by OptionsPlay's 2026-09-11 webinar (@14:08): the CBOE skew index reads "where directional demand is" --
a 95th-percentile skew into FOMC was presented as the market pricing crash risk, and by implication as information
about direction and timing. We have never tested skew as a signal (only as a descriptive column in the
credit-spread finder); the one adjacent test, oquants' momentum-skew verticals, FAILED.

SIGNAL: per trade_date, from options_daily_v3 SPY rows with 20-40 DTE, take the expiry closest to 30 DTE and read
  skew = IV(put with delta closest to -0.25) - IV(call with delta closest to +0.25)      [mid IV = (bid_iv+ask_iv)/2]
  skew_pct = percentile of skew within the trailing 252 sessions (strictly prior, min 200 obs)
CONTROL: vix_pct = percentile of VIX within the same trailing window (same construction).

TESTS (all on SPY daily closes from the intraday cache; 2010 -> 2026-02):
  A. PRIMARY -- direction: forward 21-session log return by skew_pct quintile; Q5-Q1 spread with Newey-West
     (lag 21) t on the overlapping series; halves split at 2018-01-01.
  B. timing: same for forward 5 and 10 sessions.
  C. vol: forward 21-session realised vol by quintile (does high skew forecast movement, if not direction?).
  D. INCREMENT: Fama-MacBeth-style OLS of forward return on skew_pct with vix_pct in the regression -- does skew
     add anything beyond the VIX level? (Newey-West SEs.)
PRE-REGISTERED PASS (direction): |t| >= 3 on the Q5-Q1 spread, same sign in both halves, AND the skew coefficient
in D significant at |t| >= 2 with the same sign. Anything else = NULL. The vol test (C) is descriptive: the
benchmark it must beat is the GEX regime result (negative dealer gamma = +8% realised vol beyond VIX, t 7.7).

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_skew_signal.py
"""
from __future__ import annotations
import os, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from lib.athena_lib import athena

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
CACHE = "data/cache/spy_skew_25d.parquet"
END = "2026-02-27"


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    sql = f"""
    SELECT trade_date, expiry, cp, strike, CAST(delta AS DOUBLE) d,
           CAST((bid_iv + ask_iv) / 2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker = 'SPY'
      AND trade_date >= TIMESTAMP '2010-01-01 00:00:00' AND trade_date <= TIMESTAMP '{END} 23:59:59'
      AND bid > 0 AND delta IS NOT NULL AND bid_iv > 0
      AND date_diff('day', trade_date, expiry) BETWEEN 20 AND 40
      AND ABS(delta) BETWEEN 0.15 AND 0.35
    """
    df = athena(sql); df.to_parquet(CACHE, index=False); return df


def skew_series(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df.trade_date).dt.normalize()
    df["gap"] = (df.dte - 30).abs()
    pick = df.sort_values("gap").groupby(["trade_date"]).expiry.first().rename("exp")   # expiry closest to 30 DTE
    df = df.merge(pick, left_on="trade_date", right_index=True)
    df = df[df.expiry == df.exp]
    rows = []
    for d, g in df.groupby("trade_date"):
        p = g[g.cp == "P"]; c = g[g.cp == "C"]
        if p.empty or c.empty: continue
        pi = p.iloc[(p.d + 0.25).abs().argsort()[:1]]; ci = c.iloc[(c.d - 0.25).abs().argsort()[:1]]
        if abs(abs(pi.d.iloc[0]) - 0.25) > 0.05 or abs(ci.d.iloc[0] - 0.25) > 0.05: continue
        rows.append(dict(date=d, skw=float(pi.iv.iloc[0] - ci.iv.iloc[0]), put_iv=float(pi.iv.iloc[0]), dte=int(pi.dte.iloc[0])))
    return pd.DataFrame(rows).set_index("date").sort_index()


def spy_daily() -> pd.DataFrame:
    m = pd.read_parquet("data/cache/intraday_hist/SPY_1min.parquet")
    m["date"] = m.ts.dt.normalize()
    d = m.groupby("date").close.last().to_frame("close")
    d["lr"] = np.log(d.close).diff()
    return d


def nw_t(x: pd.Series, lag: int) -> float:
    x = x.dropna()
    if len(x) < 30: return np.nan
    r = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return float(r.tvalues[0])


S = skew_series(pull())
px = spy_daily()
vix = pd.read_parquet("data/cache/vix_daily.parquet")
vix["date"] = pd.to_datetime(vix.trade_date).dt.normalize()
D = S.join(px, how="inner").join(vix.set_index("date")["vix_close"], how="left").dropna(subset=["skw", "close"])
D["skew_pct"] = D.skw.rolling(252, min_periods=200).apply(lambda w: (w[-1] > w[:-1]).mean(), raw=True)
D["vix_pct"] = D.vix_close.rolling(252, min_periods=200).apply(lambda w: (w[-1] > w[:-1]).mean(), raw=True)
for h in (5, 10, 21):
    D[f"f{h}"] = np.log(D.close.shift(-h) / D.close) * 100
    D[f"rv{h}"] = D.lr.rolling(h).std().shift(-h) * np.sqrt(252) * 100
D = D.dropna(subset=["skew_pct", "vix_pct"])
print(f"SPY skew series: {len(D):,} sessions {D.index.min().date()}..{D.index.max().date()}  "
      f"median 25d skew {D.skw.median():.3f} ({D.skw.median()*100:.1f} vol pts)  median DTE {D.dte.median():.0f}")

for col, lag, lab in [("f21", 21, "A. DIRECTION, forward 21 sessions (%)"), ("f5", 5, "B. forward 5 (%)"),
                      ("f10", 10, "B. forward 10 (%)"), ("rv21", 21, "C. forward 21-session realised vol (%)")]:
    q = pd.qcut(D.skew_pct, 5, labels=False, duplicates="drop")
    tab = D.groupby(q)[col].mean()
    hi, lo = D[q == 4][col], D[q == 0][col]
    sp = hi.mean() - lo.mean()
    j = D.assign(q=q, y=D[col]).dropna(subset=["y"]); j = j[j.q.isin([0, 4])]
    # t on the Q5-Q1 difference = HAC regression of y on a Q5 dummy (the earlier version regressed a signed
    # pooled series, which halves the coefficient)
    reg = sm.OLS(j.y.values, sm.add_constant((j.q == 4).astype(float).values)).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    t_diff = float(reg.tvalues[1])
    mid = D.index[len(D) // 2]
    h1 = D[D.index < mid]; h2 = D[D.index >= mid]
    def half_sp(x):
        qq = pd.qcut(x.skew_pct, 5, labels=False, duplicates="drop")
        return x[qq == 4][col].mean() - x[qq == 0][col].mean()
    print(f"\n{lab}\n  by skew-percentile quintile Q1..Q5: {[round(v,2) for v in tab.tolist()]}"
          f"\n  Q5-Q1 {sp:+.2f}  NW t {t_diff:+.2f}  | halves (split {mid.date()}) {half_sp(h1):+.2f} / {half_sp(h2):+.2f}"
          f"  | unconditional {D[col].mean():+.2f}")

print("\nD. does skew add anything beyond the VIX level? (OLS, Newey-West lag 21)")
for col in ("f21", "rv21"):
    X = sm.add_constant(D[["skew_pct", "vix_pct"]]); y = D[col]
    ok = X.notna().all(axis=1) & y.notna()
    r = sm.OLS(y[ok], X[ok]).fit(cov_type="HAC", cov_kwds={"maxlags": 21})
    print(f"  {col}: skew_pct {r.params.skew_pct:+.2f} (t {r.tvalues.skew_pct:+.2f})   "
          f"vix_pct {r.params.vix_pct:+.2f} (t {r.tvalues.vix_pct:+.2f})   R2 {r.rsquared:.3f}")
D.to_csv("data/studies/skew_signal_2026-09-22.csv")
