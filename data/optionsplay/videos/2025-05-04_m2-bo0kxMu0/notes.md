# OptionsPlay: "How to Manage Losing Credit Spread" (Tony Zhang, 2025-05-04, 65 min)

_Reviewed 2026-09-24. Thursday webinar: a $600k blow-up post-mortem, then the house exit rules, the credit-spread
selection rule, a platform demo and Q&A. Transcript in this folder (auto `en-orig` captions)._

## Verdict: 2.5 / 5

The **mechanics** half is correct and worth knowing: a "defined-risk" spread held through expiration is not defined
risk, because the long can still exercise an out-of-the-money option after the close. The **management** half is the
standard OptionsPlay/tastytrade bracket (50% take, 2x-credit stop, out at 21 DTE). On our data **the stop is the part
that destroys value**, and the 21-DTE rule cuts risk but earns less than holding (FIX-1 re-run 2026-09-24). The **selection** half repeats the 3.5/5 video
(`YfrZT_kTo_4`): credit/width ranked across liquid names, which is our best creator result. But here it is pushed
to a floor of 33%+, which our 30/20-delta geometry mostly reaches by moving toward the money, and that
(ARM B) buys nothing. Everything is priced at the mid ("you can execute ... near the midpoint if not at the
midpoint"). There are no costs, samples or statistics. The live demo trade, an at-the-money SPY bear call, lost
under all three of his own exits.

## His selection rule, in one line

Liquid underlying only. Credit ≥ 1/3 of the width, ranked highest-first ("start at the top of the list"). The
platform's trend signal sets the direction, and entry is timed on a pullback in an uptrend (bull put) or a rally in a
downtrend (bear call), using RSI/CCI. 45 DTE. Short strike near the money: "high delta = LESS risk".

## Claims against our ledger

| @ | Claim | Tag | Our evidence |
|---|---|---|---|
| 03:08–15:03 | Biogen, Nov 2020. 100x 292.5/290 put spread for $0.50 ($20k max risk). The stock was halted and closed ~$330 on expiry Friday. The FDA panel voted no after the close, the long exercised the OTM put, BIIB opened ~$230 Monday, and the account showed a **$625k** loss | AGREES (mechanics) · n = 1 anecdote | Correct mechanism: exercise decisions run to ~5:30 pm ET, so the seller carries after-hours risk with no hedge. Per-contract arithmetic checks out (0.50 credit, 2.00 risk, 10,000 shares x ~$62.5). Not a statistical claim |
| 14:31 | The client could have exercised the long 290 put to cap the loss at the spread's max | AGREES (mechanics) | Correct, if he caught the news inside the exercise window |
| 23:21, 59:28 | Cash-settled index options don't carry this risk | AGREES (mechanics) | Correct, and it is one more reason our certified cell is **SPX** (`spx_strangle_playbook.md` banner). SPY, the other half of the same bet, is physically settled |
| 18:22–19:13 | **Three exits: stop at 100% of max gain (sold $8 → stop at $16 = 2x credit), take at 50%, exit at 21 DTE**, on ~45-DTE spreads | see the next three rows | Same bundle as Sosnoff doctrine rules 21–22 |
| 19:13, 24:58 | **Stop at 2x the credit** | **CONTRADICTED** | The direct test is `etf_put_spread_study.md` §2. On 20 ETFs, 45 DTE, 0.35/0.25Δ, the 50%-take + 2x-stop rule **lost −4.3%/trade (t −5.4)**, negative in both halves, for almost every ETF. Separating the two (`etf_put_spread_exit_rule_2026-09-16.md`, as corrected in `etf_condor_call_side_2026-09-16.md` §1): **take-only / no stop +5.70%/trade, weekly t 4.87, monthly t 3.13**. "The stop was doing the damage, not the take." On the SPX condor the 2x stop never triggered in 142+ trades (`spx_strangle_playbook.md`), so it is harmless there, and 1.5x hurts |
| 19:13 | Take profit at 50% of max | PARTIAL | Positive in the take-only ETF bull put arm above (the take "contributes; direction does the heavy lifting"). **Untested in isolation**: `sosnoff_doctrine.md` rule 22 is still UNTESTED. ⚠ Those ETF runs are on `options_cache`, with 7.1% missing exit marks excluded (see the doc's own caveat) |
| 21:41, 25:50 | **Exit at 21 DTE**: "99.99% of the time" no early assignment and never expiration | **NULL, leaning INVERTED** (on return), AGREES (on assignment mechanics and risk) | The one study (`run_21dte_exit_test.py`, TEST_INDEX §1) dropped zero-bid expiry-day rows, i.e. the worthless-expiry winners of the hold arm; the +$1.53 / t 4.26 PASS is **RETRACTED**. FIX-1 re-run 2026-09-24 (`data/studies/logs/exit_21dte_fixed.log`, 45-DTE 20Δ strangles): 21-DTE close − hold **−$0.52/share, month-clustered t −2.42** (halves −0.63/−0.40; hold +$0.23, 74% win; 21-DTE −$0.29, 64% win) → PASS: NO; risk only (sd $9.33 vs $17.09, worst −$291 vs −$617) |
| 51:43–52:28 | At 21 DTE, **roll to a new 45-DTE spread** rather than leave money on the table | UNTESTED as stated | This is close + re-enter. Our only roll evidence is the **long 7-DTE straddle** (−50% stop −9.51pp on the breach cohort, re-entry NULL t 1.55; `straddle_stop_path_2026-09-20.md` l.39–41), a different object. Since the new spread is an ordinary 45-DTE entry, the question reduces to whether the underlying still qualifies |
| 30:24–33:15 | **Credit ≥ 1/3 of width is break-even at 67% win; 40%+ (1.5:1) needs only 60%**. Seek credit above 33%, and the ranked list is "where you get the most edge" | **AGREES across names · CONTRADICTED within a name** | ⭐ Cross-sectional: top − bottom quintile **+8.57pp, t 3.74**. Within-date +7.64pp, t 4.15 (`premium_to_width_2026-09-22.csv`, TEST_INDEX §277). Replicated head-to-head vs IV rank: cw t +2.81, ivr t −1.25. But ARM B, where the same name and date and only the wing move, is flat past the narrowest wing, and realised win tracks break-even within 0.5–3pp. So "break-even win rate" is arithmetic, not edge. ⚠ **His 33% floor is above our richest 30/20Δ quintile (mean 0.25).** Names reach 33–49% mainly by selling closer to the money, which is the within-name coordinate that buys nothing. In the index cell the sort **inverts** (−10.14pp, t −1.23; cw range 0.14–0.19) |
| 38:05, 41:56 | Only very liquid underlyings, "so you can execute ... near the midpoint if not at the midpoint" | AGREES (liquidity) · **CONTRADICTED (mid fills)** | Liquidity is our biggest cost finding. Spread predicts outcome better than premium, and liquidity is what separates the survivors in `cw_rescue` (2 of 15). But our house fill is mid − 25% of the quoted spread, and on 2026-09-22 thirteen screener spreads went from +3.8…+13.4% gross to −5.1…+5.9% net, with 0 of 13 significant |
| 33:55–36:42, 53:15 | **Timing edge**: enter bull puts on pullbacks in an uptrend and bear calls on rallies in a downtrend; RSI/CCI "to optimize timing" | **PARTIAL / mostly CONTRADICTED** | RSI on ETF put spreads is a VIX proxy (RSI<40 +3.88pp t 2.21 pooled, gone with VIX in the fit; `rsi_conditioning_study_2026-09-16.md` §A). The only certified put sale is the *extreme* pullback, bearish-high-IV (SPY t 6.07). Bullish-low-IV QQQ, the "uptrend" case, is −4.8% month-weighted (t −0.87). Pullback equity entries also fail vs the breakout (TEST_INDEX §113). And the **bear-call leg of the rule has no edge on our data**: ETF bear call −2.66%/trade (monthly t −1.21), UVXY/UVIX net-negative |
| 39:34–40:19 | **Live idea: SPY Jun-13 ~562.5/590 bear call for ~$12.12**, ~1:1 risk/reward, "timing favourable for bearish exposure" | **Lost under every one of his exits** · n = 1 | SPY closed 558.47 on 2025-05-01 and 566.76 on 05-02. It gapped to 582.99 on 05-12, was at 579.11 on 05-23 (the 21-DTE date), and closed **597.00 on 06-13 (expiry), above the long strike: max loss if held.** The 2x stop (~$24 spread value) would have fired around the 05-12 gap (committed `data/cache/SPY_stock.parquet`). ⚠ Strikes come from auto-captions ("562590"); the direction of the audit does not depend on the exact short strike |
| 61:03–62:37 | **ATM (high-delta) credit spreads are LOWER risk** (1:1 risk/reward) than far-OTM ones (orders of magnitude more risk per $1) | PARTIAL | The warning against far-OTM "picking up pennies" agrees with the 3.5/5 video and the Biogen case. Calling ATM "lower risk" confuses payoff ratio with risk. By ARM B, win rate falls one-for-one with credit/width, so moving toward the money changes variance, not EV. In SPY 1-day, "OTM strikes win more often but collect little, the edge is AT the money" (TEST_INDEX §58), but that is a positive-gamma-day index result, not a 45-DTE single-name one |
| 37:21, 49:19 | "The only person you can blame is yourself": the risk is known upfront, so a loss that is too big was too many contracts | AGREES | Sizing to max loss is our rule. The size lever works as exclusion (+0.29R OOS) |
| 20:03 | Only thinkorswim and IBKR allow OCO brackets on complex orders; tastytrade doesn't | UNVERIFIED | Broker feature claim, not checked |
| 15:20, 16:04 | Tesla and Nike reported after the Friday close and "blew up quite a few accounts" | UNVERIFIED anecdote | Not checked |

## What's new / test candidates

- **Nothing new to test.** Each claim is already answered. Stop: `etf_put_spread_study.md` §2. Take: sosnoff rule 22,
  whose 50%-take arm is already listed as a candidate in `sosnoff_doctrine.md`. 21 DTE: FIX-1 (done 2026-09-24, risk only). Credit/width: §277/§47.
  Timing via RSI: §67. Call side: §32.
- **One mechanic worth keeping, not testing:** close physically settled short options before the Friday close, or
  hold the long through the exercise window. This matters for the SPY half of the index stress bucket, not the SPX half.
- ⚠ **Ledger hygiene found during this review:** (1) the 21-DTE numbers in `data/tastylive/sosnoff_doctrine.md`
  (rule 21, scorecard C5) carry no UNDER-CORRECTION flag, though TEST_INDEX §1 does. (✅ Fixed 2026-09-24 with the FIX-1
  re-run numbers.) (2) The "roll test" cited for
  "never roll a loser" (doctrine rule 23, `data/optionsplay/index/README.md`) is a **long-straddle stop** study. The
  direct short-spread stop evidence is `etf_put_spread_study.md` §2 (−4.3%, t −5.4).
