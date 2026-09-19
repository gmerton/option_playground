#!/usr/bin/env python3
"""
Election cycles: what actually moved after each US election, and was it the narrative beneficiary?

Descriptive by construction -- 5 elections is not a sample. The question is not "can we predict elections"
but "IF you have a view on the outcome, how big and how fast is the sector rotation, and is it still
available the day after?"

Elections covered: 2016-11-08 (R sweep), 2018-11-06 (D House / R Senate), 2020-11-03 (D sweep, called 11-07),
2022-11-08 (R House / D Senate), 2024-11-05 (R sweep). 2026-11-03 midterms are ahead.
Windows: T-20 -> T0 (what was priced in), T0 -> T+1 (the gap), T+1 -> T+20 and T+1 -> T+60 (what was still
available AFTER the result was known).

Usage: PYTHONPATH=src .venv/bin/python3 run_election_cycles.py > data/studies/election_cycles_2026-09-18.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd, yfinance as yf
warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)

ELECTIONS = {"2016-11-08": "R sweep (Trump I)", "2018-11-06": "split (D House)",
             "2020-11-03": "D sweep (Biden)", "2022-11-08": "split (R House)",
             "2024-11-05": "R sweep (Trump II)"}
TICK = {"SPY": "S&P 500", "IWM": "small caps", "QQQ": "nasdaq", "XLF": "financials", "KRE": "regional banks",
        "XLE": "energy", "XOP": "E&P", "ITA": "defense", "XLV": "health care", "IBB": "biotech",
        "ICLN": "clean energy", "TAN": "solar", "XLI": "industrials", "XLU": "utilities", "XLP": "staples",
        "XRT": "retail", "TLT": "20y treasuries", "UUP": "dollar", "GLD": "gold", "XME": "metals/mining",
        "TSLA": "TSLA", "PLTR": "PLTR", "MSTR": "MSTR"}
px = yf.download(list(TICK), start="2016-08-01", end="2026-09-19", auto_adjust=True, progress=False)["Close"]
px.index = pd.to_datetime(px.index).tz_localize(None)

def win(s: pd.Series, i0: int, a: int, b: int) -> float:
    if i0 + a < 0 or i0 + b >= len(s):
        return np.nan
    x, y = s.iloc[i0 + a], s.iloc[i0 + b]
    return 100 * (y / x - 1) if np.isfinite(x) and np.isfinite(y) else np.nan

for d, lab in ELECTIONS.items():
    i0 = px.index.searchsorted(pd.Timestamp(d))
    rows = {}
    for t, name in TICK.items():
        s = px[t].dropna()
        if len(s) < 100:
            continue
        j = s.index.searchsorted(pd.Timestamp(d))
        if j >= len(s) or abs((s.index[j] - pd.Timestamp(d)).days) > 5:
            continue                                   # the ticker did not trade then (e.g. PLTR before 2020)
        rows[name] = dict(pre20=win(s, j, -20, 0), day1=win(s, j, 0, 1),
                          after20=win(s, j, 1, 20), after60=win(s, j, 1, 60))
    T = pd.DataFrame(rows).T.dropna(how="all")
    T["rel60"] = T.after60 - T.loc["S&P 500", "after60"]
    print(f"\n=== {d}  {lab} ===  (%; 'after' windows start the day AFTER the election)")
    print("  top 5 by 60-session move after the result:")
    print("   " + T.sort_values("after60", ascending=False).head(5).round(1).to_string().replace("\n", "\n   "))
    print("  bottom 5:")
    print("   " + T.sort_values("after60").head(5).round(1).to_string().replace("\n", "\n   "))
    print(f"  S&P: day1 {T.loc['S&P 500','day1']:+.1f}%, +20 {T.loc['S&P 500','after20']:+.1f}%, "
          f"+60 {T.loc['S&P 500','after60']:+.1f}% | dispersion of rel60 across vehicles: "
          f"{T.rel60.std():.1f}pp, range {T.rel60.min():+.1f} to {T.rel60.max():+.1f}")

print("\n=== how much of the 60-session move happened on day 1? (median across vehicles) ===")
rows = {}
for d, lab in ELECTIONS.items():
    fr = []
    for t in TICK:
        s = px[t].dropna()
        j = s.index.searchsorted(pd.Timestamp(d))
        if j + 60 >= len(s) or abs((s.index[j] - pd.Timestamp(d)).days) > 5:
            continue
        d1, d60 = win(s, j, 0, 1), win(s, j, 0, 60)
        if np.isfinite(d1) and np.isfinite(d60) and abs(d60) > 2:
            fr.append(d1 / d60)
    rows[f"{d} {lab}"] = dict(median_share_day1=np.nanmedian(fr), n=len(fr))
print(pd.DataFrame(rows).T.round(2).to_string())
