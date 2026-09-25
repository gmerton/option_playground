#!/usr/bin/env python3
"""
Is the crash-leader "edge" real, or is it survivorship?

The universe (broad_history) is the set of names that EXIST TODAY. A crash event in
2008 has had 18 years to prove the company survived; a 2024 event has had 2. If the
excess return is manufactured by that selection, it must DECAY MONOTONICALLY as
events get more recent. If it is a real behavioural edge, it should be roughly
era-stable (noisy, but not trending to zero).

Also profiles the payoff shape: mean vs median, win rate, and how much of the total
excess is carried by the top few percent of trades. A strategy whose mean is carried
by its tail is an option position, not a base-rate edge, and has to be sized like one.

Run:
    PYTHONPATH=src .venv/bin/python3 scratch_crash_leader_bias.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

STRONG = "data/studies/crash_leader_events.parquet"
NONE = "data/studies/crash_nostrength_events.parquet"


def era_table(ev: pd.DataFrame, h: int, entry: str, dd: float) -> pd.DataFrame:
    s = ev[(ev.h == h) & (ev.entry == entry) & (ev.dd == dd)].dropna(subset=["excess"]).copy()
    s["era"] = pd.cut(s.date.dt.year,
                      [2005, 2010, 2014, 2018, 2022, 2027],
                      labels=["2006-10", "2011-14", "2015-18", "2019-22", "2023-26"])
    out = []
    for era, g in s.groupby("era", observed=True):
        by_date = g.groupby("date").excess.mean()
        t = by_date.mean() / (by_date.std(ddof=1) / np.sqrt(len(by_date))) if len(by_date) > 2 else np.nan
        out.append({
            "era": era, "n": len(g),
            "exc%": g.excess.mean() * 100,
            "med%": g.excess.median() * 100,
            "win%": (g.excess > 0).mean() * 100,
            "t": t,
        })
    return pd.DataFrame(out)


def payoff_shape(ev: pd.DataFrame, h: int, entry: str, dd: float) -> str:
    s = ev[(ev.h == h) & (ev.entry == entry) & (ev.dd == dd)].dropna(subset=["excess"])
    x = np.sort(s.excess.to_numpy())[::-1]
    n = len(x)
    tot = x.sum()
    lines = [f"  n={n}  mean={x.mean()*100:.2f}%  median={np.median(x)*100:.2f}%  win={(x>0).mean()*100:.1f}%"]
    for pct in (0.01, 0.05, 0.10, 0.25):
        k = max(1, int(n * pct))
        lines.append(f"  top {pct*100:>4.0f}% of trades carry {x[:k].sum()/tot*100:6.1f}% of total excess")
    k5 = max(1, int(n * 0.05))
    ex_top = (tot - x[:k5].sum()) / (n - k5)
    lines.append(f"  mean excess EXCLUDING the top 5% of trades: {ex_top*100:.2f}%")
    return "\n".join(lines)


def main() -> None:
    strong = pd.read_parquet(STRONG)
    print("=" * 78)
    print("SURVIVORSHIP DECAY TEST — strength=runup, dd30, arrival, 252d")
    print("if the edge is survivorship, exc% falls monotonically toward the present")
    print("=" * 78)
    for h in (63, 252):
        print(f"\nhorizon {h}d:")
        print(era_table(strong, h, "arrival", 30).to_string(index=False,
              float_format=lambda v: f"{v:,.2f}"))

    print("\n" + "=" * 78)
    print("PAYOFF SHAPE — dd30 / arrival")
    print("=" * 78)
    for h in (63, 252):
        print(f"\nhorizon {h}d:")
        print(payoff_shape(strong, h, "arrival", 30))

    try:
        nostr = pd.read_parquet(NONE)
    except Exception:
        print("\n(control file not ready)")
        return

    print("\n" + "=" * 78)
    print("DOES 'WAS STRONG' ADD ANYTHING? — strong vs no-strength-filter, dd30/arrival")
    print("=" * 78)
    rows = []
    for h in (21, 63, 126, 252):
        for name, ev in (("strong", strong), ("any", nostr)):
            s = ev[(ev.h == h) & (ev.entry == "arrival") & (ev.dd == 30)].dropna(subset=["excess"])
            rows.append({"h": h, "cohort": name, "n": len(s),
                         "exc%": s.excess.mean() * 100,
                         "med%": s.excess.median() * 100,
                         "win%": (s.excess > 0).mean() * 100})
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))


if __name__ == "__main__":
    main()
