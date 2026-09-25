#!/usr/bin/env python3
"""
Buying great stocks at a discount: the CONFIRMATION LADDER off a pullback low (pre-registered 2026-09-25, before any
run; Gabe: "buy at a local -- ideally global -- minimum; the hard part is a signal that we are reliably exiting it").

FRAMING. A local minimum is only known after price leaves it, so every exit-from-the-low signal buys certainty with
price. Earlier ledger rows each tested ONE trigger: pullback-low vs reclaim (run_reclaim_vs_pullback.py: the low was
1.3-1.8 ADR cheaper and returned no more), EMA pullbacks (FAIL vs the breakout), counter-trend >= 3 ADR (FAIL).
NEW AXIS: the whole trade-off CURVE -- for a ladder of increasingly strict confirmations, how often the low HOLDS,
how much premium above the low it costs, and whether any rung earns an excess return. Plus the "global minimum"
bonus: do lows at longer-term support hold more often?

DATA  data/cache/liquid_panel_2009.parquet (adjusted), 2010-01 -> 2026-08 (60-session exits land by 2026-09);
      harness eligibility (ADDV >= $50M, px >= $5) at the peak.
POPULATIONS (evaluated at the swing-high day)
  P1 PRIMARY   precision tier: ADR 4-7%, within 15% of the 252d high, 10>20>50 stack held 5-40 sessions.
  P2           broad uptrend: close > 50 SMA > 200 SMA, ADR >= 3%.
EPISODE  swing high = a day whose high is the highest of the last 10 sessions; the pullback's running LOW is the lowest
      low since. The episode opens the first close at which (peak high - running low) >= 1.0 ADR (ADR in $ at the
      peak) and runs until the close above the peak high or 30 sessions after the peak. A new lower low RESETS the
      candidate low (rungs not yet fired now key off the new low). One episode per peak.
LADDER (entry at the CLOSE of the first day each rung fires; each rung at most once per episode)
  K0  the close the pullback first reaches 1 ADR (anticipation: no confirmation at all)
  K1  first close above the HIGH of the candidate-low bar                       <- PRIMARY rung
  K2  K1 AND >= 2 sessions after the low bar with no lower low (a held higher low)
  K3  first close above the 5 EMA after the low bar
  K4  first close above the 21 EMA after the low bar
  K5  first close above the peak high (the reclaim / breakout)
MEASURES per entry
  hold20      no low below the candidate low in the 20 sessions after entry (the "reliably exiting" rate)
  premium     (entry - candidate low) in ADR
  fwd         % return entry close -> close +h, h in {20 (PRIMARY), 60}; 10 bp per side; NO stop (% not R)
  CONTROL     (declared now) SAME-DATE other names in the same population and ADR tercile, not themselves in an
              episode that day -- holds the DATE fixed and moves the name. (The same-name +/-60 random-day control
              is NOT used: it was shown outcome-selected in the VCP retraction.)
  excess      fwd - control, t clustered by month
BAR   PRIMARY CELL = P1 x K1 x +20 excess. Cells = 6 rungs x 2 populations x 2 horizons = 24 -> Sidak(24) at 0.05 ->
      |t| >= 3.07 GOVERNS (stricter than the house 3), both halves (split 2018-01) the same sign, majority of years.
      A rung is a SIGNAL only if its excess passes; hold20 and premium are the descriptive curve.
POLICY COMPARISON (secondary, per episode, paired): enter at rung Kj vs at K0, scoring 0 when the rung never fires --
      does waiting for confirmation beat buying the dip, counting the trades it skips?
GLOBAL-MIN BONUS (exploratory, not bar-bearing): tag the candidate low as AT SUPPORT if within 0.5 ADR of the 50 SMA,
      the 200 SMA, or the prior base high (highest high of sessions peak-60 .. peak-20); compare hold20 and excess
      at K1, tagged vs untagged.
PRIOR (stated now): NULL on excess -- the reclaim study found the discount is eaten by the lows that fail. The curve
      itself (hold rate vs premium) is informative either way.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_low_confirmation_ladder.py   (log -> data/studies/logs/low_confirmation_ladder.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.studies.pattern_test import load_panel, SLIP

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/low_confirmation_ladder.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
START, END, SPLIT = "2010-01-01", "2026-06-30", "2018-01-01"
RUNGS = ["K0", "K1", "K2", "K3", "K4", "K5"]
HORIZONS, PEAK_N, DEPTH, MAX_LEN = (20, 60), 10, 1.0, 30
T_BAR = 3.07


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def features(P):
    C, H, L = P.close, P.high, P.low
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    stack = stack_run(C, adr=adr)
    s50, s200 = C.rolling(50).mean(), C.rolling(200).mean()
    p1 = (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (stack >= 5) & (stack <= 40)
    p2 = (C > s50) & (s50 > s200) & (adr >= 3)
    elig = P.elig.fillna(False)
    return dict(C=C.values, H=H.values, L=L.values, adr=adr.values, e5=C.ewm(span=5, adjust=False).mean().values,
                e21=C.ewm(span=21, adjust=False).mean().values, s50=s50.values, s200=s200.values,
                P1=(p1 & elig).values, P2=(p2 & elig).values, hh=(H >= H.rolling(PEAK_N).max()).values)


def episodes(F, idx):
    C, H, L, adr = F["C"], F["H"], F["L"], F["adr"]
    n, m = C.shape
    lo_i, hi_i = idx.searchsorted(pd.Timestamp(START)), idx.searchsorted(pd.Timestamp(END), side="right")
    out = []
    for j in range(m):
        t = max(lo_i, 260)
        while t < min(hi_i, n - 1):
            if not F["hh"][t, j] or not (F["P1"][t, j] or F["P2"][t, j]) or not np.isfinite(adr[t, j]):
                t += 1; continue
            p, peakH = t, H[t, j]
            adr_d = adr[p, j] / 100 * C[p, j]
            pops = [k for k in ("P1", "P2") if F[k][p, j]]
            lo_v, lo_d, opened, fired = np.inf, None, False, {}
            base_hi = np.nanmax(H[max(0, p - 60):max(1, p - 19), j]) if p > 60 else np.nan
            u = p + 1
            while u <= min(p + MAX_LEN, n - 1):
                if L[u, j] < lo_v:
                    lo_v, lo_d = L[u, j], u
                    # fired rungs stay fired; rungs not yet fired now key off this new low
                if C[u, j] > peakH:
                    if opened and "K5" not in fired:
                        fired["K5"] = (u, lo_v, lo_d)
                    break
                if not opened and (peakH - lo_v) >= DEPTH * adr_d:
                    opened = True; fired["K0"] = (u, lo_v, lo_d)
                if opened and u > lo_d:
                    cond = {"K1": C[u, j] > H[lo_d, j],
                            "K2": C[u, j] > H[lo_d, j] and u - lo_d >= 2,
                            "K3": C[u, j] > F["e5"][u, j],
                            "K4": C[u, j] > F["e21"][u, j]}
                    for r, ok in cond.items():
                        if ok and r not in fired:
                            fired[r] = (u, lo_v, lo_d)
                u += 1
            if opened:
                # support is judged on the low KNOWN AT ENTRY (lv, ld), not the episode's final low (look-ahead fix 2026-09-25)
                near = lambda low, lvl: bool(np.isfinite(lvl) and abs(low - lvl) <= 0.5 * adr_d)
                for r, (e, lv, ld) in fired.items():
                    support = near(lv, F["s50"][ld, j]) or near(lv, F["s200"][ld, j]) or near(lv, base_hi)
                    for pop in pops:
                        out.append(dict(j=j, peak=p, rung=r, pop=pop, i=e, low=lv, low_day=ld,
                                        premium=(C[e, j] - lv) / adr_d, support=support))
            t = max(u, t + 1)
    return pd.DataFrame(out)


def score(E, F, idx, P):
    C, L, adr = F["C"], F["L"], F["adr"]
    n = C.shape[0]
    in_ep = np.zeros(C.shape, bool)
    for r in E.itertuples():
        in_ep[r.peak:r.i + 1, r.j] = True
    ctl = {}
    for h in HORIZONS:
        fr = np.full(C.shape, np.nan); fr[:-h] = C[h:] * (1 - SLIP) / (C[:-h] * (1 + SLIP)) - 1
        # ADR terciles cut on the FULL eligible cross-section each date (fix 2026-09-25: cutting them on the
        # population needed >= 30 precision-tier names per date and left most P1 entries without a control)
        allb = P.elig.fillna(False).values & np.isfinite(adr)
        terc = np.full(C.shape, -1)
        for i in range(n):
            if allb[i].sum() >= 30:
                q = np.nanquantile(adr[i, allb[i]], [1 / 3, 2 / 3])
                terc[i] = np.where(adr[i] <= q[0], 0, np.where(adr[i] <= q[1], 1, 2))
        for pop in ("P1", "P2"):
            base = F[pop] & ~in_ep & np.isfinite(fr) & np.isfinite(adr)
            M = np.full((n, 4), np.nan)                    # cols 0-2 = tercile cells, col 3 = all population names that date
            for k in range(3):
                w = base & (terc == k)
                sm = np.where(w, fr, 0).sum(1); c = w.sum(1)
                M[:, k] = np.where(c >= 5, sm / np.maximum(c, 1), np.nan)
            sm = np.where(base, fr, 0).sum(1); c = base.sum(1)
            M[:, 3] = np.where(c >= 5, sm / np.maximum(c, 1), np.nan)
            ctl[(pop, h)] = (M, terc, fr)
    rows = []
    for r in E.itertuples():
        rec = dict(date=idx[r.i], sym=P.close.columns[r.j], rung=r.rung, pop=r.pop, peak=r.peak, j=r.j,
                   premium=r.premium, support=r.support)
        rec["hold20"] = bool(r.i + 20 < n and np.nanmin(L[r.i + 1:r.i + 21, r.j]) > r.low) if r.i + 20 < n else np.nan
        for h in HORIZONS:
            M, terc, fr = ctl[(r.pop, h)]
            tk = terc[r.i, r.j]
            cm = M[r.i, tk] if tk >= 0 and np.isfinite(M[r.i, tk]) else M[r.i, 3]   # fall back to all same-date population names
            rec[f"fwd{h}"] = 100 * fr[r.i, r.j]
            rec[f"x{h}"] = 100 * (fr[r.i, r.j] - cm) if np.isfinite(cm) else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def cell(T, h):
    x = T[f"x{h}"].dropna(); d = T.loc[x.index, "date"]
    mo = x.groupby(d.dt.to_period("M")).mean(); hh = mo.index < pd.Period(SPLIT, "M")
    yr = x.groupby(d.dt.year).mean()
    same = int((np.sign(yr) == np.sign(mo.mean())).sum())
    ok = abs(tstat(mo)) >= T_BAR and np.sign(mo[hh].mean()) == np.sign(mo[~hh].mean()) and same > len(yr) / 2
    return mo.mean(), tstat(mo), mo[hh].mean(), mo[~hh].mean(), f"{same}/{len(yr)}", ok


def main():
    P = load_panel(PANEL)
    idx = P.close.index
    F = features(P)
    E = episodes(F, idx)
    T = score(E, F, idx, P)
    out = ["# Confirmation ladder off a pullback low (pre-registration in the docstring)",
           f"# episodes: P1 {T[(T['pop']=='P1') & (T.rung=='K0')].shape[0]:,}  P2 {T[(T['pop']=='P2') & (T.rung=='K0')].shape[0]:,}; "
           f"{T.date.min().date()} -> {T.date.max().date()}; Sidak(24) bar |t| >= {T_BAR}"]
    R = []
    for pop in ("P1", "P2"):
        cov = T[T["pop"] == pop].x20.notna().mean()
        out.append(f"\n## {pop} {'(PRIMARY population)' if pop == 'P1' else ''}  -- control coverage {cov:.0%} of entries")
        out.append(f"  {'rung':4s} {'n':>6s} {'fires%':>6s} {'hold20':>6s} {'prem ADR':>8s} | "
                   f"{'fwd20':>6s} {'x20':>6s} {'t':>6s} {'halves':>13s} {'yrs':>5s} | {'fwd60':>6s} {'x60':>6s} {'t':>6s}")
        n0 = T[(T["pop"] == pop) & (T.rung == "K0")].shape[0]
        for r in RUNGS:
            S = T[(T["pop"] == pop) & (T.rung == r)]
            m20, t20, a20, b20, y20, ok20 = cell(S, 20)
            m60, t60, a60, b60, y60, ok60 = cell(S, 60)
            tag = " <- PRIMARY" if (pop == "P1" and r == "K1") else ""
            out.append(f"  {r:4s} {len(S):6d} {100*len(S)/max(n0,1):5.0f}% {100*S.hold20.mean():5.0f}% {S.premium.median():8.2f} | "
                       f"{S.fwd20.mean():+6.2f} {m20:+6.2f} {t20:+6.2f} {a20:+6.2f}/{b20:+6.2f} {y20:>5s} | "
                       f"{S.fwd60.mean():+6.2f} {m60:+6.2f} {t60:+6.2f}{tag}")
            R += [dict(pop=pop, rung=r, h=20, excess=m20, t=t20, h1=a20, h2=b20, yrs=y20, PASS=ok20, hold20=S.hold20.mean(),
                       premium=S.premium.median(), n=len(S)),
                  dict(pop=pop, rung=r, h=60, excess=m60, t=t60, h1=a60, h2=b60, yrs=y60, PASS=ok60, n=len(S))]
        # policy comparison vs K0, per episode (0 when the rung never fires)
        ep = T[T["pop"] == pop].pivot_table(index=["j", "peak"], columns="rung", values="fwd20", aggfunc="first")
        d0 = T[(T["pop"] == pop) & (T.rung == "K0")].set_index(["j", "peak"]).date
        out.append("  policy per episode vs K0 (+20, 0 if the rung never fires):")
        for r in RUNGS[1:]:
            if r not in ep:
                continue
            diff = (ep[r].fillna(0) - ep["K0"]).dropna()
            mo = diff.groupby(d0.reindex(diff.index).dt.to_period("M")).mean()
            out.append(f"    {r} - K0: {mo.mean():+.2f}pp month-weighted (pooled {diff.mean():+.2f}) t {tstat(mo):+.2f}  (fires on {ep[r].notna().mean():.0%} of episodes)")
        # global-min bonus at K1
        S = T[(T["pop"] == pop) & (T.rung == "K1")]
        for lab, m in (("low AT support", S.support), ("low not at support", ~S.support)):
            x = S[m].x20.dropna(); mo = x.groupby(S[m].loc[x.index, "date"].dt.to_period("M")).mean()
            out.append(f"  [bonus, exploratory] K1 {lab:19s} n {int(m.sum()):6d} hold20 {100*S[m].hold20.mean():4.0f}%  "
                       f"x20 {mo.mean():+.2f}pp t {tstat(mo):+.2f}")
    D = pd.DataFrame(R)
    passed = D[D.PASS]
    out.append("\nVERDICT: " + ("SIGNAL rungs: " + ", ".join(f"{r.pop} {r.rung} +{r.h} ({r.excess:+.2f}pp t {r.t:+.2f})"
                                                              for r in passed.itertuples()) if len(passed) else "no rung passes the Sidak(24) bar"))
    D.to_csv(REPO / "data/studies/low_confirmation_ladder_2026-09-25.csv", index=False)
    T.drop(columns=["j"]).to_csv(REPO / "data/studies/logs/low_confirmation_ladder_entries.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
