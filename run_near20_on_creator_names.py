#!/usr/bin/env python3
"""
BUY NEAR THE 20 EMA ON LUK'S AND ARIEL'S NAMES vs WAIT FOR OUR BREAKOUT (pre-registered 2026-10-04, before the run)

WHY. Descriptive comparison 2026-10-04 (run_creator_entries_vs_house.py): on Ariel's own long names, his entry beat
waiting for our end-of-day breakout by +10.3pp per entry to a common exit (median +5.5, month-clustered t 2.20, halves
+9.4 / +11.2, not pre-registered). Our breakout fires on only ~40% of their names, ~18 sessions later, ~18% higher.
Their entries sit ~0.7-0.8 ADR above the 20 EMA vs +2.8 for our precision tier. Gabe: test buying near the 20 EMA on
their names. This makes the entry MECHANICAL and IMPLEMENTABLE: we only learn of their trade when they disclose it.

EVENTS. Every long opening entry in the logs (Luk: entry / buy / reentry, worklist fixes, state ok; Ariel: entry /
  reentry, not retrospective). t0 = the first session AFTER the video date (the earliest day we could act on it); one
  event per (ticker, t0), merging events on the same ticker within 10 sessions. Prices: liquid_panel_2019 (adjusted;
  their names are mostly survivors anyway). Events need t0 + 60 sessions of data.
ARMS (same name, same COMMON EXIT = the close of t0 + 60 sessions; no stops in the primary; 10 bp per side):
  NEAR20     resting limit for sessions t0 .. t0+20 at L_d = EMA20[d-1] + 1.0 x ADR$[d-1]; filled on the first day whose
             low <= L_d, at min(open_d, L_d). Unfilled -> no trade (return 0).
  BREAKOUT   our end-of-day rule: buy the close of the first house breakout (run_precision_tier_control.build, generic
             pool) in t0 .. t0+20. None -> no trade (0).
  COPY       buy the close of t0 (copy them at disclosure).
PRIMARY: NEAR20 - BREAKOUT, % per event, mean over events, t clustered by calendar month of t0.
BAR (discovery): t >= 3 and both halves (split at the median t0) > 0. Negative t <= -3 with both halves < 0 -> the
  breakout wins. Otherwise NULL / UNDERPOWERED (MDE = 2.8 x SE).
REPORTED, not a pass: NEAR20 - COPY; BREAKOUT - COPY; fill rates; each arm's same-date ADR-band-matched excess (beta check,
  field = eligible names in the same ADR band entered the same day, held to the same exit); band 0.5 ADR; wait window
  10 / 40; a MANAGED variant (NEAR20 with a stop 1 ADR under the fill judged on the close and exit on the first close
  below the 20 EMA, vs BREAKOUT with the house day-low close stop + 20-EMA exit; % per event, unfilled 0); by trader;
  per month.
PRIOR ~40%: the descriptive gap is large and same-name, but it used their actual (discretionary) entry; a mechanical
  band may fill on falling knives they would have skipped.

  PYTHONPATH=src:. .venv/bin/python3 run_near20_on_creator_names.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run_ariel_trade_pages as AR
import run_luk_trade_pages as LK
from run_precision_tier_control import build

OUT = "data/studies/near20_on_creator_names_2026-10-04"
HZ, COST = 60, 0.001
BANDS = [(0, 3), (3, 4), (4, 6), (6, 999)]


def events(idx, cols) -> pd.DataFrame:
    l = LK.load()
    l = l[l.action.isin(["entry", "buy", "reentry"]) & (l.state == "ok") & (l.dirn == "long")]
    a = AR.load()
    a = a[a.action.isin(["entry", "reentry"]) & ~a.retro & (a.dirn == "long")]
    e = pd.concat([pd.DataFrame({"trader": "Luk", "tk": l.tk, "vid": l.vid}),
                   pd.DataFrame({"trader": "Ariel", "tk": a.tk, "vid": a.vid})], ignore_index=True)
    e = e[e.tk.isin(cols) & e.vid.notna()]
    e["t0"] = [idx.searchsorted(pd.Timestamp(v), side="right") for v in e.vid]
    e = e[e.t0 + HZ < len(idx)].sort_values(["tk", "t0"])
    keep, last = [], {}
    for r in e.itertuples():
        if r.tk in last and r.t0 - last[r.tk] <= 10:
            continue
        keep.append(r.Index); last[r.tk] = r.t0
    return e.loc[keep].reset_index(drop=True)


def ct(x: pd.Series, g: pd.Series):
    x = x.dropna(); g = g.loc[x.index]; n = len(x); mu = x.mean()
    s = (x - mu).groupby(g).sum(); G = len(s)
    se = np.sqrt((s ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1))
    return mu, mu / se if se > 0 else np.nan, n, se


def run(P, brk, E, band=1.0, wait=20, managed=False):
    C, H, Lo, O, E20 = P.close.values, P.high.values, P.low.values, P.open.reindex_like(P.close).values, P.ema20.values
    A = P.adr.values / 100
    elig = P.elig.values
    bandk = np.select([(P.adr.values >= lo) & (P.adr.values < hi) for lo, hi in BANDS], range(len(BANDS)), -1)
    rows = []
    for r in E.itertuples():
        j = P.close.columns.get_loc(r.tk); t0 = r.t0; x = t0 + HZ
        if not np.isfinite(C[t0, j]) or not np.isfinite(C[x, j]):
            continue
        def held(i_in, px, mgd_stop=None, house=False):
            if not managed:
                return C[x, j] / px - 1 - 2 * COST
            for k in range(i_in + 1, x + 1):
                c = C[k, j]
                if not np.isfinite(c):
                    continue
                if (house and c < Lo[i_in, j]) or ((not house) and c < mgd_stop) or c < E20[k, j] or k == x:
                    return c / px - 1 - 2 * COST
            return C[x, j] / px - 1 - 2 * COST
        def field(i_in):
            k = bandk[i_in, j]
            if k < 0:
                return np.nan
            m = elig[i_in] & (bandk[i_in] == k) & np.isfinite(C[i_in]) & np.isfinite(C[x])
            m[j] = False
            return np.nanmean(C[x, m] / C[i_in, m] - 1) if m.sum() >= 10 else np.nan
        # NEAR20
        nf, n_in = 0.0, None
        for d in range(t0, min(t0 + wait, x - 1) + 1):
            lvl = E20[d - 1, j] + band * A[d, j] * C[d - 1, j]
            if np.isfinite(lvl) and np.isfinite(Lo[d, j]) and Lo[d, j] <= lvl:
                px = min(O[d, j], lvl) if np.isfinite(O[d, j]) else lvl
                n_in = (d, px); break
        if n_in:
            d, px = n_in
            nf = held(d, px, mgd_stop=px * (1 - A[d, j])) * 100
            nf_ex = nf - (field(d) * 100 if np.isfinite(field(d)) else np.nan)
        else:
            nf_ex = 0.0
        # BREAKOUT
        bo, b_in = 0.0, None
        for d in range(t0, min(t0 + wait, x - 1) + 1):
            if brk.iat[d, j]:
                b_in = d; break
        if b_in is not None:
            bo = held(b_in, C[b_in, j], house=True) * 100
            bo_ex = bo - (field(b_in) * 100 if np.isfinite(field(b_in)) else np.nan)
        else:
            bo_ex = 0.0
        cp = held(t0, C[t0, j], mgd_stop=C[t0, j] * (1 - A[t0, j])) * 100
        cp_ex = cp - (field(t0) * 100 if np.isfinite(field(t0)) else np.nan)
        rows.append(dict(trader=r.trader, tk=r.tk, t0=P.close.index[t0], near20=nf, breakout=bo, copy=cp, near_filled=n_in is not None,
                         brk_fired=b_in is not None, near_ex=nf_ex, brk_ex=bo_ex, copy_ex=cp_ex))
    R = pd.DataFrame(rows); R["month"] = R.t0.dt.to_period("M")
    return R


def main() -> None:
    P, brk, prec = build()
    E = events(P.close.index, P.close.columns)
    R = run(P, brk, E); R.to_csv(f"{OUT}_events.csv", index=False)
    d = R.near20 - R.breakout
    m, t, n, se = ct(d, R.month)
    mid = R.t0.median(); h1, h2 = d[R.t0 < mid].mean(), d[R.t0 >= mid].mean()
    v = ("PASS — near-20-EMA beats waiting for the breakout" if (t >= 3 and h1 > 0 and h2 > 0) else
         "INVERTED — the breakout wins" if (t <= -3 and h1 < 0 and h2 < 0) else ("NULL" if abs(m) < 2.8 * se else "UNDERPOWERED / LEAN"))
    L = [f"# Near the 20 EMA on Luk's / Ariel's names vs our breakout ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(R)} events (t0 {R.t0.min().date()} → {R.t0.max().date()}); NEAR20 filled {R.near_filled.mean():.0%}, BREAKOUT fired {R.brk_fired.mean():.0%}.", "",
         f"**PRIMARY NEAR20 − BREAKOUT: {v}** — {m:+.2f}pp per event, t {t:.2f}, n {n}; halves {h1:+.2f} / {h2:+.2f}; MDE {2.8 * se:.2f}pp", "",
         f"- per event: NEAR20 {R.near20.mean():+.2f}% · BREAKOUT {R.breakout.mean():+.2f}% · COPY {R["copy"].mean():+.2f}%", "", "## Reported, not a pass", ""]
    for lab, x in (("NEAR20 − COPY", R.near20 - R["copy"]), ("BREAKOUT − COPY", R.breakout - R["copy"]),
                   ("beta check, excess vs same-date ADR field: NEAR20", R.near_ex), ("… BREAKOUT", R.brk_ex), ("… COPY", R.copy_ex)):
        a = ct(x, R.month); L.append(f"- {lab}: {a[0]:+.2f}pp t {a[1]:.2f} n {a[2]}")
    for lab, kw in (("band 0.5 ADR", dict(band=0.5)), ("wait 10", dict(wait=10)), ("wait 40", dict(wait=40)), ("MANAGED (stops + 20-EMA exit)", dict(managed=True))):
        X = run(P, brk, E, **kw); a = ct(X.near20 - X.breakout, X.month)
        L.append(f"- {lab}: NEAR20 − BREAKOUT {a[0]:+.2f}pp t {a[1]:.2f}; NEAR20 {X.near20.mean():+.2f}% (filled {X.near_filled.mean():.0%}), BREAKOUT {X.breakout.mean():+.2f}%")
    for tr, g in R.groupby("trader"):
        a = ct(g.near20 - g.breakout, g.month); L.append(f"- {tr}: NEAR20 − BREAKOUT {a[0]:+.2f}pp t {a[1]:.2f} n {a[2]}")
    L += ["", "Per month (mean pp, n):", "", R.assign(diff=d).groupby("month")["diff"].agg(["mean", "count"]).round(2).to_string()]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:16]))


if __name__ == "__main__":
    main()
