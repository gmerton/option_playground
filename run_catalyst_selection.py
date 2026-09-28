#!/usr/bin/env python3
"""
Catalyst as a SELECTION filter (Breitstein / Luk "in play"), TEST_INDEX §10, queued 2026-09-21, run 2026-09-28.

QUESTION. Buying the catalyst event fails (Tito B t 0.5; in-play movers −0.08R; DR-EP arm A −0.17R t −4.7; PEAD
NULL). The untested claim is that a recent catalyst marks the NAME as worth owning for the following weeks, i.e. it
is a universe filter, not an entry. Do names that had a catalyst-sized gap in the last 20 sessions earn more from a
random entry than un-flagged names on the same date with the same baseline volatility?

PRE-REGISTRATION (frozen before the first run; nothing below changed after it)
  Panel      liquid_panel_2009 (2009 → 2026-09), eligible = ADDV50 ≥ $50M, px ≥ $5, not near a split artefact;
             ETFs out. Test window 2010-03 → (needs 60 sessions of history before the flag window).
  Catalyst   gap day g: |open_g / close_{g-1} − 1| ≥ 3 × ADR_pre AND volume_g ≥ 3 × mean volume of the prior 50
             sessions, where ADR_pre = mean daily range % over sessions g−21 … g−1 (excludes the gap day).
             UP = open above the prior close; DOWN = below.
  Flag       on entry date t the name is FLAGGED if it had an UP catalyst in sessions t−20 … t−1 (the entry day
             itself is never the event).  Unflagged = no catalyst of either sign in t−20 … t−1.
  Entry      close of t, forward close-to-close return over h sessions (costs cancel in the contrast).
  Matching   baseline volatility measured BEFORE the flag window: ADRb = mean daily range % over t−60 … t−21, so the
             gap's own range cannot inflate it. Per date, eligible names are cut into ADRb quintiles; the date's
             excess = flagged-count-weighted mean over quintiles of (mean flagged − mean unflagged).
  Dates      non-overlapping: every h-th session; a date needs ≥ 5 flagged names.
  PRIMARY    UP flag, all eligible names, h = 20, ADR-matched excess; t over dates.
  Bar        |t| ≥ 3, both halves (split 2018-01-01) the same sign, per-year signs reported.
  Mechanism  (exploratory, names what the primary control varies) the primary control varies catalyst-ness AND the
             recent move. RET-matched arm: additionally match on the name's return over t−20 … t−1 (terciles within
             each ADR quintile). If the excess survives this, it is the catalyst; if it vanishes, it is momentum.
  Exploratory (not certifiable; Šidák over the 11 extra cells ≈ |t| 2.8): DOWN flag and ANY flag at h 20; UP at
             h 5 and h 60; UP inside the INT and HYB-B universes (`run_universe_test.build_masks`, 2020 →).
  Caveat     the panel is today's liquid names (survivorship lifts absolute returns; the same-date contrast is what
             is tested). Gap + volume is a news PROXY; earnings gaps dominate it.

Usage: PYTHONPATH=src .venv/bin/python3 run_catalyst_selection.py > data/studies/logs/catalyst_selection.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
SPLIT = pd.Timestamp("2018-01-01")
START = pd.Timestamp("2010-03-01")
ETF = {"SPY", "QQQ", "IWM", "RSP", "DIA"}


def load():
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(ETF)]
    p = Panel.from_long(raw)
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex_like(p.close)
    O, V = piv("open"), piv("volume")
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    return p, O, V, elig, raw


def flags(p, O, V):
    C, H, L = p.close, p.high, p.low
    rng = (H / L - 1) * 100
    adr_pre = rng.shift(1).rolling(20, min_periods=15).mean()           # g−20 … g−1 (shift 1 → excludes g)
    gap = (O / C.shift(1) - 1) * 100
    vol_ok = V >= 3 * V.shift(1).rolling(50, min_periods=30).mean()
    big = (gap.abs() >= 3 * adr_pre) & vol_ok
    up = (big & (gap > 0)).fillna(False)
    dn = (big & (gap < 0)).fillna(False)
    # flag at t = any event in t−20 … t−1
    win = lambda m: m.astype(int).shift(1).rolling(20, min_periods=1).sum().fillna(0) > 0
    adrb = rng.shift(21).rolling(40, min_periods=30).mean()             # t−60 … t−21
    ret20 = C.shift(1) / C.shift(21) - 1                                # t−20 … t−1 close-to-close
    return win(up), win(dn), up, dn, adrb, ret20


def excess(fr, flag, clean, elig, adrb, ret20, dates, ret_match=False, mask=None):
    """per-date ADR-matched (optionally also return-matched) flagged-minus-unflagged forward return."""
    out = {}
    base = elig if mask is None else (elig & mask)
    for d in dates:
        e = base.loc[d]
        f = flag.loc[d] & e
        u = clean.loc[d] & e
        if f.sum() < 5:
            continue
        a = adrb.loc[d].where(e)
        q = pd.qcut(a.rank(method="first"), 5, labels=False)
        r = fr.loc[d]
        cells = [q]
        if ret_match:
            rr = ret20.loc[d].where(e)
            t3 = rr.groupby(q).transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False) if s.notna().sum() >= 6 else s * np.nan)
            cells = [q, t3]
        df = pd.DataFrame(dict(r=r, f=f, u=u, q=q, t3=cells[1] if ret_match else 0)).dropna(subset=["r", "q", "t3"])
        num, den = 0.0, 0
        for _, g in df.groupby(["q", "t3"]):
            fg, ug = g[g.f], g[g.u]
            if len(fg) and len(ug):
                num += len(fg) * (fg.r.mean() - ug.r.mean())
                den += len(fg)
        if den >= 5:
            out[d] = num / den
    return pd.Series(out)


def summarise(s, label):
    t = s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 else np.nan
    h1, h2 = s[s.index < SPLIT], s[s.index >= SPLIT]
    return dict(cell=label, dates=len(s), excess_pp=100 * s.mean(), t=t, h1_pp=100 * h1.mean(), h2_pp=100 * h2.mean(),
                pos_dates=100 * (s > 0).mean())


def main():
    p, O, V, elig, raw = load()
    fu, fd, up, dn, adrb, ret20 = flags(p, O, V)
    fany = fu | fd
    clean = ~fany
    C = p.close
    print(f"panel {C.shape}, {C.index.min().date()} -> {C.index.max().date()}")
    ev = lambda m: int((m & elig).values.sum())
    print(f"catalyst days (eligible): UP {ev(up):,}  DOWN {ev(dn):,}")
    rows, per_year = [], None
    fr_cache = {}
    for h in (20, 5, 60):
        fr = C.shift(-h) / C - 1
        fr_cache[h] = fr
        dates = C.index[C.index >= START][::h]
        dates = dates[dates <= C.index[-1 - h]]
        cells = [("UP", fu)] if h != 20 else [("UP", fu), ("DOWN", fd), ("ANY", fany)]
        for lab, fl in cells:
            s = excess(fr, fl, clean, elig, adrb, ret20, dates)
            name = f"{'PRIMARY ' if (h == 20 and lab == 'UP') else ''}{lab} h{h} ADR-matched"
            rows.append(summarise(s, name))
            if h == 20 and lab == "UP":
                per_year = s.groupby(s.index.year).agg(["mean", "size"])
                per_year["mean"] *= 100
                prim = s
                sr = excess(fr, fl, clean, elig, adrb, ret20, dates, ret_match=True)
                rows.append(summarise(sr, "UP h20 ADR+RET-matched (mechanism)"))
                # flagged names' own mean forward return and share of dates, descriptive
                fl_n = (fl & elig).loc[dates].sum(axis=1)
                print(f"UP-flagged names per test date: median {fl_n.median():.0f}, p10 {fl_n.quantile(.1):.0f}, p90 {fl_n.quantile(.9):.0f}")
    # universe masks (INT, HYB-B) from the universe test, on the same panel
    try:
        from lib.studies.pattern_test import DailyPanel
        import run_universe_test as ut
        P = DailyPanel(open=O, high=p.high, low=p.low, close=C, adr=(p.high / p.low - 1).shift(1).rolling(20).mean() * 100,
                       elig=elig, ema20=C.ewm(span=20, adjust=False).mean())
        masks = ut.build_masks(P, raw)
        fr = fr_cache[20]
        dates = C.index[C.index >= pd.Timestamp(ut.START)][::20]
        dates = dates[dates <= C.index[-21]]
        for u in ("INT", "HYB-B"):
            s = excess(fr, fu, clean, elig, adrb, ret20, dates, mask=masks[u])
            rows.append(summarise(s, f"UP h20 inside {u} (2020-)"))
    except Exception as exc:  # the masks are exploratory; never block the primary
        print(f"(universe masks skipped: {exc})")
    T = pd.DataFrame(rows)
    print("\n" + T.round(3).to_string(index=False))
    print("\nPRIMARY per-year excess (pp, dates):")
    print(per_year.round(3).to_string())
    r = T.iloc[0]
    ok = abs(r.t) >= 3 and np.sign(r.h1_pp) == np.sign(r.h2_pp) == np.sign(r.t)
    print(f"\nPRE-REGISTERED BAR (primary): {'PASS' if ok else 'FAIL'}")
    prim.rename("excess").to_csv("data/studies/logs/catalyst_selection_primary_dates.csv")


if __name__ == "__main__":
    main()
