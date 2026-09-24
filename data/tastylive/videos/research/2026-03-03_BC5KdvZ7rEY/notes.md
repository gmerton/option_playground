# tastylive / Market Measures: "We Tested Strangles Across Sectors, Here's What Wins More" (2026-03-03, 9 min)

_Reviewed 2026-09-23. A live-show segment: the research slides are read in between market chatter (oil up 6%, ES
stair-stepping down). The transcript (`en-orig` auto) is in this folder. Only success rates are read out._

## Verdict: 1.5 / 5

The only metric is **success rate**: the share of 16Δ / 30Δ strangles that expire inside their strikes. It's compared
with the theoretical 68% / 58%. Beating that rate is a restatement of "implied vol usually exceeds realised". Our VRP panel
agrees on that point and measures its size.

But **a success rate isn't a P&L.** The video shows no P&L, no losses, no costs and no period, and the one analytical
slide finds **no relation between success and premium level or IV**. Our own strangle panel looked like it answered
the P&L question for these ETFs (all negative at real fills), **but it turned out, verified here, to drop the both-legs-worthless
winners**, so on P&L we're open too. The title's "what wins more" is literally true and says nothing about returns.

## Data audit

| item | what the video gives |
|---|---|
| Underlyings | 5 sector ETFs (XLE, XLK, XLF, XLV, XLU) + the **top 5 holdings of each** (current holdings, e.g. XOM, NVDA, BRK.B, UNH, NEE). **Survivorship: today's top holdings, applied backwards** |
| Period | **not stated** |
| Structure | 16Δ and 30Δ short strangles, 45 DTE |
| Management | not stated. "Success" reads as expire-inside-the-strikes, i.e. **held to expiry** |
| n | not stated |
| Metric | success rate only, vs theoretical 68% (16Δ) and 58% (30Δ) |
| Fills / costs | irrelevant to a success rate, which is exactly the problem |
| Compared to | the theoretical probability, SPY, and ETFs vs their holdings |
| Mean / tail | **none shown** |
| Significance | none |
| Selection | current top holdings = survivors. UNH is in the basket, and its 2025 collapse is the kind of tail a success rate hides |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 02:20–02:23 | Average pairwise correlation of the top-5 holdings basket: **0.29** |
| 03:07–03:10 | Theoretical success for a 1-SD (16Δ) strangle: **68%** |
| 03:36–03:39 | Observed 16Δ success: **72% technology (XLK), 77% energy (XLE)**, "etc." (others ≥ 68%) |
| 03:31–03:34 | Every sector ETF hit 68% "if not more" |
| 05:31–05:36 | 30Δ strangle: every success rate above the expected **58%** ("about a 60% probability") |
| 07:13–07:17 | Technology ETFs had "slightly lower success rates than other sectors" |
| 07:40–07:44 | **No strong relationship** between success rate and IV or premium level (premium ÷ underlying) |
| 08:24–08:30 | Sector ETF success rates slightly above SPY's |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 00:38–00:50, 03:13–03:20 | Success rates beat theoretical everywhere because "implied volatility is overstated" | ✅ **Agrees on direction, and we have the size.** VRP panel (10 ETFs incl. XLE / XLF / XLV / XLU / XLP, 2010–2026): the **10d** premium is +1.75vp (t_NW 8.93), all 10 tickers clear, 17/17 years. XLF +2.52 (t 4.50), XLE +2.00 (5.01), XLV +1.79 (6.62), XLU +1.54 (4.09). IV > RV on **~70% of days**, which is their "above theoretical" in another form. ⚠ **But at 30d, the tenor nearest their 45 DTE, the premium is +0.78vp pooled and t 2.08, which doesn't clear.** By ticker: XLE +0.61 (t 0.93), XLU +0.39 (0.73), XLF +1.22 (1.95), XLV +0.87 (2.10). The frequency is robust; the magnitude at their tenor isn't |
| 03:42–03:56 | Individual names are "a little more volatile" but in line with their ETFs | **Success rate, maybe. P&L: single names are worse.** Short-dated single-name selling is net negative (10 DTE: costs = 136% of gross), and liquidity is the gate (tradeable set = SPY + NVDA/AMZN/AAPL/V). The 45-DTE per-name strangle numbers in our 21-DTE CSV (NVDA −$12.46, META −10.95 held…) are **not citable**: that sample drops the both-worthless winners (caveat below) |
| 04:44–05:07 | Ramp up size when vol is high; use the ETF rather than the stock to "get smaller" | **First half agrees** with the VIX-gated certified bucket. **Second half agrees** with our liquidity gate and with Sosnoff's own exclusions |
| 07:13–07:22 | Tech has the lowest success rate | Plausible: tech had the most drift through the short call. Our per-ETF strangle numbers (XLK, SOXX) come from the winner-depleted sample, so no P&L comparison is citable |
| 07:40–08:10 | No relation between success and IV / premium level: "you just look at IV" | ⚠ **They measured the wrong outcome.** Success rate *shouldn't* move with premium level. Delta-matched strikes set the probability by construction. The question is whether **P&L per unit of risk** rises with premium, and **on our data it does, across names**: premium-to-width quintiles −2.96% → +4.07% net ROC, top−bottom **+8.57pp t 3.74**, within-date +7.64pp t 4.15, *while the win rate falls* 79.6 → 75.7. Their null on success rate is what you'd expect, and it tells you nothing about selection |
| 08:13–08:21 | Takeaway: success rates higher than theoretical ⇒ "implied volatility is typically overstated to realized" | ✅ as a frequency statement. ⚠ As a trading claim it's **unproven by them and open on our side.** The 30d VRP magnitude doesn't clear on these ETFs (above), and our strangle P&L panel is invalid on the hold arm (caveat below) |

### Settlement caveat on our strangle panel (applies to every per-share number above)

⛔ **VERIFIED 2026-09-23 while writing these notes: the hold-to-expiry arm of `run_21dte_exit_test.py` drops the
winners.**

- **The mechanism:** line 83 applies `df[(bid > 0) & (ask > 0)]` to the **whole** frame, expiry day included. A leg that
  expires worthless has a zero bid on expiry day, so it's filtered out. When **both** legs expire worthless, `fin` is
  empty, and the `continue` at the settlement step **discards the trade**.
- **The effect:** the sample is selected on the expiry outcome, and the discarded trades are exactly the full-credit
  winners.
- **The check** was a targeted SQL re-pull of SPY (entries at 40–50 DTE, plus all expiry-day rows, same `pick()` and
  settlement as the study). Script: `data/tastylive/videos/research/check_21dte_settlement_spy.py`.
  - It reproduces the study exactly: **242 kept, mean −$1.77, 58.3% win.**
  - Out of **408** SPY entries, **166 were dropped. 160 of those have expiry-day rows**, all zero-bid, i.e. both legs
    worthless. The dropped trades average **+$5.51** (≈ the full credit).
  - **With them restored, SPY hold-to-expiry is +$1.13/share mean, median +$3.72, 75% win (n 402).**
    **The sign flips.**
- ⟹ The "45-DTE strangle loses at real fills" headline (hold −$2.55 / 21-DTE −$1.02 on the 44-name panel) is **not
  reliable as stated.** The **21-DTE PASS (+$1.53, t 4.26)** is computed on the same winner-depleted sample, so it's biased
  toward the early exit: on a full-credit winner, holding beats closing at 21 DTE.
- **The PASS needs a re-run** with settlement at intrinsic from chain-recovered spot (no bid filter on expiry day) before
  anything cites it. **The TEST_INDEX row isn't edited here (per instructions). Flagged to the caller.**
- Same failure family as the `run_iv_condor_study.py` INVALID row, pointing the other way: that one booked missing marks
  as wins; this one deletes the wins.

## What I would take

1. **"IV > RV most of the time" holds on sector ETFs.** That's our VRP panel, already measured.
2. **The method lesson:** a success rate is a probability restatement, not a return. It's the same trap as the 94%-win
   screener spreads the 2026-09-22 cost sweep killed. Their "no relation to premium level" shows the metric can't
   see the variable that actually sorts returns (credit/width).
3. **Nothing to adopt.**

## Not tested, could be

**Sector-ETF strangle P&L vs VRP, net of costs.** Take the 45-DTE 16Δ strangle on XLE/XLK/XLF/XLV/XLU, 2010–2026, from v3.
Sell the bid; exit at 21 DTE at the ask, or hold with settlement at chain-recovered intrinsic. Report success rate
**and** mean net P&L, worst trade and month-clustered t side by side, to show the gap between the two metrics on the
same trades. Add a within-date credit/width sort across the 5 ETFs.
- **Effort:** ~½ day. It's the 21-DTE harness restricted to 5 tickers and extended to 2010.
- **Prior:** success > 68% and mean P&L ≈ 0 to negative after costs.
- **Yield:** METHOD (win rate vs expectancy on the same trades). Not queued; low value unless Gabe wants the illustration.
