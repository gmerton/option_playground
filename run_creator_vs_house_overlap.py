#!/usr/bin/env python3
"""
How many of Luk's and Ariel's long entries were a HOUSE BREAKOUT, and where do the rest diverge? (descriptive,
2026-10-03; Gabe: "look at Luk and Ariel's trades and say how many coincide with our house breakout strategy. If they
diverge, how do they diverge?"). No outcomes are used: this is a feature comparison, so no pre-registration bar.

ENTRIES. Opening rows with a resolved ticker and fill date, one per (trader, ticker, fill date), long side only (the
house rule is long-only; shorts are counted and set aside).
  Luk    run_luk_trade_pages.load() (Gabe's worklist fixes applied), actions entry / buy / reentry, state ok.
  Ariel  run_ariel_trade_pages.load(), actions entry / reentry, not retrospective.
HOUSE RULE. run_precision_tier_control.build() on liquid_panel_2019: the generic breakout pool (`brk`) and the
precision tier on top of it (`precision`). Every gate is evaluated on the fill day so a miss can be attributed:
  universe   eligible (ADDV50 >= $50M, px >= $5, not suspect), ADR >= 3, 52-week range >= 17%
  trigger    close >= 15-day pivot (prior 15 highs) AND prior close < pivot (fresh) AND RVOL >= 1.1 AND close in the
             top half of the day's range
  trend      EMA stack >= 5 days
  no chase   gap < 5% and day change < 8%
  precision  ADR 4-7, within 15% of the 52-week high, stack <= 40 days
REPORTED per trader: n in the panel; share that were a house breakout / precision breakout that day and within 3
sessions either side; the share failing each gate; the FIRST failing gate in the order above (one bucket per entry);
and medians of the features beside the same-date precision tier.

  PYTHONPATH=src:. .venv/bin/python3 run_creator_vs_house_overlap.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run_ariel_trade_pages as AR
import run_luk_trade_pages as LK
from run_luk_picks_vs_controls import stack_run
from run_precision_tier_control import build

OUT = "data/studies/creator_vs_house_overlap_2026-10-03.md"


def entries() -> pd.DataFrame:
    l = LK.load()
    l = l[l.action.isin(["entry", "buy", "reentry"]) & (l.state == "ok") & l.fill.notna()]
    l = pd.DataFrame({"trader": "Luk", "tk": l.tk, "side": l.dirn, "fill": l.fill})
    a = AR.load()
    a = a[a.action.isin(["entry", "reentry"]) & ~a.retro & a.fill.notna()]
    a = pd.DataFrame({"trader": "Ariel", "tk": a.tk, "side": a.dirn, "fill": a.fill})
    e = pd.concat([l, a], ignore_index=True)
    e = e[e.tk.str.fullmatch(r"[A-Z][A-Z0-9.\-]{0,6}", na=False)]
    return e.drop_duplicates(["trader", "tk", "fill", "side"]).reset_index(drop=True)


def main() -> None:
    P, brk, prec = build()
    C, H, L, O = P.close, P.high, P.low, P.open
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "dolvol", "close"])
    V = (raw.pivot(index="date", columns="ticker", values="dolvol") / raw.pivot(index="date", columns="ticker", values="close")).reindex_like(C)
    adr = P.adr
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    piv = H.shift(1).rolling(15).max()
    F = dict(
        elig=P.elig, adr=adr, range52=(hi52 - lo52) / C * 100, piv=piv, rvol=V / V.shift(1).rolling(50).mean(),
        pos=(C - L) / (H - L).replace(0, np.nan), gap=(O / C.shift(1) - 1) * 100, chg=C.pct_change(fill_method=None) * 100,
        stack=stack_run(C, adr=adr), off52=(C / hi52 - 1) * 100, ext=(C / P.ema20 - 1) * 100 / adr,
        vs_piv=(C / piv - 1) * 100 / adr, prev_above=(C.shift(1) >= piv))
    GATES = [
        ("not in liquid universe / ADR < 3 / 52wk range < 17%", lambda f: not (f["elig"] and f["adr"] >= 3 and f["range52"] >= 17)),
        ("closed below the 15-day pivot (inside the base / pullback)", lambda f: f["vs_piv"] < 0),
        ("already above the pivot the day before (not fresh)", lambda f: bool(f["prev_above"])),
        ("volume < 1.1x 50-day", lambda f: f["rvol"] < 1.1),
        ("closed in the bottom half of the day's range", lambda f: f["pos"] < 0.5),
        ("EMA stack < 5 days (not yet trending)", lambda f: f["stack"] < 5),
        ("chase: gap >= 5% or day change >= 8%", lambda f: f["gap"] >= 5 or f["chg"] >= 8),
        ("breakout, but outside precision (ADR 4-7, <15% off high, stack <= 40)", lambda f: True),
    ]
    E = entries()
    rows = []
    for r in E.itertuples():
        d = pd.Timestamp(r.fill)
        if r.tk not in C.columns:
            rows.append(dict(**r._asdict(), inpanel=False)); continue
        k = C.index.searchsorted(d)
        if k >= len(C.index):
            rows.append(dict(**r._asdict(), inpanel=False)); continue
        dd = C.index[k]
        f = {n: F[n].at[dd, r.tk] for n in F}
        if not np.isfinite(C.at[dd, r.tk]):
            rows.append(dict(**r._asdict(), inpanel=False)); continue
        b, p = bool(brk.at[dd, r.tk]), bool(prec.at[dd, r.tk])
        win = slice(max(0, k - 3), k + 4)
        near_b = bool(brk[r.tk].iloc[win].any()); near_p = bool(prec[r.tk].iloc[win].any())
        first = "PRECISION BREAKOUT" if p else next((g for g, fn in GATES if _safe(fn, f)), "breakout, but outside precision (ADR 4-7, <15% off high, stack <= 40)")
        fails = {g: _safe(fn, f) for g, fn in GATES[:-1]}
        rows.append(dict(**r._asdict(), inpanel=True, brk=b, prec=p, near_brk=near_b, near_prec=near_p, first=first,
                         **{f"F_{n}": f[n] for n in ("adr", "off52", "ext", "vs_piv", "stack", "rvol", "gap")}, **{f"x_{i}": v for i, v in enumerate(fails.values())}))
    R = pd.DataFrame(rows)
    R.to_csv(OUT.replace(".md", "_rows.csv"), index=False)

    # same-date precision tier medians, for context
    Pm = {}
    for n in ("adr", "off52", "ext", "vs_piv", "stack", "rvol", "gap"):
        v = F[n].where(prec)
        Pm[n] = float(np.nanmedian(v.loc[v.index >= "2025-04-01"].values))
    L_ = [f"# Luk and Ariel long entries vs the house breakout ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
          "Descriptive, no outcomes. House rule = run_precision_tier_control.build() on liquid_panel_2019 (2026 survivors).", ""]
    for t, g in R.groupby("trader"):
        s = g[g.side == "short"]; lg = g[(g.side == "long")]; ip = lg[lg.inpanel == True]
        L_ += [f"## {t}", "",
               f"Entries {len(g)} ({len(lg)} long, {len(s)} short, set aside). Long entries in the panel: {len(ip)} "
               f"({len(lg) - len(ip)} not in it: small/illiquid names, ETFs, or dates outside it). Fill dates {g.fill.min().date()} -> {g.fill.max().date()}.", "",
               f"- house breakout that day: **{ip.brk.mean():.0%}** ({int(ip.brk.sum())}); precision tier that day: **{ip.prec.mean():.0%}** ({int(ip.prec.sum())})",
               f"- within 3 sessions either side: breakout {ip.near_brk.mean():.0%}, precision {ip.near_prec.mean():.0%}", "",
               "First gate the entry fails (one bucket each, in rule order):", ""]
        for k_, v in ip["first"].value_counts().items():
            L_.append(f"- {k_}: {v} ({v / len(ip):.0%})")
        L_ += ["", "Share failing each gate (not exclusive):", ""]
        for i, (gname, _) in enumerate(GATES[:-1]):
            L_.append(f"- {gname}: {ip[f'x_{i}'].mean():.0%}")
        L_ += ["", "| feature (median) | his/her long entries | same-period precision tier |", "|---|---|---|"]
        for n, lab in (("adr", "ADR %"), ("off52", "% off 52-week high"), ("ext", "close vs 20 EMA, ADR"), ("vs_piv", "close vs 15-day pivot, ADR"),
                       ("stack", "EMA stack days"), ("rvol", "volume / 50-day"), ("gap", "gap %")):
            L_.append(f"| {lab} | {np.nanmedian(ip[f'F_{n}']):+.2f} | {Pm[n]:+.2f} |")
        L_.append("")
    open(OUT, "w").write("\n".join(L_) + "\n")
    print("\n".join(L_))


def _safe(fn, f) -> bool:
    try:
        return bool(fn(f))
    except Exception:
        return False


if __name__ == "__main__":
    main()
