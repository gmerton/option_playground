#!/usr/bin/env python3
"""
Walk-forward of the candidate straddle filter from rsi_conditioning_study_2026-09-16.md:
skip gated 7-DTE long-straddle entries whose RSI(14) at the entry close is >= 70.

Set before running (the in-sample study already used the full 2018-2026 sample, so
only checks that do not re-fit on it count as out of sample):

  1. FIXED 70, year by year. Each calendar year scored separately: sleeve mean with and
     without the skip, and the mean of the skipped trades vs the kept ones. Pass =
     skipping helps in a clear majority of years, not just on the pooled mean.
  2. EXPANDING-WINDOW THRESHOLD CHOICE. Fold design matches run_straddle_rebuild_wf.py:
     for test year N in 2020..2026, choose the cutoff from {60, 65, 70, 75, 80, none}
     that maximises the kept-trade mean on entries with year < N, apply it to year N.
     Tests whether the *procedure* generalises and whether it keeps landing near 70.
  3. WITHIN-WEEK PLACEBO. Shuffle RSI among the trades of the same entry week 5,000
     times and re-apply the >= 70 skip. Keeps the number skipped per week and the
     market timing identical; only which name gets skipped is random. p = share of
     shuffles whose improvement is >= the real one.
  4. PLATEAU. Kept-trade mean and monthly t for cutoffs 60..85 in steps of 5, so a
     single-value spike at 70 is visible.
  5. BREADTH. Is the penalty a few tickers? Leave-one-ticker-out on the skipped group,
     and the share of tickers whose >= 70 trades underperform their own other trades.
  6. MEDIAN and ex-top-1% alongside every mean: the straddle's mean is tail-driven, so
     a skip that only removes a couple of lucky losers-to-be would not move the median.

Input: data/cache/rsi_straddle.parquet (written by run_rsi_conditioning_study.py).

Usage:
  PYTHONPATH=src .venv/bin/python3 run_rsi_straddle_walkforward.py
"""
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
rng = np.random.default_rng(20260916)

B = pd.read_parquet("data/cache/rsi_straddle.parquet")
B["yr"] = B.entry_date.dt.year
B["mo"] = B.entry_date.dt.to_period("M")
CUT = 70
GRID = [60, 65, 70, 75, 80, None]


def kept(d, cut):
    return d if cut is None else d[d.rsi.isna() | (d.rsi < cut)]


def summ(x):
    if len(x) == 0:
        return dict(n=0)
    r = x.roc
    m = r.groupby(x.mo).mean()
    q = r.quantile(0.99)
    return dict(n=len(x), mean=r.mean(), median=r.median(), win=100 * (r > 0).mean(),
                ex_top1=r[r < q].mean(),
                t_month=m.mean() / m.std() * np.sqrt(len(m)) if len(m) > 2 else np.nan)


# ---------- 1. fixed 70, year by year ----------
rows = []
for y, g in B.groupby("yr"):
    k, s = kept(g, CUT), g[g.rsi >= CUT]
    rows.append(dict(year=y, n=len(g), n_skip=len(s), all_mean=g.roc.mean(), kept_mean=k.roc.mean(),
                     lift=k.roc.mean() - g.roc.mean(), skip_mean=s.roc.mean() if len(s) else np.nan,
                     skip_median=s.roc.median() if len(s) else np.nan, all_median=g.roc.median(), kept_median=k.roc.median(),
                     all_ex_top1=summ(g)["ex_top1"], kept_ex_top1=summ(k)["ex_top1"]))
Y = pd.DataFrame(rows)
print("##### 1. FIXED RSI>=70 SKIP, EACH YEAR")
print(Y.round(2).to_string(index=False))
full = Y[Y.year < 2026]
print(f"years skip helped the mean: {(full.lift > 0).sum()}/{len(full)} full years "
      f"(+2026 partial: {'yes' if Y.iloc[-1].lift > 0 else 'no'}); "
      f"median helped: {(full.kept_median > full.all_median).sum()}/{len(full)}; "
      f"ex-top-1% helped: {(full.kept_ex_top1 > full.all_ex_top1).sum()}/{len(full)}")

# ---------- 2. expanding-window threshold choice ----------
print("\n##### 2. EXPANDING WINDOW: cutoff chosen on years < N, applied to N")
oos, picks = [], []
for N in range(2020, 2027):
    IS, TS = B[B.yr < N], B[B.yr == N]
    score = {c: kept(IS, c).roc.mean() for c in GRID}
    best = max(score, key=score.get)
    picks.append(dict(test_year=N, is_years=f"{IS.yr.min()}-{N-1}", chosen=best,
                      is_best_mean=score[best], is_none_mean=score[None],
                      oos_all=TS.roc.mean(), oos_kept=kept(TS, best).roc.mean(),
                      oos_fixed70=kept(TS, 70).roc.mean()))
    oos.append(kept(TS, best))
P = pd.DataFrame(picks)
print(P.round(2).to_string(index=False))
O = pd.concat(oos)
T = B[B.yr >= 2020]
F70 = kept(T, 70)
print("\npooled 2020-2026 test years:")
print(pd.DataFrame({"no filter": summ(T), "walk-forward cutoff": summ(O), "fixed 70": summ(F70)}).T.round(2).to_string())

# ---------- 3. within-week placebo ----------
print("\n##### 3. WITHIN-WEEK PLACEBO (5,000 shuffles of RSI inside each entry week)")
d = B[B.rsi.notna()].copy()
wk = d.entry_date.dt.to_period("W-FRI").values
real_lift = kept(B, CUT).roc.mean() - B.roc.mean()
real_med = kept(B, CUT).roc.median() - B.roc.median()
nan_roc = B[B.rsi.isna()].roc.values
order = np.argsort(wk, kind="stable")
roc_s, rsi_s, wk_s = d.roc.values[order], d.rsi.values[order], wk[order]
bounds = np.flatnonzero(np.r_[True, wk_s[1:] != wk_s[:-1], True])
lifts, meds = np.empty(5000), np.empty(5000)
for i in range(5000):
    perm = np.empty_like(rsi_s)
    for a, b in zip(bounds[:-1], bounds[1:]):
        perm[a:b] = rng.permutation(rsi_s[a:b])
    keep = np.r_[roc_s[perm < CUT], nan_roc]
    lifts[i] = keep.mean() - B.roc.mean()
    meds[i] = np.median(keep) - B.roc.median()
print(f"real mean lift {real_lift:+.2f}pp  placebo mean {lifts.mean():+.2f}  95th pct {np.percentile(lifts, 95):+.2f}  "
      f"p = {(lifts >= real_lift).mean():.4f}")
print(f"real median lift {real_med:+.2f}pp  placebo mean {meds.mean():+.2f}  95th pct {np.percentile(meds, 95):+.2f}  "
      f"p = {(meds >= real_med).mean():.4f}")

# ---------- 4. plateau ----------
print("\n##### 4. PLATEAU: kept sleeve by cutoff (full sample, in-sample by construction)")
pl = {("none" if c is None else f">={c} skipped"): {**summ(kept(B, c)), "n_skipped": len(B) - len(kept(B, c))}
      for c in [None, 60, 65, 70, 75, 80, 85]}
print(pd.DataFrame(pl).T.round(2).to_string())

# ---------- 5. breadth ----------
print("\n##### 5. BREADTH")
S = B[B.rsi >= CUT]
print(f"skipped trades {len(S)} across {S.ticker.nunique()} tickers; top-5 tickers by count: "
      f"{S.ticker.value_counts().head(5).to_dict()}")
loo = []
for t in S.ticker.unique():
    rest_s, rest_k = S[S.ticker != t], kept(B[B.ticker != t], CUT)
    loo.append(dict(ticker=t, n=(S.ticker == t).sum(), gap=rest_s.roc.mean() - rest_k.roc.mean()))
L = pd.DataFrame(loo).sort_values("gap", ascending=False)
print(f"skipped-minus-kept gap, full: {S.roc.mean() - kept(B, CUT).roc.mean():+.2f}pp; "
      f"leave-one-ticker-out range {L.gap.min():+.2f} .. {L.gap.max():+.2f}pp "
      f"(most influential ticker: {L.iloc[-1].ticker if abs(L.gap.min()) > abs(L.gap.max()) else L.iloc[0].ticker})")
tk = []
for t, g in B.groupby("ticker"):
    hi, lo = g[g.rsi >= CUT].roc, g[g.rsi.isna() | (g.rsi < CUT)].roc
    if len(hi) >= 3 and len(lo) >= 3:
        tk.append(hi.mean() < lo.mean())
print(f"tickers with >=3 trades each side: {len(tk)}; share where RSI>=70 trades underperform: {100*np.mean(tk):.0f}%")
