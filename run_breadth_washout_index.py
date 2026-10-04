#!/usr/bin/env python3
"""
[AH-2] BREADTH WASHOUT -> INDEX BOUNCE, AND AS A BOOK-GATE RE-ENTRY (pre-registered 2026-10-03, before the run)

WHY. Ariel 2026-10-03 (OpTzYiMBNOQ): stocks have lived under their 50-day for weeks while QQQ sits at an all-time high;
"when we're getting this persistence of weakness around the market, it tends to lead to a bit of a market bounce."
Gabe 2026-10-03: there will be an opportunity here. We are in a washout episode since 2026-09-15 with the book gate OFF.
Neither the names that held up (weak-tape leaders, t -1.50) nor the first to bounce (strongest bounce, t -0.84) led the
next 40 days; this asks the index-level question, and whether the washout should re-open the book gate.

EPISODES (identical to run_weak_tape_leaders.py / run_washout_bounce_leaders.py): liquid_panel_2009, eligible = ADDV50 >=
  $50M, price >= $5, not suspect; breadth = % of eligible names above their 50 SMA; an episode starts (DAY 0) on the first
  close < 35% after breadth was >= 45%. ~61 episodes 2010-26. ⚠ survivor-panel breadth (2026's liquid names).
OUTCOME: index ETF return from the DAY-0 close to the close h sessions later (adjusted, from the same panel).
  Excess = that return minus the mean h-session return over ALL sessions 2010-01 -> the panel end (the unconditional drift).
PRIMARY: SPY, h = 20, excess averaged over episodes, t across episodes (one observation each).
BAR (discovery): t >= 3, both halves (split 2018-01-01) > 0, >= 60% of episodes positive. Expected power LOW (~60
  episodes, overlapping in clusters); UNDERPOWERED is an acceptable outcome.
REPORTED, not a pass:
  - QQQ and IWM; h = 10 and 40; a deeper threshold (first close < 25% after >= 45%);
  - NARROW-TAPE subset = the current situation: SPY within 5% of its 252-session high at DAY 0;
  - the BOOK-GATE OVERRIDE: the house breakout R030 book (run_luk_regime_book_switch.py, ENTRY_GATE arm) with the gate
    forced ON for the 20 sessions after each DAY 0 (WASHOUT_OVERRIDE) vs the plain ENTRY_GATE: CAGR, max DD and the
    monthly log-return difference (NW t), 2010-01 -> 2025-10;
  - per-episode table and the live episode.
PRIOR ~35%: washout bounces are a classic short-horizon mean-reversion effect and our one index pass (the dip rule,
  t 3.72) is the same family; but shallow episodes (median 2 sessions from start to recovery) dilute it.

  PYTHONPATH=src:. .venv/bin/python3 run_breadth_washout_index.py
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/studies/breadth_washout_index_2026-10-03"
SPLIT = pd.Timestamp("2018-01-01")
P0, P1 = pd.Timestamp("2010-01-04"), pd.Timestamp("2025-10-31")


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def episodes(breadth: pd.Series, lo: float, reset: float = 45.0) -> list:
    eps, armed = [], True
    for d, b in breadth.items():
        if armed and b < lo:
            eps.append(d); armed = False
        elif not armed and b >= reset:
            armed = True
    return eps


def main() -> None:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    idxs = raw[raw.ticker.isin(["SPY", "QQQ", "IWM"])].pivot(index="date", columns="ticker", values="close").sort_index()
    idxs.index = pd.to_datetime(idxs.index)
    hi = raw[raw.ticker == "SPY"].set_index("date").high.sort_index(); hi.index = pd.to_datetime(hi.index)
    spy_hi252 = hi.shift(1).rolling(252, min_periods=200).max()
    st = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    p = Panel.from_long(st)
    C = p.close
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    sma50 = C.rolling(50).mean()
    denom = (elig & sma50.notna()).sum(axis=1)
    breadth = 100 * ((C > sma50) & elig & sma50.notna()).sum(axis=1) / denom
    breadth = breadth[denom >= 0.5 * denom.rolling(20, min_periods=5).median().shift(1).fillna(denom)]
    breadth = breadth[breadth.index >= "2010-01-01"]
    I = idxs.reindex(breadth.index)

    def fwd(sym, h):
        return I[sym].shift(-h) / I[sym] - 1

    def cell(eps, sym, h, sub=None):
        f = fwd(sym, h); base = f[f.index >= "2010-01-01"].mean()
        x = pd.Series({d: f.get(d, np.nan) - base for d in eps if sub is None or sub(d)}).dropna() * 100
        d = pd.to_datetime(x.index)
        return x.mean(), tstat(x), len(x), (x > 0).mean(), x[d < SPLIT].mean(), x[d >= SPLIT].mean()

    E35, E25 = episodes(breadth, 35.0), episodes(breadth, 25.0)
    m, t, n, pos, h1, h2 = cell(E35, "SPY", 20)
    v = "PASS" if (t >= 3 and h1 > 0 and h2 > 0 and pos >= 0.6) else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")
    L = [f"# Breadth washout -> index bounce ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(E35)} episodes (< 35% after >= 45%), {len(E25)} deep (< 25%); 2010 -> {breadth.index[-1].date()}.", "",
         f"**PRIMARY SPY 20-session excess over the unconditional drift: {v}** — {m:+.2f}pp, t {t:.2f}, n {n}, "
         f"{pos:.0%} positive, halves {h1:+.2f} / {h2:+.2f}", "", "## Reported, not a pass", ""]
    narrow = lambda d: I.at[d, "SPY"] >= 0.95 * spy_hi252.get(d, np.nan) if d in spy_hi252.index else False
    for lab, eps, sym, h, sub in (("QQQ 20d", E35, "QQQ", 20, None), ("IWM 20d", E35, "IWM", 20, None),
                                  ("SPY 10d", E35, "SPY", 10, None), ("SPY 40d", E35, "SPY", 40, None),
                                  ("IWM 40d", E35, "IWM", 40, None), ("deep < 25%, SPY 20d", E25, "SPY", 20, None),
                                  ("deep < 25%, IWM 20d", E25, "IWM", 20, None),
                                  ("NARROW TAPE (SPY within 5% of its high), SPY 20d", E35, "SPY", 20, narrow),
                                  ("NARROW TAPE, IWM 20d", E35, "IWM", 20, narrow), ("NARROW TAPE, QQQ 20d", E35, "QQQ", 20, narrow)):
        a = cell(eps, sym, h, sub)
        L.append(f"- {lab}: {a[0]:+.2f}pp, t {a[1]:.2f}, n {a[2]}, {a[3]:.0%} positive, halves {a[4]:+.2f} / {a[5]:+.2f}")

    # book-gate override
    import run_breakout_sizing_sim as S
    import run_luk_regime_book_switch as B
    on, q = B.regime()
    ov = on.copy()
    pos_i = {d: i for i, d in enumerate(on.index)}
    for d in E35:
        if d in pos_i:
            i = pos_i[d]; ov.iloc[i + 1:i + 21] = True
    T, C2 = S.load()
    M = {}
    for name, series in (("ENTRY_GATE", on), ("WASHOUT_OVERRIDE", ov)):
        Eq = B.simulate(T, C2, B.R030, series, "entry", q)
        M[name] = Eq.resample("ME").last().pct_change().dropna()
    d = (np.log1p(M["WASHOUT_OVERRIDE"]) - np.log1p(M["ENTRY_GATE"]))
    d = d[(d.index >= P0) & (d.index <= P1)]
    L += ["", f"- BOOK-GATE OVERRIDE (gate forced ON 20 sessions after each episode start) − ENTRY_GATE: "
              f"{d.mean() * 100:+.2f}pp/month, NW t {B.nw_t(d.values):.2f}, halves {d[d.index < SPLIT].mean() * 100:+.2f} / {d[d.index >= SPLIT].mean() * 100:+.2f}",
          "", "| arm, 2010-01 → 2025-10 | CAGR | max DD | worst month |", "|---|---|---|---|"]
    for k, mm in M.items():
        L.append(B.stats(mm[(mm.index >= P0) & (mm.index <= P1)], k))
    rows = []
    for d0 in E35:
        rows.append(dict(day0=d0.date(), breadth=round(breadth[d0], 1), spy_vs_high=round((I.at[d0, "SPY"] / spy_hi252.get(d0, np.nan) - 1) * 100, 1),
                         spy20=round(fwd("SPY", 20).get(d0, np.nan) * 100, 2), iwm20=round(fwd("IWM", 20).get(d0, np.nan) * 100, 2),
                         qqq20=round(fwd("QQQ", 20).get(d0, np.nan) * 100, 2)))
    L += ["", "## Episodes (raw 20-session returns, %)", "", pd.DataFrame(rows).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:22]))


if __name__ == "__main__":
    main()
