# Supplemental Notes — 2026-09-04 "Which Trading Psychology Concepts Actually Work?" (9rBgnMnDp_0)

Presenter Brendan (AI Pathways). Reviewed 2026-09-22 → `../../../2026-09-04_trading_psychology_review.md` (2.5/5).
Third AI Pathways video in the KB. Chronology: **June (9,000 strategies, 2/5) → August (25k ICT, 3/5) → this one.**

## Caption garbles
- [12:40] "a **forest** trade gives up" = "a *forced* trade gives up"
- [21:28] "Claude or Claude **a code**" = "Claude or Claude Code"
- [19:14] "**her** baseline is a profitable trader" = "*the* baseline is..."
- "school" = Skool (the paid community) throughout

## The simulation, as stated
| parameter | value | where |
|---|---|---|
| win rate | 37% | [02:03] |
| risk per trade | $500 (1% of account) | [02:03] |
| stated expectancy | "about $50 a trade" | [04:22] |
| trades per year | 750 (~3/day) | [02:18] |
| account | $50,000 | [02:33] |
| replications | 10,000 simulated years | [02:33] |
| concepts scraped | 83, "almost every one" tested | [00:15] |
| control | same trade stream, same order, rule applied on top | [02:49] |
| streakiness | injected as a second scenario; **level never stated** | [03:04] |

**There is no market data in this video.** No instrument, no period, no strategy ([01:48], said explicitly and
defended as a feature).

## Reconstruction of their generator (all checks in the review)
Solving 0.37·W − 0.63·$500 = $50 gives **W = $986 ≈ 1.97R**. Then per-trade σ = **$718**, Sharpe/trade = **0.0697**.
Every headline number in the video falls out of this i.i.d. Bernoulli model exactly:

- "10 losses in a row in 94% of years" → 1 − exp(−750·0.37·0.63¹⁰) = **93.5%** ✓
- "median losing streak 12" → ln(750·0.37)/ln(1/0.63) = **12.2** ✓
- "you need ~800 trades to know your edge" → n for t = 2 is **824** ✓ (house bar t = 3 needs **1,854**)
- "hesitation costs ~$600 per 1% of the year skipped, a straight line" → slope = annual profit ÷ 100. Zero
  information beyond *profit is proportional to trades taken*.
- Revenge trader's "average position size ≈ 3.5×" → a martingale **capped at 3 doublings (8× max)** gives
  E[size] = 3.42×. Uncapped it diverges. See review §"The revenge number is capped and they don't say so".

## Claim ledger (their verdicts)
| # | concept | mechanical rule | their verdict | our read |
|---|---|---|---|---|
| 1 | one trade means nothing / streaks are normal | — (descriptive) | TRUE | correct, and it is a power calc |
| 2 | revenge trading | double size after each loss | "true, but it's just size" | capped martingale, mislabelled |
| 3 | hesitation / fear after a loss | skip next trade after 1–2 losses | costs $17k (calm) | tautology |
| 4 | tilt | stand down after 2 consecutive losses | −$8,442 calm / **+$14,721 streaky** | the only live question |
| 5 | green-day profit target | stop for day at +$X | costs $15k, worst rule in the video | tautology |
| 6 | chasing a target when down | forced extra trades | costs only ~$3k | tautology |
| 7 | sizing up after a hot streak | 2/3/4 wins, up on day/week/month, new equity high | **ZERO** in every variant | honest null |
| 8 | be picky / fewer better trades | take only top 50% / top 17% of graded setups | ~$85 (≈0); pickier is WORSE | generator artefact |
| 9 | size up A+ setups | 1.5× on the better-graded half | **+$32,000/yr**, "cleanest result" | contradicts our size-lever study |
| 10 | protect capital | 1% vs 2% vs 5% risk with 20×-stop tail | TRUE, 1% | correct, arbitrary tail |

Unexplained: the "**0.6 bar**" for the A+/other win-rate gap [22:15] — quoted as a threshold, never derived.

## Their four prompts (the funnel product) [21:10–23:00]
1. **Streakiness check** — overall win rate vs win rate on trades taken right after 2 consecutive losses.
   Needs ≥1 year; "on two years of records it gets the answer right about 19 out of 20 times."
2. **Day-trader replay** — replay a real broker CSV under skip-after-loss / stop-after-2-losses / daily loss
   limit / daily profit target, reported in dollars.
3. **A+ grading check** — do your A+ trades actually win more, does the gap clear 0.6, what would 1.5× be worth.
4. **Survival check** — worst fills; flag any single trade that could take ≥20% of the account.

⭐ Prompt 1 and prompt 2 are, almost line for line, the **Breitstein test 1 / IQCapital** spec already queued in
`TEST_INDEX.md` §10. That overlap is the main reason this video is worth anything to us.
