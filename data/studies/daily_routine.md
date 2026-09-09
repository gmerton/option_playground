# Daily routine — what to run, what to act on

*2026-09-08. Turns the September studies into a fixed sequence. `daily_desk.sh` runs steps 1–5 and writes to `data/watchlist/`. Every number a scanner prints is descriptive of the current tape; the validations say which parts carry expectancy.*

## Evening (15:45 ET for a live read, or after the close)

| step | command | act on | ignore |
|---|---|---|---|
| 1 Regime | `run_trailing_retro.py` | the state line (SPY trend × breadth) — it selects which row of each study's conditional table applies today | the trailing style spread and "what worked last 30 days" as forecasts (no persistence, `trailing_regime_validation.md`) |
| 2 Adhikary scan | `run_adhikary_scan.py` → `alerts_latest.csv` | **SETUP rows with `precision=YES`**: set a buy-stop at the pivot. A-block rows with `precision=YES` that broke today on a close in the upper half | B catalysts (no validated edge); the C block (daily bar is a continuation signal, never short it) |
| 2b Live alert monitor (market hours) | `./start_alerts.sh` (wraps `run_universe_monitor.py`) on `universe_focus.txt` (+ plan names) → terminal/dialog + `data/watchlist/logs/universe_alerts_<date>.log` | **UR** = flush (≥0.25 ADR from max(open, prev close)) that undercuts the prior-day low or tags/opens below the 9/21 EMA, then a 1-min close back above VWAP → stop = session low. **ORB9** = opened and held the daily 9 EMA + VWAP, 5-min close above the 15-min opening-range high before noon → stop = OR low / bar low. **BIR** (short) = name below its 9/21 EMA bounces ≥0.4 ADR into a level above (9/21/50 EMA, 50/200 SMA, PDH), first 5-min close below the prior 5-min low → stop above the bounce high. **FBO** (short, every name) = a 5-min close above the prior-day high or 15-min OR high, then a 5-min close back below it and VWAP within 90 min of the high → stop above the failed high; on a long-universe name it is also the exit tell. Short universe = `universe_short.txt` + long-list names below their 9/21 EMA. Read the tags before acting: `still below 9 EMA`, `light vol`, `GAP ≥1 ADR`, `stop in noise` (<0.4 ADR), `SPY vs VWAP` and the ADR-vs-21-EMA number are the lens gates; `--index-gate` mutes longs under / shorts over the index VWAP | Alerts are pattern hits, not entries: on 9/8 the same UR fired on SPCX/TXG/TGTX (worked) and OKTA/RVMD/ILMN/MSFT (failed). Replay any day with `--replay YYYY-MM-DD SYMS` |
| 5b Process report card | `run_journal_grades.py` → `data/studies/journal_process_grades.md` (+ csv) | Read the GRADE, not the P&L: entry quality (share of discretionary entries reviewed good), stock same-day round trips, fills, too-soon exits, vehicle doubling. A = the rules held; D = they did not. First thing on the desk next morning | Aug-Sep 2026: 20 of 26 sessions graded D; the score has ~zero correlation with day P&L (P&L is the option book + beta), which is the point: the grade is the signal, the P&L is noise |
| 3 House breakout scan | `run_preferred_breakouts.py` | POTENT names within 3% of pivot that are ≤1 ADR above the 21 EMA | anything >2 ADR above the 21 EMA or gapping >3% (the August loss bands) |
| 4 Straddles (Fri) | `run_straddle_fvr_scan.py --universe …pool_323.txt` then `run_straddle_iv_gate.py --from-scan` | names passing FVR ≥1.20 **and** IV percentile ≤30 **and** worst bid-ask ≤25% / OI ≥50 | full-size FVR ≥1.40 prints on thin chains (AMLP/ANVS-type artifacts) |
| 5 Journal | pending notes list | add same-day notes for every trade (`add_pending_note`) so the Flex pull can grade them | — |

## Entry rules that survived the studies (apply to every long)

1. **Location:** within 1 ADR of the 21 EMA. The 1–2 ADR band lost −$4.6k in August; >2 ADR is a chase.
2. **No gap-up buys** (≥3% gap, first hour). No buying below falling EMAs (the laggard-bounce class, −$3.8k).
3. **Trigger, not anticipation:** a reclaim (VWAP, 9/21 EMA, pivot) with the reclaim bar's low as the stop. For laggards, wait for the 50-day to be reclaimed and back-tested.
4. **Stop ≤2% or size down to it.** 82 losers past 2% cost $13k in August. Size = risk ÷ stop distance; never widen.
5. **No same-day exits unless the stop is hit.** Same-day round trips: 132 trades, −$7.9k.
6. **Vehicle follows entry quality:** clean pullback + IV <60% → stock (or ITM 45+ DTE call); extended/uncertain or IV >60% → 30/15-delta put spread; never a 9%-OTM 3-week call held a day.
7. **Exits:** grind → first daily close below the 20 EMA; spike (option 3× in days) → sell into strength / GTC target at +200–300%.

## Monthly

- `run_trade_lens.py --start --end --out …` — score the month against the Luk/Tito rules; compare to August (`august_2026_luk_tito_lens.md`).
- `run_build_liquid_panel.py` — refresh the long-history panel, then re-run `run_regime_validation.py` and `run_adhikary_validation.py` so the conditional tables include the newest regime.
- Re-read the conditional row for today's state before trusting any pooled number (feedback: weight current conditions).

## Open builds, in priority order

1. Intraday 620 / VWAP-reclaim logging in `ibkr_bot/fade_watch.py` (Ariel's trigger; the only untested entry layer).
2. Intraday C-archetype (0DTE fade) test — needs minute data; the daily proxy is refuted.
3. Options-vehicle overlay on the precision tier (his 0.2–0.35Δ ≥15 DTE rule) with sell-the-spike, on real prints.
4. Score Ariel's nightly calls (`data/ariel_hernandez/analysis/`) — hit rate accrues per video.
