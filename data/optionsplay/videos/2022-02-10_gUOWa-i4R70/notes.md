# OptionsPlay: "How to Trade Credit Spreads for An EDGE! MUST KNOW Credit Spread Trading Secrets" (Dan Passarelli, 2022-02-10, 62 min)

_Reviewed 2026-09-24. ⚠ **The presenter is Dan Passarelli, not Tony Zhang.** It is a guest education webinar on the
OptionsPlay channel, and none of the OptionsPlay report machinery appears in it. It is slides plus Q&A, with no
platform demo. Transcript in this folder (auto `en-orig`)._

## Verdict: 2 / 5. The "edge" in the title is support/resistance strike placement, not credit/width, and it comes with no evidence

The index README asked whether the edge here is credit/width or POP. **It is neither.** His edge is **selling the
short strike at or beyond a support/resistance level** ("resistance tends to hold… more often than not", 12:01),
plus IV percentile as a richness check (59:01). He never states a credit/width floor or ranking. The nearest he comes
is the 60:05 example: a 3%-OTM $1-wide call spread at $0.35 vs $0.45, used to show that higher IV lowers max
loss. The mechanics are correct and well taught: max loss = width − credit, short leg = the trade, long leg = the
insurance. But every rule is asserted without a number. One of his practical rules (take the narrowest width) is
contradicted by our fills, and another (exit when the short strike is crossed) is the kind of stop our data
rejects. He is also candid in a useful way: he says delta is arbitrary and that no delta is better than another,
which is closer to our within-name finding than most sellers get.

## His selection rule

- **Underlying:** a "boring" stock with no news, no earnings and no Fed meeting before expiry. For a bull put it
  should sit near support at the bottom of a channel; for a bear call, near resistance at the top (06:01, 17:01).
- **Strike:** short strike **at or beyond the S/R level** (12:01, 30:03), which he prefers over a delta target (41:04).
- **Width:** usually the **narrowest** available, one strike wide, "nine times out of ten" (51:02).
- **Tenor:** 1 week to 2 months, **shorter is better** (08:01, 53:01).
- **Vol:** use IV percentile, and sell when options are "overpriced", unless the IV is high because of earnings (59:01–61:01).
- **Exit:** take profits at ~50–65% of max (42:00, 55:00). **Close or roll as soon as the stock crosses the short
  strike** (44:00, 57:04).

## Claims against our ledger

| @ | Claim | Tag | Our evidence (source) |
|---|---|---|---|
| 12:01, 30:03 | **The edge: short strike at/beyond S/R, because levels hold more often than not** | **UNTESTED for spreads · adjacent NULL** | The equity version is NULL: "Level triggers: pivot vs 6 other prices, BREAK and HOLD", 0/12 arms, −0.06 to −0.10R (TEST_INDEX §5). No test has placed an option strike at a level against a delta-matched strike |
| 08:01, 53:01 | Shorter tenor is better: more theta, and a narrower range of outcomes | **CONTRADICTED on single names · PARTIAL at the index** | Single-name 10-DTE selling is NET NEGATIVE, with costs at 136% of gross (TEST_INDEX §1; doctrine scorecard C5). The premium itself is largest at short tenor (10d VRP +1.75vp t 8.93 vs 30d t 2.08, `vrp_panel_study.md` §1), and the certified index cells are short-dated (SPY bull put 20 DTE t 6.07; SPY 1-day fly t 3.4). So "shorter" pays only where the spread is cheap |
| 09:03, 21:01–23:00 | ATM credit spreads have lower POP but better risk/reward; OTM the reverse | **AGREES (mechanics)** | Doctrine rule 14 (POP is a dial). The 1-day SPY GEX study: "the edge is AT the money"; OTM 16/5Δ strikes win 94% but collect little, +1.9% on risk (`gex_spy_condor_putspread_2026-09-21.md` l.34–38) |
| 20:02–22:01 | Unusual-activity scan: most traded credit spreads are ATM-short | **UNTESTABLE** | Descriptive flow observation, with no data shown. It also concerns the unsigned direction of prints |
| 40:00, 56:01 | "No one delta is better to sell than another; the model ensures fairness" | **PARTIAL** | ✅ Within a name: ARM B of `premium_to_width_2026-09-22.csv`. Realised win tracks break-even within 0.5–3pp, and ROC is flat past the 0.20Δ wing. ❌ The model is not "fair" to the seller: implied exceeds realised (10d +1.75vp, t 8.93), and across names the richer chains earn more (cw top − bottom +8.57pp, t 3.74) |
| 51:02 | **Narrowest (1-strike) width gives better risk/reward "nine times out of ten"** | **CONTRADICTED at real fills** | ARM B recut (doctrine rule 16, from `premium_to_width_2026-09-22.csv`, which I re-checked): the narrowest wing (0.25Δ on a 0.30Δ short, ~$5.8 mean width) earns **−0.04% net ROC** vs +2.66 / +3.10 / +2.98% for the 0.20 / 0.15 / 0.10Δ wings. At a real fill its credit/width is **0.202 vs 0.201** for the next wing, so the "better risk/reward" he sees is a mid-price artefact. The extra spread cost on the narrow wing eats it |
| 42:00, 55:00 | Take profit at ~50–65%, don't wait to expiry | **NULL at real fills (was AGREES)** | `etf_put_spread_exit_rule_2026-09-16.md`: 45 DTE 0.35/0.25, 50% take, no stop, **+5.70%/trade, monthly t 3.13** after the ceiling-filter erratum. ⚠ *corrected 2026-09-24: the +5.70% was GROSS and came from `options_cache`, which drops zero-bid quotes and so flatters take-profit fills. On unfiltered v3 at house fills the 50% take is **−2.78%/trade** (hold −1.37%); take − hold −1.42pp, t −1.77 → NULL (`putspread_exit_capital_time_2026-09-24.md`)*. 65% is untested |
| 44:00, 57:04 | **Exit (or roll) as soon as the short strike goes ITM** | **CONTRADICTED (stops)** | Every stop we have tested destroys value: ETF 50% take + 2× stop **−4.3%/trade, t −5.4** (`etf_put_spread_study.md` §2). Paid-to-wait: "never close on the break" (TEST_INDEX §1). The straddle −50% stop: 69.8% of breaches were better held. A strike-cross exit is a price stop. It is untested as such but falls in the same family |
| 59:01–61:01 | Use IV percentile; sell only when options are overpriced (but not for earnings) | **CONTRADICTED per name · AGREES on "richness"** | `ivrank_vs_cw_2026-09-22.md`: IV rank **−1.89pp (t −1.25)**, quintiles backwards. Percentile is the same own-history-relative object. His underlying idea, that you should sell *expensive* options, is what credit/width captures in absolute terms (cw's mechanism is entry IV 0.25 → 0.48). Earnings exclusion AGREES (earnings premium −0.428% at the bid, §9) |
| 35:01–37:00 | Cash-secured puts in the IRA when you want the stock | **CONTRADICTED as an edge** | BCI CSP study: the same as stock at the same delta, minus costs (TEST_INDEX §1, `bci_csp_study_2026-09-17.md`). It is harmless as an entry vehicle if you want the stock anyway |
| 58:01 | Iron condor = two credit spreads; close each side separately | **AGREES (the decomposition)** | ETF condor +0.36%/trade, t 0.6: the call side adds nothing (`etf_condor_call_side_2026-09-16.md`). Treating the sides separately is the right accounting |
| 49:00 | Roll a losing spread down/out only if the new trade meets the criteria | **UNTESTED** | Low prior: every loss-conditioned management we have tested inverts |

## What's new / test candidates

1. **Short strike at a support level vs a delta-matched strike on the same name-date.** This is genuinely untested
   for options. No TEST_INDEX row places a strike at a level; the nearest is the equity level-trigger NULL (§5,
   0/12). Arms: bull put with the short strike at the nearest `pivot_detector` swing low below spot, vs the same
   name-date and expiry at the matched delta; real fills, held to expiry, month-clustered, both halves. **Prior:
   low.** Levels carried nothing in the equity test, and a level-placed strike is mostly a delta choice, which ARM B
   says is flat. **Do not queue** unless Gabe wants the S/R claim closed. It is cheap only if the chain cache covers
   the strikes (it holds 0.10–0.40Δ at 25–40 DTE).
2. **Not new, don't re-test:** narrow vs wide wings (doctrine rule 16 / ARM B), IV percentile (ivrank-vs-cw row),
   50% take (ETF exit-rule row), stops (ETF put-spread §2), CSPs (BCI row), condor vs two spreads (ETF condor row).
