#!/usr/bin/env python3
"""
COPY BERKSHIRE'S DISCLOSED BUYS: buy each new Berkshire Hathaway position when its 13F first makes it public, hold
12 months (pre-registered 2026-09-25, before any code or data pull; Gabe, prompted by Buffett's Japan trading-house
stakes. The Japan bet itself is one decision on five TSE names and can't be tested; this is the testable,
repeatable version). ⛔ NOT RUN -- Gabe: "pre-register it, don't run it now". Queued in TEST_INDEX section 10.

WHY NEW. The ledger has no 13F / superinvestor copy test. Related rows: KINFO/USIC "verified != edge" (contest
winners, survivorship), and the congress-copy idea (queued with the LEAP interest, not run). Published work
(Martin & Puthenpurackal 2008) reports that mimicking Berkshire after disclosure beat the S&P by ~10%/yr (1976-2006).
Two decades later, with Berkshire's size pushing it into mega-caps, whether that still holds is the question.

DATA
  filings  SEC EDGAR 13F-HR and 13F-HR/A for Berkshire Hathaway Inc, CIK 0001067983 (free; XML information tables from
           2013-Q2, text tables before). ⚠ Berkshire routinely gets CONFIDENTIAL TREATMENT: a position can first appear
           in a later amendment. The event date is when the position FIRST became PUBLIC (original or amendment
           acceptance timestamp), never the quarter-end: using the quarter-end is look-ahead.
  prices   PRIMARY 2010-2026 on silver.chain_spot_daily (survivorship-free, split-adjusted; every Berkshire holding is
           optionable). EXPLORATORY 1999-2009 on yfinance (survivor-biased, which will be stated).
EVENTS    PRIMARY: a NEW position = a CUSIP absent from the previous PUBLIC holdings set. Share-class duplicates are
          collapsed to one issuer. EXPLORATORY: an ADD of >= 50% more shares in an existing position.
ENTRY     the close of the first full session after the EDGAR acceptance datetime (after 16:00 ET -> the next session).
          Hold 12 months (PRIMARY), with 3 and 6 months also reported; a delisted name exits at its last close.
CONTROLS  (1) SPY over the identical window (the headline benchmark); (2) the SPDR sector ETF mapped from the issuer's
          SIC code (holds the sector fixed: Berkshire is heavy in financials and energy); (3) descriptive: the same
          stock from the quarter-end to the disclosure date, i.e. what the lag costs a copier.
STATS     excess return per event, clustered by FILING (positions disclosed together share dates), t on the cluster
          means. Horizons M = 3 -> Sidak |t| >= 2.39; the house |t| >= 3 GOVERNS; both halves (split 2018-01) the
          same sign; a majority of years positive. PRIMARY = new positions, 12 months, vs the sector ETF.
POWER     expect ~5-10 new positions a year -> ~80-150 events in ~50-60 filing clusters for 2010-2026. Report the minimum
          detectable effect at 80% power up front; a null below it is UNDERPOWERED, not NULL.
CONFOUND  the 13F mixes Buffett's picks with those of his two portfolio managers (Combs, Weschler), which aren't
          distinguished. EXPLORATORY split by the position's $ size at first disclosure: the top quartile (likely
          Buffett's) vs the rest.
READ      a pass means a copy sleeve (buy at disclosure, 12-month hold) is worth running forward as its own lockbox, like
          the momentum sleeve. Given the concentrated mega-cap book, the prior is that the post-2010 edge has shrunk
          toward zero vs the sector.
Local vs cloud: local (EDGAR pulls are ~150 small filings; prices already cached). EDGAR fair-access rules: <= 10
requests/s, with a User-Agent that includes contact info.

Usage (when approved): PYTHONPATH=src:. .venv/bin/python3 run_berkshire_13f_copy.py
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-25, not built/run yet (Gabe: don't run it now). See the docstring and TEST_INDEX section 10.")
