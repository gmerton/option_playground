#!/usr/bin/env python3
"""
SMALL CAPS: does the book's equity evidence (12-1 momentum, the precision breakout) hold in the universe our studies
excluded? PRE-REGISTERED 2026-09-29 -- NOT RUN (Gabe: "pre-register, don't run now").

WHY. A coverage check (2026-09-29) found that of ~1,060 US small caps ($0.3-2B, price >= $5), only ~1% pass the
>= $50M ADDV filter every equity study uses and ~10% the $30M panel cut: the ledger's momentum / breakout / dip
evidence is mid- and large-cap evidence. Gabe wants a small-cap rebound plan (IWM -8.8% from 8/14).

DATA (built when run, never overwriting the nightly liquid panel)
  S  data/cache/smallcap_panel_2009.parquet:
       PYTHONPATH=src .venv/bin/python3 run_build_liquid_panel.py --addv 5e6 --addv-max 50e6 --start 2009-01-01 \
           --out data/cache/smallcap_panel_2009.parquet
     = yfinance adjusted OHLCV for names whose 50d ADDV is $5-50M and price >= $5 on the Minervini cache's last date
     (~1,200 names, ~88% of them $0.3-2B at the $5-15M end). SURVIVORSHIP-BIASED (today's names only).
  M  data/cache/liquid_panel_2009.parquet (mid/large reference, the same code paths).
  X  data/cache/chain_spot/chain_spot_daily.parquet (closes only, INCLUDES delisted) for the survivorship check.

TESTS
  T1 MOMENTUM (primary). Monthly: names eligible on the formation date (S: 50d ADDV $5-50M, price >= $5; point-in-time
     ADDV, so the band is re-applied every month). Sort on 12-1 return; hold top vs bottom decile equal-weight for one
     month; costs 20 bp per side (small-cap round trip ~40 bp; M uses 5 bp as elsewhere). Statistic: monthly
     top-minus-bottom net spread, Newey-West t (lag 3); also top decile minus the band's equal-weight mean (the
     long-only version the book would trade). Same code on M for the reference row.
     PASS iff small-cap top-minus-bottom net t >= 3, both halves (split 2018-01) positive, >= 60% of years positive.
  T2 PRECISION BREAKOUT (primary). The precision tier (run_oneil_pyramid_8wk.py definition) on S, house trade
     (close entry, day-low stop judged on the close, 20-EMA exit, 60-session cap), costs 20 bp per side, % per trade.
     Controls: (a) SELECTION = a random same-date eligible S name bought at the same close with the same exit rule
     (ADR-tercile matched); (b) TIMING = the same name at a random later session within 60 sessions.
     PASS (selection) iff signal - (a) >= 0 with t >= 3 (date-clustered) and both halves positive; timing reported.
  T3 SURVIVORSHIP CHECK (decides how T1 is read). Re-run T1 on X, restricted to names whose 50d mean option volume is
     in the bottom half of optionable names each month (the closest small-cap proxy X allows; no market cap there),
     closes only, same costs. If T1 passes on S but X's spread is <= 0 or < half of S's -> T1 is a SURVIVORSHIP
     ARTEFACT; if X confirms (same sign, >= half) -> T1 stands.
  Multiple testing: 2 primaries (T1, T2) -> Sidak-2 |t| >= 3.2 governs, not 3.
  Caveats: survivorship in S is worse than in M (small caps delist more); yfinance small-cap bars have more gaps
  (run_build_liquid_panel's Polygon gap-fill applies); no market-cap history -> the ADDV band is the size proxy.

Usage (when approved): build S (above), then PYTHONPATH=src:. .venv/bin/python3 run_smallcap_tests.py > data/studies/logs/smallcap_tests.log
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.exit("PRE-REGISTERED ONLY (2026-09-29). Implementation is written when Gabe approves the run; the spec above is "
             "frozen as of this commit.")
