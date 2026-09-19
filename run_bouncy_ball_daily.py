#!/usr/bin/env python3
"""
Lance Breitstein's "bouncy ball" short continuation, tested on DAILY bars 2019-2026.

Spec (data/lance_breitstein/principles/setup-grading-chart-nuance.md 2e), translated to daily bars and
pre-registered before the run:

  down leg      from a swing high, price falls >= LEG_ADR (default 3) ADR within <= LEG_MAX sessions
  bounces       >= 2 local bounce highs since that swing high, each strictly LOWER than the previous
                (fractal high: high > the highs of 2 sessions either side)
  fading        the last bounce retraces less than the one before it (the ball is dying)
  tightening    the 5-session range <= TIGHT (0.6) x the prior 5-session range, measured into the break
  support       the lowest low since the swing high
  trigger       a daily CLOSE below support
  entry         next session's open, short, 10 bps against
  stop          the trigger bar's high (his "trail on prior bar highs" at its widest first step)
  R             (entry - exit) / (stop - entry)

  arms          stop_close    stop on a close above it, else exit at the close N sessions later (N=5)
                t1R / t2R     first close at or below entry - 1R / - 2R, else stop, else N-session close
                trail_highs   cover on the first close above the PRIOR session's high (his trail)
                ema20         cover on the first close above the 20 EMA
  control       same name, a random session in the same month with no signal, same stop distance in %,
                same arms -- does the PATTERN matter, or is it just "short this name that month"?
  splits        2019-2022 vs 2023-2026; t clustered by signal date; bar |t| >= 3 and both halves positive.

Costs: 10 bps each side. NO borrow cost is modelled -- a positive result must survive that haircut later.

Usage: PYTHONPATH=src .venv/bin/python3 run_bouncy_ball_daily.py > data/studies/bouncy_ball_daily_2026-09-18.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

SLIP, LEG_ADR, LEG_MAX, TIGHT, HOLD = 0.0010, 3.0, 20, 0.6, 5
RNG = np.random.default_rng(20260918)
ARMS = ["stop_close", "t1R", "t2R", "trail_highs", "ema20"]


def fractal_highs(h: np.ndarray, k: int = 2) -> np.ndarray:
    out = np.zeros(len(h), bool)
    for i in range(k, len(h) - k):
        w = h[i - k:i + k + 1]
        if np.isfinite(h[i]) and h[i] == np.nanmax(w) and np.argmax(w) == k:
            out[i] = True
    return out


def score(C, H, L, E20, j, i, entry_i, stop, arm) -> float | None:
    """Short from entry_i's open; returns R."""
    entry = C[entry_i, j] if False else None
    return None


def main() -> None:
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L = p.close, p.high, p.low
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    e20 = C.ewm(span=20, adjust=False).mean()
    rng5 = (H.rolling(5).max() - L.rolling(5).min())
    tight = rng5 / rng5.shift(5)

    idx, cols = C.index, C.columns
    Cv, Ov, Hv, Lv, E20v, ADRv, TIGHTv, ELIGv = (C.values, O.values, H.values, L.values,
                                                 e20.values, adr.values, tight.values, elig.values)
    sig_rows = []
    for j, sym in enumerate(cols):
        h = Hv[:, j]
        fr = fractal_highs(h)
        fr_idx = np.flatnonzero(fr)
        if len(fr_idx) < 3:
            continue
        for a in range(len(fr_idx) - 2):
            hi_i = fr_idx[a]                                   # the swing high the leg starts from
            bounces = [fr_idx[b] for b in range(a + 1, len(fr_idx)) if fr_idx[b] <= hi_i + LEG_MAX]
            if len(bounces) < 2:
                continue
            bh = [h[x] for x in bounces]
            if not all(bh[k + 1] < bh[k] for k in range(len(bh) - 1)):   # each bounce lower than the last
                continue
            last = bounces[-1]
            seg_lo_i = int(np.nanargmin(Lv[hi_i:last + 1, j])) + hi_i
            support = Lv[seg_lo_i, j]
            a_pct = ADRv[last, j]
            if not np.isfinite(a_pct) or a_pct <= 0:
                continue
            drop_adr = (h[hi_i] - support) / (h[hi_i] * a_pct / 100)
            if drop_adr < LEG_ADR:
                continue
            # fading: the last bounce retraces less of its leg than the previous one did
            r1 = (bh[-1] - Lv[seg_lo_i, j]) / max(bh[-2] - Lv[seg_lo_i, j], 1e-9)
            if r1 >= 1.0:
                continue
            for i in range(last + 1, min(last + 1 + LEG_MAX, len(Cv) - HOLD - 2)):
                if not np.isfinite(Cv[i, j]):
                    continue
                if Cv[i, j] > bh[-1]:                          # bounce exceeded the last bounce high: dead
                    break
                if Cv[i, j] < support:                         # trigger: close below support
                    if not ELIGv[i, j] or not np.isfinite(TIGHTv[i, j]) or TIGHTv[i, j] > TIGHT:
                        break
                    sig_rows.append(dict(j=j, sym=sym, i=i, date=idx[i], year=idx[i].year,
                                         drop_adr=drop_adr, n_bounces=len(bh), tight=TIGHTv[i, j],
                                         stop=Hv[i, j], support=support, adr=a_pct))
                    break
    S = pd.DataFrame(sig_rows)
    print(f"signals: {len(S):,} on {S.sym.nunique()} names, {S.date.min().date()} -> {S.date.max().date()}"
          f" | median drop {S.drop_adr.median():.1f} ADR, bounces {S.n_bounces.median():.0f}, tight {S.tight.median():.2f}")

    def run(j, i, stop) -> dict | None:
        entry = Ov[i + 1, j] * (1 - SLIP)
        if not np.isfinite(entry) or not np.isfinite(stop) or stop <= entry:
            return None
        risk = stop - entry
        out = {}
        for arm in ARMS:
            r = np.nan
            for k in range(i + 1, min(i + 1 + HOLD, len(Cv))):
                c = Cv[k, j]
                if not np.isfinite(c):
                    continue
                if c > stop:
                    r = (entry - c * (1 + SLIP)) / risk
                    break
                if arm == "t1R" and c <= entry - risk:
                    r = 1.0
                    break
                if arm == "t2R" and c <= entry - 2 * risk:
                    r = 2.0
                    break
                if arm == "trail_highs" and k > i + 1 and c > Hv[k - 1, j]:
                    r = (entry - c * (1 + SLIP)) / risk
                    break
                if arm == "ema20" and c > E20v[k, j]:
                    r = (entry - c * (1 + SLIP)) / risk
                    break
            if not np.isfinite(r):
                k = min(i + HOLD, len(Cv) - 1)
                r = (entry - Cv[k, j] * (1 + SLIP)) / risk
            out[arm] = r
        return out

    recs, ctrl = [], []
    sig_key = {(r.j, r.i) for r in S.itertuples()}
    for r in S.itertuples(index=False):
        o = run(r.j, r.i, r.stop)
        if o:
            recs.append({**o, "sym": r.sym, "date": r.date, "year": r.year, "drop_adr": r.drop_adr,
                         "n_bounces": r.n_bounces, "tight": r.tight})
        # control: same name, random sessions in the same month, no signal, same stop % distance
        month = (idx.year == r.date.year) & (idx.month == r.date.month)
        cand = [k for k in np.flatnonzero(month) if (r.j, k) not in sig_key and k + HOLD + 2 < len(Cv)
                and np.isfinite(Cv[k, r.j]) and ELIGv[k, r.j]]
        if cand:
            stop_pct = r.stop / Ov[r.i + 1, r.j] - 1
            for k in RNG.choice(cand, size=min(3, len(cand)), replace=False):
                k = int(k)
                o = run(r.j, k, Ov[k + 1, r.j] * (1 + stop_pct))
                if o:
                    ctrl.append({**o, "sym": r.sym, "date": idx[k], "year": idx[k].year})
    T, K = pd.DataFrame(recs), pd.DataFrame(ctrl)
    T.to_parquet("data/cache/bouncy_ball_daily.parquet", index=False)

    def stats(x, arm):
        s = x[arm].dropna()
        if len(s) < 20:
            return dict(n=len(s))
        d = s.groupby(x.loc[s.index, "date"]).mean()
        return dict(n=len(s), meanR=s.mean(), medR=s.median(), win=100 * (s > 0).mean(),
                    t=d.mean() / d.std() * np.sqrt(len(d)))

    print(f"\n=== BOUNCY BALL (daily), {len(T):,} trades vs {len(K):,} control entries — R per trade ===")
    tab = pd.DataFrame({a: stats(T, a) for a in ARMS}).T
    tab["ctrl"] = [K[a].dropna().mean() for a in ARMS]
    tab["edge"] = tab.meanR - tab.ctrl
    print(tab.round(3).to_string())
    print("\n=== by half ===")
    h1, h2 = T[T.year <= 2022], T[T.year >= 2023]
    print(pd.DataFrame({"2019-22": {a: h1[a].mean() for a in ARMS}, "n1": {a: len(h1) for a in ARMS},
                        "2023-26": {a: h2[a].mean() for a in ARMS}, "n2": {a: len(h2) for a in ARMS}}).round(3).to_string())
    print("\n=== by year (trail_highs / ema20) ===")
    print(T.groupby("year")[["trail_highs", "ema20"]].agg(["mean", "size"]).round(3).to_string())
    print("\n=== by depth of the down leg (ADR units) ===")
    print(T.groupby(pd.cut(T.drop_adr, [3, 5, 8, 12, 100]), observed=True)[ARMS].mean()
          .join(T.groupby(pd.cut(T.drop_adr, [3, 5, 8, 12, 100]), observed=True).size().rename("n")).round(3).to_string())


if __name__ == "__main__":
    main()
