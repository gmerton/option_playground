# OptionsPlay — "How to Find High-Probability Trend Following Setups" (Tony Zhang, 2026-02-18, 11 min)

_Reviewed 2026-09-24. Short Growth Lab tutorial: a rule stated in two minutes, then a platform walk-through
(Technical Ideas → trend-following filter), three live bearish examples (DLTR, AVGO, ABBV) and a scale-in recipe.
No backtest, no win rate, no sample and no statistic. He calls the strategy "back battle tested" (00:23) but shows
nothing. Transcript in this folder._

## Verdict: 2 / 5

The rule is precise enough to code, which is to his credit. It is also the **pullback-then-resume family, which
our ledger has already tested on daily bars more than once**, and the tests agree: it does **not** beat the breakout
entry (row 123) or a same-name random-later control (row 97). "High probability" is asserted, not measured. On our
data this family wins **~31–37%** of the time. The one detail he adds is the "tight stop below the recent low"
for a better risk-to-reward, and that is the version that fails worst on daily closes. All three live examples are **shorts**
("given the current market conditions … bearish ideas"). Our ledger has no short-selectable single-name universe
(row 178) and the pullback-short arrival signal FAILS (row 177). Nothing new to test.

**His rule in one line:** CCI(50) > 0 defines the primary uptrend (< 0 for a downtrend). Price must first "break
out" to confirm the trend. Then wait for a pullback: a close through the **26-period EMA**. Aggressive entry = the
cross below the EMA. Conservative entry = the cross back above. Stop tight under the recent swing low. Scale in:
1% risk on the pullback, full 2% on the cross back, then +2–3% after a full bar beyond the EMA (up to ~5% notional
risk). Exit within **2–3 weeks**. Options vehicle: a 2–3-week ATM / ~1-SD debit spread (ABBV put spread, risk $551
to make $949).

## Data audit

| item | what he shows | problem |
|---|---|---|
| Evidence | Three current charts, all hand-picked, all bearish, outcome unknown at recording | No history, no sample. The one historical example (ABBV, "look how fast it moved") is chosen after the move |
| "High probability" | Asserted at 01:05 and 05:00, and in the title | No win rate given. Trend-following families have low win rates and a right-tail payoff. See below |
| "Back battle tested" | 00:23 | No backtest shown |
| Vehicle pricing | Platform's structured debit spread ($551 / $949, $2,900 / $6,000) | Priced at the mid; payoff quoted at max, no probability of reaching the short strike |
| Pitch | 04:50–05:48, 10:05 | The signal list is OptionsPlay's Technical Ideas screen. The rule itself is public (CCI + EMA), so the platform is a convenience, not an edge |

## Claims as spoken

| @ | Claim |
|---|---|
| 00:54–01:17 | Trend following has a "higher probability of success"; "quick and fast results with tight stops and strong risk-to-reward" |
| 01:31–01:43 | Good setups fire "one, two, three, four signals" within weeks on the same symbol |
| 01:57–02:27 | **Rule:** 50-period CCI for the primary trend; a pullback below the 26-day EMA; the resumption back above it is the signal |
| 03:13–03:26 | Don't buy breakouts and chase; wait for the pullback. The 26 EMA sets "how big of a healthy pullback" |
| 03:38–04:08 | "Price action is king": the trend must be confirmed by a price breakout **before** the pullback is tradeable |
| 04:10–04:31 | Aggressive entry = the cross below the EMA; conservative, "higher confidence" = the cross back above |
| 04:31–05:00 | Stop "very tightly below the recent lows" → strong risk-to-reward and "high probability of success" |
| 05:17–05:31 | Filter out illiquid option symbols first |
| 05:33 | In the current market, favour bearish signals |
| 07:49–08:25 | Vehicle: weekly or 2–3-week options, buy ATM, sell ~1 SD out (ABBV 215 put, risk 551 / make 949, "nearly 2:1") |
| 08:44–09:49 | Scale in: 1% on the first signal, the full position on the cross back over the EMA, then +2–3% after a full bar beyond it (up to ~5% total) |
| 09:52–10:01 | Exit within 2–3 weeks; "in and out" |

## Claims vs our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 01:57–03:26 | **Pullback below a mid-length EMA, then resume above it → better than buying the breakout** | ❌ **CONTRADICTED on daily bars (neighbouring parameters).** Pullback entries on leaders (`pullback_entry_study_2026-09-17.md`, row 123): the **reclaim of the 21 EMA** earns **+0.12R, t 0.8, 32% win, +1.3%/trade**; the 50-EMA reclaim +0.16R (t 0.6). The breakout pool earns **+0.55R, +2.6%** on the same panel, and the pullback is **below the breakout on every cut**. The creators' reclaim vs the pullback low (`reclaim_vs_pullback_2026-09-23.md`, row 97, 6 cells, 26k–57k pullbacks): reclaim edge vs a same-name random-later session **−0.004…+0.108R**, best raw t 2.69, **pre-2023 half negative in all 6 cells**. ⚠ Not his exact parameters: CCI(50) > 0 instead of our leader/stacked-EMA gate, and the 26 EMA instead of 21. Both are neighbours of cells that failed, so a re-run at 26/CCI would be a parameter hunt |
| 04:10 | Aggressive = buy the cross below; conservative = buy the cross back above ("higher confidence") | **Answered, and neither arm wins.** Pullback-low (A) and reclaim (B) are both ≈ their control. Same-exit win rates are equal (35.1–35.4% vs 34.4–36.5%), so the "higher confidence" entry does not win more often either (row 97). His scale-in blends A and B, and a blend of two null arms is null |
| 00:54 / 05:00 / title | **"High probability of success"** | ❌ **Contradicted as a description of the family.** Our pullback and reclaim arms win **31–37%**. The house breakout wins **30%**, and its return is the right tail (top 1% = 26% of gross, `breitstein_tests/precision_tier_control_2026-09-19.md`). Trend following is a low-win-rate, right-tail strategy. On the options side, the probability of a vertical is **priced by its strikes** (row 281), so "high probability plus 2:1 payout" on one debit spread is a claim that the market misprices it, which he never shows |
| 04:31 | **Stops "very tightly below the recent lows"** → better risk-to-reward | ❌ **The worst cell we have in this family.** Luk's ≤ 3%-above-the-low pullback: **−0.74 / −0.92R** (9 / 21 EMA), 21% / 5% winners, both halves negative (row 123). Judged on daily closes, a 2–3% stop on a 4–7% ADR name is hit by noise before the trend resumes. The same study found that pullback entries do better on a stop-only hold than on the 20-EMA trail (+3.4% vs +1.2%), since the trail sits under an entry bought at the EMA |
| 03:38 | Trade only after price has already broken out, then pulled back | ⚠ **PARKED.** Deferring entry from the breakout to a retrace beats the breakout in all 6 cells but **t 0.48** (row 16 qualifiers). Directionally his side, statistically unconfirmed |
| 01:31 | Good trends fire repeated signals on the same symbol | Descriptive (a trending name pulls back repeatedly). As a *selector*, first vs later pullback is +0.06 vs 0.00R (row 123 doc), so later signals are, if anything, worse |
| 05:33 / 05:48–08:25 | Current conditions → take the **bearish** signals (DLTR, AVGO, ABBV shorts) | ❌ **No short edge in our data.** Five short-candidate universes: **0 of 10 cells pass; 10/10 have negative excess but 0/10 a negative absolute return**, because weak names still drift up (row 178). The pullback-short arrival signal is **−1.5%/10d** and worse in a weak tape (row 177). Buying puts adds the short-dated option premium on top of that |
| 07:49–08:25 | 2–3-week ATM/1-SD debit spread, "nearly 2:1" | **Not tested as a bearish vehicle.** The long-side analogue (precision-tier breakout, 0.30/0.15 put credit spread vs stock) is NULL leaning stock, because the spread sells the right tail (row 25). A capped vertical on a strategy whose payoff *is* the tail has the same problem. No real-fill figure for his structure |
| 08:44–09:49 | Pyramid 1% → 2% → up to ~5% on confirmation | Adds scale the same edge and do not improve it (row 121, pyramid NULL). Here the base edge is itself ≈ control (rows 97, 123), so the add schedule increases risk on a zero-edge entry. 5% per trade is 2.5× the house risk unit |
| 09:52 | Exit within 2–3 weeks | Untested as a fixed time stop on this entry. For the breakout book, every fixed hold of 0–5 sessions loses to the 20-EMA trail (−0.13…−0.04R vs +0.89R, `exit_timing_study_2026-09-18.md`), and the 8-week hold is NULL (row 121). A 10–15-session cap itself was never run. It would sit between those two and truncate the right tail the family depends on |
| 05:17 | Drop illiquid option names | ✅ Agrees: liquidity is our biggest cost finding (see YfrZT notes) |

## Not tested, could be

Specs only. Nothing here is queued or run.

1. **Nothing new.** His exact parameters (CCI(50) > 0 gate, 26 EMA, both entries) are neighbours of the
   pullback-reclaim cells in rows 97 and 123, which failed their controls across 21/50-EMA and 6 pullback-depth ×
   wait cells. Running CCI/26 now would be a parameter search on a null family. **Only if someone insists:** one
   pre-registered cell via `lib.studies.pattern_test`, liquid panel 2019-10+, event = CCI(50) > 0 AND a close
   back above EMA(26) within 10 sessions of a close below it, AND a 20d-high close in the prior 40 sessions (his
   "breakout first"). Close entry, stop = 1 ADR (not his swing low, which is the failed tight-stop cell), exit =
   his 15-session time stop vs the 20-EMA trail as two exits. Controls `post` + `xname`, % per trade, bar |t| ≥ 3
   with both halves, and the Šidák charge for the rows-97/123 family. Prior: NULL.
2. The short side is closed by row 178 until a short-selectable universe exists.
