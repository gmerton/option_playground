#!/usr/bin/env python3
"""
QUIET KNIFE x CROWDED SHORT x SCHEDULED CATALYST: is a beaten-down, quiet stock a buy when a KNOWN catalyst is coming
and the short side is crowded? (pre-registered 2026-09-27, before any code or data work; Gabe: "yes". ⛔ NOT RUN --
queued in TEST_INDEX section 10; run on command.)

WHY. Gabe's Aug-2026 IBIT buys rode a rebound whose drivers were partly knowable before entry: a White House crypto
summit announced in advance (8/19), and a crowded short (~$2.7B liquidated in 24 h). Alone, "quiet and low in its
range" is a loser (quiet_knife_leaps_2026-09-27: stock lagged same-date control -7.7pp over 180 d; LEAPs INVERTED,
t -4.09). Scheduled catalysts alone don't pay here either (buying into earnings, earnings proximity RETRACTED,
post-catalyst entry NULL, FOMC noise) and neither does high short interest on breakouts (BB-1 NULL, leans negative).
The CONJUNCTION -- quiet knife + crowded short + a catalyst dated before entry -- has never been tested. Stock returns
only (Gabe: "I wouldn't focus on the vehicle").

UNIVERSE   liquid_panel_2009 (1,728 names, yfinance-adjusted; ⚠ survivor-biased, which FLATTERS buying low -- the
           same-date control shares the bias), eligible = ADDV >= $50M and price >= $5 on the prior day.
WINDOW     weekly evaluation dates (last session of each week) 2018-01 -> 2026-06, set by short-interest coverage
           (FINRA via Polygon, data/cache/short_interest.parquet, 2017-12 ->) and a 60-session exit.
STATE      QUIET KNIFE, a vectorised equivalent of lib.sleeping_giants.detector with the coiling gate flipped (as in
           run_quiet_knife_leaps.py): ATR(14)% in the bottom 25% of its trailing 756 sessions AND ATR(14) < ATR(50);
           trailing-1,500-session high-low range >= 50% of price; price <= 40% of that range; the window high set
           >= 1.5 years ago. VALIDATION (declared): on 200 random name-dates the vectorised flag must agree with
           analyze() >= 95% of the time, else fall back to analyze() on the episodes' dates.
           Episodes: first qualifying week, a new episode after a > 60-day gap (as before).
SHORT      days-to-cover from the latest FINRA settlement that was PUBLIC at entry: settlement date + 10 trading
           days (FINRA's publication lag) <= entry date. HIGH = top tercile of DTC within that week's eligible names;
           LOW = bottom tercile. (BB-1 used the same field.)
CATALYST   a scheduled earnings report (data/cache/earnings_yf.parquet) inside the first 30 calendar days after
           entry. ⚠ yfinance stores actual report dates; companies announce them ~2-5 weeks ahead, so the 30-day window
           is the stated point-in-time proxy.
TRADE      buy the close of the episode date, hold 60 sessions (exit at the close); no stop (the question is the
           direction of the drift, not a stop rule); 10 bp per side.
CONTROL    SAME-DATE: every other eligible name that week with the SAME short tercile and the SAME catalyst flag but
           NOT in the quiet-knife state -- holds the market, the short crowding and the catalyst fixed, varies only
           the quiet-knife state. excess = episode return - control mean.
PRIMARY    the HIGH-SHORT x CATALYST cell: mean excess 60-session return, t on entry-week cluster means.
           BAR: t >= 3, both halves (split 2022-01) positive, positive in a majority of years with episodes.
SECONDARY  (declared) the full 2x2 (short HIGH/LOW x catalyst YES/NO) and the interaction
           [HIGH & CAT] - [LOW & NO CAT]; 4 cells -> Sidak |t| ~ 2.5 for the secondaries.
POWER      report n per cell first; if the primary cell has < 40 episodes, the verdict is UNDERPOWERED whatever the t.
PRIOR      low: each ingredient alone is null or negative; the conjunction is the whole hypothesis.
Local vs cloud: local (cached panel, SI and earnings; the vectorised gates are minutes; the validation sample calls
analyze() 200 times).

Run (when approved): PYTHONPATH=src:. .venv/bin/python3 run_quiet_knife_catalyst.py
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-27, not built/run yet. See the docstring and TEST_INDEX section 10.")
