#!/usr/bin/env python3
"""
RS-loss exit vs the house 20-EMA trail (pre-registered 2026-09-30, BEFORE running; spec copied from
data/optionsplay/videos/2026-04-20_9VylBGWJVT8/notes.md "RS-loss exit"; TEST_INDEX §10 row queued 2026-09-24).

Claim (Tony Zhang, OptionsPlay 2026-04-20 [21:05-22:26]): get out when the name drops off the leaderboard, i.e. when it
stops leading the S&P on its relative-strength horizons. No RS-based exit has been tested here; every house exit is
price-level.

RS state (fixed before the run): rs_h = (C_t / C_{t-h}) / (SPY_t / SPY_{t-h}) - 1 for h in {21, 63, 126};
  "leading" at h if rs_h > 0; tier = count of leading horizons (0..3).
Pools (entry = breakout CLOSE +SLIP, initial stop = breakout-day low judged on the close, risk floor 2%, cap 25%,
  60-session cap; same construction as run_qullamaggie_exit.py):
  PRIMARY  precision-tier house breakouts (run_precision_tier_control.build), 2019-10 -> 2026-09
  second   generic house breakouts (ADR >= 3)
Arms (identical entry, identical stop, identical cap; paired on the same trade, t clustered by entry date):
  A          20-EMA close trail (house)
  B PRIMARY  exit at the first close where the tier DROPS to <= 1 (a transition: some close since entry, entry day
             included, had tier >= 2), or A's exit, whichever comes first
  C          B's RS condition alone, no 20-EMA trail (stop + cap still apply)
  Pre-declared detail: a trade that enters at tier <= 1 and never reaches 2 is identical to A under B (share reported).
Metric: % per trade (primary), paired B - A; R second (2% floor, R capped +-20 shown). Report the share of trades where
  B != A and B - A on that subset only (the rest are identical by construction).
Control (secondary, the "clean result is a bug" check): on the B != A subset, RAND = exit A's trade at a session
  count drawn from B's own exit-count distribution on OTHER differing trades (permutation, truncated below A's exit),
  200 draws averaged. Tests whether B beats merely EXITING EARLIER.
Bar: |t| >= 3 on B - A (%), both halves (split 2023-01-01) the same sign, per-year table. Sidak k = 2 (B, C) ->
  |t| ~2.24 is looser, so the house 3 governs. Confound reports: by SPY 63d return tercile at entry; survivorship
  (panel = names liquid as of 2026) noted, not fixed.
Prior: low-moderate. Losing RS may just restate the price fall the 20-EMA trail already catches; where they differ
  (RS lost while the name holds its 20 EMA in a rising tape) an earlier exit cuts the right tail that is the edge.

Run: PYTHONPATH=src .venv/bin/python3 run_rs_loss_exit.py   (log -> data/studies/logs/rs_loss_exit.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/rs_loss_exit.log"
SLIP, HOLD, FLOOR, START, SPLIT = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01"
HORIZONS = (21, 63, 126)
ARMS = ("A", "B", "C")
NPERM = 200


def rs_tier(C: pd.DataFrame) -> np.ndarray:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "close"])
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    spy.index = pd.to_datetime(spy.index)
    spy = spy.reindex(pd.to_datetime(C.index))
    tier = np.zeros(C.shape)
    valid = np.ones(C.shape, dtype=bool)
    for h in HORIZONS:
        rs = C.div(C.shift(h)).div(spy / spy.shift(h), axis=0) - 1
        tier += (rs > 0).values
        valid &= rs.notna().values
    tier[~valid] = np.nan
    return tier, (spy / spy.shift(63) - 1).values


def simulate(C, E20, L, T, i, j):
    """Returns {arm: (exit index, R, pct)} plus entry tier and whether B had armed at entry."""
    entry = C[i, j] * (1 + SLIP)
    stop = L[i, j]
    risk = entry - stop
    end = min(i + HOLD, len(C) - 1)
    out = {}
    for arm in ARMS:
        armed = np.isfinite(T[i, j]) and T[i, j] >= 2
        k = i
        for k in range(i + 1, end + 1):
            c = C[k, j]
            if not np.isfinite(c):
                continue
            if c < stop:
                break
            if arm in ("A", "B") and np.isfinite(E20[k, j]) and c < E20[k, j]:
                break
            if arm in ("B", "C"):
                t = T[k, j]
                if armed and np.isfinite(t) and t <= 1:
                    break
                if np.isfinite(t) and t >= 2:
                    armed = True
        px = C[k, j] * (1 - SLIP)
        out[arm] = (k, (px - entry) / risk, 100 * (px / entry - 1))
    return out, entry, risk


def tstat_by_date(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def run_pool(label, mask, P, tier, spy63, lines, tag):
    C, L, E20 = P.close.values, P.low.values, P.ema20.values
    m = mask[mask.index >= START]
    off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP)
        risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C):
            continue
        res, entry, risk = simulate(C, E20, L, tier, i, j)
        rec = dict(date=P.close.index[i], sym=P.close.columns[j], i=i, j=j, tier0=tier[i, j], spy63=spy63[i],
                   entry=entry, risk=risk)
        for a in ARMS:
            rec[a + "_k"], rec[a], rec[a + "_pct"] = res[a][0] - i, res[a][1], res[a][2]
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["date"] = pd.to_datetime(T.date)
    h1 = T.date < SPLIT
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates "
                 f"({T.date.min().date()} -> {T.date.max().date()})")
    lines.append("entry tier distribution: " + T.tier0.value_counts(dropna=False).sort_index().to_string().replace("\n", "; "))
    out = []
    for a in ARMS:
        dp, dr = T[a + "_pct"] - T.A_pct, T[a] - T.A
        diff = T[a + "_k"] != T.A_k
        out.append(dict(arm=a, pct=T[a + "_pct"].mean(), R=T[a].mean(), R_cap20=T[a].clip(-20, 20).mean(),
                        hold=T[a + "_k"].mean(), d_pct=dp.mean(), t_pct=tstat_by_date(dp, T.date),
                        h1=dp[h1].mean(), h2=dp[~h1].mean(), d_R=dr.clip(-20, 20).mean(),
                        t_R=tstat_by_date(dr.clip(-20, 20), T.date), share_diff=100 * diff.mean(),
                        d_pct_on_diff=dp[diff].mean() if diff.any() else np.nan,
                        t_on_diff=tstat_by_date(dp[diff], T.date[diff]) if diff.sum() > 3 else np.nan))
    S = pd.DataFrame(out)
    lines.append("arm - A, paired, t clustered by entry date; % per trade; R clipped +-20")
    lines.append(S.round(3).to_string(index=False))

    # random-earlier-exit control on the B != A subset
    D = T[T.B_k != T.A_k].reset_index(drop=True)
    rng = np.random.default_rng(20260930)
    Cv = C
    if len(D) > 5:
        pool_k = D.B_k.values
        rand = np.zeros(len(D))
        for _ in range(NPERM):
            draw = rng.permutation(pool_k)
            for r_, row in enumerate(D.itertuples()):
                k = min(int(draw[r_]), int(row.A_k))
                k = max(k, 1)
                px = Cv[row.i + k, row.j]
                if not np.isfinite(px):
                    px = Cv[row.i + row.A_k, row.j]
                rand[r_] += 100 * (px * (1 - SLIP) / row.entry - 1)
        D["RAND_pct"] = rand / NPERM
        dbr = D.B_pct - D.RAND_pct
        dra = D.RAND_pct - D.A_pct
        lines.append(f"\nB != A subset n {len(D):,}: B {D.B_pct.mean():+.3f}%  RAND {D.RAND_pct.mean():+.3f}%  "
                     f"A {D.A_pct.mean():+.3f}%  | B - RAND {dbr.mean():+.3f}pp t {tstat_by_date(dbr, D.date):+.2f}  "
                     f"| RAND - A {dra.mean():+.3f}pp t {tstat_by_date(dra, D.date):+.2f}  "
                     f"| hold B {D.B_k.mean():.1f} vs A {D.A_k.mean():.1f} sessions")
    else:
        dbr = pd.Series(dtype=float)

    Y = pd.DataFrame({a + "-A": (T[a + "_pct"] - T.A_pct).groupby(T.date.dt.year).mean() for a in ("B", "C")})
    Y["n"] = T.groupby(T.date.dt.year).size()
    Y["B!=A %"] = (T.B_k != T.A_k).groupby(T.date.dt.year).mean() * 100
    lines.append("\nper year (% per trade):\n" + Y.round(2).to_string())
    T["spy_terc"] = pd.qcut(T.spy63, 3, labels=["low", "mid", "high"])
    Z = T.groupby("spy_terc", observed=True).apply(
        lambda g: pd.Series(dict(n=len(g), B_A=(g.B_pct - g.A_pct).mean(),
                                 t=tstat_by_date(g.B_pct - g.A_pct, g.date),
                                 diff_share=100 * (g.B_k != g.A_k).mean())))
    lines.append("\nby SPY 63d return tercile at entry (B - A, %):\n" + Z.round(3).to_string())
    T.drop(columns=["i", "j"]).to_parquet(REPO / f"data/studies/logs/rs_loss_exit_{tag}_trades.parquet", index=False)
    return S, dbr, D


def main():
    P, brk, prec = build()
    tier, spy63 = rs_tier(P.close)
    lines = ["# RS-loss exit vs 20-EMA trail (pre-registration in the docstring)"]
    Sp, dbr, D = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, tier, spy63, lines, "precision")
    run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, tier, spy63, lines, "generic")
    print("\n".join(lines))
    r = Sp.set_index("arm").loc["B"]
    print(f"\nPRIMARY B - A (precision, %): {r.d_pct:+.3f}pp t {r.t_pct:+.2f} halves {r.h1:+.3f}/{r.h2:+.3f} | "
          f"B!=A {r.share_diff:.1f}% of trades, {r.d_pct_on_diff:+.3f}pp on that subset (t {r.t_on_diff:+.2f})")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
