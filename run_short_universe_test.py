#!/usr/bin/env python3
"""
Is there a SHORT-selectable universe at all? (pre-registered 2026-09-23, before the first run)

THE GAP. Every maintained selection layer in this book was built and validated for LONGS — the preferred
list, INT, the precision tier, the breakout scorecard, the alert rubric. Q1 of `run_universe_test.py` asks
"does this universe select?" by comparing a random member's forward return against the eligible panel on
the same dates. **Nobody has ever run it looking for universes with NEGATIVE excess.** That is the short
analog of the question answered for longs on 2026-09-22, and it comes before any setup work: if no
universe produces materially negative forward returns, the rest of the short effort is not worth funding.

Every obvious short ANALOG of a long strategy is already dead (short 7-DTE straddle NULL with the long's
gates inverting at significance; bear call spreads 0-for-3; bouncy ball, counter-trend, pullback-short and
the capitulation scorecard all FAIL). So this does not look for a mirror. It asks the prior question:
**is there a population whose forward returns are bad enough to be worth being short?**

ARMS (5 short-candidate universes, all with a liquidity floor — a short needs borrow and an exit):
  INV-TT   the Trend Template inverted: close < 150 & 200 SMA, 150 < 200, 200 SMA FALLING, 50 < 150,
           close < 50 SMA, within 30% of the 252d LOW, RS percentile <= 30
  DOWN     plain downtrend: EMA9 < EMA21 < EMA50 and close < SMA50, 21 EMA declining
  LAGGARD  the pullback-short precondition: >= 30% below the 252d high, 50 SMA declining
  CRASH-H  the crash-leader veto INVERTED: >= 40% below the 252d high WHILE SPY is above a rising 200 SMA.
           A confirmed veto on the long side is a candidate signal on the short side; never tested.
  DIST     distribution: close < 200 SMA and RS percentile <= 20

⚠ TWO CONFOUNDS, both handled:
 1. **ADR.** Downtrending names are more volatile, and higher-ADR names have higher raw forward returns.
    Every cell is ADR-MATCHED — the benchmark is reweighted to the members' own ADR-decile mix on that
    date — so an arm cannot look good merely by holding calmer or wilder names. The ADR-matched column
    governs; raw is shown beside it.
 2. **A short is not a long with the sign flipped.** Beating the panel is enough for a long. A short must
    overcome the market's upward drift, borrow, and financing. So "less positive than the panel" is NOT
    shortable. **This reports the ABSOLUTE forward return as well as the excess, and the pass bar requires
    the absolute return to be negative.**

⚠ SURVIVORSHIP CUTS THE WRONG WAY HERE, and it matters more than it did for longs. The panel is today's
liquid names, so anything that was delisted, acquired or went to zero is absent — and that is precisely a
short's best outcome. The panel is therefore biased AGAINST finding short edge. Read a null as "not proven
on survivors" rather than "no edge exists", and read a positive as stronger than it looks.

PRE-REGISTERED PASS (declared before the first run): an arm passes only if, at the 20-day horizon,
  (a) ADR-matched excess is NEGATIVE with month-clustered |t| >= the Sidak bar below,
  (b) both halves of the sample agree in sign (split 2023-01-01), and
  (c) the ABSOLUTE mean forward return is negative.
5 arms x 2 horizons = 10 cells; Sidak at alpha 0.05 -> |t| >= 2.81. The house |t| >= 3 is the stricter of
the two, so **|t| >= 3 governs**.

PRIOR, stated now: the most likely outcome is that every arm has NEGATIVE excess but POSITIVE absolute
return — i.e. weak names underperform but still drift up — which would mean there is no short-selectable
universe on survivors and the short effort should go to index vol (where the book's only confirmed cells
already live: SPY 1-day short straddle on positive-gamma days, t 5.6) rather than to single-name shorts.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u run_short_universe_test.py
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import DailyPanel

START, SPLIT = "2020-01-01", "2023-01-01"
ADDV_MIN = 100e6
N_CELLS = 10
SIDAK_T = float(stats.norm.ppf(1 - (1 - (1 - 0.05) ** (1 / N_CELLS)) / 2))
BAR_T = max(3.0, SIDAK_T)
ARMS = ["INV-TT", "DOWN", "LAGGARD", "CRASH-H", "DIST"]


def build_masks(P: DailyPanel, raw: pd.DataFrame, spy: pd.Series) -> dict:
    C, H, L = P.close, P.high, P.low
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex(
        index=C.index, columns=C.columns)
    dolvol = piv("dolvol")
    sma50, sma150, sma200 = (C.rolling(n, min_periods=n).mean() for n in (50, 150, 200))
    e9, e21, e50 = (C.ewm(span=n, adjust=False).mean() for n in (9, 21, 50))
    hi252 = H.rolling(252, min_periods=200).max()
    lo252 = L.rolling(252, min_periods=200).min()
    addv = dolvol.rolling(50, min_periods=50).mean()
    rs = 2 * C / C.shift(63) + C / C.shift(126) + C / C.shift(189) + C / C.shift(252)
    rs_pct = rs.where(P.elig).rank(axis=1, pct=True) * 100
    adr = (H / L - 1).rolling(20).mean() * 100
    liq = addv >= ADDV_MIN

    # SPY in a healthy tape: above a rising 200 SMA (broadcast to every column)
    spy_s200 = spy.rolling(200, min_periods=200).mean()
    healthy = ((spy > spy_s200) & (spy_s200 > spy_s200.shift(20))).reindex(C.index).fillna(False)
    healthy_wide = pd.DataFrame(np.repeat(healthy.values[:, None], C.shape[1], axis=1),
                                index=C.index, columns=C.columns)

    m = {
        "INV-TT":  (C < sma150) & (C < sma200) & (sma150 < sma200) & (sma200 < sma200.shift(20))
                   & (sma50 < sma150) & (C < sma50) & (C <= 1.30 * lo252) & (rs_pct <= 30),
        "DOWN":    (e9 < e21) & (e21 < e50) & (C < sma50) & (e21 < e21.shift(5)),
        "LAGGARD": (C <= 0.70 * hi252) & (sma50 < sma50.shift(20)),
        "CRASH-H": (C <= 0.60 * hi252) & healthy_wide,
        "DIST":    (C < sma200) & (rs_pct <= 20),
    }
    out = {}
    for k, v in m.items():
        v = (v & liq & P.elig).shift(1).fillna(False).astype(bool)   # membership as of the PRIOR close
        v[v.index < START] = False
        out[k] = v
    out["_adr"] = adr.shift(1)
    return out


def per_date(P, m, fr, dates, adr, base):
    """Members' mean forward return, the ADR-matched benchmark, and the member count, per date."""
    mm = fr.where(m).loc[dates]
    dec = adr.loc[dates].rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int)
    panel_fr = fr.where(base).loc[dates]
    bench = {}
    for d in dates:
        md, pd_ = dec.loc[d].where(m.loc[d]), dec.loc[d].where(base.loc[d])
        w = md.value_counts(normalize=True)
        if w.empty:
            bench[d] = np.nan; continue
        g = panel_fr.loc[d].groupby(pd_).mean()
        common = w.index.intersection(g.index)
        bench[d] = float((w[common] / w[common].sum() * g[common]).sum()) if len(common) else np.nan
    return mm.mean(axis=1), pd.Series(bench), mm.count(axis=1)


def main() -> None:
    import run_precision_tier_control as pc
    P, _brk, _p = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    idx = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    masks = build_masks(P, raw, idx)
    adr, C = masks["_adr"], P.close
    base = P.elig.shift(1).fillna(False).astype(bool)

    print(f"panel {C.shape}, window {START} -> {C.index.max().date()}, ADDV floor ${ADDV_MIN/1e6:.0f}M")
    print(f"multiple testing: {N_CELLS} cells, Sidak |t| >= {SIDAK_T:.2f}; house bar 3.00 -> BAR {BAR_T:.2f}")
    print("⚠ survivorship biases this AGAINST finding short edge (delisted names absent)\n")

    print(f"{'arm':9s}{'names/day':>10s}{'ADR%':>7s}")
    for a in ARMS:
        m = masks[a][masks[a].index >= START]
        print(f"{a:9s}{int(m.sum(axis=1).median()):>10d}{float(adr.where(masks[a]).stack().median()):>7.2f}")

    rows = []
    for h in (20, 5):
        fr = C.shift(-h) / C - 1
        dates = C.index[C.index >= START][::h]
        dates = dates[dates <= C.index[-1 - h]]
        for a in ARMS:
            mean_r, bench, n = per_date(P, masks[a], fr, dates, adr, base)
            ok = n >= 5
            d = (mean_r - bench)[ok].dropna()
            absr = mean_r[ok].dropna()
            if len(d) < 30:
                continue
            t = d.mean() / d.std(ddof=1) * sqrt(len(d))
            h1, h2 = d[d.index < SPLIT], d[d.index >= SPLIT]
            rows.append(dict(horizon=f"{h}d", arm=a, dates=len(d),
                             abs_ret=100 * absr.mean(), excess_adj=100 * d.mean(), t=t,
                             h1=100 * h1.mean(), h2=100 * h2.mean(),
                             halves_agree=bool(np.sign(h1.mean()) == np.sign(h2.mean())),
                             passes=bool(d.mean() < 0 and abs(t) >= BAR_T
                                         and np.sign(h1.mean()) == np.sign(h2.mean())
                                         and absr.mean() < 0)))
    R = pd.DataFrame(rows)
    R.to_csv(pt.REPO / "data/studies/short_universe_test_2026-09-23.csv", index=False)

    for h in ("20d", "5d"):
        print(f"\n{'='*104}\n{h} horizon — ADR-matched. A short needs BOTH a negative excess AND a negative absolute return.\n{'='*104}")
        sub = R[R.horizon == h].sort_values("excess_adj")
        print(sub[["arm", "dates", "abs_ret", "excess_adj", "t", "h1", "h2", "halves_agree", "passes"]].round(3).to_string(index=False))

    n_pass = int(R.passes.sum())
    print(f"\ncells meeting ALL of (negative excess, |t| >= {BAR_T:.2f}, halves agree, NEGATIVE absolute return): {n_pass} of {len(R)}")
    neg_x = int((R.excess_adj < 0).sum()); neg_a = int((R.abs_ret < 0).sum())
    print(f"  cells with negative ADR-matched excess: {neg_x}/{len(R)}   with negative ABSOLUTE return: {neg_a}/{len(R)}")
    if neg_x and not neg_a:
        print("  ⟹ weak names underperform but still DRIFT UP: no short-selectable universe on survivors.")
    print("\nwrote data/studies/short_universe_test_2026-09-23.csv")


if __name__ == "__main__":
    main()
