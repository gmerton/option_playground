# tastylive / Anatomy of a Trade: "How to Manage Strangles" (2023-07-01, 18:35)

_Reviewed 2026-09-24. Two hosts walk through one closed ROKU short strangle (opened 2023-05-12, closed the morning of
recording) from a slide deck, then a "delta slide" of the net delta after each adjustment. Transcript (`en-orig`
auto-captions) is in this folder. The slides aren't in the transcript; every number below was spoken. **There is no
study here: it is one trade (n = 1).**_

## Verdict: 1.5 / 5

An honest, well-narrated anecdote with real fills quoted at each step, and one genuinely specifiable rule: **adjust
when the position reaches net 50–70 deltas, by rolling the untested short to ~20–30Δ, and keep net delta inside
about ±30–35** (14:44–16:30). That rule is codable, so the video earns something over a pure war story.

It can't earn more, for four reasons:

- **n = 1, and the one trade was picked after it ended.** A near-scratch (−$32) after a ~33% move in five weeks is
  the kind of trade that gets a segment. We don't see the adjusted trades that lost more than holding would have.
- **The "−$2,000 if I'd done nothing" comparison is one counterfactual path, scored after the fact.** The host
  concedes the hindsight twice: "the adjustment in hindsight helped me" (04:24) and, of the inversion, "the stock
  comes down and I would have been better off not going inverted" (13:51).
- **The dollar figures don't agree with the size.** Buying power "$600–800" (00:34) and "a 32 cent loss or 32 dollars"
  (01:43 / 07:43) mean one lot. On one lot, the original 50/60 strangle for 2.67 held with ROKU at ~75 loses about
  (75 − 60 − 2.67) × 100 ≈ **$1,230**, not "two thousand" (06:15) and not "eight, nine thousand dollar pain" (11:27).
  Either the position was bigger than stated, or the counterfactual is loose speech. In both cases the headline
  benefit of adjusting is not pinned down.
- **No costs.** The trade has at least six adjustments (roll call down, roll put up, roll call up and out, roll put
  up, invert, buy the guts / sell the wings, then close). Each one crosses two or four single-name spreads on a
  name that is not in our tradeable set. None of that is counted, and the final −$0.32 is the only net figure.

## Data audit

| item | what the video gives |
|---|---|
| underlying | ROKU, one trade. Host trades it "quite frequently" (00:39) |
| period | 2023-05-12 → close on the day of recording (~late June 2023) |
| n | **1** |
| entry rule | ~20Δ short strangle, 50P/60C with stock ~56, **2.67 credit**, ~$600–800 BPR, ~45 DTE (the first roll is "at 31 days") |
| management | discretionary delta rebalancing: roll the untested side toward the stock, roll out in time once, go inverted, then buy the guts / sell the wings (Sosnoff's re-center) |
| fills | each adjustment's credit/debit is quoted; no bid/ask, no commissions |
| control | none. The only comparison is the host's estimate of holding the original strangle |
| win rate / avg / tail | n/a (one trade, −$32) |
| significance | none |
| selection | a winner-by-survival shown after it closed. The adjustments that made things worse are acknowledged but not costed |

## Numbers as spoken

| @ | number |
|---|---|
| 00:25–00:31 | opened ~May 12: **50/60 strangle, stock ~56, sold at 2.67** |
| 00:34 | "only use six, seven, eight hundred bucks in buying power" |
| 00:52 | "starter position" for a **$25–50k** account |
| 00:54–00:58 | breakevens ~47.3 / ~62.7 ("47 60 and 67 ish" in the captions) |
| 01:01–01:04 | "basically a **20 delta** short option on either side" |
| 01:26–01:43 | stock down a couple of dollars in ~3 days → **roll the call down at 31 DTE for 2.17**, total "almost five bucks" |
| 01:57–02:09 | 5–6 days later, stock back to 56 → **roll the put up at 24 DTE for 1.64** |
| 02:11–02:17 | stock moving "two or three dollars a day", ~5% moves |
| 02:30–03:34 | ~9–10 days later, from the **55 straddle**, stock ~60: **roll out in time and roll the call up $5 for a 1.25 credit** → total **7.73** |
| 03:47–03:50 | two-day move **59 → 68** |
| 04:04–04:42 | roll the put up, "collect another buck" → **60 straddle, $8 and change** total premium |
| 05:00–05:11 | 68 → 73 over ~a week; "60 to the mid 70s… 20 to 25%" |
| 05:17–05:41 | roll the put up to 65 → **inverted 65P/60C, $5 inverted, max profit 4.88** |
| 05:51–05:54 | "the stock's gone up **40 or 50 percent**" (56 → mid-70s is ~33%) |
| 06:12–06:17 | scratch vs "a **two thousand dollar loser** had I done nothing" |
| 06:48–07:16 | **buy the guts, sell the wings for a 6.75 debit**, "really a debit of 1.75" net of the $5 inversion |
| 07:19–07:24 | new breakevens **56 / 73**, stock 64 |
| 07:41–07:47 | closed for **a 32-cent loss ($32)** |
| 08:45–08:49 | after the re-center, ~**$3 credit** left on a 10-point-wide strangle |
| 11:22–11:28 | holding = "the eight, nine thousand dollar pain to the upside" |
| 12:05–12:12 | "the current expected move for 200 days out is 20 points" (captions probably garbled) and they realised it in two weeks |
| 15:17–15:22 | adjusts at net **40, 50 or 60 deltas** |
| 15:43–15:52 | rolls the untested short "to collect around **20 or 30 deltas**", back to a 20–30Δ position |
| 16:01–16:08 | net delta after every adjustment "between **30 plus or minus**" |
| 16:14–16:23 | "gets to 60 maybe 70 and I roll up to the 30 delta put… 70 long delta, roll down to the 30 delta call" |
| 18:11–18:14 | WBA contrast: "29 implied volatility" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 14:44–16:30 | **Mechanical delta bands**: adjust at net 50–70Δ by rolling the untested short to 20–30Δ; keep net delta within ±30–35 | **UNTESTED.** We have never tested any roll on a short strangle (see `2023-01-23_W9KBp_3BpVM/notes.md`, "the question Gabe asked"). The nearest external evidence is tastylive's own 17-year SPY study, where the roll-the-untested-side arm beat holding on the breached subset (−$5 vs −$55 average, 65% vs 58% win) with no n, no t and probably at mid (that notes file, 2.5/5). The one number of ours that bears on the cost: each band trigger is two more single-name spread crossings, and single-name short premium already fails on costs (10-DTE selling: **costs = 136% of gross**, TEST_INDEX §1 "Short-dated (10-DTE) premium selling on single names"). Specced below |
| 02:30–03:31 | Rolling out in time lets you move strikes because you "sell so much extrinsic value" | ⚠ **Mechanically true, economically empty.** Longer-dated extrinsic value is where our premium is weakest: VRP 10d **+1.75vp, t 8.93**; 30d **+0.78vp, t 2.08**; 90d **t 1.30** (TEST_INDEX §9 row "More Tom… 26 clips"). The credit is larger because the option is longer, not because it's richer |
| 05:17–06:20 | Going inverted aims to scratch, not profit; scratch vs a $2,000 loser | **UNTESTED, and the comparison is outcome-scored.** The inversion locks in $5 of intrinsic loss in exchange for more extrinsic value; whether that beats holding depends on the next path, which is exactly what one trade can't tell you. The host says so at 13:51. See also the size inconsistency in the verdict |
| 06:23–07:16 | "Buy the guts, sell the wings" (Tom's re-center) decays faster because "the tail of the distribution will go to zero quicker" | **UNTESTED on short premium.** Our only re-center evidence is the **long** 7-DTE straddle: re-center / flat-take **REJECTED** (`project_straddle_recenter_study`; TEST_INDEX §2 "roll at −50%" row: "don't roll; let it expire"). Opposite sign of gamma, so it doesn't transfer. The "tails decay quicker" part is standard theta arithmetic, not an edge claim |
| 08:07–08:22 | "Stay small enough to be able to fight the position"; every adjustment hinges on size | ✅ **AGREES.** Size is the only tail lever on our ledger that isn't inverted (`sosnoff_doctrine.md` rule 25; every non-size tail-management variant INVERTED, TEST_INDEX §10 "21-DTE management rule" row, which lists them). Our held 45-DTE/20Δ strangles (`exit_21dte_2026-09-23_fixed.csv`, 14,367 trades) lose more than their credit **17.1%** of the time and more than **3× the credit 7.6%** of the time (quick check, this review). Unadjusted, this ROKU trade would have sat in that 3×+ tail (~$12.3 intrinsic loss at 75 on a 2.67 credit ≈ 4.6×). Size is what makes that survivable |
| 08:25–09:26 | Whether you can scratch depends on the credit left relative to the position; if only ~$1, roll out a cycle first | Reasonable bookkeeping; untested. It's a rule for *when* you can close for a scratch, not evidence that the adjusting beats holding |
| 10:22–10:28 | High implied volatility "allows you the flexibility to manage" | ⚠ **Flexibility isn't edge.** On single names, relative IV doesn't sort the premium (`sosnoff_doctrine.md` §"Per name: FAILS, and in places INVERTS"), and high-IV names carry the widest spreads, which every adjustment pays again |
| 11:08–12:45 | Doing nothing turns a neutral trade into a directional one ("now you're just short stock") | ✅ True in delta terms. It's a framing claim: delta-neutral is a preference, not a source of return. Our 21-DTE panel shows the unmanaged hold at **+$0.23/share, 74% win** versus **−$0.29** for the 21-DTE close (paired −$0.52, t −2.42; FIX-1, `exit_21dte_2026-09-23_fixed.csv`); that is, the one management rule we've measured on this structure earns *less* than holding and buys only lower variance |
| 16:36–16:57 | "If you wait till your delta's at 90 you're done" | Plausible as risk budgeting. Untested as a P&L claim |
| 17:36–18:21 | ROKU's high extrinsic value makes reversals cheap to roll; low-IV WBA short puts "whacked you" | Anecdote, n = 2 names, and not comparable (different trades, different moves). ROKU isn't in our tradeable set (SPY + NVDA/AMZN/AAPL/V from `vrp_shortdte_names_study.md`) or in the 44-name 21-DTE panel |

## What I would take

1. **The delta-band rule, as a spec.** "Rebalance at |net Δ| ≥ 50–70, back to ~30 via the untested side" is the
   most concrete management rule in the tastylive batch so far. It's worth writing down precisely because it's
   testable.
2. **"Stay small enough to fight"** is our size-is-the-only-lever finding in their words.
3. **Nothing to adopt.** One trade, no costs, a counterfactual that doesn't reconcile with the stated size.

## Not tested, could be

**Delta-band rebalancing on the 45-DTE / 20Δ short strangle, at real fills** (specs only; not queued):
- **Universe:** the 44-name liquid panel and entries of `exit_21dte_2026-09-23_fixed.csv` (Fridays, 45 DTE, ~20Δ
  each side, sell the bid), so the hold arm is already computed. Daily chain path from `silver.options_daily_v3`
  (the 21-DTE harness already walks it); spot from `chain_spot.py` since v3 strikes are RAW.
- **Trigger:** EOD net position delta per 1-lot ≥ +0.50 or ≤ −0.50 (sensitivity: 0.40 / 0.60 / 0.70).
- **Arms:** (A) hold to expiry; (B) at the trigger close, buy the untested short at the ask and sell the same-expiry
  30Δ on that side at the bid, repeat at each new trigger; (C) B, but the roll may cross the tested strike
  (inversion allowed); (D) B plus a "buy the guts / sell the wings" re-center when inverted and spot is between the
  strikes.
- **Settle** at intrinsic from the chain-recovered spot.
- **Primary:** B − A paired per entry, month-clustered t ≥ 3, both halves the same sign, per-year check. Report
  worst trade, CVaR 1%, and the number of spread crossings per trade.
- **Overlap:** this is the same harness as the roll-untested-side spec in `2023-01-23_W9KBp_3BpVM/notes.md`; run
  them as one study, with the breach trigger and the delta-band trigger as sibling arms, not as two tests.
- **Prior:** B − A roughly zero at mid, negative after costs on single names (≥2 extra crossings per trigger);
  lower variance, as with the 21-DTE close. Yield if NULL: MECHANISM ("rebalancing = more short gamma sold, paid
  for in spread").
