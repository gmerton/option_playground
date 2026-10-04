#!/usr/bin/env python3
"""
STRONGEST BOUNCE SINCE THE CORRECTION'S KEY LOW (pre-registered 2026-10-03, before the run; queued 2026-09-30 from
Ariel -dv_2h61a2o / Richard / Boboch)

WHY. Gabe 2026-10-03: far more stocks sit at 20-day lows than highs (book gate OFF on net highs-lows); neither buying
strategy can buy beaten-down names as they start rising (the precision tier needs <= 15% off the 52-week high, momentum
ranks them last). The weak-tape test (2026-09-24) found that rebounds out of breadth washouts are led by what FELL, not
by the names that held up (STRONG -0.69pp, t -1.50). So: at the moment breadth starts to recover, do the names that have
bounced hardest off the washout's low keep leading?

EPISODES (identical to run_weak_tape_leaders.py): liquid_panel_2009, eligible = ADDV50 >= $50M, price >= $5, not suspect;
  breadth = % of eligible names above their 50 SMA; an episode starts on the first close < 35% after breadth was >= 45%.
  KEY LOW  = the lowest-breadth close from the episode start up to day 0 (known at day 0).
  DAY 0    = the first close after the key low with breadth back >= 35% (the turn; implementable at that close).
  An episode with no day 0 before the next episode start is dropped (counted).
SCORE at day 0: BOUNCE = close[day 0] / close[key low] - 1, over eligible names.
ARMS (entry at the day-0 close, held 20 and 40 sessions, no stop):
  TOP     top quintile of BOUNCE
  BEATEN  names >= 25% below their prior 252-session high at the KEY LOW that are also in the top BOUNCE quintile
          (the direct form of Gabe's question: beaten-down names once they start rising)
  BOTTOM  bottom quintile of BOUNCE (reported)
CONTROL: the ADR-matched field = all other eligible names on day 0 in the same ADR band (bands 0-2-3-4-6+%), the
  weak-tape test's construction. Excess = arm return minus its band's field mean, averaged per episode.
PRIMARY: TOP 40-session excess, one observation per episode, t across episodes. KEY SECONDARY: BEATEN, same metric.
BAR (discovery): t >= 3, both halves (split 2018-01-01) > 0, >= 70% of episodes positive. Expected power LOW (~40-60
  episodes); UNDERPOWERED is an acceptable outcome.
⚠ SURVIVOR PANEL: names liquid as of 2026. Beaten-down names that went on to fail are missing, which FLATTERS the BEATEN
  arm most of all. A pass on BEATEN must be re-tested on the survivorship-free chain_spot series before it counts.
Reported, not a pass: 20-session horizon; BOTTOM; TOP vs BOTTOM; per-year; days from episode start to day 0; and the
  live episode (start, key low, whether day 0 has happened, today's TOP / BEATEN names if it has).

  PYTHONPATH=src:. .venv/bin/python3 run_washout_bounce_leaders.py
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/studies/washout_bounce_leaders_2026-10-03"
LO, HI_RESET, BEATEN_OFF = 35.0, 45.0, 0.75
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    p = Panel.from_long(raw)
    C, H, L = p.close, p.high, p.low
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    sma50 = C.rolling(50).mean()
    denom = (elig & sma50.notna()).sum(axis=1)
    breadth = 100 * ((C > sma50) & elig & sma50.notna()).sum(axis=1) / denom
    breadth = breadth[denom >= 0.5 * denom.rolling(20, min_periods=5).median().shift(1).fillna(denom)]
    breadth = breadth[breadth.index >= "2010-01-01"]
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    band = pd.DataFrame(np.select([(adr >= lo) & (adr < hi) for lo, hi in BANDS], range(len(BANDS)), -1),
                        index=adr.index, columns=adr.columns)
    idx = C.index

    eps, armed = [], True
    for d, b in breadth.items():
        if armed and b < LO:
            eps.append(d); armed = False
        elif not armed and b >= HI_RESET:
            armed = True

    def excess(d0, h, mask):
        i = idx.get_loc(d0)
        if i + h >= len(idx):
            return np.nan, 0
        fwd = C.iloc[i + h] / C.iloc[i] - 1
        ok = elig.loc[d0] & fwd.notna(); bd = band.loc[d0]
        arm, fld = ok & mask, ok & ~mask
        if arm.sum() < 3:
            return np.nan, int(arm.sum())
        ex = []
        for k in range(len(BANDS)):
            a, b = fwd[arm & (bd == k)], fwd[fld & (bd == k)]
            if len(a) and len(b) >= 10:
                ex.append((a - b.mean()).values)
        return (100 * np.concatenate(ex).mean() if ex else np.nan), int(arm.sum())

    rows, dropped, live = [], 0, None
    for n, s in enumerate(eps):
        nxt = eps[n + 1] if n + 1 < len(eps) else None
        w = breadth[(breadth.index >= s) & ((breadth.index < nxt) if nxt is not None else True)]
        # day 0 = first close >= 35% after the running key low; the key low is the min so far at that point
        d0, klow = None, None
        run_min, run_min_d = np.inf, None
        for d, b in w.items():
            if b < run_min:
                run_min, run_min_d = b, d
            if d > s and b >= LO and run_min_d is not None and d > run_min_d:
                d0, klow = d, run_min_d; break
        if d0 is None:
            if nxt is None:
                live = dict(start=s.date(), key_low=run_min_d.date(), key_low_breadth=round(run_min, 1), day0=None)
            else:
                dropped += 1
            continue
        e = elig.loc[d0] & C.loc[klow].notna()
        bounce = (C.loc[d0] / C.loc[klow] - 1).where(e)
        q80, q20 = bounce.quantile(0.8), bounce.quantile(0.2)
        top, bot = (bounce >= q80) & e, (bounce <= q20) & e
        beaten = top & (C.loc[klow] <= BEATEN_OFF * hi252.loc[klow])
        rec = dict(start=s.date(), key_low=klow.date(), day0=d0.date(), days_to_d0=idx.get_loc(d0) - idx.get_loc(s),
                   key_low_breadth=round(breadth[klow], 1), n_elig=int(e.sum()))
        for h in (20, 40):
            for name, m in (("top", top), ("beaten", beaten), ("bottom", bot)):
                rec[f"{name}_{h}"], rec[f"n_{name}"] = excess(d0, h, m)
        rows.append(rec)
        if nxt is None:
            live = dict(start=s.date(), key_low=klow.date(), day0=d0.date(),
                        top=" ".join(bounce[top].sort_values(ascending=False).index[:25]),
                        beaten=" ".join(bounce[beaten].sort_values(ascending=False).index[:25]))
    E = pd.DataFrame(rows)
    E.to_csv(f"{OUT}_episodes.csv", index=False)

    def cell(col):
        x = E[col].dropna(); d = pd.to_datetime(E.loc[x.index, "day0"])
        return x.mean(), tstat(x), len(x), (x > 0).mean(), x[d < SPLIT].mean(), x[d >= SPLIT].mean()

    m, t, n, pos, h1, h2 = cell("top_40")
    v = "PASS" if (t >= 3 and h1 > 0 and h2 > 0 and pos >= 0.7) else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")
    L_ = [f"# Strongest bounce since the washout's key low ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
          f"{len(eps)} washout episodes 2010 →; scored {len(E)}; dropped (no day 0 before the next episode) {dropped}. "
          f"Median sessions from episode start to day 0: {E.days_to_d0.median():.0f}.", "",
          f"**PRIMARY TOP-bounce quintile, 40-session ADR-matched excess: {v}** — {m:+.2f}pp, t {t:.2f}, n {n} episodes, "
          f"{pos:.0%} positive, halves {h1:+.2f} / {h2:+.2f}", ""]
    for lab, col in (("KEY SECONDARY BEATEN (>= 25% off the high at the key low) & top bounce, 40d", "beaten_40"),
                     ("TOP, 20d", "top_20"), ("BEATEN, 20d", "beaten_20"), ("BOTTOM, 40d", "bottom_40"), ("BOTTOM, 20d", "bottom_20")):
        a = cell(col)
        L_.append(f"- {lab}: {a[0]:+.2f}pp, t {a[1]:.2f}, n {a[2]}, {a[3]:.0%} positive, halves {a[4]:+.2f} / {a[5]:+.2f}")
    tb = (E.top_40 - E.bottom_40).dropna()
    L_ += [f"- TOP − BOTTOM, 40d: {tb.mean():+.2f}pp, t {tstat(tb):.2f}", "",
           "⚠ Survivor panel: the BEATEN arm is the most flattered (beaten names that later failed are missing).", "",
           "## Live episode", "", str(live), "", "## Episodes", "",
           E[["start", "key_low", "day0", "days_to_d0", "key_low_breadth", "n_top", "top_40", "n_beaten", "beaten_40", "bottom_40"]].round(2).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L_) + "\n")
    print("\n".join(L_[:16]))


if __name__ == "__main__":
    main()
