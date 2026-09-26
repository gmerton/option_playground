#!/usr/bin/env python3
"""
VOLATILITY-SCALED MOMENTUM: does scaling the 12-1 sleeve's exposure by its own recent volatility cut the momentum
crash without giving up return? (pre-registered 2026-09-26, before the run; Gabe: "yes please" -- ahead of the
sleeve's first lockbox formation 2026-09-30.)

WHY NEW. momentum_portfolio_2026-09-25 SUPPORTED 12-1 top-decile momentum (t 2.93) and listed the crash risk only
descriptively (worst excess months 2019-09 rotation, 2020-11 vaccine rotation). No sizing rule has been tested on it.
Barroso & Santa-Clara (2015) and Daniel & Moskowitz (2016): momentum's own realised volatility forecasts its crashes,
and scaling exposure by it roughly doubles momentum's Sharpe in US data 1927-2011. Untested here.

DATA / PORTFOLIO  identical to run_momentum_portfolio.py's PRIMARY: silver.chain_spot_daily (incl. delisted,
  split-adjusted), liquidity = 50-session option volume >= 1,000 and price >= $5, top decile of 12-1 (close t-21 /
  close t-252), equal weight, monthly, 10 bp/side on turnover. Formations 2011-01 -> 2026-01.
  ⚠ The window starts after the 2009 crash, the canonical case this rule exists for.
SCALING (no look-ahead)
  sigma_t  realised vol of the strategy's own DAILY returns (EW over the names it actually held) over the 126
           sessions before formation t, annualised.
  target   the expanding median of sigma up to t (first 12 formations: weight 1).
  weight   w_t = min(CAP, target / sigma_t); the rest in cash at 0%. PRIMARY CAP = 1.0 (de-risk only: a cash
           account, no leverage). Weight changes cost 10 bp x |dw|.
ARMS     UNSCALED (the tested sleeve) · VOLSCALED cap 1.0 (PRIMARY) · exploratory: cap 1.5 (leverage allowed),
         Daniel-Moskowitz bear state (w = 0.5 while the EW universe's trailing 24-month return < 0, else 1).
CONTROL  (declared now) STATIC: constant weight = the mean of the PRIMARY's weights over the sample. This holds the
         average exposure fixed, so a drawdown cut that comes only from owning less stock doesn't count.
         (The mean weight uses the whole sample -- acceptable in a control, never in the rule.)
BAR      PRIMARY vs STATIC. CANDIDATE only if ALL hold: (i) dSharpe > 0 with the 95% block-bootstrap interval
         (12-month blocks, 5,000 draws) above 0; (ii) max drawdown lower; (iii) mean of the worst 5 months better.
         If (ii)-(iii) hold but (i)'s interval spans 0: RISK RESHAPER (no return value, still usable as sizing).
         Otherwise NULL. Also reported vs UNSCALED, per-year, weights over time, and 2020-11 / 2019-09 months.
POWER    ~180 months and 2-3 momentum-crash episodes; a Sharpe difference needs a large effect to exclude 0.
Local vs cloud: local (cached chain_spot, minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_momentum_volscale.py   (log -> data/studies/logs/momentum_volscale.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_momentum_portfolio as MP

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_volscale.log"
COST, VOL_WIN, BLOCK, DRAWS = MP.COST, 126, 12, 5000


def portfolio_daily(C: pd.DataFrame, elig: pd.DataFrame, lookback=252, skip=21, top=0.10):
    """MP.portfolio's PRIMARY, plus the strategy's DAILY EW return series over the names actually held."""
    idx = C.index; Cv = C.values; E = elig.values
    R = C.pct_change(fill_method=None).values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in MP.month_ends(idx) if pd.Timestamp(MP.START) <= idx[i] <= pd.Timestamp(MP.END)]
    rows, prev_mom, prev_ew = [], set(), set()
    daily = pd.Series(np.nan, index=idx)
    for a, b in zip(me[:-1], me[1:]):
        if a - lookback < 0:
            continue
        score = Cv[a - skip] / Cv[a - lookback] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            continue
        names = np.flatnonzero(ok)
        cut = np.nanquantile(score[names], 1 - top)
        mom = names[score[names] >= cut]
        exit_i = np.minimum(b, last_valid[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        smom, sew = set(C.columns[mom]), set(C.columns[names])
        to_m = 1 - len(smom & prev_mom) / max(len(smom), 1)
        to_e = 1 - len(sew & prev_ew) / max(len(sew), 1)
        rows.append(dict(month=idx[b].to_period("M"), a=a, mom=r.reindex(mom).mean() - 2 * COST * to_m,
                         ew=r.mean() - 2 * COST * to_e, turnover=to_m))
        d = np.clip(R[a + 1:b + 1][:, mom], -0.9, 5)
        daily.iloc[a + 1:b + 1] = np.nanmean(d, axis=1)
        prev_mom, prev_ew = smom, sew
    return pd.DataFrame(rows).set_index("month"), daily


def stats(r: pd.Series) -> dict:
    cum = (1 + r).cumprod()
    return dict(mean=100 * r.mean(), vol=100 * r.std() * np.sqrt(12), sharpe=r.mean() / r.std() * np.sqrt(12),
                maxDD=100 * (1 - cum / cum.cummax()).max(), worst5=100 * r.nsmallest(5).mean(),
                cagr=100 * (cum.iloc[-1] ** (12 / len(r)) - 1))


def sharpe(x: np.ndarray) -> float:
    return x.mean() / x.std(ddof=1) * np.sqrt(12)


def boot_dsharpe(a: pd.Series, b: pd.Series, seed=20260926) -> tuple[float, float]:
    A, B = a.values, b.values; n = len(A); rng = np.random.default_rng(seed); out = np.empty(DRAWS)
    nb = int(np.ceil(n / BLOCK))
    for k in range(DRAWS):
        st = rng.integers(0, n - BLOCK + 1, nb)
        ix = np.concatenate([np.arange(s, s + BLOCK) for s in st])[:n]
        out[k] = sharpe(A[ix]) - sharpe(B[ix])
    return tuple(np.percentile(out, [2.5, 97.5]))


def scaled(P: pd.DataFrame, daily: pd.Series, cap: float) -> tuple[pd.Series, pd.Series]:
    sig = np.array([daily.iloc[max(0, a - VOL_WIN + 1):a + 1].dropna().std() * np.sqrt(252) for a in P.a])
    sig = pd.Series(sig, index=P.index)
    tgt = sig.expanding().median()
    w = (tgt / sig).clip(upper=cap)
    w.iloc[:12] = 1.0
    w = w.fillna(1.0)
    r = w * P.mom - COST * w.diff().abs().fillna(0)
    return r, w


def main():
    import run_dip_survivorship as DS
    out = ["# Vol-scaled 12-1 momentum (pre-registration in the docstring)"]
    d = DS.pull(); C, V = DS.adjust_and_clean(d)
    liq = ((V.rolling(50, min_periods=30).mean() >= MP.OPTVOL_MIN) & (C >= MP.PX_MIN)).fillna(False)
    P, daily = portfolio_daily(C, liq)
    base = P.mom
    rP, wP = scaled(P, daily, 1.0)
    rL, wL = scaled(P, daily, 1.5)
    ew24 = (1 + P.ew).rolling(24).apply(np.prod, raw=True).shift(1) - 1
    wD = pd.Series(np.where(ew24 < 0, 0.5, 1.0), index=P.index)
    rD = wD * P.mom - COST * wD.diff().abs().fillna(0)
    wbar = wP.mean()
    rS = wbar * P.mom
    arms = {"UNSCALED (sleeve as tested)": base, "VOLSCALED cap 1.0 *PRIMARY*": rP,
            f"STATIC w = {wbar:.2f} (control)": rS, "[expl] VOLSCALED cap 1.5": rL, "[expl] DM bear state": rD}
    T = pd.DataFrame({k: stats(v) for k, v in arms.items()}).T
    out.append(f"window {P.index.min()} -> {P.index.max()} ({len(P)} months); mean PRIMARY weight {wbar:.2f}, "
               f"min {wP.min():.2f}; months at w < 0.75: {(wP < 0.75).mean():.0%}")
    out.append(T.round(3).to_string())
    lo, hi = boot_dsharpe(rP, rS)
    lo2, hi2 = boot_dsharpe(rP, base)
    dS = sharpe(rP.values) - sharpe(rS.values)
    out.append(f"\nPRIMARY - STATIC: dSharpe {dS:+.3f}  95% block-bootstrap [{lo:+.3f}, {hi:+.3f}]")
    out.append(f"PRIMARY - UNSCALED: dSharpe {sharpe(rP.values) - sharpe(base.values):+.3f}  [{lo2:+.3f}, {hi2:+.3f}]")
    for m in ("2019-09", "2020-03", "2020-04", "2020-11", "2021-02", "2022-01"):
        p = pd.Period(m, "M")
        if p in P.index:
            out.append(f"  {m}: unscaled {100*base[p]:+.1f}%  primary {100*rP[p]:+.1f}% (w {wP[p]:.2f})  static {100*rS[p]:+.1f}%")
    Y = pd.DataFrame({k: v.groupby(v.index.year).apply(lambda s: 100 * ((1 + s).prod() - 1)) for k, v in
                      {"unscaled": base, "primary": rP, "static": rS}.items()})
    out.append("\nannual return %:\n" + Y.round(1).T.to_string())
    out.append("\nPRIMARY weight at each year-end: " + " ".join(f"{y}:{v:.2f}" for y, v in
                                                            wP.groupby(wP.index.year).last().items()))
    s, c = T.loc["VOLSCALED cap 1.0 *PRIMARY*"], T.loc[f"STATIC w = {wbar:.2f} (control)"]
    i_ok, ii_ok, iii_ok = lo > 0 and dS > 0, s.maxDD < c.maxDD, s.worst5 > c.worst5
    verdict = "CANDIDATE" if (i_ok and ii_ok and iii_ok) else ("RISK RESHAPER" if (ii_ok and iii_ok) else "NULL")
    out.append(f"\nBAR vs STATIC: (i) dSharpe>0 & CI>0 {i_ok} | (ii) maxDD {s.maxDD:.1f} vs {c.maxDD:.1f} {ii_ok} | "
               f"(iii) worst-5 {s.worst5:+.2f} vs {c.worst5:+.2f} {iii_ok}  ->  VERDICT: {verdict}")
    pd.DataFrame({"unscaled": base, "primary": rP, "w_primary": wP, "static": rS, "cap15": rL, "dm": rD}) \
        .to_csv(REPO / "data/studies/momentum_volscale_2026-09-26.csv")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
