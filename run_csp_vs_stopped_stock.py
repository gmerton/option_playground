#!/usr/bin/env python3
"""
Is the cash-secured put's apparent edge over shares really a STOP-MANAGEMENT artefact?

Motivation (2026-09-23, Gabe, after the OneOption review): the BCI study found a CSP ~= the stock held at the put's
delta, minus costs -- but both arms were UNMANAGED. In practice the share buyer sets a reasonably tight stop that
breaches in chop; the put seller sets none. Hypothesis: "puts beat shares in a choppy market" is the whipsaw cost
of a tight resting stop, not premium.

PRE-REGISTERED 2026-09-23, before any stop arm was computed:

  Sample     data/cache/bci_csp/trades.parquet (built by run_bci_csp_study.py): straddle pool, every Friday
             2018-01 -> 2026-02, OTM put nearest 0.30 delta (rule "30"), tenors M (~28 DTE) and W (~7 DTE), real
             fills (sell at mid - 25% of spread, $0.0065/share), settled at intrinsic from the raw close.
  Arms (same name, same entry date, same collateral K - premium; all in % of collateral)
    a  PUT      the CSP held to expiry (the cached csp column).
    b  REST     stock at |delta| shares per share of collateral, bought at the entry close; stop RESTING
                intraday: exit on the first session whose low <= stop, filled at min(open, stop) (gaps fill worse).
    c  CLOSE    same stock, same stop level, judged on the CLOSE: exit at the first close < stop.
    d  HOLD     same stock, no stop, sold at the settlement close (= the BCI benchmark, now with stock costs).
             Stock cost: 10 bp per side of traded notional (pattern_test SLIP), charged on b/c/d alike.
             A stopped arm sits in cash for the rest of the window (0 return).
  Stop levels (below the entry close, ADR = 20-session mean of high/low - 1, known at entry)
    T05  0.5 ADR       <- PRIMARY: "a reasonably tight stop"
    LOW  the entry session's low (the house tight stop), floored at 0.5% of price
    T10  1.0 ADR       (the house disaster-stop width)
  PRIMARY CELL  tenor M, stop T05, contrast a - b, month-clustered t.
    Prediction: a - b > 0, |t| >= 3, both chronological halves (2018-2021 / 2022-2026) positive, and a - c and
    a - d NOT significant (i.e. the put's advantage is the resting stop, not premium).
  Regime (pre-registered interaction): SPY 20-session efficiency ratio at entry, |C_t - C_t-20| / sum|dC|,
    terciles over entry dates; CHOPPY = bottom tercile, TREND = top. Prediction: (a - b) larger in CHOPPY.
  Multiple testing: everything besides the primary is secondary -- 2 tenors x 3 stops x {a-b, a-c, c-b} plus the 6
    regime interactions = 24 cells, Sidak 5% two-sided -> |t| >= 3.07 governs them.
  Mechanism diagnostics (descriptive): stop-hit rate, and the share of REST-stopped trades whose stock finished
    ABOVE the entry by expiry (the whipsaw share).

Usage:
  PYTHONPATH=src .venv/bin/python3 run_csp_vs_stopped_stock.py > data/studies/csp_vs_stopped_stock_2026-09-23.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
SLIP = 0.0010
MIN_STOP = 0.005
SIDAK_T = 3.07

T = pd.read_parquet("data/cache/bci_csp/trades.parquet")
T = T[T.rule == "30"].copy()
T["trade_date"], T["expiry"] = pd.to_datetime(T.trade_date), pd.to_datetime(T.expiry)

P = pd.read_parquet("data/cache/bci_csp/prices.parquet").sort_values(["ticker", "date"])
for c in ("open", "high", "low"):
    P["r" + c] = P[c] * P.factor                                   # RAW prices: strikes/S0/ST are raw
P["adr"] = (P.high / P.low - 1).groupby(P.ticker).transform(lambda s: s.rolling(20).mean())

spy = P[P.ticker == "SPY"].set_index("date").close
er = ((spy - spy.shift(20)).abs() / spy.diff().abs().rolling(20).sum()).rename("spy_er")

# ------------------------------------------------------------------ path simulation, per ticker
out = []
for tk, g in T.groupby("ticker"):
    p = P[P.ticker == tk]
    if p.empty:
        continue
    d = p.date.values
    o, h, l, c = p.ropen.values, p.rhigh.values, p.rlow.values, p.raw_close.values
    adr = p.adr.values
    i0 = np.searchsorted(d, g.trade_date.values)
    i1 = np.searchsorted(d, g.expiry.values, side="right") - 1      # last session on/before expiry
    ok = (i0 < len(d)) & (d[np.minimum(i0, len(d) - 1)] == g.trade_date.values) & (i1 > i0)
    g = g[ok].copy()
    i0, i1 = i0[ok], i1[ok]
    S0 = g.S0.values
    stops = {"T05": S0 * (1 - 0.5 * adr[i0]),
             "T10": S0 * (1 - 1.0 * adr[i0]),
             "LOW": np.minimum(l[i0], S0 * (1 - MIN_STOP))}
    for name, st in stops.items():
        xr = np.full(len(g), np.nan); xc = np.full(len(g), np.nan)
        hr = np.zeros(len(g), bool); hc = np.zeros(len(g), bool)
        for k in range(len(g)):
            a, b = i0[k] + 1, i1[k] + 1
            if not np.isfinite(st[k]):
                continue
            lw = np.nonzero(l[a:b] <= st[k])[0]
            if len(lw):
                j = a + lw[0]; xr[k] = min(o[j], st[k]); hr[k] = True
            cl = np.nonzero(c[a:b] < st[k])[0]
            if len(cl):
                xc[k] = c[a + cl[0]]; hc[k] = True
        g[f"xr_{name}"], g[f"xc_{name}"] = np.where(hr, xr, g.ST), np.where(hc, xc, g.ST)
        g[f"hr_{name}"], g[f"hc_{name}"] = hr, hc
        g[f"ok_{name}"] = np.isfinite(st)
    g["adr0"] = adr[i0]
    out.append(g)
D = pd.concat(out, ignore_index=True)
D = D.merge(er, left_on="trade_date", right_index=True, how="left")

coll = D.strike - D.sellpx
dshares = D.delta.abs()
cost = 100 * 2 * SLIP * dshares * D.S0 / coll                        # stock round trip, % of collateral
D["a"] = D.csp
D["d"] = 100 * dshares * (D.ST - D.S0) / coll - cost
for s in ("T05", "LOW", "T10"):
    D[f"b_{s}"] = 100 * dshares * (D[f"xr_{s}"] - D.S0) / coll - cost
    D[f"c_{s}"] = 100 * dshares * (D[f"xc_{s}"] - D.S0) / coll - cost
D["half"] = np.where(D.trade_date < "2022-01-01", "H1 2018-21", "H2 2022-26")
D["year"] = D.trade_date.dt.year
ed = D.drop_duplicates("trade_date").spy_er.dropna()
q1, q2 = ed.quantile([1 / 3, 2 / 3])
D["regime"] = np.select([D.spy_er <= q1, D.spy_er >= q2], ["CHOPPY", "TREND"], "MID")


def ct(x: pd.DataFrame, col: str, cl: str) -> tuple[float, float, int]:
    s = x.groupby(cl)[col].mean().dropna()
    return x[col].mean(), (s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan), len(s)


def fmt(m, t, n):
    return f"{m:+7.3f} (t {t:+5.2f}, n_cl {n})"


print(f"CSP vs stopped stock -- {len(D):,} trades, {D.ticker.nunique()} names, "
      f"{D.trade_date.min().date()} -> {D.trade_date.max().date()}; SPY ER terciles {q1:.3f} / {q2:.3f}")
print(f"Sidak threshold for the 24 secondary cells: |t| >= {SIDAK_T}")

summary = []
for tenor in ("M", "W"):
    x = D[D.tenor == tenor].copy()
    cl = "month" if tenor == "M" else "week"
    print(f"\n{'#' * 110}\n# tenor {tenor}  ({len(x):,} trades, t clustered by {cl})\n{'#' * 110}")
    print("\nlevels (% of collateral per trade):")
    lv = {"a PUT": ct(x, "a", cl), "d HOLD": ct(x, "d", cl)}
    for s in ("T05", "LOW", "T10"):
        lv[f"b REST {s}"] = ct(x, f"b_{s}", cl); lv[f"c CLOSE {s}"] = ct(x, f"c_{s}", cl)
    for k, v in lv.items():
        print(f"  {k:14s} {fmt(*v)}")
    for s in ("T05", "LOW", "T10"):
        x[f"ab_{s}"] = x.a - x[f"b_{s}"]; x[f"ac_{s}"] = x.a - x[f"c_{s}"]; x[f"cb_{s}"] = x[f"c_{s}"] - x[f"b_{s}"]
        print(f"\n-- stop {s}: REST hit {100 * x[f'hr_{s}'].mean():.1f}%  CLOSE hit {100 * x[f'hc_{s}'].mean():.1f}%  "
              f"whipsaw (REST-stopped, stock ended above entry) "
              f"{100 * (x.loc[x[f'hr_{s}'], 'ST'] > x.loc[x[f'hr_{s}'], 'S0']).mean():.1f}%")
        for lab, col in (("a - b (put minus resting stop)", f"ab_{s}"), ("a - c (put minus close stop)", f"ac_{s}"),
                         ("c - b (close minus resting)", f"cb_{s}")):
            m, t, n = ct(x, col, cl)
            h = {hh: ct(z, col, cl) for hh, z in x.groupby("half")}
            rg = {r: ct(z, col, cl) for r, z in x.groupby("regime")}
            prim = " <== PRIMARY" if (tenor == "M" and s == "T05" and col.startswith("ab")) else ""
            print(f"  {lab:32s} {fmt(m, t, n)}  | halves " +
                  "  ".join(f"{k} {v[0]:+.3f} (t {v[1]:+.2f})" for k, v in h.items()) + prim)
            print(f"  {'':32s} regime: " + "  ".join(f"{k} {v[0]:+.3f} (t {v[1]:+.2f})" for k, v in rg.items()))
            summary.append(dict(tenor=tenor, stop=s, contrast=col[:2], mean=m, t=t, n_cl=n,
                                h1=h.get("H1 2018-21", (np.nan,))[0], h2=h.get("H2 2022-26", (np.nan,))[0]))
        # regime interaction: CHOPPY minus TREND on a - b, clustered by the entry cluster
        z = x[x.regime.isin(["CHOPPY", "TREND"])]
        s_c = z[z.regime == "CHOPPY"].groupby(cl)[f"ab_{s}"].mean()
        s_t = z[z.regime == "TREND"].groupby(cl)[f"ab_{s}"].mean()
        diff = s_c.mean() - s_t.mean()
        se = np.sqrt(s_c.var() / len(s_c) + s_t.var() / len(s_t))
        print(f"  interaction (a-b CHOPPY minus TREND): {diff:+.3f} (Welch t {diff / se:+.2f}; {len(s_c)} vs {len(s_t)} clusters)")
        summary.append(dict(tenor=tenor, stop=s, contrast="ab_chop-trend", mean=diff, t=diff / se, n_cl=len(s_c) + len(s_t)))
    print("\nby year, a - b and a - d (stop T05):")
    print(x.groupby("year")[["a", "d", "b_T05", "c_T05", "ab_T05", "ac_T05"]].mean().round(3).to_string())

S = pd.DataFrame(summary)
S["passes_sidak"] = S.t.abs() >= SIDAK_T
S.to_csv("data/studies/csp_vs_stopped_stock_2026-09-23.csv", index=False)
print("\nsummary (data/studies/csp_vs_stopped_stock_2026-09-23.csv):")
print(S.round(3).to_string(index=False))

# ------------------------------------------------------------------ EXPLORATORY (added after the primary was read)
# The stopped arms sit in cash most of the window, so raw means compare positions of very different risk.
print("\n# EXPLORATORY (not pre-registered): risk per arm")
for tenor in ("M", "W"):
    x = D[D.tenor == tenor]
    cl = "month" if tenor == "M" else "week"
    rows = {}
    for col in ("a", "d", "b_T05", "c_T05", "b_T10", "c_T10"):
        s, m = x[col], x.groupby(cl)[col].mean()
        rows[col] = dict(mean=s.mean(), sd=s.std(), worst1pct=s[s <= s.quantile(0.01)].mean(),
                         cluster_sharpe=m.mean() / m.std())
    print(tenor); print(pd.DataFrame(rows).T.round(3).to_string())
    print("  2020 only:", x[x.year == 2020][["a", "d", "b_T05", "c_T05"]].mean().round(2).to_dict(),
          "| ex-2020 a - b T05:", round((x[x.year != 2020].a - x[x.year != 2020].b_T05).mean(), 3))
