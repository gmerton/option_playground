# tastylive — "The Dark Side of Tom Sosnoff's Iron Condor Strategy" (2023-09-08, 21:38, 31k views)

_Reviewed 2026-09-23. Research segment: tight-wing vs wide-wing SPY iron condors. Presented by **Kai** (tastylive
research, slides) with host **Nick** (Battista), then a break into "Scotty's" trade-desk segment. Transcript in
this folder._

## ⚠ Who is speaking: NOT Sosnoff

**Tom Sosnoff is not in this video.** The title attaches his name to it. The on-air exchange at 11:45 settles it:
*"you're sitting on Tom's chair" / "No, I'm in Bat's chair"*. The host is sitting in for Tony Battista, and Tom is
absent. The presenter addresses the host as "Nick" at 08:17. The "five points wide is our minimum" rule (15:09)
is Nick's statement of house practice, not Sosnoff's. ⟹ **`data/tastylive/index/README.md` lists this as one of
"the 4 titles that are Sosnoff himself". Only three of the four are**, and one of those three
(`9vwnX5mTT9M`) is probable rather than confirmed. Treat everything below as **tastytrade house doctrine on
Sosnoff's trade**, not as his words.

## Verdict: 3 / 5

It's the best of the four on evidence, and the one where our own data backs the headline. It shows an actual
historical comparison: SPY iron condors at 1/2/3/5/10/20/30/40-dollar wings. The number that matters most is
honest: **expected ROC ~50% on a 1-wide becomes realised < 1%**. Its central claim is **fewer wide condors beat
many narrow ones for the same buying power**. Our single-name bull put CSV agrees on the same name and date:
**the narrowest wing is about 3pp of net ROC worse than any wider wing, month-clustered t 4.5–11.7, both halves**.
The advantage then flattens.

It is capped at 3 because it gives no sample period, no n, no fill convention (tastylive studies are
conventionally mid) and no cost line. It also never states the most obvious mechanism: twenty 1-wide condors pay
twenty times the commissions of one 20-wide.

## The rules, in codable form (house, not Sosnoff)

| dimension | rule as stated |
|---|---|
| structure | Defined-risk iron condor on SPY (the same logic applies to any name, scaled to price) |
| wing width | **Minimum $5 wide for underlyings in the $100–500 range** (SPY, AAPL). Narrower only for ~$20 stocks (15:09–15:47). Small accounts (~$5k) may start at $2–3 wide, then widen (20:27–20:40) |
| sizing | For the same buying power, **one wide condor rather than many narrow ones**: "$2,000 to risk → one 20-wide, not twenty 1-wides" (09:33–09:47) |
| tenor | ~45-day cycle (04:25) |
| take profit | **50% of max profit** (25% for straddles) (16:04–16:10) |
| time exit | **Close at least three weeks before expiration**, i.e. the 21-DTE rule (18:28–18:33) |
| redeploy | Wider wings reach 50% sooner, which frees capital for the next high-IV opportunity (16:15–17:45) |

## Data shown: audit

| item | what the video gives | assessment |
|---|---|---|
| universe | SPY only | one name; the "5-wide minimum for AAPL" is extrapolated, not shown |
| sample | "historical performance", period **not stated** | can't check regime composition |
| n | not stated | no t, no CI anywhere |
| fills | not stated; the 1-wide example is priced "theoretically" at a 33c credit | ⚠ likely mid. On a 1-wide, crossing four bid-ask spreads is a large share of a 33c credit. At the house cost model ($0.65/leg/side + 25% of the quoted spread) the commission alone on 4 legs round-trip is $5.20 per condor, **16% of a $33 credit** and 0.26% of a 20-wide's ~$2,000 risk |
| control | the wing widths are each other's control (same entry, same tenor) | ✅ a legitimate paired design. That's why it rates above the others |
| results quoted | 1–2-wide success rate **below 65–67%**; realised ROC **< 1%** for 1–2 wide vs **~3%** for 5/10/20 and similar at 30/40; expected-vs-realised ROC gap narrows as width grows; P&L variance of narrow condors spikes in the last 2–3 weeks | plausible and consistent with ours (below); unverifiable without n and fills |

## Claim by claim

| @ | Claim | Our evidence | new vs `data/more_tom` |
|---|---|---|---|
| 01:47–02:35 | A 1-wide SPY condor at a 33c credit caps the loss at ~$67, so "downside protection" is excellent | **True per unit, meaningless per dollar.** Max loss per contract is not risk per dollar of buying power. The video's own next section says so | new |
| 04:05–04:47 | 50% theoretical ROC × 8 cycles/yr requires a 100% success rate | ✅ **Agrees. This is POP ≠ edge.** The theoretical ROC is max profit over max loss. Our credit/width quintiles show win rate and payoff trading off (win 79.6 → 75.7, net ROC −2.96 → +4.07) | dup of More Tom #11 |
| 06:01–07:29, 10:17–10:43 | Narrow wings: win rate < 65–67%, all-or-nothing outcomes, **realised ROC < 1% vs ~3% for 5–20 wide** | ✅ **Agrees, exploratory, on our data.** Re-reading `data/studies/premium_to_width_2026-09-22.csv` (single-name 30Δ bull puts, 20 names, 2018-01 → 2026-01, real fills + commissions, held to expiry; ARM B varies only the long wing on the same name and date). Net ROC / P(max loss) / ROC sd by wing: **0.25Δ (~$3 wide) −0.04% / 18.2% / 0.50**; 0.20Δ (~$5) +2.66% / 14.2% / 0.46; 0.15Δ (~$10) +3.10% / 10.2% / 0.41; 0.10Δ (~$15) +2.98% / 7.0% / 0.36. **Paired vs the narrowest wing: 0.20Δ +2.93pp (month-t 11.66), 0.15Δ +3.42pp (t 6.91), 0.10Δ +3.30pp (t 4.50), 97 months, both halves positive.** Past ~0.20Δ it is flat: 0.10Δ − 0.20Δ = +0.37pp (t 0.83). ⚠ This recut was not pre-registered; the pre-registered ARM B test was monotonicity, which fails. Three contrasts, all well above Šidák | ⭐ new |
| 08:13–10:10 | For the same buying power, one 20-wide beats twenty 1-wides: lower P(max loss), better break-even | ✅ **Agrees** (same table: P(max loss) falls from 18.2% to 7.0% as the wing widens). Mechanism the video omits: **commissions and bid-ask scale with the contract count**, not with the risk. Twenty narrow condors are eighty legs crossing the spread twice | ⭐ new |
| 11:00–11:45, 13:02–14:30 | Wide wings give a steadier, more "replicable" return; narrow ones can "destroy the portfolio in 45 days" | ✅ Agrees on variance (ROC sd 0.50 → 0.36 above). Same shape as our 1-day SPY fly: **1× wings FAIL (t 2.0), 2× wings PASS (+5.8% on max risk, t 3.4)** on positive-gamma days. Narrow wings "eat most of the credit" | new |
| 15:09–15:47 | **$5 minimum width** for $100–500 underlyings | ✅ **Consistent.** Our narrowest bucket (median ~$3) is the only one that loses; ~$5 and wider are statistically indistinguishable. Stated in delta, the threshold is "long wing no closer than ~0.20Δ to a 0.30Δ short". Ours is in delta and theirs in dollars, so the mapping is approximate | new |
| 15:54–17:45 | Wider wings reach the 50% target sooner, freeing capital for new high-IV trades | **Untested.** The redeploy benefit is an opportunity-cost argument. Note it only pays if the next trade has positive expectancy, and on single names our ungated selling doesn't (10-DTE single-name selling: costs = 136% of gross) | new |
| 18:04–18:33 | Close at least three weeks before expiry | ✅ **Agrees on risk, not on return.** The 21-DTE test: paired +$1.53/strangle, t 4.26, sd $23.58 → $11.86, worst −$617 → −$259, but **both arms negative** (verified at `exit_21dte_2026-09-23.csv`: hold −2.55, 21-DTE −1.02 per share, n 6,558; medians ≈ 0) | dup (OptionsPlay 21-DTE) |
| 18:33–20:15 | Narrow-condor P&L becomes binary and volatile in the last 2–3 weeks | ✅ Agrees mechanically: that's gamma. It's also the stated rationale of the 21-DTE rule, whose test halved the variance | new |

## What I would take

1. ⭐ **Don't sell a spread whose long wing is within one strike of the short.** On our own CSV, the narrowest wing
   is the **only** losing wing. It's about 3pp of net ROC worse, at t 4.5–11.7 in both halves. It's a cheap rule
   and it's consistent with the retired small-credit filler (UVIX, SQQQ, ASHR...). **Candidate rule: the long leg
   at ≤0.20Δ when the short is at 0.30Δ.** ⚠ It comes from an exploratory recut. Confirm it before it touches
   sizing.
2. **Don't read wider as always better.** Our curve is flat from ~0.20Δ outward. The gain is "not the narrowest",
   not "the wider the better".
3. Correct the attribution: this is house doctrine, not Sosnoff on camera.

## Not tested, could be

- **Pre-registered wing-width confirmation on the index bull put (SPY/QQQ, the in-book structure).** Arms: long
  leg at short−1 strike / 0.20Δ / 0.15Δ / 0.10Δ, same entries, real fills, primary = narrowest vs 0.20Δ,
  month-clustered t. ~1 hour on `run_premium_to_width.py`. Prior: replicates, because it's largely a friction
  effect. **Not queued**, pending Gabe.
- ⚠ **Doc error found in passing:** `data/optionsplay/videos/2026-07-25_YfrZT_kTo_4/notes.md` (ARM B) lists the
  ROC series "+2.98 / +3.10 / +2.66 / −0.04" against wings "0.25/0.20/0.15/0.10Δ". The CSV maps it the other way
  round: **0.10Δ → +2.98, 0.15Δ → +3.10, 0.20Δ → +2.66, 0.25Δ → −0.04**. Its reading ("dialling your own width buys
  nothing") also misses that the narrowest wing is significantly worse. Not edited here (out of scope). Flagged
  for the owner.
