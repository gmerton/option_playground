# Trailing-window regime rules — validation 2019–2026

*2026-09-05. Follow-up to `august_2026_retrospective.md`. Question: can the machinery be updated so that a replay of August would have gone better, WITHOUT fitting to one month? Method: encode the August lessons as rolling rules on the trailing 21 sessions, then test them on 2019-01 → 2026-09 (yfinance adjusted panel of the 1,765 names liquid on 2026-07-31, eligibility applied point-in-time: trailing-50 ADDV ≥ $30M, price ≥ $5; ~1,030 eligible names/day). Code: `src/lib/regime/trailing.py`, `run_trailing_retro.py`, `run_regime_validation.py`. Rebuild the panel with the scratchpad `pull_panel.py` pattern (yfinance `download`, 100-ticker chunks, ~2 min).*

**Survivorship caveat:** the universe is today's liquid names, so laggard bounces are flattered (the laggards that died are absent). Absolute levels are optimistic; the relative comparisons below are the evidence, and note that laggard breakouts lose even with the bias in their favour.

## Verdict

None of the three August "implications" survive. The August pattern was real but was not forecastable from the trailing 30 days.

| August lesson, encoded as a rule | 2019–2026 result | Keep? |
|---|---|---|
| Trailing laggard-minus-leader spread > +3pp ⇒ "laggard-turn regime", expect it to continue | corr(trailing spread, next-21 spread) = **−0.11**, sign agreement 48%. Every band (2/3/5pp) and every year: next-spread mean ≈ 0 or negative | No. Style does not persist month to month |
| Laggard breakout (≥30% off 52-wk high, close > 50d high on ≥1.5× vol) as a candidate source | 10-session excess **−1.35pp** (win 46%), 21-session −2.08pp; negative in 7 of 8 years. Leader breakouts +0.1 to +0.3pp | No. Confirms the Part II vetoes (below 200-day, 6mo < −10%) |
| Breadth gate: only take pullback / U&R entries when the 10-day advancer average ≥ 50% | ON vs OFF excess: pullback +0.07 vs +0.24, U&R-20d −0.02 vs +0.15, U&R-50 −0.06 vs +0.14. OFF is slightly better; by-year signs flip | No |
| "Stop initiating longs when adv10 < 50%" (the 8/18 call) | adv10 < 50% ⇒ next-21 median stock **+1.57%** (P>0 67%, t 2.29) vs +0.47% when ≥ 50%. Holds in 7 of 8 years incl. 2022 (+0.87 vs −1.78). Ex-2020 t 1.54 | Inverted. Weak breadth has been a mild buy, not a sell |
| Trailing setup scoreboard ("what worked last 30 days keeps working") | trailing-21 excess vs next-21 excess of the same setup: corr between −0.17 and +0.19 for every setup, sign agreement 42–63% | Descriptive only |

Other things checked while there:
- Thrust days (two straight 70%+ advancer sessions): next-21 median stock −0.24% (n=109). Not a buy signal on its own.
- NH−NL (10-day sum) < 0 ⇒ next-21 median stock +2.62% vs +0.50% when > 0; same mean-reversion story, same weak t.
- Extension at entry: house-rule breakouts more than 25% above the 50-day had the BEST 10-session excess (+0.75pp); pullbacks to the 20 EMA on names 15–25% above the 50-day +1.06pp. No basis for an extension veto.
- EP-gap chasing (+10% on ≥3× vol, buy the close): excess +0.20 / −0.21pp by breadth state. No edge either way over seven years; August's −2.3% was noise around zero.

## What is actually left for a better August

1. **The August damage was selection and frequency, not a missing regime rule.** The house-rule leader breakout was flat in August and is slightly positive over seven years. The book's own August (journal summary 9/4) was ~430 trades at a 21% long-stock win rate, concentrated in semis, quantum and crypto entered on gap days. Nothing in this validation would have changed that except taking fewer, rule-qualified trades.
2. **Keep the existing vetoes**, which this data independently confirms: no breakouts below the 200-day or with a negative six-month return (the laggard cohort), and no chasing +10% gap days.
3. **The trailing tool stays as a post-mortem dashboard.** `run_trailing_retro.py --asof DATE` reproduces the August study for any window using only data available on that date, and prints the non-persistence numbers under its own output so it cannot be over-read.
4. **One candidate signal, opposite in sign to the August lesson:** weak breadth (10-day advancer average under 50%) has preceded above-average 21-session broad returns in seven of eight years. It is a mean-reversion signal with t ≈ 1.5 ex-2020, not yet an edge. If anything is built next it is this, tested on a longer, non-survivor panel first.

## What August tells you in hindsight vs in real time

| Date | Trailing read (ex-ante) | What followed |
|---|---|---|
| 8/4 | breadth ON, style LAGGARD-TURN (+3pp) | laggards did lead for 21 days; next-21 median stock −2.8% |
| 8/18 | breadth OFF, LAGGARD-TURN (+8pp) | broad tape fell to 8/31, then flat |
| 9/4 | breadth OFF, NEUTRAL (+1pp) | open |

The reads were "right" in August, which is exactly why a one-month validation is dangerous: across 2019–2026 the same reads have no forecasting power.
