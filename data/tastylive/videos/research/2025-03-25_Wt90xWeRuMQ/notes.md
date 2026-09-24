# tastylive: "I Stopped Trading Strangles After This Study" (2025-03-25, 16 min)

_Reviewed 2026-09-23. Tom Preston ("Mr. Preston", 00:57) plus a senior host. The host's allocation numbers ("defined 0.5–2%,
undefined 3–7%") and "I will be trading 20 years from now" are the tastylive house voice; the captions don't identify him.
The transcript (`en-orig` auto) is in this folder. It has the most numbers of the batch, but they're **premium-to-buying-power
ratios and win rates, not P&L.**_

## Verdict: 2 / 5

**The title is false again.** The study compares 16Δ strangles with 16/10Δ iron condors, and the conclusion is to keep
trading both. Strangles make "more dollars", condors "more percent" ("we pay our bills with dollars, not percents",
10:36–10:44). Nobody stops trading strangles.

The design is a fair paired comparison: same 45-DTE entries, same 21-DTE management, same underlying. It shows the right
mechanism: the wings are a capital decision, and the P&L direction is identical. But:
- there's no dollar mean, t-stat or cost model;
- it's likely at mid, and the condor's four legs pay twice the friction;
- the win-rate gap (strangles 10–15% higher) comes from the 50%-take-style early exit the host names himself.

It's a capital-efficiency discussion. It isn't evidence that either structure has an edge.

## Data audit

| item | what the video gives |
|---|---|
| Underlying | SPY (implied by "SPY moves greater than 2%", 03:39) |
| Period | "10 years" (~2015–2025); a yearly panel covers 2018, 2020, 2021–2025 |
| Arms | 16Δ short strangle vs **16/10Δ iron condor** (short 16Δ, long 10Δ wings) |
| DTE / management | 45 DTE, **managed at 21 DTE** (01:14–01:16). The host also implies a profit target on strangles (05:00–05:06) |
| Buckets | outcome by underlying move over the trade: down >5%, 0 to −5%, 0–2%, up to 5%, up >5% |
| n | "hundreds of these" (04:20–04:22) |
| Metrics | win rate, premium ÷ buying power, max loss ÷ buying power, cumulative P&L chart |
| Fills / costs | not stated (tastylive convention: mid, no commissions). ⚠ A condor has 4 legs vs 2, so costs aren't neutral between the arms |
| Compared to | each other. The paired design is fine for "wings or not", but there's **no benchmark for whether either pays** |
| Win vs mean vs tail | win rates and loss ÷ BP given; **no dollar means read out** |
| Significance | none |
| Selection | ⚠ **move buckets condition on the realised outcome.** "Strangles do great in 0–2%" is true by construction and can't be traded, since the move isn't known at entry |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 01:01–01:16 | 16Δ strangle vs 16/10Δ iron condor, 45 DTE, managed at 21 DTE, 10 years |
| 01:43–01:57 | Strangles best when the move is 0 to +2%; condors better when drops exceed 5% |
| 03:28–03:36 | Highest-probability range: 0–2% moves |
| 04:28–04:37 | Strangles have a higher win rate than condors **in every bucket** |
| 05:28–05:32 | 2020: strangles "challenged" |
| 05:46–06:04 | Reduce strangle size in 2018 and 2020; increase it in 2021–2023 |
| 07:28–07:33 | Strangle win rates are **10–15% higher** than condors' "across various market conditions" |
| 07:39–07:44 | Reassess condors if their win rate falls **below 60%** |
| 10:13–10:28 | Condor premium ÷ buying power is **12–15%**, "**2 to 3 times** higher than strangles" |
| 11:44–12:12 | House allocation: **0.5–2% of BP per defined-risk trade, 3–7% undefined**, a 3:1 to 6:1 ratio |
| 12:21–12:31 | Strangles can lose **> 50% of BP** in extreme moves; condor max losses stay **under 65% of BP** "even in the worst scenarios" |
| 13:55–14:16 | 2018 and 2020 had the highest max-loss/BP; 2021–25 lower, "because we've started to close everything at 21 DTE" |
| 15:18–15:21 | Explosive volatility "only happens about 10% of the time" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| title | "I stopped trading strangles" | ❌ Contradicted by the video: "a balanced strategy using iron condors… and strangles… is supported by all the data we have" (15:30–15:38) |
| 02:07–03:07 | Strangles and condors are "basically the same trade". The wings are only there for capital; P&L has the same sign, smaller in both directions | ✅ **Agrees, and it matches Sosnoff's own "no theoretical difference in edge between the tight condor and the wide strangle"** (OptionsPlay interview @54:44–57:23): true **within a name** on our data, where dialling your own credit/width does nothing (ARM B, non-monotone). ⚠ At real fills the wings aren't free. They're two more spread crossings on the cheapest options in the chain, and **every small-credit spread in our screener was a mid-pricing artefact** (UVIX +11.0% gross → −8.8% net) |
| 01:43–03:28 | Strangles excel on 0–2% moves, condors on > 5% drops; "consider early exit when SPY moves > 2%" | ⚠ **Outcome-conditioned buckets.** Every short-premium structure wins when the realised move is small. That's the payoff diagram, not a finding. "Exit when SPY moves > 2%" is a **P&L-conditioned stop**, and every such exit in our ledger is negative (straddle −50% stop −3.84pp; profit locks, BE stops and trims all cost). tastylive's own 2023 rolling study found exit-at-breach the worst arm (32% win) |
| 04:28–05:06, 07:28 | Strangles win 10–15% more often, partly because "you can take strangles off when they hit a certain profit target" | ✅ Mechanically right. ❌ **Not edge.** Win rate is the metric our ledger most often finds moving against expectancy (premium-to-width: win falls 79.6 → 75.7 while net ROC rises −2.96 → +4.07, t 3.74) |
| 05:24–06:04 | 2020 hurt strangles; size down in "uncertain" years (2018, 2020) and up in recoveries (2021–23) | ⚠ **Hindsight labels.** "Uncertain" and "recovery" are only knowable afterwards. Our tested version, **sell index premium after a selloff at VIX ≥ 20**, is the *opposite* sizing rule (size up into the stress, not down). It's the one bucket that certifies (SPY bull put t 6.07, SPX condor t 5.21). "Regime can't be forecast" is our broader result (breakout-regime feedback, strategy localisation persistence ρ −0.01) |
| 06:35–07:18 | The cumulative strangle P&L "offsets" 2020; keep doing it year after year | ⚠ **Unresolved on our data, and our old answer was wrong.** The ledger's 21-DTE study reported that the 45-DTE 20Δ strangle loses at real fills (44 names: hold −$2.55, 21-DTE close −$1.02; SPY −$1.77 / −$0.46). **But that sample drops every trade whose two legs both expired worthless** (settlement caveat below). With them restored, SPY held to expiry is **+$1.13/share, median +$3.72, 75% win (n 402)**, and 2020 is inside that. So their "cumulative P&L offsets 2020" is *consistent* with our corrected SPY number. **Re-run 2026-09-24 (FIX-1, 44 names, n 14,367):** hold **+$0.23/share, 74% win**; 21-DTE close **−$0.29** — ≈ flat, not a loser |
| 10:13–11:34 | Condors earn 12–15% premium/BP, 2–3× strangles; but "we pay our bills with dollars, not percents" | ✅ **The dollars-vs-percent point is right and it's our capital rule** (the put spread ties up 4–7× the capital of a debit spread; judge on $/risk and on delta). ⚠ But premium/BP is a *collected* ratio, not a *realised* one. At real fills the condor's extra 2 legs cost 25% of their spread each way |
| 11:44–12:16 | Allocate 0.5–2% per defined-risk trade, 3–7% per undefined-risk trade | **Consistent with our sizing rule** (size by max loss; the certified bucket is capped at $3,000 total). The 3–7% of BP for a naked strangle is a **margin** number. A −50% of BP loss (their own 12:21 figure) on a 7% allocation is −3.5% of the account per position in a crash, and the positions are correlated |
| 12:21–12:31 | Strangles can lose > 50% of BP; the condor max loss stays < 65% of BP | ✅ Consistent with our tail numbers: the SPY hold arm's worst is −$82.88 on a $3.71 credit (2020-02-07), −22× credit. The certified SPX cell uses 0.10Δ wings, and its worst trade is −41.9% of risk vs −100% for the SPY bull put |
| 13:55–14:28 | Max-loss ratios fell in 2021–25 "because we've started to close everything at 21 DTE" | ✅ **Our 21-DTE test agrees on the mechanism.** The close halves the variance (sd $11.86 vs $23.58) and the worst trade (−$259 vs −$617). ⚠ But 2021–25 was also a lower-stress period, so their before/after comparison confounds rule and regime. Ours is paired. **Re-run 2026-09-24 (FIX-1):** the variance cut survives (sd $9.33 vs $17.09, worst −$291 vs −$617); the mean does not — 21-DTE close − hold **−$0.52/share, t −2.42** (NULL leaning INVERTED) |
| 15:07–15:21 | Everything falters in explosive volatility, "only about 10% of the time" | The truth of the matter: the tail *is* the P&L. Corrected SPY hold arm: median +$3.72 vs mean +$1.13. The tail takes ~70% of the median trade back, and 2020-02 entries alone lost up to −$82.88 on a $3.71 credit |

### Why "stopped trading strangles"?

They didn't. What the data showed them:
1. the condor's P&L is the strangle's P&L, shrunk;
2. the condor is more capital-efficient per unit of premium;
3. the strangle makes more dollars and wins more often;
4. both do badly in stress years, and the 21-DTE close cut the max-loss ratios.

**None of that says either structure has positive expectancy after costs.** Their comparison is paired, so it can't. On
that question our certified answer is narrow: a **skewed, VIX-gated, winged** SPX version after selloffs certifies (t 5.21).
The ledger's broad "the naked 45-DTE strangle loses at real fills" result is **invalid as it stands**: the hold arm dropped
the both-legs-worthless winners. Corrected SPY is +$1.13/share held. The unconditional strangle is **open**, not failed.
**Re-run 2026-09-24 (FIX-1):** 44-name panel held +$0.23/share (74% win) — ≈ flat, no edge shown, not a loser.

### Settlement caveat on our strangle panel

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
  anything cites it. ✅ **Done 2026-09-24 (FIX-1): PASS RETRACTED.** n 14,367: 21-DTE close − hold **−$0.52/share,
  month-clustered t −2.42**, halves −0.63/−0.40 → NULL on return, leaning INVERTED; risk reducer only (TEST_INDEX §1). **The TEST_INDEX row isn't edited here (per instructions). Flagged to the caller.**
- Same failure family as the `run_iv_condor_study.py` INVALID row, pointing the other way: that one booked missing marks
  as wins; this one deletes the wins.

## What I would take

1. **"Wings are a capital decision, not an edge decision"** is right, and it matches Sosnoff within a name.
2. **The 21-DTE close cuts the tail.** Their before/after agrees with our paired result on variance. On return it costs: −$0.52/share, t −2.42 (PASS retracted 2026-09-24, FIX-1).
3. **Size by max loss, not by margin.** Their own −50%-of-BP figure shows why.

## Not tested, could be

**Paired strangle vs condor at real fills, per-leg costs.** SPY 2010–2026 from v3, 45 DTE, 16Δ short, wings at 10Δ vs 5Δ vs none,
closed at the first session ≤ 21 DTE at the ask. Report the net $ mean, net return on max loss, worst trade, CVaR-5% and
month-clustered t for condor − strangle, with a per-year panel. It answers "does the wing pay for itself after 2 extra
spread crossings" directly.
- **Effort:** ~½ day on the 21-DTE harness plus the v3 call pull shared with the bullish-strangle test.
- **Prior:** the condor is worse on mean, better on CVaR, and the certified SPX cell's 0.10Δ wing is the only version worth
  its cost.
