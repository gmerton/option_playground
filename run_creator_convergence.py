#!/usr/bin/env python3
"""
CONVERGENCE: WHEN LUK AND ARIEL BOTH GO LONG THE SAME NAME (OR INDUSTRY), IS IT BETTER THAN EITHER'S SOLO PICK?
(pre-registered 2026-10-04, before the run)

WHY. Gabe 2026-10-03/04: Luk, Ariel and Gabe all bought crypto proxies in the same week of August 2026 (Gabe's journal:
+$6.3k realized, entries 8/14-8/21), which suggests something real that our variables do not measure. The counter-
arguments are that the agreement may be one signal counted three times (shared lineage, shared feeds) and that we
notice agreement when it worked. Both are tested here, on every agreement in the logs, winners and losers. Gabe's own
trades are NOT used (house rule: his log is not evidence for selection).

DATA. Long opening entries with a fill date, one per (trader, ticker, fill date):
  Luk    run_luk_trade_pages.load() (worklist fixes applied), actions entry / buy / reentry, state ok.
  Ariel  run_ariel_trade_pages.load(), actions entry / reentry, not retrospective.
  Window: both logs active, 2025-11-26 -> 2026-09-18 (fills). Prices: liquid_panel_2019 (adjusted; 2026 survivors).
EVENTS (sessions = panel trading days):
  CONVERGENT  a ticker both traders entered long within 5 sessions of each other. Event date = the LATER of the two
              fills (the first day the agreement is knowable). Pairs on the same ticker within 10 sessions of an earlier
              event are the same event.
  SOLO        a trader's long entry with no long entry by the OTHER trader on that ticker within 10 sessions either way.
OUTCOME. Entry at the event-date close; 10- and 20-session forward return minus the mean return of the same-date
  ADR-matched field (eligible names, ADDV50 >= $50M, price >= $5, ADR bands 0-3 / 3-4 / 4-6 / 6+%).
  Payoff shape over the 20 sessions, in ADR units of the entry: MAE (worst low vs entry) and MFE (best high vs entry);
  'asymmetric win' = MAE > -1 ADR and MFE > +3 ADR.
PRIMARY: CONVERGENT minus SOLO, 20-session excess, two-sample with date clustering.
BAR (discovery): t >= 3 and both halves (split at the median event date) the same sign. Expected n: CONVERGENT in the
  tens -> UNDERPOWERED is likely and acceptable; the point estimate and the payoff shape are the read.
SECONDARY:
  INDUSTRY convergence: both traders long names in the same yfinance 'industry' within 5 sessions (different tickers
  allowed); scored on each of those entries, vs the solo pool of entries with no other-trader entry in the industry
  within 10 sessions.
  Each arm's absolute 20-session excess (t), MAE / MFE medians, share of asymmetric wins; the list of convergent events
  with outcomes (so the failures are visible, not just the crypto August).

  PYTHONPATH=src:. .venv/bin/python3 run_creator_convergence.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_ariel_trade_pages as AR
import run_luk_trade_pages as LK

PANEL = "data/cache/liquid_panel_2019.parquet"
OUT = "data/studies/creator_convergence_2026-10-04"
IND_CACHE = Path("data/cache/yf_industry.json")
W0, W1 = pd.Timestamp("2025-11-26"), pd.Timestamp("2026-09-18")
BANDS = [(0, 3), (3, 4), (4, 6), (6, 999)]


def entries() -> pd.DataFrame:
    l = LK.load()
    l = l[l.action.isin(["entry", "buy", "reentry"]) & (l.state == "ok") & l.fill.notna() & (l.dirn == "long")]
    a = AR.load()
    a = a[a.action.isin(["entry", "reentry"]) & ~a.retro & a.fill.notna() & (a.dirn == "long")]
    e = pd.concat([pd.DataFrame({"trader": "Luk", "tk": l.tk, "fill": l.fill}),
                   pd.DataFrame({"trader": "Ariel", "tk": a.tk, "fill": a.fill})], ignore_index=True)
    e = e[e.tk.str.fullmatch(r"[A-Z][A-Z0-9.\-]{0,6}", na=False) & (e.fill >= W0) & (e.fill <= W1)]
    return e.drop_duplicates(["trader", "tk", "fill"]).reset_index(drop=True)


def industries(tks) -> dict:
    cache = json.loads(IND_CACHE.read_text()) if IND_CACHE.exists() else {}
    import yfinance as yf
    for t in sorted(set(tks) - set(cache)):
        try:
            cache[t] = yf.Ticker(t).info.get("industry") or ""
        except Exception:
            cache[t] = ""
    IND_CACHE.parent.mkdir(parents=True, exist_ok=True); IND_CACHE.write_text(json.dumps(cache))
    return cache


def ct(x: pd.Series, d: pd.Series):
    x = x.dropna(); d = d.loc[x.index]; n = len(x)
    if n < 3:
        return np.nan, np.nan, n
    mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
    se = np.sqrt((g ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1))
    return mu, mu / se if se > 0 else np.nan, n


def main() -> None:
    raw = pd.read_parquet(PANEL, columns=["date", "ticker", "close", "high", "low", "dolvol"])
    C = raw.pivot(index="date", columns="ticker", values="close").sort_index(); C.index = pd.to_datetime(C.index)
    H = raw.pivot(index="date", columns="ticker", values="high").reindex_like(C)
    L = raw.pivot(index="date", columns="ticker", values="low").reindex_like(C)
    D = raw.pivot(index="date", columns="ticker", values="dolvol").reindex_like(C)
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    elig = (D.rolling(50, min_periods=30).mean() >= 50e6) & (C >= 5)
    band = pd.DataFrame(np.select([(adr >= lo) & (adr < hi) for lo, hi in BANDS], range(len(BANDS)), -1), index=adr.index, columns=adr.columns)
    idx = C.index
    si = lambda d: idx.searchsorted(pd.Timestamp(d))

    E = entries()
    E["s"] = [si(d) for d in E.fill]
    E = E[E.tk.isin(C.columns) & (E.s < len(idx))]

    def outcome(tk, s):
        if s + 20 >= len(idx) or not np.isfinite(C.iat[s, C.columns.get_loc(tk)]):
            return None
        j = C.columns.get_loc(tk); c0 = C.iat[s, j]; a = adr.iat[s, j]
        r = {}
        for h in (10, 20):
            f = C.iloc[s + h] / C.iloc[s] - 1; k = band.iat[s, j]
            fld = f[elig.iloc[s] & (band.iloc[s] == k) & f.notna()].drop(tk, errors="ignore")
            r[f"ex{h}"] = (f.iat[j] - fld.mean()) * 100 if len(fld) >= 10 and k >= 0 else np.nan
        hh = H.iloc[s + 1:s + 21, j].max(); ll = L.iloc[s + 1:s + 21, j].min()
        unit = a / 100 * c0 if np.isfinite(a) and a > 0 else np.nan
        r.update(mfe=(hh - c0) / unit, mae=(ll - c0) / unit)
        r["asym"] = bool(r["mae"] > -1 and r["mfe"] > 3) if np.isfinite(r["mae"]) else np.nan
        return r

    # ticker convergence
    lk, ar = E[E.trader == "Luk"], E[E.trader == "Ariel"]
    conv, used = [], []
    for t, g in E.groupby("tk"):
        gl, ga = g[g.trader == "Luk"], g[g.trader == "Ariel"]
        for x in gl.itertuples():
            for y in ga.itertuples():
                if abs(x.s - y.s) <= 5:
                    s = max(x.s, y.s)
                    if any(u[0] == t and abs(u[1] - s) <= 10 for u in used):
                        continue
                    used.append((t, s)); conv.append((t, s))
    rows = []
    for t, s in conv:
        o = outcome(t, s)
        if o:
            rows.append(dict(arm="CONVERGENT", tk=t, date=idx[s], **o))
    for x in E.itertuples():
        other = E[(E.tk == x.tk) & (E.trader != x.trader)]
        if len(other) and (other.s - x.s).abs().min() <= 10:
            continue
        o = outcome(x.tk, x.s)
        if o:
            rows.append(dict(arm=f"SOLO_{x.trader}", tk=x.tk, date=idx[x.s], **o))
    R = pd.DataFrame(rows)
    R["solo"] = R.arm.str.startswith("SOLO")
    R.to_csv(f"{OUT}_events.csv", index=False)
    cv, so = R[R.arm == "CONVERGENT"], R[R.solo]
    m1, t1, n1 = ct(cv.ex20, cv.date); m2, t2, n2 = ct(so.ex20, so.date)
    se = np.sqrt((m1 / t1) ** 2 + (m2 / t2) ** 2) if np.isfinite(t1) and np.isfinite(t2) else np.nan
    diff = m1 - m2; tt = diff / se
    mid = cv.date.median()
    h1 = cv[cv.date < mid].ex20.mean() - so[so.date < mid].ex20.mean(); h2 = cv[cv.date >= mid].ex20.mean() - so[so.date >= mid].ex20.mean()
    v = "PASS" if (tt >= 3 and h1 > 0 and h2 > 0) else ("NULL" if (abs(diff) < 2.8 * se) else "UNDERPOWERED / LEAN")

    # industry convergence
    ind = industries(E.tk.unique())
    E["ind"] = E.tk.map(ind).fillna("")
    irows = []
    for x in E[E.ind != ""].itertuples():
        other = E[(E.ind == x.ind) & (E.trader != x.trader)]
        near = (other.s - x.s).abs()
        lab = "IND_CONV" if len(near) and near.min() <= 5 else ("IND_SOLO" if not len(near) or near.min() > 10 else None)
        if lab:
            o = outcome(x.tk, x.s)
            if o:
                irows.append(dict(arm=lab, tk=x.tk, ind=x.ind, date=idx[x.s], **o))
    I = pd.DataFrame(irows)
    a1, b1, c1 = ct(I[I.arm == "IND_CONV"].ex20, I[I.arm == "IND_CONV"].date); a2, b2, c2 = ct(I[I.arm == "IND_SOLO"].ex20, I[I.arm == "IND_SOLO"].date)

    shape = lambda X: f"MAE median {X.mae.median():+.2f} ADR, MFE median {X.mfe.median():+.2f} ADR, asymmetric wins {X.asym.mean():.0%}"
    Lg = [f"# Luk + Ariel convergence ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
          f"Window {W0.date()} → {W1.date()}; long entries Luk {len(lk)}, Ariel {len(ar)}; convergent ticker events {len(cv)}, solo {len(so)}.", "",
          f"**PRIMARY CONVERGENT − SOLO, 20-session excess: {v}** — {diff:+.2f}pp, t {tt:.2f}; halves {h1:+.2f} / {h2:+.2f}", "",
          f"- CONVERGENT: {m1:+.2f}pp (t {t1:.2f}, n {n1}); 10d {cv.ex10.mean():+.2f}; {shape(cv)}",
          f"- SOLO: {m2:+.2f}pp (t {t2:.2f}, n {n2}); 10d {so.ex10.mean():+.2f}; {shape(so)}",
          f"  - Luk solo {R[R.arm == 'SOLO_Luk'].ex20.mean():+.2f}pp (n {(R.arm == 'SOLO_Luk').sum()}), Ariel solo {R[R.arm == 'SOLO_Ariel'].ex20.mean():+.2f}pp (n {(R.arm == 'SOLO_Ariel').sum()})", "",
          "## Secondary: same-industry convergence (yfinance industry)", "",
          f"- IND_CONV {a1:+.2f}pp (t {b1:.2f}, n {c1}) vs IND_SOLO {a2:+.2f}pp (t {b2:.2f}, n {c2}); difference {a1 - a2:+.2f}pp; "
          + (shape(I[I.arm == "IND_CONV"]) if c1 else ""), "",
          "## Convergent ticker events (every one, winners and losers)", "",
          cv[["date", "tk", "ex10", "ex20", "mae", "mfe", "asym"]].assign(date=lambda z: z.date.dt.date).round(2).to_string(index=False), "",
          "## Industry-convergence clusters", "",
          (I[I.arm == "IND_CONV"].groupby("ind").agg(n=("tk", "size"), names=("tk", lambda s: " ".join(sorted(set(s)))), ex20=("ex20", "mean")).round(2)
           .sort_values("n", ascending=False).to_string() if c1 else "none")]
    open(f"{OUT}_results.md", "w").write("\n".join(Lg) + "\n")
    print("\n".join(Lg[:14]))


if __name__ == "__main__":
    main()
