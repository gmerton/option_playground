#!/usr/bin/env python3
"""
ARIEL HERNANDEZ'S BROKER-LOGGED TRADES: SELECTION vs MANAGEMENT (pre-registered 2026-10-01, before any scoring;
Gabe: "good. go"). Creator record -> DISCOVERY track (|t| >= 3).

WHY. The goal is triple-digit returns in the style of Luk / Tito / Qullamaggie / Ariel. For Luk, neither his selection
at the close (picks look 2, t -0.07) nor his mechanical entry/stop (tight-stop test, t +0.02) carried an edge. Ariel's
record is different evidence: complete monthly trade tables from his broker software, Oct 2025 -> Mar 2026, every month
reconciling to his own total (data/studies/ariel_broker_log_2026-10-01.md). 27% winners, a 4.6x payoff, and the 10
largest winners = 185% of the closed P&L. The question is where that tail comes from:
  SELECTION -- the names and days he picks move his way more than comparable names on the same day, or
  MANAGEMENT -- the moves are ordinary, and the dollars come from how he sizes, adds, cuts and holds.
⚠ His record is the object of study here (as with Luk's picks), not Gabe's trades.

DATA  data/ariel_hernandez/trades/broker_trades.csv: one row per position opened (open_date, symbol, % and $ P&L,
      open / closed), direction from his slides (114) or the caption log (66; the two agree on all 106 overlaps).
      Scored: rows with an open date and a direction (181 of 202). The 21 without a direction are excluded, not guessed.
      Repeated opens of the same (symbol, direction) within 2 sessions are one pick (his re-tries), dated at the first.
ENTRY the CLOSE of the open date (scores selection, not his intraday fill). Prices: liquid_panel_2019 panel, yfinance
      for names outside it (ETFs, young listings), adjusted. Signed by direction. Costs 10 bp per side.
HORIZON PRIMARY 10 sessions (his stated winner holds: 10-12 days in Oct/Nov, 11 in Mar, 20 for 2025 overall);
      secondary 20 and 5.
CONTROLS
  C1  same-date eligible names (the panel's elig mask) in the pick's ADR tercile, signed the same way. Holds the day,
      the direction and the volatility fixed; varies the NAME. <- primary control
  C3  the same name on up to 5 random sessions 20-120 later with a full window (seed 20261001): varies the MOMENT.
PRIMARY  picks minus C1, 10 sessions, signed, net; t on open-date cluster means. BAR: t >= 3, both halves (split at
         the median open date) positive, and >= 4 of 6 months positive. MDE at 80% power reported first; below it the
         verdict is UNDERPOWERED, not NULL.
SECONDARY (4; 5 cells in all, Sidak 5% two-sided |t| >= 2.57; the discovery bar of 3 governs adoption)
         S1 longs only vs C1 (10)  S2 shorts only vs C1 (10)  S3 all vs C1 at 20  S4 all vs C3 at 10.
DESCRIPTIVE (no claim) -- the MANAGEMENT side, which this data can only describe:
  M1 tail: do his 10 largest dollar winners also rank top-decile on the signed 10-session C1 excess?
  M2 implied position size = |pnl_usd| / |pnl_pct| x 100 (his software's % is cumulative over adds, so this is a
     traded-notional proxy, not a clean size); winners vs losers, Mann-Whitney.
  M3 what a fixed 10-session hold at equal size earns on his picks vs his realised % (does his exit beat holding?).
⚠ Six months, one regime. His P&L % is cumulative over adds and trims (his own clarifying slide), so % comparisons
  to a fixed hold are indicative only. Self-published record; it includes losers and a losing month.
Local (a few hundred picks, cached panel + yfinance).
"""
from __future__ import annotations

import warnings
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import mannwhitneyu

from run_precision_tier_control import build

warnings.filterwarnings("ignore")
LOG = Path("data/studies/logs/ariel_broker_picks.log")
SRC = Path("data/ariel_hernandez/trades/broker_trades.csv")
COST, SEED = 0.002, 20261001
H_MAIN = 10


def picks() -> tuple[pd.DataFrame, pd.DataFrame]:
    b = pd.read_csv(SRC, dtype={"open_date": str})
    b["open_date"] = pd.to_datetime(b.open_date, errors="coerce")
    raw = b.copy()
    b = b[b.open_date.notna() & b.direction.isin(["long", "short"])].sort_values("open_date")
    keep, last = [], {}
    for r in b.itertuples():
        k = (r.symbol, r.direction)
        if k in last and (r.open_date - last[k]).days <= 3:          # ~2 sessions: same idea, re-try
            continue
        last[k] = r.open_date
        keep.append(r.Index)
    return b.loc[keep].reset_index(drop=True), raw


def main() -> None:
    out = ["# Ariel broker-logged picks: selection vs management (pre-registered 2026-10-01); see docstring"]
    pk, raw = picks()
    out.append(f"broker rows {len(raw)}; with date+direction {int((raw.open_date.notna() & raw.direction.isin(['long','short'])).sum())}; "
               f"picks after merging re-tries {len(pk)} ({(pk.direction=='long').sum()} long, {(pk.direction=='short').sum()} short), "
               f"{pk.open_date.nunique()} dates")
    P, _, _ = build()
    C, adr, elig = P.close.copy(), P.adr.copy(), P.elig
    extra = sorted(set(pk.symbol) - set(C.columns))
    if extra:
        y = yf.download(extra, start="2025-01-01", auto_adjust=True, progress=False)
        for t in extra:
            try:
                c, h, l = y["Close"][t].dropna(), y["High"][t].dropna(), y["Low"][t].dropna()
            except KeyError:
                continue
            c.index = pd.to_datetime(c.index).tz_localize(None)
            C[t] = c.reindex(C.index)
            a = (h / l - 1).shift(1).rolling(20).mean() * 100
            a.index = c.index
            adr[t] = a.reindex(C.index)
    out.append(f"prices: panel to {C.index.max().date()}; {len(extra)} from yfinance ({', '.join(extra)})")
    Cf, idx = C.ffill(), C.index
    rng = np.random.default_rng(SEED)
    rows = []
    for r in pk.itertuples():
        d = r.open_date
        if d not in idx or r.symbol not in C.columns or pd.isna(C.at[d, r.symbol]):
            rows.append(dict(ok=False, symbol=r.symbol, d=d))
            continue
        i, s = idx.get_loc(d), (1 if r.direction == "long" else -1)
        rec = dict(ok=True, symbol=r.symbol, d=d, dirn=r.direction, sgn=s, pnl_usd=r.pnl_usd, pnl_pct=r.pnl_pct,
                   status=r.status, month=r.month)
        for h in (5, 10, 20):
            if i + h >= len(idx):
                continue
            k = C.columns.get_loc(r.symbol)
            pick = s * (Cf.iat[i + h, k] / C.iat[i, k] - 1) - COST
            fwd = Cf.iloc[i + h] / C.iloc[i] - 1
            el = elig.iloc[i]
            a_el = adr.iloc[i][el.index[el.values]].dropna()
            a_p = adr.at[d, r.symbol] if r.symbol in adr.columns else np.nan
            c1 = np.nan
            if len(a_el) > 30 and pd.notna(a_p):
                q1, q2 = a_el.quantile([1 / 3, 2 / 3])
                peers = a_el[a_el <= q1] if a_p <= q1 else a_el[(a_el > q1) & (a_el <= q2)] if a_p <= q2 else a_el[a_el > q2]
                c1 = s * fwd[peers.index.difference([r.symbol])].dropna().mean() - COST
            cand = [j for j in range(i + 20, min(i + 121, len(idx) - h)) if pd.notna(C.iat[j, k])]
            c3 = np.nan
            if cand:
                js = rng.choice(cand, size=min(5, len(cand)), replace=False)
                c3 = float(np.mean([s * (Cf.iat[j + h, k] / C.iat[j, k] - 1) for j in js])) - COST
            rec.update({f"p{h}": pick, f"c1_{h}": c1, f"c3_{h}": c3})
        rows.append(rec)
    R = pd.DataFrame(rows)
    out.append(f"unpriced (dropped): {int((~R.ok).sum())} {sorted(R[~R.ok].symbol.unique())}")
    R = R[R.ok].copy()

    def cell(x: pd.Series, label: str) -> float:
        g = pd.DataFrame({"x": x, "d": R.loc[x.index, "d"], "m": R.loc[x.index, "month"]}).dropna()
        if len(g) < 5:
            out.append(f"  {label:30s} n {len(g)} -- too few")
            return np.nan
        dm = g.groupby("d").x.mean()
        se = dm.std(ddof=1) / sqrt(len(dm))
        med = g.d.sort_values().iloc[len(g) // 2]
        h1, h2 = g[g.d < med].x.mean(), g[g.d >= med].x.mean()
        mo = g.groupby("m").x.mean()
        out.append(f"  {label:30s} n {len(g):3d} / {len(dm):3d} dates | mean {100*g.x.mean():+6.2f}pp | date-cluster t {dm.mean()/se:+.2f}"
                   f" | MDE(80%) {100*2.8*se:.1f}pp | halves {100*h1:+.2f} / {100*h2:+.2f} | months + {int((mo>0).sum())}/{len(mo)}"
                   f" | win {100*(g.x>0).mean():.0f}%")
        return dm.mean() / se

    out.append(f"\n## raw signed {H_MAIN}-session return of his picks: mean {100*R[f'p{H_MAIN}'].mean():+.2f}%, "
               f"median {100*R[f'p{H_MAIN}'].median():+.2f}%; C1 mean {100*R[f'c1_{H_MAIN}'].mean():+.2f}%")
    out.append(f"## PRIMARY: picks - C1 at {H_MAIN} sessions (bar t >= 3, halves +, >= 4/6 months +)")
    cell(R[f"p{H_MAIN}"] - R[f"c1_{H_MAIN}"], "ALL vs C1 (10)")
    out.append("## SECONDARY (Sidak |t| >= 2.57)")
    L, S = R.dirn == "long", R.dirn == "short"
    cell((R[f"p{H_MAIN}"] - R[f"c1_{H_MAIN}"])[L], "S1 longs vs C1 (10)")
    cell((R[f"p{H_MAIN}"] - R[f"c1_{H_MAIN}"])[S], "S2 shorts vs C1 (10)")
    cell(R["p20"] - R["c1_20"], "S3 all vs C1 (20)")
    cell(R[f"p{H_MAIN}"] - R[f"c3_{H_MAIN}"], "S4 all vs C3 same name later (10)")
    out.append("## reported: 5 sessions")
    cell(R["p5"] - R["c1_5"], "all vs C1 (5)")

    out.append("\n## DESCRIPTIVE (management)")
    R["x10"] = R[f"p{H_MAIN}"] - R[f"c1_{H_MAIN}"]
    top = R.nlargest(10, "pnl_usd")
    dec = R.x10.quantile(0.9)
    out.append(f"  M1 his 10 largest $ winners: {int((top.x10 >= dec).sum())}/10 are top-decile on the 10-session C1 excess; "
               f"their mean excess {100*top.x10.mean():+.1f}pp vs all picks {100*R.x10.mean():+.1f}pp; "
               f"Spearman($ P&L, excess) {R[['pnl_usd','x10']].corr('spearman').iloc[0,1]:+.2f}")
    z = R[(R.status == "closed") & R.pnl_pct.notna() & (R.pnl_pct.abs() > 0.05)].copy()
    z["notional"] = (z.pnl_usd / z.pnl_pct * 100).abs()
    w, l = z[z.pnl_usd > 0].notional, z[z.pnl_usd <= 0].notional
    p = mannwhitneyu(w, l).pvalue if len(w) > 3 and len(l) > 3 else np.nan
    out.append(f"  M2 implied traded notional: winners median ${w.median():,.0f} (n {len(w)}) vs losers ${l.median():,.0f} (n {len(l)}); "
               f"Mann-Whitney p {p:.3f}")
    zz = z.dropna(subset=[f"p{H_MAIN}"])
    out.append(f"  M3 his realised % (cumulative, indicative) mean {zz.pnl_pct.mean():+.2f}% vs a fixed {H_MAIN}-session hold from the "
               f"close on the same picks {100*zz[f'p{H_MAIN}'].mean():+.2f}% (n {len(zz)}); winners realised {zz[zz.pnl_usd>0].pnl_pct.mean():+.2f}% "
               f"vs fixed-hold {100*zz[zz.pnl_usd>0][f'p{H_MAIN}'].mean():+.2f}%; losers {zz[zz.pnl_usd<=0].pnl_pct.mean():+.2f}% vs "
               f"{100*zz[zz.pnl_usd<=0][f'p{H_MAIN}'].mean():+.2f}%")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
