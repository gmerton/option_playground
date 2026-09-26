#!/usr/bin/env python3
"""
Vol-decay (Hawkes) exit vs the house 20-EMA close trail on precision-tier breakouts (pre-registered 2026-09-26,
before the run; from neurotrader wdsiZBIhAFw, queued in TEST_INDEX section 10 the same day; Gabe: "yes please").

WHY NEW. Every exit tested so far is price-based: 20-EMA / 10-EMA trails, BE and profit locks, trims, Qullamaggie's
partial-then-SMA trail [WL-4] (INVERTED). All were NULL or INVERTED against BASE. This exit uses a different input,
the decay of the volatility burst that came with the trend. neurotrader: "its main power is the exit. I use this
exact exit on many of my momentum-based strategies" -- asserted, never isolated (his entry and exit are one rule,
BTC hourly, gross).

POOL (same builder, fills and pools as WL-4, run_qullamaggie_exit.py): entry = breakout CLOSE + slip; initial stop =
  breakout-day low judged on the CLOSE; risk floor 2%, cap 25%; max hold 60 sessions; 2019-10 -> 2026-09.
  PRIMARY = precision-tier pool; second = generic house breakouts (ADR >= 3), because the tier is NULL on freeze-forward.
INDICATOR (daily translation of his hourly rule; no look-ahead):
  x_t   = (H_t / L_t - 1) * 100 / ADR_t     (ADR = the house 20-day ADR, already lagged one day)
  hk_t  = kappa * (hk_{t-1} * exp(-kappa) + x_t)          (his code, incl. the kappa normalisation)
  lo_t  = 5th percentile of hk over the PRIOR `lb` sessions (t-lb .. t-1)
ARMS (every arm on the SAME trades; initial stop kept in every arm; exit at the close, never intraday):
  BASE             20-EMA close trail from day 1 (the house rule)
  VD_k{K}_L{LB}    replace the EMA trail with: exit on the first close where hk_t < lo_t.
                   grid kappa {0.1, 0.2, 0.3} x lb {20, 60, 120} = 9 cells.
                   PRIMARY CELL = VD_k0.1_L60 (his kappa; lb ~ a quarter of daily bars).
  exploratory (primary params):
  VD_SWITCH        BASE's EMA trail until hk has closed above its prior-lb 95th percentile since entry (the burst he
                   says comes with a trend), then the vol-decay exit instead -- his mechanism in its most literal form.
  VD_OR_EMA        exit on whichever of the two fires first (a tighter hybrid).
MEASURE  arm - BASE in % return per trade (NOT R: the stop is identical, but judge in percent per house rule), paired,
  t clustered by entry date. R, hold days and the tail reported alongside: share of BASE's top-decile winners that the
  arm keeps, and mean % on those trades (the book's edge lives in the few big winners; an exit that fires when
  volatility calms could cut them in a quiet grind).
BAR  the primary cell passes only at |t| >= 3 with both halves (split 2023-01) the same sign, and not negative in a
  majority of years. Multiple testing: 11 arms -> Sidak |t| ~ 2.84, but the house 3 governs the primary. For the grid
  as a whole: p_opt = sign-flip permutation of the paired differences, one flip per ENTRY DATE applied to all 9 cells
  (keeps the cells' correlation), statistic = max |t| over the grid, 2,000 flips. Report plateau vs spike (share of the
  9 cells with the primary's sign).
PRIOR  NULL to slightly negative: every exit variant so far loses to the EMA trail or ties it, and a vol-decay exit is
  earlier in a smooth grind (Tito's grind archetype) -- expect it to cut the tail.
Local vs cloud: local (cached liquid panel, ~2k trades x 12 arms, minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_vol_decay_exit.py   (log -> data/studies/logs/vol_decay_exit.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/vol_decay_exit.log"
SLIP, HOLD, FLOOR, START, SPLIT = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01"
KAPPAS, LBS = (0.1, 0.2, 0.3), (20, 60, 120)
GRID = [f"VD_k{k}_L{lb}" for k in KAPPAS for lb in LBS]
PRIMARY = "VD_k0.1_L60"
ARMS = ["BASE"] + GRID + ["VD_SWITCH", "VD_OR_EMA"]


def hawkes(x: pd.DataFrame, kappa: float) -> pd.DataFrame:
    a = np.exp(-kappa); X = x.values; out = np.full_like(X, np.nan, dtype=float)
    prev = np.full(X.shape[1], np.nan)
    for t in range(len(X)):
        xt = X[t]
        cur = np.where(np.isnan(prev), xt, prev * a + np.nan_to_num(xt))
        cur = np.where(np.isnan(xt) & np.isnan(prev), np.nan, cur)
        out[t] = cur; prev = cur
    return pd.DataFrame(out * kappa, index=x.index, columns=x.columns)


def indicators(P):
    x = (P.high / P.low - 1) * 100 / P.adr
    ind = {}
    for k in KAPPAS:
        hk = hawkes(x, k)
        for lb in LBS:
            lo = hk.shift(1).rolling(lb, min_periods=lb // 2).quantile(0.05)
            hi = hk.shift(1).rolling(lb, min_periods=lb // 2).quantile(0.95)
            ind[(k, lb)] = (hk.values, lo.values, hi.values)
    return ind


def simulate(C, L, E20, ind, i, j, arm):
    entry = C[i, j] * (1 + SLIP); stop = L[i, j]; risk = entry - stop
    if arm == "BASE":
        key = None
    elif arm in ("VD_SWITCH", "VD_OR_EMA"):
        key = (0.1, 60)
    else:
        k, lb = arm[4:].split("_L"); key = (float(k), int(lb))
    hk, lo, hi = ind[key] if key else (None, None, None)
    burst = False
    end = min(i + HOLD, len(C) - 1); k = i
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop:
            break
        ema_hit = np.isfinite(E20[k, j]) and c < E20[k, j]
        vd_hit = key is not None and np.isfinite(hk[k, j]) and np.isfinite(lo[k, j]) and hk[k, j] < lo[k, j]
        if arm == "BASE" and ema_hit:
            break
        if arm in GRID and vd_hit:
            break
        if arm == "VD_OR_EMA" and (ema_hit or vd_hit):
            break
        if arm == "VD_SWITCH":
            if (vd_hit if burst else ema_hit):
                break
            if np.isfinite(hi[k, j]) and hk[k, j] > hi[k, j]:
                burst = True          # takes effect from the next close
    exit_px = C[k, j] * (1 - SLIP)
    return (exit_px - entry) / risk, 100 * (exit_px / entry - 1), k - i


def tstat_by_date(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def p_opt(T: pd.DataFrame, perms: int = 2000, seed: int = 20260926) -> tuple[float, float]:
    D = pd.DataFrame({a: T[a + "_pct"] - T.BASE_pct for a in GRID}).groupby(T.date).mean()  # date-cluster means
    obs = np.nanmax(np.abs(D.mean() / D.std(ddof=1) * np.sqrt(len(D))))
    rng = np.random.default_rng(seed); X = D.values; n = len(X); null = np.empty(perms)
    for b in range(perms):
        s = rng.choice([-1.0, 1.0], size=(n, 1)); Y = X * s
        null[b] = np.nanmax(np.abs(Y.mean(0) / Y.std(0, ddof=1) * np.sqrt(n)))
    return float(obs), float((np.sum(null >= obs) + 1) / (perms + 1))


def run_pool(label, mask, P, ind, lines, tag):
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    m = mask[mask.index >= START]; off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP); risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C) \
                or not np.isfinite(ADR[i, j]):
            continue
        rec = dict(date=P.close.index[i], sym=P.close.columns[j])
        for a in ARMS:
            r, pc, held = simulate(C, L, E20, ind, i, j, a)
            rec[a], rec[a + "_pct"], rec[a + "_held"] = r, pc, held
        rows.append(rec)
    T = pd.DataFrame(rows); T["date"] = pd.to_datetime(T.date)
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates "
                 f"({T.date.min().date()} -> {T.date.max().date()})")
    h1 = T.date < SPLIT
    top = T.BASE_pct >= T.BASE_pct.quantile(0.9)
    out = []
    for a in ARMS:
        dp = T[a + "_pct"] - T.BASE_pct
        yrs = dp.groupby(T.date.dt.year).mean()
        out.append(dict(arm=a + (" *P*" if a == PRIMARY else ""), pct=T[a + "_pct"].mean(), R=T[a].mean(),
                        held=T[a + "_held"].mean(), d_pct=dp.mean(), t_pct=tstat_by_date(dp, T.date),
                        h1=dp[h1].mean(), h2=dp[~h1].mean(), yrs_neg=f"{(yrs < 0).sum()}/{len(yrs)}",
                        d_R=(T[a] - T.BASE).mean(), top10_pct=T.loc[top, a + "_pct"].mean(),
                        win=100 * (T[a + "_pct"] > 0).mean()))
    S = pd.DataFrame(out)
    lines.append("arm - BASE, paired, t clustered by entry date; % per trade; top10_pct = mean % on BASE's top-decile trades")
    lines.append(S.round(3).to_string(index=False))
    Y = pd.DataFrame({a: (T[a + "_pct"] - T.BASE_pct).groupby(T.date.dt.year).mean() for a in ARMS[1:]})
    Y["n"] = T.groupby(T.date.dt.year).size()
    lines.append("per year, arm - BASE (% per trade):\n" + Y.round(2).T.to_string())
    obs, p = p_opt(T)
    sgn = np.sign(S.set_index("arm").loc[PRIMARY + " *P*"].d_pct)
    same = (np.sign(S[S.arm.str.replace(" *P*", "", regex=False).isin(GRID)].d_pct) == sgn).sum()
    lines.append(f"grid: max |t| {obs:.2f}, p_opt {p:.4f} (2,000 date-level sign flips, all 9 cells); "
                 f"{same}/9 cells share the primary's sign")
    T.to_parquet(REPO / f"data/studies/logs/vol_decay_exit_{tag}_trades.parquet", index=False)
    return S, p


def main():
    P, brk, prec = build()
    ind = indicators(P)
    lines = ["# Vol-decay (Hawkes) exit vs the 20-EMA trail (pre-registration in the docstring)"]
    Sp, pp = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, ind, lines, "precision")
    Sg, pg = run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, ind, lines, "generic")
    print("\n".join(lines))
    r = Sp.set_index("arm").loc[PRIMARY + " *P*"]
    ok = abs(r.t_pct) >= 3 and np.sign(r.h1) == np.sign(r.h2)
    print(f"\nPRIMARY CELL {PRIMARY} - BASE (precision, %): {r.d_pct:+.3f}pp t {r.t_pct:+.2f} halves "
          f"{r.h1:+.3f}/{r.h2:+.3f} years negative {r.yrs_neg} | R {r.d_R:+.3f} | held {r.held:.1f}d vs BASE "
          f"{Sp.iloc[0].held:.1f}d | top-decile {r.top10_pct:+.2f}% vs BASE {Sp.iloc[0].top10_pct:+.2f}%")
    print(f"BAR: {'PASS' if ok else 'NOT MET'} (|t| >= 3, halves same sign); grid p_opt precision {pp:.4f}, generic {pg:.4f}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
