#!/usr/bin/env python3
"""
Retrospective: Gabe's long straddles, his early exits vs the playbook's hold-to-expiry, SIZE-NEUTRAL (2026-10-04).

Gabe: "exiting early is beating the house strategy, which is negative -- but the straddles don't all have the same
position size." The Performance page compares DOLLARS (realized vs 'if held to expiry'), which weights big positions
more. This puts every trade on the same footing: P&L as a % of the premium paid.

Rows: data/journal/trade_reviews_data.json, vehicle 'long straddle' (systematic = tag straddle_screener and not
'discretionary'; the rest = discretionary), closed, with the hold-to-expiry value settled (expiry passed). Premium and
hold P&L use the page's own functions (run_trade_review_pages._multileg_entry_premium / _attach_hold_to_expiry: the
ORIGINAL opening legs settled at intrinsic on the underlying's expiry close, commissions ignored on the hold side).
Reported per group (systematic / discretionary / all):
  - dollar totals: realized vs hold (what the page shows)
  - equal-weighted: mean and median % on premium, early exit vs hold; paired difference with t clustered by entry date
    (Friday batches share a market move)
  - size check: premium quartiles; correlation of premium with (exit% - hold%); dollar-weighted vs equal-weighted gap
  - where the early exit helped: split by hold outcome (would have expired worthless-ish vs finished in the money)
  - per $1,000 of premium: early exit vs hold.
This is the journal used for EXECUTION / management quality (admissible), not for setup selection.

  PYTHONPATH=src:. .venv/bin/python3 run_straddle_retro.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from lib.mysql_lib import _get_conn
from run_trade_review_pages import _attach_hold_to_expiry, _multileg_entry_premium

OUT = "data/studies/straddle_retro_2026-10-04"


def ct(x: pd.Series, g: pd.Series):
    x = x.dropna(); g = g.loc[x.index]; n = len(x)
    if n < 3:
        return np.nan, np.nan, n
    mu = x.mean(); s = (x - mu).groupby(g).sum(); G = len(s)
    se = np.sqrt((s ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1))
    return mu, mu / se if se > 0 else np.nan, n


def main() -> None:
    rows = json.load(open("data/journal/trade_reviews_data.json"))["rows"]
    st = [r for r in rows if r.get("vehicle") == "long straddle" and r.get("isPrimary", True)]
    conn = _get_conn()
    try:
        _attach_hold_to_expiry(conn, st)
        for r in st:
            r["_prem"] = _multileg_entry_premium(conn, r["underlying"], r["entryDate"])
    finally:
        conn.close()
    D = pd.DataFrame([dict(tk=r["underlying"], entry=r["entryDate"], exit=r.get("exitDate"), tags=r.get("tags") or [],
                           realized=r.get("realizedPnl"), hold=r.get("_holdPnl"), prem=r.get("_prem")) for r in st])
    D["system"] = D.tags.apply(lambda t: "straddle_screener" in t and "discretionary" not in t)
    D = D[D.exit.notna() & D.hold.notna() & D.realized.notna() & (D.prem.fillna(0) > 0)].copy()
    D["entry"] = pd.to_datetime(D.entry); D["exit"] = pd.to_datetime(D.exit)
    D["exit_pct"] = D.realized / D.prem * 100; D["hold_pct"] = D.hold / D.prem * 100
    D["diff_pct"] = D.exit_pct - D.hold_pct
    D.drop(columns="tags").to_csv(f"{OUT}_trades.csv", index=False)

    L = [f"# Long straddles: early exit vs hold to expiry, size-neutral ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         "P&L as % of premium paid; hold = original legs settled at intrinsic on expiry (commissions ignored on the hold side).", ""]
    for lab, X in (("SYSTEMATIC (straddle screener)", D[D.system]), ("DISCRETIONARY", D[~D.system]), ("ALL", D)):
        if not len(X):
            continue
        m, t, n = ct(X.diff_pct, X.entry)
        q = pd.qcut(X.prem, 4, labels=["Q1 smallest", "Q2", "Q3", "Q4 largest"], duplicates="drop") if len(X) >= 8 else None
        L += [f"## {lab}: {len(X)} closed straddles, {X.entry.min().date()} → {X.entry.max().date()}", "",
              f"- **Dollars (what the page shows):** realized {X.realized.sum():+,.0f} vs hold-to-expiry {X.hold.sum():+,.0f} → early exits {X.realized.sum() - X.hold.sum():+,.0f}; total premium {X.prem.sum():,.0f}",
              f"- **Per $1,000 of premium:** early exit {X.realized.sum() / X.prem.sum() * 1000:+,.0f} vs hold {X.hold.sum() / X.prem.sum() * 1000:+,.0f}",
              f"- **Equal-weighted (size-neutral):** early exit mean {X.exit_pct.mean():+.1f}% (median {X.exit_pct.median():+.1f}%) vs hold mean {X.hold_pct.mean():+.1f}% (median {X.hold_pct.median():+.1f}%)",
              f"- **Paired early − hold:** {m:+.1f}pp per trade, t {t:.2f} (clustered by entry date, {X.entry.nunique()} dates), n {n}; early exit better on {(X.diff_pct > 0).mean():.0%} of trades",
              f"- win rate: early exit {(X.exit_pct > 0).mean():.0%} vs hold {(X.hold_pct > 0).mean():.0%}; hold lost ≥ 75% of premium on {(X.hold_pct <= -75).mean():.0%}",
              f"- size check: corr(premium, early − hold) {X.prem.corr(X.diff_pct):+.2f}; dollar-weighted gap {(X.realized.sum() - X.hold.sum()) / X.prem.sum() * 100:+.1f}% of premium vs equal-weighted {X.diff_pct.mean():+.1f}pp"]
        if q is not None:
            g = X.groupby(q, observed=True).agg(n=("prem", "size"), prem=("prem", "median"), exit=("exit_pct", "mean"), hold=("hold_pct", "mean"), diff=("diff_pct", "mean"))
            L += ["", "By position size (premium quartile; mean % of premium):", "", g.round(1).to_string()]
        good = X.hold_pct > 0
        L += ["", f"- where holding would have WON (n {good.sum()}): early exit {X[good].exit_pct.mean():+.1f}% vs hold {X[good].hold_pct.mean():+.1f}% (early exit gave up {X[good].diff_pct.mean():+.1f}pp)",
              f"- where holding would have LOST (n {(~good).sum()}): early exit {X[~good].exit_pct.mean():+.1f}% vs hold {X[~good].hold_pct.mean():+.1f}% (early exit saved {X[~good].diff_pct.mean():+.1f}pp)", ""]
    L += ["## Trades", "", D[["tk", "entry", "exit", "system", "prem", "realized", "hold", "exit_pct", "hold_pct", "diff_pct"]]
          .assign(entry=lambda z: z.entry.dt.date, exit=lambda z: z.exit.dt.date).sort_values("entry").round(1).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
