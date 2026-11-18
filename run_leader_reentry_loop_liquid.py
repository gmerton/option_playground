"""ROBUSTNESS (exploratory, not pre-registered) for run_leader_reentry_loop.py, 2026-11-17.
Same events/arms/metrics on liquid_panel_2009 (yfinance ADJUSTED closes, no break-cleaning) because the chain_spot
cleaning drops 26.4% of ticker-days (4,191 tickers) -- plausibly censoring the explosive names this test is about.
⚠ survivorship: liquid as of 2026 (dead names absent), which flatters longer holding (C) most.
Liquidity: 50d mean dollar volume >= $20M and close >= $5. Same 2011-01 -> 2025-02 event window.
Then the post-hoc arithmetic re-score on the same events."""
import sys, subprocess; sys.path.insert(0, '.')
import pandas as pd
import run_leader_reentry_loop as L, run_dip_survivorship as DS
def load():
    p = pd.read_parquet('data/cache/liquid_panel_2009.parquet'); p['date'] = pd.to_datetime(p.date)
    C = p.pivot(index='date', columns='ticker', values='close').sort_index()
    V = p.pivot(index='date', columns='ticker', values='dolvol').reindex_like(C)
    return C, V
L.load = load; DS.OPTVOL_MIN = 20e6; L.OUT = 'data/studies/leader_reentry_loop_2026-11-17_liquid'
L.main()
