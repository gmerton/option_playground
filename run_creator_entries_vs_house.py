#!/usr/bin/env python3
"""
ALL of Luk's and Ariel's long entries vs our end-of-day breakout (descriptive, 2026-10-04; Gabe: "broaden the data to
include all their long entries, not just the ones where they concurred").

For every long opening entry with a fill date (Luk: entry / buy / reentry, worklist fixes applied, state ok; Ariel:
entry / reentry, not retrospective), one per (trader, ticker, fill date), on liquid_panel_2019 (adjusted; 2026
survivors):
  THEIR PRICE      unknown intraday; proxied by the fill day's MIDPOINT (low + high) / 2. The fill-day CLOSE position in
                   the range (0 = low, 100 = high) shows what buying the close instead would have cost.
  OUR SIGNAL       the first house breakout (run_precision_tier_control.build: generic pool `brk`, and the precision
                   tier) from the fill date through 60 sessions later.
  COMMON EXIT      the close 60 sessions after THEIR fill (or the panel end). Returns: from their midpoint, from the
                   fill-day close, and from our breakout close where it fired.
Reported per trader and pooled: share where our breakout fired (and how many sessions later, at what premium over
their midpoint); among those, the share of their move our entry captured; among never-fired entries, their return
(missed winners vs avoided losers); the same-day close premium. No pass bar: this describes the gap, it does not test
an edge. Their logs are their own accounts (not audited fills).

  PYTHONPATH=src:. .venv/bin/python3 run_creator_entries_vs_house.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run_ariel_trade_pages as AR
import run_luk_trade_pages as LK
from run_precision_tier_control import build

OUT = "data/studies/creator_entries_vs_house_2026-10-04"
HZ = 60


def entries() -> pd.DataFrame:
    l = LK.load()
    l = l[l.action.isin(["entry", "buy", "reentry"]) & (l.state == "ok") & l.fill.notna() & (l.dirn == "long")]
    a = AR.load()
    a = a[a.action.isin(["entry", "reentry"]) & ~a.retro & a.fill.notna() & (a.dirn == "long")]
    e = pd.concat([pd.DataFrame({"trader": "Luk", "tk": l.tk, "fill": l.fill}),
                   pd.DataFrame({"trader": "Ariel", "tk": a.tk, "fill": a.fill})], ignore_index=True)
    e = e[e.tk.str.fullmatch(r"[A-Z][A-Z0-9.\-]{0,6}", na=False)]
    return e.drop_duplicates(["trader", "tk", "fill"]).reset_index(drop=True)


def main() -> None:
    P, brk, prec = build()
    C, H, L = P.close, P.high, P.low
    idx = C.index
    rows = []
    for r in entries().itertuples():
        if r.tk not in C.columns:
            continue
        s = idx.searchsorted(pd.Timestamp(r.fill))
        if s >= len(idx) or not np.isfinite(C.iat[s, C.columns.get_loc(r.tk)]):
            continue
        j = C.columns.get_loc(r.tk)
        lo, hi, c = L.iat[s, j], H.iat[s, j], C.iat[s, j]
        mid = (lo + hi) / 2
        x = min(s + HZ, len(idx) - 1); cx = C.iat[x, j]
        rec = dict(trader=r.trader, tk=r.tk, fill=idx[s], mid=mid, close=c, close_pos=(c - lo) / (hi - lo) * 100 if hi > lo else np.nan,
                   close_prem=(c / mid - 1) * 100, ret_mid=(cx / mid - 1) * 100, ret_close=(cx / c - 1) * 100, full=x == s + HZ)
        for lab, M in (("brk", brk), ("prec", prec)):
            w = M.iloc[s:x + 1, j]
            hit = np.flatnonzero(w.values)
            if len(hit):
                b = s + hit[0]; cb = C.iat[b, j]
                rec.update({f"{lab}_lag": hit[0], f"{lab}_prem": (cb / mid - 1) * 100, f"{lab}_ret": (cx / cb - 1) * 100})
            else:
                rec.update({f"{lab}_lag": np.nan, f"{lab}_prem": np.nan, f"{lab}_ret": np.nan})
        rows.append(rec)
    R = pd.DataFrame(rows)
    R.to_csv(f"{OUT}_rows.csv", index=False)

    def block(X: pd.DataFrame, lab: str) -> list[str]:
        F = X[X.full]
        out = [f"## {lab}: {len(X)} long entries ({X.fill.min().date()} → {X.fill.max().date()}); {len(F)} with a full {HZ}-session follow-up", ""]
        out.append(f"- Buying the fill-day CLOSE instead of their (midpoint) price: median close position {X.close_pos.median():.0f}% of the range, "
                   f"median premium {X.close_prem.median():+.2f}%, mean {X.close_prem.mean():+.2f}%; closed in the top third {(X.close_pos >= 67).mean():.0%}, bottom third {(X.close_pos <= 33).mean():.0%}")
        for k, name in (("brk", "house breakout (generic pool)"), ("prec", "precision tier")):
            f = F[F[f"{k}_lag"].notna()]; nf = F[F[f"{k}_lag"].isna()]
            if not len(F):
                continue
            cap = (f[f"{k}_ret"] / f.ret_mid.replace(0, np.nan))
            out.append(f"- {name}: fired within {HZ} sessions on **{len(f) / len(F):.0%}** ({len(f)}/{len(F)}); median {f[f'{k}_lag'].median():.0f} sessions later at a median "
                       f"**{f[f'{k}_prem'].median():+.1f}%** above their price (mean {f[f'{k}_prem'].mean():+.1f}%)")
            out.append(f"    - where it fired: their return to the common exit {f.ret_mid.mean():+.1f}% (median {f.ret_mid.median():+.1f}%) vs ours {f[f'{k}_ret'].mean():+.1f}% "
                       f"(median {f[f'{k}_ret'].median():+.1f}%); winners only (their ret > 0, n {(f.ret_mid > 0).sum()}): median share of their move we kept "
                       f"{cap[f.ret_mid > 0].median():.0%}")
            out.append(f"    - never fired (n {len(nf)}): their return {nf.ret_mid.mean():+.1f}% (median {nf.ret_mid.median():+.1f}%); "
                       f"missed winners > +10%: {(nf.ret_mid > 10).sum()}, avoided losers < −10%: {(nf.ret_mid < -10).sum()}")
        return out + [""]

    Lg = [f"# Luk + Ariel long entries vs our end-of-day breakout ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
          "Descriptive. Their price = fill-day midpoint (fills are intraday and unstated); returns to a common exit "
          f"{HZ} sessions after their fill; liquid_panel_2019 (survivors).", ""]
    for t in ("Luk", "Ariel"):
        Lg += block(R[R.trader == t], t)
    Lg += block(R, "Both pooled")
    open(f"{OUT}_results.md", "w").write("\n".join(Lg) + "\n")
    print("\n".join(Lg))


if __name__ == "__main__":
    main()
