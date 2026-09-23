#!/usr/bin/env python3
"""
Does a stop FLOOR help UR and FBO alerts, as it did for ORB9? (pre-registered 2026-09-23, before the run)

THE GAP. A 0.60-ADR stop floor was adopted for **ORB9 only** on 2026-09-21 (`detectors.py:68`): the
structural stop was median 0.15 ADR with 96% under 0.4, and flooring it took the arm from roughly flat
(2nd half -0.08R) to **+0.08R, t 3.4, both halves positive, stop-outs 73% -> 17%**. UR and FBO were never
re-run and still emit unfloored stops -- 0.35 and 0.48 ADR on 2026-09-22, both losses.

⚠ IT IS NOT A COSMETIC GAP. On 2026-09-23 three live exits fired on sub-0.5-ADR levels (TXG, TGTX, then
NBIS and SNDK off a stop table built from the wrong reference). The alerting system is the one place that
still emits such stops unprompted, so this is the live version of that failure.

THE TWO STOPS ARE DIFFERENT OBJECTS, and the floor must be applied accordingly:
  UR  (LONG)  `detectors.py:363` -- stop = the flush/session LOW. Below entry. Floor pushes it DOWN.
  FBO (SHORT) `detectors.py:519` -- stop = failed high x (1 + 0.10 x ADR). ABOVE entry. Floor pushes it UP.
FBO already carries a 0.10-ADR buffer and a `STOP_NOISE_ADR = 0.40` *tag*, but the tag only annotates; it
never widens the stop. Sign errors here would invert the result, so side is carried explicitly.

DESIGN
  Every cached UR / FBO alert in `alert_study_scores.csv` (2026-02-02 -> 2026-09-10, 153 dates), re-scored
  on the cached 1-min bars with the stop floored at k ADR under (UR) / over (FBO) the entry:
      dist   = side * (entry - struct_stop)              # positive distance, whichever side
      dist_k = max(dist, k * ADR_px)                     # WIDEN only, never tighten
      stop_k = entry - side * dist_k
  Stopped if the session touches stop_k after the alert; otherwise marked out at the session close.
  R = -1 when stopped, else side * (close - entry) / dist_k.
  Arms: base (as emitted) + floors 0.25 / 0.40 / 0.50 / 0.60 / 0.80 / 1.00 ADR.
  Reported for the curated universe and the blind control (`universe_study_extra.txt`) separately, both
  halves of the date range, and split by whether the emitted stop was already inside the noise (<0.4 ADR).

PRE-REGISTERED PASS, per kind: the best floor beats `base` on mean R with |t| >= 3 on the arm's own mean
AND both halves of the date range the same sign AND the improvement present in the curated universe (not
only the control). 2 kinds x 6 floors = 12 cells; Sidak at 0.05 -> |t| >= 2.87, so the house 3.0 governs.

PRIOR, stated before running. Two-sided and worth recording because they conflict:
  * FOR: the ORB9 result was large and mechanically identical -- a stop inside the noise gets taken out by
    ordinary movement, and widening it is free apart from the larger per-trade risk.
  * AGAINST: Stage A found **every intraday arm is worth -0.10 to -0.13R and indistinguishable from a
    random later minute**. If the base expectancy is negative, a floor most likely moves it from negative
    to less negative -- a risk result, not a return result, exactly like the 21-DTE and spike/grind
    findings. **Widening a stop on a trigger with no edge buys nothing; it only re-sizes the loss.**
  Most likely outcome: stop-out rate falls sharply (as with ORB9), mean R improves but stays <= 0, and the
  honest conclusion is "floor them to stop bleeding on noise", not "this makes UR/FBO profitable".

Usage: PYTHONPATH=src .venv/bin/python3 -u run_ur_fbo_stop_floor_study.py 2>&1 | tee data/studies/logs/ur_fbo_floor.log
"""
from __future__ import annotations

import os
import warnings
from functools import lru_cache
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 260)

BARS = "data/cache/intraday_1min"
SIDE = {"UR": +1, "FBO": -1}          # +1 long, -1 short
FLOORS = (0.25, 0.40, 0.50, 0.60, 0.80, 1.00)
ARMS = ["base"] + [f"floor{k:g}" for k in FLOORS]
NOISE = 0.40


@lru_cache(None)
def ctx(dt: str):
    f = f"data/cache/alert_ctx_v7_{dt}.parquet"
    return pd.read_parquet(f).set_index("symbol") if os.path.exists(f) else None


def score(kind: str, d: pd.DataFrame, control: set) -> pd.DataFrame:
    side = SIDE[kind]
    a = d[(d.kind == kind) & d.R.notna()].drop_duplicates(["date", "t", "sym"])
    rows, skipped = [], 0
    for r in a.itertuples():
        c = ctx(r.date); f = f"{BARS}/{r.sym}_{r.date}.parquet"
        if c is None or r.sym not in c.index or not os.path.exists(f):
            skipped += 1; continue
        adr = c.loc[r.sym, "adr_pct"]
        if not adr or adr != adr:
            skipped += 1; continue
        m = pd.read_parquet(f); hm = m.index.strftime("%H:%M")
        m = m[(hm >= "09:30") & (hm < "16:00")]
        seg = m[m.index.strftime("%H:%M") > r.t]
        if seg.empty:
            skipped += 1; continue
        adr_px = r.px * adr / 100.0
        dist = side * (r.px - r.stop)                  # positive distance to the emitted stop
        if not np.isfinite(dist) or dist <= 0 or adr_px <= 0:
            skipped += 1; continue
        close = seg.close.iloc[-1]
        out = dict(kind=kind, date=r.date, sym=r.sym, t=r.t, ctl=r.sym in control,
                   dist_adr=dist / adr_px, day_state=getattr(r, "day_state_logged", None))
        for arm, k in [("base", None)] + [(f"floor{k:g}", k) for k in FLOORS]:
            dk = dist if k is None else max(dist, k * adr_px)
            stop_k = r.px - side * dk
            hit = (seg.low <= stop_k).any() if side > 0 else (seg.high >= stop_k).any()
            out[arm] = -1.0 if hit else side * (close - r.px) / dk
            out[arm + "_st"] = bool(hit)
            out[arm + "_pct"] = (-dk if hit else side * (close - r.px)) / r.px * 100
        rows.append(out)
    print(f"  {kind}: scored {len(rows):,}, skipped {skipped:,} (no bars/ctx)")
    return pd.DataFrame(rows)


def tab(g: pd.DataFrame) -> pd.DataFrame:
    out = []
    for v in ARMS:
        x = g[v].dropna()
        if len(x) < 20:
            out.append(dict(arm=v, n=len(x))); continue
        t = x.mean() / (x.std(ddof=1) / sqrt(len(x)))
        out.append(dict(arm=v, n=len(x), meanR=x.mean(), t=t,
                        stop_pct=100 * g[v + "_st"].mean(), ret_pct=g[v + "_pct"].mean()))
    return pd.DataFrame(out)


def main() -> None:
    d = pd.read_csv("data/watchlist/logs/alert_study_scores.csv")
    control = {l.split()[0] for l in open("data/watchlist/universe_study_extra.txt")
               if l.strip() and not l.startswith("#")}
    print(f"control names: {len(control)}\n")

    frames = [score(k, d, control) for k in SIDE]
    X = pd.concat(frames, ignore_index=True)
    X.to_csv("data/studies/ur_fbo_stop_floor_2026-09-23.csv", index=False)

    for kind in SIDE:
        K = X[X.kind == kind]
        if K.empty:
            continue
        days = sorted(K.date.unique()); half = set(days[:len(days) // 2])
        print(f"\n{'='*118}\n{kind}  (side {'LONG' if SIDE[kind]>0 else 'SHORT'})  n={len(K):,}  "
              f"median emitted stop {K.dist_adr.median():.2f} ADR  |  share < {NOISE} ADR: "
              f"{100*(K.dist_adr < NOISE).mean():.0f}%\n{'='*118}")
        for name, g in [("ALL", K), ("curated", K[~K.ctl]), ("control", K[K.ctl]),
                        ("curated · half A", K[~K.ctl & K.date.isin(half)]),
                        ("curated · half B", K[~K.ctl & ~K.date.isin(half)]),
                        (f"curated · emitted stop < {NOISE} ADR", K[~K.ctl & (K.dist_adr < NOISE)]),
                        (f"curated · emitted stop >= {NOISE} ADR", K[~K.ctl & (K.dist_adr >= NOISE)])]:
            if len(g) < 20:
                continue
            print(f"\n{name}  n={len(g):,}")
            print(tab(g).to_string(index=False, float_format=lambda v: f"{v:,.3f}"))

        cur = K[~K.ctl]
        best = max(ARMS[1:], key=lambda v: cur[v].dropna().mean())
        b, x = cur["base"].dropna(), cur[best].dropna()
        ha, hb = cur[cur.date.isin(half)], cur[~cur.date.isin(half)]
        tb = x.mean() / (x.std(ddof=1) / sqrt(len(x)))
        agree = np.sign(ha[best].mean() - ha["base"].mean()) == np.sign(hb[best].mean() - hb["base"].mean())
        passed = bool(x.mean() > b.mean() and abs(tb) >= 3 and agree)
        print(f"\n  best floor for {kind}: {best}   meanR {x.mean():+.3f} (t {tb:+.2f}) vs base {b.mean():+.3f}"
              f"   halves agree on the improvement: {agree}")
        print(f"  PRE-REGISTERED PASS ({kind}): {'YES' if passed else 'NO'}")

    print("\nwrote data/studies/ur_fbo_stop_floor_2026-09-23.csv")


if __name__ == "__main__":
    main()
