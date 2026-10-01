#!/usr/bin/env python3
"""
TIGHT-STOP SURVIVAL AT LUK-STYLE INTRADAY PULLBACK ENTRIES, WITH A MACRO GATE
Pre-registered 2026-09-30, before any scoring. ⛔ NOT RUN -- waits for Gabe's go on where to run it (see RUN).
Creator method -> DISCOVERY track (|t| >= 3).

WHY. The goal (Gabe, 2026-09-30) is triple-digit returns in the style of Luk / Tito / Qullamaggie / Ariel. Two results
from today frame this test:
  * picks test (luk_picks_vs_controls_2026-09-30.md): his long picks held 20 sessions from the close earn +6.5% vs
    +5.1% for our same-date breakouts, t 0.92. Selection at the close does not explain his return.
  * entry cards (luk_entry_cards_2026-09-30.md): where he states them, stops are 1.0-2.5% (median 1.6%), risk 0.3% of
    the account, positions 20-30%, the book about 200% long; 88% of stated triggers are 1- to 60-minute bars; 30 of 45
    same-stream outcomes are stop-outs.
So the candidate source is POSITION SIZE BOUGHT WITH A VERY TIGHT STOP at an intraday entry. That contradicts the house
rule (stops under ~0.5 ADR are widened; resting tight stops intraday lost: entry study 2026-09-17, DINO 2026-09-22) and
Stage A (11,227 intraday alerts ~ a random later minute). What is NEW here: (1) his entry LOCATION (a pullback into the
rising EMAs, not a breakout or an alert), (2) the stop judged as a survival / payoff question in PERCENT, (3) the
account arithmetic at fixed risk, and (4) Gabe's observation that he spends long stretches with no longs at all, so
the same entry is scored inside and outside a macro gate. The "intraday version" of the Luk/Ariel pullback entry is
listed as untested in TEST_INDEX sections 9 and 10.

DATA
  intraday  s3://gmerton-stock-data/backfill/intraday_1min/bars/<SYM>/ -- Polygon 1-min, 1,715 liquid names,
            2024-10-01 -> 2026-09-24 (complete: 37,245 objects, 11.3 GB). The local watchlist cache (148 names) is NOT
            used: its names were chosen with hindsight.
  daily     data/cache/liquid_panel_2019.parquet (same universe). QQQ 1-min: data/cache/intraday_hist/QQQ_1min.parquet.
  sample    entries 2024-10-01 -> 2026-08-26, so every trade has 20 sessions of follow-up (the daily panel starts in
            2019, so the EMAs and betas need no warm-up inside the sample).
  ⚠ the universe is today's liquid list (survivor-biased), which flatters every long arm's LEVEL. Differences between
    arms on the same entries are much less affected. One tape (2024-10 -> 2026-09).

THE ENTRY (mechanical reading of principles.md: "buy pullbacks into the rising EMAs ... skip if price is > ~3% above
the LOD"; "the intraday trigger is the previous-bar-high breakout after a fast flush"; "sit out the first 15-30
minutes"; "avoid gap-ups"; leading list = price > 50 EMA, 50 > 150)
  daily state, all known at the prior close (t-1):
    price >= $5, 20-day average dollar volume >= $100M, ADR(20) >= 4%
    close > EMA50, EMA50 > EMA150, EMA21 higher than 5 sessions earlier
  day t, 5-minute bars built from the 1-minute bars, regular session only:
    no gap-up chase   open_t <= close_(t-1) + 0.5 ADR$            (ADR$ = ADR% x close_(t-1))
    pullback zone     session low so far L satisfies  EMA21_(t-1) - 0.5 ADR$ <= L <= EMA9_(t-1) + 0.25 ADR$
    trigger           between 10:00 and 15:30 ET, price trades above the high of the previous completed 5-minute bar,
                      and that bar's high is below the high of the bar before it (a step down, then the turn)
    not extended      entry <= L x 1.03, and stop distance d = (entry - stop) / entry is between 0.4% and 3.0%
    fill              max(trigger price, the open of the 1-minute bar that trades through it)
    one entry per name per day (the FIRST qualifying trigger). Re-entries after a stop-out (up to 2 more, same rules)
    are a secondary, descriptive arm: he re-enters, but the primary must not depend on it.
  STOP   L - $0.01, resting, regular session only. Entry day on 1-minute bars (a new low in the entry minute counts as
         stopped). Later days on daily bars: a gap below the stop fills at the open (as he does), else at the stop.
  EXIT   first daily close below that day's 9 EMA, on any day after the entry day; cap 20 sessions. No partial sales
         into strength and no trailing (both are discretionary in his telling; stated as a limitation).
  COSTS  10 bp per side.

ARMS (same entries throughout)
  TIGHT   the stop above.
  WIDE    stop = entry - 1.0 ADR$ (the house disaster width), same exit.
  RANDOM  same name-day, entry at a random LATER minute (after the trigger, before 15:30; 5 draws, seed 20260930) with
          the same percentage stop distance d. Later, not earlier: an earlier minute is hindsight (Stage A lesson).
  BETA    beta_i x QQQ return over the trade's exact window (entry minute to exit), beta_i = 120-session daily beta to
          QQQ at t-1. The exposure-matched control the ledger requires for anything long.

PRIMARY  TIGHT net % return per trade minus BETA, on entry-date cluster means; t.
         BAR: t >= 3, both halves (2024-10 -> 2025-09 / 2025-10 -> 2026-08) positive, a majority of quarters positive.
         Report the minimum detectable effect at 80% power first; below it the verdict is UNDERPOWERED, not NULL.
         This asks: per dollar deployed, does the tight-stopped entry beat holding its own market exposure? If it does
         not, a 200% book of these is leveraged beta, whatever the equity curve looks like.
SECONDARY (4 cells; 5 in all with the primary, Sidak 5% two-sided |t| >= 2.57; the discovery bar of 3 governs)
  S1  trigger: TIGHT minus RANDOM, % per trade (does the turn matter, or just the name-day?).
  S2  stop width at equal dollars: TIGHT minus WIDE, % per trade (what the tight stop costs or saves per dollar).
      Judged in PERCENT; R is reported but never used to rank the stops.
  S3a MACRO, mechanical: primary excess with QQQ close_(t-1) > its 21 EMA and 9 EMA > 21 EMA (ON) minus OFF.
  S3b MACRO, his actual stance: primary excess in his LONG weeks minus his SHORT/EMPTY weeks. Weeks are labelled from
      the direction and stream date of the entry / add / hold rows in his log (no prices, no outcomes; rows still open
      on the clarification worklist are used for direction and date only): LONG if long rows > short rows. Counted
      before any scoring: 37 stream weeks 2025-11-22 -> 2026-09-25, 22 LONG and 15 SHORT/EMPTY, with runs of 7 weeks
      (2026-01-24 -> 03-13) and 4 weeks (2026-08-22 -> 09-18) short. Weeks with no stream are excluded. ⚠ This label
      is his discretion in hindsight, not a rule we can trade; it asks whether standing aside is where the value is.
DESCRIPTIVE (no claim)
  survival: share stopped the same day, within 3 sessions, ever; distribution of R (share >= 5R, >= 10R); share of the
  total from the top 10% of trades; re-entry arm.
  ACCOUNT SIMULATION, labelled a simulation: risk 0.3% of equity per trade, position = min(0.3% / d, 30%), gross cap
  200%, signals taken in time order and skipped at the cap; total return and max drawdown 2024-10 -> 2026-09, for all
  days and for the mechanical gate ON only; the same book with the WIDE stop at the same risk. Ignores margin
  interest, partial sales and fast-market slippage. This is the "does the mechanical version reach triple digits"
  number; it is beta-laden and survivor-flattered, and it is not the test.

RUN  Not a small panel: 37,245 parquet chunks, 11.3 GB in S3 (0.8 s per chunk measured). Local, streamed per name with
     ~16 parallel readers and nothing persisted (32 GB of disk free), is an estimated 40-60 minutes; the alternative is
     an ECS task next to the data. Gabe decides (CLAUDE.md: decide local vs cloud before running).
"""
import sys

if __name__ == "__main__":
    sys.exit("pre-registered 2026-09-30; not run. See the docstring (RUN).")
