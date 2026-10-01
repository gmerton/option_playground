#!/usr/bin/env python3
"""
MARTIN LUK'S ACTUAL PICKS vs OUR SELECTION: does his discretion carry information our filters don't? (pre-registered
2026-09-27, before any scoring; Gabe: "yes, pre-register both". INTERIM RUN authorised 2026-09-30, see the amendment at
the end of this docstring.)

WHY. Gabe: "how can we be as successful as Luk, Tito and Ariel -- what are we missing?" Every mechanical rule we
coded from these traders failed or was marginal; the parts that survive (selection of leaders, buying strength,
letting winners run) are already the book. The open question is whether their DISCRETIONARY selection contains
information the panel can't see (theme, catalyst quality, fundamentals, young stocks). Scoring the picks he actually
disclosed answers it directly. (His trades are admissible here: they are the object of study, not Gabe's own record.)

DATA   data/martin_luk/trades/observed_trades.jsonl (504 rows from his livestreams, 2025-11 -> 2026-09) with Gabe's
       fixes from clarify_worklist.csv applied: ticker_fixed / direction_fixed / fill_date_fixed override;
       keep_or_drop = drop removes the row (rows matched on the worklist's stable `key`
       column, source|ticker|action|direction#n, never on line numbers); a ticker_fixed holding several symbols separated by ';' expands
       into one pick per symbol (same direction and fill date). ⚠ CLARIFICATION RULE (declared now): resolve from what he says or shows
       on screen only, never from charts or memory of what moved; unresolved "?" tickers and non-day fill dates
       are DROPPED, not guessed.
PICKS  action in {entry, buy, short, reentry}; adds, trims, holds, watches excluded (not independent picks). One pick
       per (ticker, direction, fill date). Direction long / short as logged.
       ⚙ AMENDED 2026-09-27 (before any scoring): CONTEMPORANEOUS picks only -- a pick counts only if he disclosed it on
       the stream of its fill date or within 7 calendar days after it. Retrospective selections are excluded because
       he chose them knowing the outcome: the whole 2026-01-31 presentation (VKNEJA5r8zw, "+969% Return in 1 Year",
       hand-picked 2025 trades) and any pick whose fill is > 7 days before its video or only month-level dated
       (e.g. "Oct trades | 25 Nov 2025").
ENTRY  the CLOSE of the fill date (the house entry; this scores his SELECTION, not his intraday execution).
       Prices: liquid_panel_2019 refreshed first; names outside it (ETFs, young listings) from yfinance, adjusted.
RETURN signed by direction, 20 sessions (PRIMARY) and 5 sessions, net 10 bp/side; a name without 20 later sessions
       (delisted) exits at its last close.
CONTROLS (declared now)
  C2  OUR SELECTION: every precision-tier breakout (run_precision_tier_control.build()) on the same date, held the
      same way; if none that date, those of the same calendar week. <- the key comparison
  C1  MARKET: same-date eligible names (ADDV >= $50M, px >= $5) in the same ADR tercile (holds volatility fixed).
  C3  TIMING: the same name on a random session 20-120 sessions later (5 draws; seed 20260927) -- is it the name or
      the moment he picked?
PRIMARY  LONG picks, 20-session return minus the same-date C2 mean, t on fill-date cluster means.
         BAR: t >= 3 and both halves (split at the median fill date) positive. Report the minimum detectable effect at
         80% power FIRST; if the observed |excess| is below it, the verdict is UNDERPOWERED, not NULL.
SECONDARY (declared) longs vs C1 and vs C3; SHORT picks vs C1 (short excess = control return - pick return); all at
         5 sessions too. 5 secondary cells -> Sidak |t| ~ 2.6.
THEN (only if the primary passes or longs beat C2 at t >= 2): compare the FEATURES of his long picks with same-date
         precision-tier picks -- ADR, distance from the 52-week high, stack days, days since IPO, sector/theme, float,
         earnings within 10 days -- to name what his selection sees that ours doesn't.
⚠ One regime (2025-11 -> 2026-09, a strong tape for leaders) and ~130 long picks: power is modest by construction.
Local.

⚙ AMENDED 2026-09-30 (before any scoring; Gabe: "run it now on the unambiguous trades. I will continue to work through
the ambiguous ones so we can continue refining"). INTERIM LOOK 1:
  * worklist rows still open (no keep_or_drop) are EXCLUDED, not guessed; rows he resolved are used with his fixes;
    rows never on the worklist are used as logged. Pick count at this look: 106 (69 long, 37 short), 62 fill dates.
  * a pick is scored at a horizon only if that many sessions have elapsed in the price data (September picks have no
    20-session return yet); the delisting rule is unchanged.
  * every later re-run on a fuller worklist is another look at the same primary: the bar is 3.0 at this look and
    Sidak-charged after (2 looks -> 3.2, 3 -> 3.3).
  * ⚠ the result is reported in aggregate only. No per-pick outcome is printed for any name, so the remaining
    clarifications stay blind (the rule is still "resolve from the video only").
  * implementation notes fixed now: C1 terciles are cut on the eligible names' ADR that date and the pick is placed in
    them by its own ADR; C3 draws come from sessions 20-120 after the fill that have a full holding window, up to 5;
    an extra, more conservative t on ISO-week cluster means is printed beside the pre-registered fill-date t because
    20-session windows from neighbouring dates overlap. Exploratory: longs excluding leveraged / inverse ETFs.

Run: PYTHONPATH=src:. .venv/bin/python3 run_luk_picks_vs_controls.py   (log -> data/studies/logs/luk_picks_vs_controls.log)
"""
from __future__ import annotations

import warnings
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import run_luk_trade_pages as luk
from lib.commons.ma_stack import stack_run
from run_precision_tier_control import build

warnings.filterwarnings("ignore")
LOG = Path("data/studies/logs/luk_picks_vs_controls.log")
COST, SEED, RETRO_VIDEO = 0.002, 20260927, "VKNEJA5r8zw"
LEVERED = {"SQQQ", "TQQQ", "UVXY", "TSLL", "DRIP", "SOXL", "SOXS", "BOIL", "KOLD", "UVIX", "SVIX"}


def picks() -> tuple[pd.DataFrame, dict]:
    d = luk.load()
    op = d[d.action.isin(luk.OPENERS)].copy()
    n = dict(openers=len(op), pending=int((op.state == "pending").sum()), retrospective=int((op.state == "retrospective").sum()))
    op = op[op.state == "ok"]
    op = op[~op.tk.isin(["?", "", "nan"]) & ~op.tk.str.contains(r"[/ ]") & op.fill.notna()]
    lag = (op.vid - op.fill).dt.days
    op = op[(lag >= 0) & (lag <= 7) & ~op.source.str.contains(RETRO_VIDEO)]
    op = op[op.dirn.isin(["long", "short"])].drop_duplicates(["tk", "dirn", "fill"])
    n["scored_rows"] = len(op)
    return op[["tk", "dirn", "fill"]].reset_index(drop=True), n


def main() -> None:
    out = ["# Martin Luk's picks vs our selection -- INTERIM LOOK 1 (unambiguous picks only); pre-registration in the docstring"]
    pk, n = picks()
    out.append(f"opener rows {n['openers']}: pending (excluded) {n['pending']}, retrospective (excluded) {n['retrospective']}; "
               f"scored picks {len(pk)} ({(pk.dirn == 'long').sum()} long, {(pk.dirn == 'short').sum()} short), "
               f"{pk.fill.nunique()} fill dates, {pk.fill.min().date()} -> {pk.fill.max().date()}")

    P, brk, prec = build()
    C, H, L_ = P.close.copy(), P.high, P.low
    adr, elig = P.adr.copy(), P.elig
    extra = sorted(set(pk.tk) - set(C.columns))
    if extra:
        y = yf.download(extra, start="2025-01-01", auto_adjust=True, progress=False)
        for t in extra:
            try:
                c, h, l = y["Close"][t].dropna(), y["High"][t].dropna(), y["Low"][t].dropna()
            except KeyError:
                continue
            c.index = pd.to_datetime(c.index).tz_localize(None)
            C[t] = c.reindex(C.index)
            a = ((h / l - 1).shift(1).rolling(20).mean() * 100)
            a.index = c.index
            adr[t] = a.reindex(C.index)
    out.append(f"prices: panel to {C.index.max().date()}; {len(extra)} names from yfinance ({', '.join(extra)})")
    Cf = C.ffill()
    last_valid = C.apply(lambda s: s.last_valid_index())
    rng = np.random.default_rng(SEED)
    idx = C.index
    rows = []
    for r in pk.itertuples():
        if r.fill not in idx or r.tk not in C.columns or pd.isna(C.at[r.fill, r.tk]):
            rows.append(dict(tk=r.tk, dirn=r.dirn, fill=r.fill, ok=False))
            continue
        i = idx.get_loc(r.fill)
        rec = dict(tk=r.tk, dirn=r.dirn, fill=r.fill, ok=True)
        for h in (20, 5):
            if i + h >= len(idx):
                continue
            raw = Cf.iat[i + h, C.columns.get_loc(r.tk)] / C.at[r.fill, r.tk] - 1       # delisted -> last close via ffill
            fwd = Cf.iloc[i + h] / C.iloc[i] - 1
            # C2: same-date precision-tier breakouts, else the same ISO week's
            m = prec.iloc[i]
            names = list(m.index[m.values])
            c2 = fwd[names].dropna()
            if c2.empty:
                wk = [j for j in range(max(0, i - 4), min(len(idx) - h, i + 5))
                      if idx[j].isocalendar()[:2] == r.fill.isocalendar()[:2]]
                vals = []
                for j in wk:
                    mj = prec.iloc[j]
                    vals += list((Cf.iloc[j + h] / C.iloc[j] - 1)[list(mj.index[mj.values])].dropna().values)
                c2 = pd.Series(vals, dtype=float)
            # C1: same-date eligible names in the pick's ADR tercile
            el = elig.iloc[i]
            a_el = adr.iloc[i][el.index[el.values]].dropna()
            c1 = np.nan
            a_p = adr.at[r.fill, r.tk] if r.tk in adr.columns else np.nan
            if len(a_el) > 30 and pd.notna(a_p):
                q1, q2 = a_el.quantile([1 / 3, 2 / 3])
                peers = a_el[(a_el <= q1)] if a_p <= q1 else a_el[(a_el > q1) & (a_el <= q2)] if a_p <= q2 else a_el[a_el > q2]
                c1 = fwd[peers.index.difference([r.tk])].dropna().mean()
            # C3: the same name on random sessions 20-120 later with a full window
            cand = [j for j in range(i + 20, min(i + 121, len(idx) - h)) if pd.notna(C.iat[j, C.columns.get_loc(r.tk)])]
            c3 = np.nan
            if cand:
                js = rng.choice(cand, size=min(5, len(cand)), replace=False)
                k = C.columns.get_loc(r.tk)
                c3 = float(np.mean([Cf.iat[j + h, k] / C.iat[j, k] - 1 for j in js]))
            rec.update({f"raw{h}": raw, f"c2_{h}": c2.mean() if len(c2) else np.nan, f"n_c2_{h}": len(c2),
                        f"c1_{h}": c1, f"c3_{h}": c3})
        rows.append(rec)
    R = pd.DataFrame(rows)
    out.append(f"unpriced or non-session fill date (dropped): {int((~R.ok).sum())}")
    R = R[R.ok].copy()

    def cellstat(x: pd.Series, by: pd.Series, label: str) -> str:
        g = pd.DataFrame({"x": x, "d": by}).dropna()
        if len(g) < 5:
            return f"  {label:34s} n {len(g)} -- too few"
        dm = g.groupby("d").x.mean()
        se = dm.std(ddof=1) / sqrt(len(dm))
        wk = g.groupby(g.d.dt.strftime("%G-%V")).x.mean()
        tw = wk.mean() / (wk.std(ddof=1) / sqrt(len(wk))) if len(wk) > 2 else np.nan
        med = g.d.sort_values().iloc[len(g) // 2]
        h1, h2 = g[g.d < med].x.mean(), g[g.d >= med].x.mean()
        return (f"  {label:34s} n {len(g):3d} / {len(dm):2d} dates | mean {100 * g.x.mean():+6.2f}pp | date-cluster {100 * dm.mean():+6.2f}pp, "
                f"t {dm.mean() / se:+.2f} | week-cluster t {tw:+.2f} ({len(wk)} wks) | MDE(80%) {100 * 2.8 * se:.1f}pp | "
                f"halves {100 * h1:+.2f} / {100 * h2:+.2f} | win {100 * (g.x > 0).mean():.0f}%")

    for side in ("long", "short"):
        S = R[R.dirn == side]
        sgn = 1 if side == "long" else -1
        out.append(f"\n## {side.upper()} picks ({len(S)} priced)")
        for h in (20, 5):
            if f"raw{h}" not in S:
                continue
            s = S.dropna(subset=[f"raw{h}"])
            out.append(f"  -- {h} sessions: {len(s)} picks with a full window; raw signed return net of costs "
                       f"{100 * (sgn * s[f'raw{h}'] - COST).mean():+.2f}% (median {100 * (sgn * s[f'raw{h}'] - COST).median():+.2f}%), "
                       f"win {100 * (sgn * s[f'raw{h}'] > COST).mean():.0f}%; C2 names per pick median {s[f'n_c2_{h}'].median():.0f}; "
                       f"C2 mean {100 * (s[f'c2_{h}'] - COST).mean():+.2f}%, C1 mean {100 * (s[f'c1_{h}'] - COST).mean():+.2f}%")
            tag = " <- PRIMARY" if (side, h) == ("long", 20) else ""
            if side == "long":
                out.append(cellstat(s[f"raw{h}"] - s[f"c2_{h}"], s.fill, f"vs C2 our precision tier{tag}"))
                out.append(cellstat(s[f"raw{h}"] - s[f"c1_{h}"], s.fill, "vs C1 same-date ADR tercile"))
                out.append(cellstat(s[f"raw{h}"] - s[f"c3_{h}"], s.fill, "vs C3 same name later"))
                e = s[~s.tk.isin(LEVERED)]
                out.append(cellstat(e[f"raw{h}"] - e[f"c2_{h}"], e.fill, "(exploratory) ex levered ETFs vs C2"))
            else:
                out.append(cellstat(s[f"c1_{h}"] - s[f"raw{h}"], s.fill, "vs C1 (control - pick)"))

    # THEN: features, only if longs beat C2 at t >= 2 (computed, not printed per name)
    s = R[(R.dirn == "long")].dropna(subset=["raw20", "c2_20"])
    dm = (s.raw20 - s.c2_20).groupby(s.fill).mean()
    t_primary = dm.mean() / (dm.std(ddof=1) / sqrt(len(dm)))
    out.append(f"\n## PRIMARY: longs vs C2 at 20 sessions, date-cluster t {t_primary:+.2f} (bar 3.0 at look 1; both halves positive)")
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    off52 = (P.close / hi52 - 1) * 100
    stack = stack_run(P.close, adr=P.adr)
    age = P.close.notna().cumsum()
    feats = {"ADR %": P.adr, "off 52wk high %": off52, "stack days": stack, "sessions in panel (IPO-age proxy)": age}
    out.append("## Features: his long picks vs the same-date precision tier (medians; descriptive" +
               ("" if t_primary >= 2 else "; the pre-registered trigger t >= 2 was NOT met, shown for context only") + ")")
    L = R[R.dirn == "long"]
    for name, F in feats.items():
        a, b = [], []
        for r in L.itertuples():
            if r.tk in F.columns and r.fill in F.index:
                a.append(F.at[r.fill, r.tk])
                m = prec.loc[r.fill]
                b += list(F.loc[r.fill, list(m.index[m.values])].dropna().values)
        a, b = pd.Series(a, dtype=float).dropna(), pd.Series(b, dtype=float)
        out.append(f"  {name:34s} his picks median {a.median():8.1f} (n {len(a)}) | precision tier median {b.median():8.1f} (n {len(b)})")
    inprec = np.mean([bool(prec.at[r.fill, r.tk]) if r.tk in prec.columns else False for r in L.itertuples()])
    inbrk = np.mean([bool(brk.at[r.fill, r.tk]) if r.tk in brk.columns else False for r in L.itertuples()])
    out.append(f"  share of his long picks that were a house breakout that day: {100 * inbrk:.0f}%; a precision-tier breakout: {100 * inprec:.0f}%")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
