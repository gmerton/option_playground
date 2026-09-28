#!/usr/bin/env python3
"""
MARTIN LUK'S ACTUAL PICKS vs OUR SELECTION: does his discretion carry information our filters don't? (pre-registered
2026-09-27, before any scoring; Gabe: "yes, pre-register both". ⛔ NOT RUN -- waits for Gabe's clarification pass on
data/martin_luk/trades/clarify_worklist.csv. Queued in TEST_INDEX section 10.)

WHY. Gabe: "how can we be as successful as Luk, Tito and Ariel -- what are we missing?" Every mechanical rule we
coded from these traders failed or was marginal; the parts that survive (selection of leaders, buying strength,
letting winners run) are already the book. The open question is whether their DISCRETIONARY selection contains
information the panel can't see (theme, catalyst quality, fundamentals, young stocks). Scoring the picks he actually
disclosed answers it directly. (His trades are admissible here: they are the object of study, not Gabe's own record.)

DATA   data/martin_luk/trades/observed_trades.jsonl (504 rows from his livestreams, 2025-11 -> 2026-09) with Gabe's
       fixes from clarify_worklist.csv applied: ticker_fixed / direction_fixed / fill_date_fixed override;
       keep_or_drop = drop removes the row. ⚠ CLARIFICATION RULE (declared now): resolve from what he says or shows
       on screen only, never from charts or memory of what moved; unresolved "?" tickers and non-day fill dates
       are DROPPED, not guessed.
PICKS  action in {entry, buy, short, reentry}; adds, trims, holds, watches excluded (not independent picks). One pick
       per (ticker, direction, fill date). Direction long / short as logged.
ENTRY  the CLOSE of the fill date (the house entry; this scores his SELECTION, not his intraday execution).
       Prices: liquid_panel_2019 refreshed first; names outside it (ETFs, young listings) from yfinance, adjusted.
RETURN signed by direction, 20 sessions (PRIMARY) and 5 sessions, net 10 bp/side; a name without 20 later sessions
       (delisted) exits at its last close.
CONTROLS (declared now)
  C2  OUR SELECTION: every precision-tier breakout (run_precision_tier_control.build()) on the same date, held the
      same way; if none that date, those of the same calendar week. <- the key comparison
  C1  MARKET: same-date eligible names (ADDV >= $50M, px >= $5) in the same ADR tercile (holds volatility fixed).
  C3  TIMING: the same name on a random session 20-120 sessions later (5 draws; seed 20260927) -- is it the name or
      the moment he picked?
PRIMARY  LONG picks, 20-session return minus the same-date C2 mean, t on fill-date cluster means.
         BAR: t >= 3 and both halves (split at the median fill date) positive. Report the minimum detectable effect at
         80% power FIRST; if the observed |excess| is below it, the verdict is UNDERPOWERED, not NULL.
SECONDARY (declared) longs vs C1 and vs C3; SHORT picks vs C1 (short excess = control return - pick return); all at
         5 sessions too. 5 secondary cells -> Sidak |t| ~ 2.6.
THEN (only if the primary passes or longs beat C2 at t >= 2): compare the FEATURES of his long picks with same-date
         precision-tier picks -- ADR, distance from the 52-week high, stack days, days since IPO, sector/theme, float,
         earnings within 10 days -- to name what his selection sees that ours doesn't.
⚠ One regime (2025-11 -> 2026-09, a strong tape for leaders) and ~130 long picks: power is modest by construction.
Local.

Run (when the worklist is done): PYTHONPATH=src:. .venv/bin/python3 run_luk_picks_vs_controls.py
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-27; waits for data/martin_luk/trades/clarify_worklist.csv. See the docstring.")
