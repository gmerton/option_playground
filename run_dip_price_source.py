#!/usr/bin/env python3
"""Dip-in-uptrend sign flip: price source vs definition (2026-09-29, audit step 3 item 6).

PRE-REGISTERED: data/studies/dip_price_source_2026-09-29.md (committed fb0e91a before this ran).
run_dip_survivorship.run() unchanged, on the survivor names only, fed (a) chain-spot closes and (b) liquid_panel_2009
closes; same tickers, dates, option-volume liquidity gate and k. Primary: SURV P2 K0 month-clustered excess.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_dip_price_source.py > data/studies/dip_price_source_2026-09-29.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run_dip_survivorship as ds


def main():
    Cc, V = ds.adjust_and_clean(ds.pull())
    raw = pd.read_parquet(ds.REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    raw["date"] = pd.to_datetime(raw.date)
    Cp = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    cols = sorted(set(Cp.columns) & set(Cc.columns))
    Cc, V = Cc[cols], V[cols]
    Cp = Cp.reindex(index=Cc.index, columns=cols)
    surv = set(cols)
    k = ds.k_scale()
    rc, rp = Cc.pct_change(fill_method=None), Cp.pct_change(fill_method=None)
    corr = pd.Series({c: rc[c].corr(rp[c]) for c in cols}).dropna()
    gap = (Cc / Cp - 1).abs().stack()
    print(f"survivor names in both sources: {len(cols)}; dates {Cc.index.min().date()} -> {Cc.index.max().date()}; k {k:.3f}")
    print(f"daily-return correlation chain vs panel, per name: median {corr.median():.3f}, p10 {corr.quantile(.1):.3f}; "
          f"|chain/panel - 1| median {gap.median() * 100:.2f}%, p90 {gap.quantile(.9) * 100:.2f}%")
    rows = []
    for lab, C in (("chain-spot closes", Cc), ("panel closes", Cp)):
        E, fr, in_ep, terc, pops, cc = ds.run(C, V, surv, k)
        E = E.copy(); E["x"] = ds.excess(E, fr, in_ep, terc, pops, cc, surv, "SURV")
        for rung in ("K0", "K3"):
            T = E[(E["pop"] == "P2") & (E.rung == rung)]
            st, _ = ds.cellstats(T.x.values, T.date)
            rows.append(dict(source=lab, rung=rung, fwd=T.fwd.mean(), **st))
    R = pd.DataFrame(rows)
    print(R.round(3).to_string(index=False))
    p = R[(R.source == "panel closes") & (R.rung == "K0")].iloc[0]
    read = ("DEFINITION drives the flip -> NULL (fragile)" if p.excess <= 0 else
            "PRICE SOURCE drives the flip -> stays PARKED, survivorship unresolved" if p.excess >= 0.5 and p.t >= 2 else
            "ambiguous -> stays PARKED")
    print(f"\nREAD (panel closes, P2 K0: {p.excess:+.2f}pp, t {p.t:+.2f}): {read}")
    R.to_csv(ds.REPO / "data/studies/dip_price_source_2026-09-29.csv", index=False)


if __name__ == "__main__":
    main()
