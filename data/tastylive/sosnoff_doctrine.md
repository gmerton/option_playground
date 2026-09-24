# Tom Sosnoff's doctrine: the reference rule set, scored against our ledger

_Compiled 2026-09-23 for Gabe's question: *understand Tom Sosnoff's strategies* ("he doesn't look at charts, he
focuses on volatility and selling volatility")._

## Sources merged

| source | what it contributes | score |
|---|---|---|
| `data/more_tom/` (26 podcast clips, 2026-09) | philosophy, psychology, risk budget; no numbers | 2.5/5 |
| `data/optionsplay/2024-10-14_sosnoff_interview_review.md` (60-min webinar) | **the full executable rule set** + one live trade; no numbers | 3/5 |
| `videos/research/2025-07-01_9vwnX5mTT9M` "Won't trade stock" | options-vs-stock framing, vol-regime sizing, stops | 2/5, probably Sosnoff |
| `videos/research/2024-01-07_eUTCEbx2pco` "Daily routine" | what he ignores / watches (futures, vol curve) | 1.5/5, Sosnoff |
| `videos/research/2023-09-08_C6vrj2zu6Hc` "Dark side of the iron condor" | wing-width house rule + a real width study | 3/5, ⚠ **Sosnoff NOT present** (house doctrine) |
| `videos/research/2024-01-27_p_X8dyNXlUE` "0DTE verticals" | **his actual 0DTE structure** + a 0DTE study | 2/5, Sosnoff |

**Tags.** **AGREES**: our data supports it. **CONTRADICTED**: our data says otherwise. **PARTIAL**: right in one
form or arena, wrong in another. **UNTESTED**: no evidence either way (says why).

⚠ Every AGREES below agrees on **direction**, never on **return**. In ~30 videos and hours of airtime, there is not
one sample size, fill convention, cost line or test statistic attached to any rule of his. The rules are
hypotheses. Our tags come from our data, not his.

---

## The doctrine in one paragraph

Don't forecast price. Trade **implied volatility**:
- Sell premium, mostly as **~45-DTE, ~20Δ (≈1 SD) short strangles**. About 75% of his book is undefined risk;
  the defined 25% is iron condors and verticals.
- Trade only **liquid** underlyings, **with high IV rank**. Skip vol products and biotechs.
- Keep each position **small** and spread across **70–80 names plus 10–12 futures products**.
- **Take profits early** (50% of max; 25% for straddles and 0DTE). **Manage everything at 21 DTE** regardless of
  P&L.
- Never roll a loser out and wider. When wrong, sell the opposite side "to reduce basis".
- Don't buy premium and don't hedge much. Size is the tail defence.
- Watch futures, not ETFs. Ignore news, analysts and charts.
- On 0DTE, sell the ATM straddle with wings at the expected move.
- He trades ~100 times a day and calls the scalping a hobby.

**What our data says his book is.** One piece of it is the single certified short-premium result we have. That's
**selling index put risk after a selloff when implied vol is high** (SPY bull put t 6.07 + SPX condor t 5.21, one
bet). The generic, always-on version of the same rules loses on single names after real fills:
- 45/20Δ strangles across 44 liquid names are negative in both exit arms;
- 10-DTE selling costs 136% of gross.

His philosophy of what *not* to trust (charts, news, forecasts, intraday triggers) is the part our equity ledger
independently confirms.

---

## A. What he looks at, and what he ignores

| # | rule | source | verdict | one-line evidence |
|---|---|---|---|---|
| 1 | **No charts; no price forecast.** "Charts mean absolutely nothing" | More Tom `GlyqfnRNeSo`; eUTCEbx2pco 07:03 | **AGREES** | Our own book, against its interest: house breakout +0.014R; within-date ranking NULL (t −0.11, 71/72 cells fail); 9 chart features can't call a 1.647R spread; `sma_stacked` INVERTS |
| 2 | "There is no statistical edge for retail, ever" | More Tom `GlyqfnRNeSo` | **CONTRADICTED** | Falsified by his own trade type: SPY bearish-high-IV bull put t 6.07; 10d VRP +1.75vp, t 8.93, 17/17 yrs. "Charts don't forecast" and "no edge" are independent claims, and our data separates them |
| 3 | Ignore news, analysts, other people's opinions; "market awareness" doesn't improve decisions ("so much is random"); it is engagement | eUTCEbx2pco 00:28–02:48; More Tom #8 | **AGREES** | FOMC/macro = noise (catalyst studies); Stage A: 11,227 intraday alerts ≈ a random later minute |
| 4 | **IV level selects the trade: sell when IV (rank) is high; reduce risk when IV is low** | 9vwnX5mTT9M 05:16; More Tom `s9JYik5DV7k`, `7oqOCrL7TJk`; OptionsPlay | **PARTIAL** | Yes at index level after stress (the certified cell); put credit at low IVR −$62 (t −2.14); QQQ bullish-low-IV −4.8% (t −0.87); paid-to-wait IV≥60th pct +5.7% net vs −3.3% ungated (not certified). No as a cross-sectional sort (zivr −1.89pp, t −1.25) or vehicle chooser (t 0.68); own-IV ≥80th pct is a mild veto on QQQ/IWM bull puts |
| 5 | Skew extremes are a signal | More Tom `7oqOCrL7TJk` | **CONTRADICTED** | SPY 25Δ skew Q5−Q1 +1.72%/21d, t 1.44; adds nothing beyond VIX (t −1.22 vs vix_pct t 6.54). His *history* of skew ("velocity of risk", post-1987) is right |
| 6 | **Liquidity first**: only highly liquid underlyings; exclude vol products and biotechs | More Tom `pZm-y3oxzIQ`; OptionsPlay | **AGREES** ⭐ | 10-DTE single-name selling: costs = 136% of gross, "liquidity is the gate"; UVXY/UVIX/ASHR/SQQQ/TMF/XOP retired net-negative after costs |
| 7 | Open interest is not a signal (only a tradability check) | More Tom `7oqOCrL7TJk` | **AGREES** | We use OI + bid/ask% as a universe gate, never a signal |
| 8 | **Watch futures, not ETFs** (/ES /GC /ZB /CL, "the first dollar goes there"); trade futures options with the identical rule | eUTCEbx2pco 04:38; OptionsPlay | **UNTESTED** | We have no futures-option data. At index level SPY vs SPX gave the *same* certified bucket. Do not transfer the single-name null onto his futures book |
| 9 | Watch the vol curve (contango/backwardation) | eUTCEbx2pco 04:22 | **UNTESTED** (adjacent negative) | VRP panel: term structure absent, FVR doesn't sort the premium; FVR does gate the *long* straddle |
| 10 | Guess market extremes; contrarian ("bearish because everyone's bullish"); "no such thing as a trend"; don't buy at all-time highs | eUTCEbx2pco 03:17, 04:09; More Tom #5, #12 | **PARTIAL** | CONTRADICTED on single names and timing: reversion 0 for 5 (bouncy ball, capitulation, exhaustion fade, counter-trend); FTD/regime timing NULL 5×; shorts 0 of 10 universes. AGREES at index level via volatility: the certified bucket *is* "sell fear after a selloff". The long form says he's delta-neutral, not a trend-fader |

## B. Structure and strikes

| # | rule | source | verdict | one-line evidence |
|---|---|---|---|---|
| 11 | **Core trade: ~45-DTE short strangle at ~20Δ (just outside the expected move)**, slight skew for a lean; 75% undefined / 25% defined | OptionsPlay; Freedom Income (ES 10Δ put variant) | **CONTRADICTED on single names · UNTESTED on futures** | 7,265 strangles / 44 liquid names / 2018–26, real fills: **hold −2.55, 21-DTE −1.02 per share, both negative**, medians ≈ 0 (verified at `data/studies/exit_21dte_2026-09-23.csv`). 30d VRP +0.78vp, t 2.08: absent at his tenor. The index version certifies **only in the bearish-high-IV regime** (SPX condor t 5.21) |
| 12 | IV exceeds realised: "realised is higher only ~15% of the time", and that's why you sell | More Tom `wR5M8Z6qhcI` | **PARTIAL** | Right sign; realised beats implied **25% (10d) / 29% (30d, 90d)**, not 15%; the premium is significant only at 10d |
| 13 | ~1 SD strikes, not 2 SD ("too cheap"); **sell near-the-money premium**: "eat like a bird, poop like an elephant"; "I like to sell the $6 call" | More Tom `s9JYik5DV7k`; p_X8dyNXlUE 08:18–08:35 | **AGREES** (1-day) / UNTESTED (45-DTE sweep) | SPY 1-day, positive gamma: **2× fly +5.8% vs 16/5Δ condor +1.8% vs 16/5Δ put spread +1.9%**, "the edge is AT the money". Credit/width top quintile +6.52% net (t 2.40) |
| 14 | Probability of profit is a dial, **not an edge** ("right 80% of the time doesn't mean you make money") | 9vwnX5mTT9M 05:38; OptionsPlay | **AGREES** | Across credit/width quintiles win rate *falls* 79.6→75.7 while net ROC *rises* −2.96→+4.07 (t 3.74) |
| 15 | Structures are "symmetrically perfect": no edge difference between a tight condor and a wide strangle | OptionsPlay 54:44–57:23 | **PARTIAL** | Across names, wrong: credit/width sorts ROC +8.57pp (t 3.74; within-date +7.64pp, t 4.15). Within a name, roughly right, **except the narrowest wing** (rule 16) |
| 16 | **Wide wings, fewer contracts**: for equal buying power one 20-wide beats twenty 1-wides; **$5 minimum width** on $100–500 names | C6vrj2zu6Hc 08:13–15:47 (house, not Tom) | **AGREES** (exploratory) ⭐ new | Recut of `premium_to_width_2026-09-22.csv`, same name and date: narrowest wing (0.25Δ long on a 0.30Δ short, ~$3) **−0.04% net ROC, P(max loss) 18%** vs 0.20Δ/0.15Δ/0.10Δ +2.66/+3.10/+2.98%; paired +2.9…+3.4pp, **month-t 4.5–11.7, both halves**. Flat past 0.20Δ (t 0.83). Not pre-registered |
| 17 | Options beat stock because they're "strategic": you choose the skew, tail, width and mean | 9vwnX5mTT9M 02:18, 08:01 | **CONTRADICTED** (on the mean) | Put credit 30/20Δ vs delta-matched stock +$7 (t 0.26); BCI CSP = stock minus costs; unstopped stock beats the CSP +0.49 vs +0.36 with a smaller tail (−16.9 vs −41.0, exploratory) |
| 18 | **0DTE: sell the SPX ATM straddle, wings at the expected move**, near the open; 25% take | p_X8dyNXlUE 02:56–03:32 | **CONTRADICTED unfiltered · AGREES gamma-filtered at 2×** ⭐ new | SPY 1-day fly, real fills: **1× wings +6.8% (t 2.0, FAIL) on positive gamma, −12.0% (t −3.7) on negative**; 2× wings 0.0% every day, **+5.8% (t 3.4, 14/17 yrs) on positive gamma only**; WiFly 1.34× unfiltered −3.79%. The gamma filter he never mentions is the whole edge. (Ours enters at the prior close, his at the open) |
| 19 | 0DTE is "45 DTE, just faster"; at all-time highs the 0DTE tail is upside | p_X8dyNXlUE 10:09–11:00 | **PARTIAL / UNTESTED** | Short tenor is where the premium lives (10d t 8.93 vs 30d t 2.08), not just faster; 1-day sign flips with dealer gamma (+5.8% vs −5.4%). The upside-tail claim is a 10-month-sample statement; 1-day call spreads untested |
| 20 | No premium buying ("haven't bought premium in 26 years"), except wings | More Tom `1itwTWKGVyM` | **CONTRADICTED** | Our other surviving leg is a **long** 7-DTE straddle (SUPPORTED, t 3.7) gated on **low** own-IV (≤20th pct mid +9.19 vs +5.05 ungated), the inverse of his rule |

## C. Management

| # | rule | source | verdict | one-line evidence |
|---|---|---|---|---|
| 21 | **Manage at 21 DTE**, regardless of P&L (roll or close) | OptionsPlay; C6vrj2zu6Hc 18:28 | **AGREES on risk, not return** ⭐ | First exit rule to certify: paired **+$1.53/strangle, t 4.26**, halves +1.07/+2.17, sd halved, worst −$617 → −$259, but **both arms negative**. It removes gamma, not losers |
| 22 | Take profits early: 50% of max (25% for straddles / 0DTE) | C6vrj2zu6Hc 16:04; p_X8dyNXlUE 04:44 | **UNTESTED** (in isolation) | The 50%-take arm of the queued 21-DTE design was never run; ungated SPY 45-DTE 50%-take put spread only t 1.2 monthly (Freedom Income row) |
| 23 | **Never roll a loser out and wider** ("a $3 spread became a $9 spread") | More Tom `qo9466KD_u8` | **AGREES** | Roll test: the stop is a cost (−9.51pp on the breach cohort, 69.8% better held); re-entry NULL (t 1.55) |
| 24 | Instead, sell the opposite-side spread "to reduce basis" | More Tom `qo9466KD_u8`, `FZfndYs_nXc` | **UNTESTED** (negative prior) | Every call-side premium result is negative: ETF condor call side t 0.6, UVXY bear call −7.4% (t −3.65), UVIX −8.8%. It's a margin argument, not an edge argument |
| 25 | Stops aren't risk reduction, and "reducing size isn't necessarily" either; the tail defence is size (+ 21 DTE) | 9vwnX5mTT9M 04:01 vs More Tom `LJl1N4VuJnQ` | **PARTIAL**: he contradicts himself | Stops on short premium are a cost (straddle −50% stop INVERTED). On stock, a resting 0.5-ADR stop is cheap crash insurance (~0.37pp). Size is the only non-inverted lever, and it works as *exclusion* (+0.29R OOS) |

## D. Portfolio, sizing, costs

| # | rule | source | verdict | one-line evidence |
|---|---|---|---|---|
| 26 | **Trade small, trade often** (law of large numbers); 0.5–5% of BP per trade; 70–80 names | More Tom `FNrpK9OWnNc`; OptionsPlay; p_X8dyNXlUE 00:57 | **PARTIAL** | Repetition only helps a positive expectancy; 3,377 bull puts = 53 independent dates; same-date positions are not independent bets |
| 27 | Portfolio theta 0.1–0.2% of net liq; deploy more when VIX is high | More Tom `Co1-RL9AKp8`, `FNrpK9OWnNc` | **PARTIAL** | Vol-scaling AGREES (rule 4). A standing theta *budget* has nowhere to go: 1 certified bucket, 0 of 13 screener spreads certify |
| 28 | Diversify by product **and** strategy; under-hedge | More Tom `FZfndYs_nXc`, `cULgbk0e0-o` | **AGREES** (qualitative) | Straddle + bull put PAIR corr −0.25, blend t 2.5 (not certified); tail overlay NULL / negative carry (5Δ same-expiry −100% every trade). His "30% risk reduction" has no source |
| 29 | Costs are negligible on liquid options ("a penny or two") | OptionsPlay | **CONTRADICTED** | Measured straddle spreads median **6.5% of mid**; the 2026-09-22 cost sweep killed 9 strategies; UVIX bear call +11.0% gross → −8.8% net. And twenty narrow condors pay 20× the commissions of one wide one (rule 16) |
| 30 | 30/30/40 trading / long-term / cash at today's rates | More Tom `YF9BKb-aCOU` | **UNTESTED** (allocation, not a trade) | — |

---

## Scorecard

| tag | rules |
|---|---|
| AGREES | 1, 3, 6, 7, 13, 14, 16, 21 (risk only), 23, 28 |
| PARTIAL | 4, 10, 12, 15, 19, 25, 26, 27 |
| CONTRADICTED | 2, 5, 11 (single names), 17, 18 (unfiltered), 20, 29 |
| UNTESTED | 8, 9, 22, 24, 30 (+ 11 on futures) |

**Where he is right**, he's right about **what not to trust**: charts, forecasts, news, POP, rolling losers,
illiquid chains. And about **two mechanics**: the 21-DTE gamma truncation, and near-the-money over penny premium.

**Where he is wrong**, it's about **the return of the trade itself**. Always-on 45/20Δ strangles and unfiltered
1×-EM 0DTE flies lose at real fills. The part of his book that pays is conditional:
- index put risk sold after a selloff (the certified bucket);
- the 1-day fly only on positive-dealer-gamma days at 2× wings.

Neither condition is in his rule set.

**The biggest open question** is his futures book (crude / gold / bonds strangles). The liquidity objection that
sinks our single-name selling doesn't apply there, and we have no data. That's the one arena where "his doctrine
fails" would be an unsupported statement.

---

## Verification notes and errata found while compiling

- ⚠ **Attribution:** `C6vrj2zu6Hc` does not feature Sosnoff ("you're sitting on Tom's chair" / "No, I'm in Bat's
  chair", 11:45). `data/tastylive/index/README.md` counts it among "the 4 titles that are Sosnoff himself". Only 3
  are, and `9vwnX5mTT9M` is probable rather than confirmed (no self-identification in the captions).
- ⚠ **TEST_INDEX row inconsistency:** the Freedom Income row quotes the 21-DTE arms as "−$0.46 vs −$1.77". The
  primary CSV reproduces the §1 row instead: hold −2.547, 21-DTE −1.016, diff +1.531, n 6,558 resolved of 7,265.
  The §1 row is correct. ⚠ The $ means are price-weighted: pre-split AMZN supplies the 5 worst trades. The result
  survives without AMZN (−2.32 / −0.82) and in ROC terms (−134% vs −60% of credit, mean). Medians are ≈ 0 (hold
  −0.10, 21-DTE +0.12 per share).
- ⚠ **Doc error:** `data/optionsplay/videos/2026-07-25_YfrZT_kTo_4/notes.md` lists ARM B's ROC series against the
  wings in reverse order. The CSV maps **0.10Δ → +2.98, 0.15Δ → +3.10, 0.20Δ → +2.66, 0.25Δ → −0.04**, so the
  narrowest wing is the loser. That changes "dialling your own width buys nothing" to **"anything but the
  narrowest wing"** (rule 16).

## Test candidates (not queued, pending Gabe)

1. **Wing-width confirmation on the in-book index bull put.** Pre-registered narrowest-vs-0.20Δ, ~1 h on
   `run_premium_to_width.py`. Prior: replicates, because it's friction.
2. **50%-take arm on the existing 21-DTE strangle harness.** Rule 22 is his most-repeated untested rule. It's
   cheap because the path-coverage guard exists.
3. **VIX term structure as a gate inside the certified bucket.** ⚠ Best-of-k on the one certified cell, with a
   handful of episodes, so it's probably UNDERPOWERED.
