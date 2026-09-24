# Nichol Hermel — "Black Swan Hedges Explained: Tail Risk Protection with Deep OTM Puts" (2026-01-15, 18 min)

_Reviewed 2026-09-23. Solo screen-share: a thinkorswim ThinkBack replay of SPY puts through March 2020, the standard
tail-hedge talking points (0.5–2% budget, 1–5Δ strikes, 1–4 month tenors, index options), then a live build of a
March-2026 SPY 400P hedge in OptionStrat. Transcript (`en-orig` auto-captions) in this folder._

The review question: **would a deep-OTM put overlay improve the certified index put-sale bucket's risk-adjusted
return after costs, or is it negative carry that never pays?**

## Verdict: 2.5 / 5

He's honest and the mechanics are mostly right:
- he names the negative carry and the long dry spells;
- he says academics find the cost usually outweighs the benefit "unless an investor is uniquely exposed to severe
  tail risk or uses the strategy to take more equity risk" (07:40), which is the correct framing;
- he prefers index options and liquid strikes.

The evidence is one hand-picked episode. The only historical example is an entry **two sessions after the 2020 top**,
exited **one session before the low**. That's the best entry and exit in the last 16 years, both chosen with
hindsight. There's no base rate, no count of the years it paid nothing, and no portfolio-level result. The forward
example is a what-if slider (IV × 2), not a measurement. Its IV assumption is more extreme than what his own 2020
example actually did (see 14:41 below).

**On our question: already answered once, NULL, but not in this form.** Our cheap-convexity overlay
(`put_overlay_2026-09-20.md`) measured the carry and found no book-level benefit. It tested 5–10% OTM puts at
75 DTE, gated on **low** VIX, on the old risk-parity book. It did **not** test Hermel's 1–5Δ strikes. It also did
not test the certified bucket, which only trades when **VIX ≥ 20**. See "Not tested, could be".

## Results / evidence audit

**The 2020 example, re-priced on `silver.options_daily_v3` (SPY 2020-06-30 puts, queried 2026-09-23):**

| date | strike | his number | v3 bid / ask | v3 IV (bid–ask) | v3 Δ |
|---|---|---|---|---|---|
| 2020-02-21 (entry) | 250P | $0.72, IV "just over 31%", Δ .04 | **0.86 / 0.88** | 28.0–28.1% | −0.036 |
| 2020-03-20 (his exit) | 250P | ~$33, IV "just shy of 54%", Δ .49 | **32.26 / 34.79** | 41.7–47.1% | −0.58 |
| 2020-03-23 (the low) | 250P | — | 35.89 / 36.71 | 36.0–38.2% | −0.70 |
| 2020-04-17 (4 weeks later) | 250P | — | **7.26 / 7.31** | 42% | −0.21 |
| 2020-06-30 (expiry) | 250P | — | 0.00 / 0.01 | — | — |
| 2020-03-20 | 185P | $11.64, IV 72%, Δ .19 | 10.68 / 10.83 | 64.1–64.5% | −0.20 |

- **The headline holds in order of magnitude at real fills.** Buying at the ask ($0.88) and selling at the bid
  ($32.26) is **36.7×**, not ~45×. Twenty lots: $1,760 → $64,520, a **+$62,760** gain, about his "$65k". His entry
  mark ($0.72) is below v3's bid, so the ThinkBack figure flatters the multiple.
- **Most of the payoff was price, not vega.** On 3/20 SPY closed at ~$229, so the 250P had ~$21 of intrinsic out of
  $33. About ⅔ of the gain is delta/gamma. That contradicts his 06:00 line "you buy these for the vega, not the delta".
- **The payoff had a four-week half-life.** Worth $32 on 3/20, $7.26 by 4/17, **zero at expiry**. Anyone who held it,
  or used the "roll every 1–4 months" routine without a monetisation rule, kept a small fraction of the peak. The
  exit rule is the strategy. The video never states one.
- **IV at the strike rose ×1.5–1.7, not ×2.** The 250P went from 28% to 42–47%. The deeper 185P printed 64%, not 72%.
  This matters for the 14:41 forward scenario.

**No base rate.** One crash, one entry date, one exit date. Our own carry measurement for the adjacent structure
(SPY 5% / 10% OTM puts, 75 DTE, bought at the ask and sold at the bid a month later, 2011–2026):

| structure | mean / month on premium | months it pays | best month |
|---|---|---|---|
| 5% OTM, always on | **−25.6%** | 21.5% | +403% |
| 10% OTM, always on | **−32.3%** | 17.7% | +583% |
| 5/15 spread, VIX < 20 | −19.6% | 22.4% | +373% |

His 1–5Δ strikes (20–30% OTM, 1–4 months) sit further out than our 10% row. We haven't measured them. By
construction they should pay in fewer months with a larger best month.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:22 | Deep-OTM puts: small recurring losses, large payoff in a crash, "compensation just when a portfolio needs it most" | **Mechanically true; "when it needs it most" is the unproven half.** Carry measured on 5–10% OTM SPY puts: **−25.6% / −32.3% of premium per month**, paying in 18–22% of months (`put_overlay_2026-09-20.md` §1). Whether the payoff lines up with the *portfolio's* bad months is an empirical question. For our book it doesn't: book-vs-SPY monthly corr **0.22**, and **5 of the book's 10 worst months had SPY UP** (§3) |
| 01:34–03:54 | Feb-21-2020 buy of 20 × Jun-30 250P (Δ .04) for ~$1,440 → ~$65k unrealised on Mar 20 | **Reproduced, and cherry-picked.** v3 at real fills: 0.88 ask → 32.26 bid = **36.7×, +$62,760** on 20 lots (table above). The entry is 2 sessions after the Feb-19 top and the exit is 1 session before the low, both chosen after the fact. Four weeks later the same put was $7.26, and it expired worthless |
| 05:26 | When IV spikes, deltas across the chain "merge toward 0.5"; you can no longer find a 5Δ put | **Correct direction, loose wording.** Higher vol flattens the delta profile across strikes. v3 185P went from far-OTM to Δ −0.20 on 3/20 |
| 05:45 | Deep-OTM IV "not uncommon to double or even triple" in a spike | **Overstated for his own example.** 250P: 28% → 42–47% (×1.5–1.7). The *index* (VIX) more than quadrupled, but fixed-strike IV on a strike that was already on the steep part of the skew rose far less. Deep puts are priced for crashes, so the vega multiple is smaller than the VIX multiple |
| 06:00 | "You buy these for the vega exposure, not the delta" | **Contradicted by his own example.** ~$21 of the $33 was intrinsic on 3/20. In a real crash the deep put ends up in or near the money, and delta/gamma dominate. Vega is the early-crash accelerant, and it reverses fast (3/23 IV was *lower* than 3/20 while the price was higher) |
| 06:48, 08:40 | Allocate 0.5–2% of the portfolio per year | **Tested on our book, NULL.** 1–5%/yr premium budgets: ΔSharpe **−0.05…0.00**, Δmax-DD **≤ ±0.6pp** at 2%/yr. The best cell (VIX<20 5/15 spread at 5%/yr, book without the straddle) cut max DD **38.1 → 36.4** with Sharpe flat. **2022 must-pass FAILS** (VIX > 20, gate closed). **The straddle sleeve is worth ~13pp of DD vs ~1.7pp for the best overlay** (`put_overlay_2026-09-20.md` §2–3) |
| 07:00 | Diversification fails in crises (correlations → 1); deep puts are one of the few things that spike | **True of the index.** It doesn't transfer to our book's losses, which are mostly *not* index crashes (see 00:22). Where the book is crash-exposed, the 7-DTE long straddle already carries the convexity: the book made **+32% in 2020** |
| 07:25–08:20 | Persistent drag; needs discipline; people give up just before the crash | **Honest, and it's the whole problem.** "Give up just before" is survivorship in reverse: it remembers the quitters whose crash came, not the ones whose didn't. No base rate is offered. Our 10% OTM row pays in **17.7%** of months at −32%/month average |
| 07:40 | Academics: long-run cost outweighs benefit unless uniquely tail-exposed or used to carry more equity risk | ✅ **Agrees with our result.** The overlay is only worth it if it lets you run more of something with a positive edge. Our null says the book doesn't need it at budgets that fit |
| 08:37 | Roll 1–4 month puts, or use longer-dated ones to cut transactions | **Untested as a rule; the 2020 table says the missing piece is the monetisation rule.** A hedge rolled on a calendar, not sold into the spike, gives back most of the payoff (250P: $32 → $7 in four weeks) |
| 09:10–09:59 | Prefer index (SPX/SPY/ES); ES options capture overnight vol | **Index: agrees** (liquidity; our overlay's 5% put bid/ask was 0.8% of mid). **Overnight: plausible, untested for this use.** Our overnight split for SPY is ~half the day's variance (`gex_spy_ironfly_2026-09-21.md` diagnostic). That matters for *monetising* a gap, not for holding a 3-month put |
| 10:00 | 3–10Δ strikes give "maximum vega / convexity relative to cost" | ⚠ **The far-OTM preference was a mid-price artefact in our one direct test.** Event convexity: 0.12Δ over 0.25Δ was +19.5pp at mid (t 2.73) → **+1.9pp (t 0.29) at realistic fills** (TEST_INDEX §2, `event_spread_2026-09-20.md`). Relative bid-ask is widest at the lowest deltas. His own quotes show it: 400P "just over a dollar" at 2Δ |
| 11:40–12:44 | Pick the strike by open interest (400P, OI 15k, skip the 450P at OI 716) | **Wrong proxy.** Open interest is a stock of past trades; the cost you pay is the bid-ask. Galarnyk's rule (reject bid-ask > 10% of contract cost, TEST_INDEX §9) is the measurable version |
| 14:20–16:10 | 400P at IV 44.5%: IV × 2 with SPY flat → ~$43k on $2,250; −10% + IV × 2 → >$60k; halfway through → ~$25k | **A slider, not evidence, and the IV leg exceeds his own crash.** A 400P at 44.5% doubled is ~89% IV. In March 2020 the deepest strike he showed (185P) peaked around 64–72%, and his 250P rose ×1.5–1.7. A 10% selloff is also not a crash: in 2020 the strike ended up in the money because SPY fell ~32%. The slider's joint scenario (−10%, IV × 2) has no frequency attached |
| 16:20 | Can enable higher exposure to risky assets, if cost and sizing are managed | ✅ **Correct framing, and the only one under which the carry can pay.** For us: the certified bucket already caps its loss (below), so the overlay isn't what lets it be sized up |

## What I would take

1. **Nothing to adopt.** The general claim (a small deep-put budget improves a portfolio) is our put-overlay test,
   NULL. His one example is the best-case window, and at real fills it was still worth ~37×.
2. **The monetisation rule is the real content, and he skips it.** The 250P lost ~80% of its value in the four weeks after the
   low ($35.89 → $7.26 bid). Any tail hedge we ever run needs a pre-registered sell rule (e.g. sell when the put's delta crosses −0.30 or
   VIX crosses X), not a calendar roll.
3. **Our bear leg is still the straddle.** Our overlay study's conclusion stands: keep the straddle/put-spread pair
   balanced rather than buy index puts.

## Not tested, could be

**Deep-OTM put overlay on the certified bearish-high-IV bucket.** This is the version our overlay test didn't cover.

**Why it's a separate question.** The certified bucket = SPY 0.25/0.15Δ bull put, ~20 DTE, 50% take, no stop,
Fridays with SPY < 50MA and VIX ≥ 20 (plus the SPX 45-DTE condor, the same bet). It only trades when index puts are
**expensive**, so it sits exactly in the states our low-VIX-gated overlay excluded. Its tail is already defined:
- SPY: **3 of 75 trades hit −100% of max loss** (2018-12-07, 2020-03-06, 2022-06-03), all capped by the 0.15Δ long leg
  (`tierab_trades_2026-09-22.csv`);
- SPX condor worst: −42% (2022-09-02).

So an overlay wouldn't limit a loss the spread leaves open. It would turn the capped disasters into gains in crashes
that keep going, which makes it a bet on crash *continuation* entered at peak skew.

**Spec (pre-register before any pull):**
- *Universe:* the 75 SPY bucket entries in `tierab_trades_2026-09-22.csv` (2018-02 → 2026-02). SPX condor entries as a
  robustness row, not a second test (it is the same bet).
- *Arms:*
  - A = bucket alone.
  - B = bucket + SPY put at the nearest **5Δ**, same expiry as the spread.
  - C = bucket + **3Δ** put at ~60 DTE, sold after 20 sessions or at the spread's exit, whichever is first.
  - Sizing is fixed as a premium budget: overlay premium = **10% of the spread's credit**. Secondary: 5% and 20%.
- *Fills:* buy at the ask, sell at the bid. Settle at intrinsic if held to expiry, with spot from the chain
  (`chain_spot`, since v3 strikes are raw). House commission applies.
- *Control:* the same overlay bought on **non-bucket Fridays with VIX ≥ 20** (holds the vol state fixed, moves the
  bucket signal). Also a descriptive carry table for 3/5Δ puts at VIX ≥ 20 vs < 20. The VIX ≥ 20 half has never
  been measured.
- *Primary cell:* arm B at 10%. Measures: month-clustered paired Δ in net ROC; Δ CVaR-5% by month; Δ worst month;
  per-year signs.
- *Bar:* a Δ-mean t ≥ 3 is unreachable here and the pre-registration should say so. The **effective n is the number
  of stress episodes (~3: 2018-Q4, 2020-03, 2022-H1), not 75**, so the best achievable verdict is
  **UNDERPOWERED-helps-the-tail** or **NULL/negative carry**. Accept as a risk tool only if it improves the
  worst-month / CVaR by more than it costs in mean ROC *and* the improvement isn't 2020-03 alone
  (leave-one-episode-out).
- *Prior:* **NULL, leaning negative on mean.** The bucket's edge is thin (+6.8%/trade net) and the overlay is bought
  at the richest skew of the cycle. The post-shock premium test says IV after a shock is no richer than the VIX level
  implies. Negative-gamma days do realise more vol than VIX implies (+8.1%, t 7.7), but the long straddle on those
  days is fairly priced (−0.05%). Expect the overlay to rescue 2020-03, cost 1–3 points of the bucket's mean
  elsewhere, and fail leave-one-episode-out. *(The 1–3 point range is a guess, not a measurement.)*
- *Effort:* **~1 day.** It reuses `run_put_overlay_study.py`'s leg pricing and the Tier A/B trade dump. One Athena pull
  of SPY puts |Δ| ≤ 0.10, 2018–2026-02.
- *Not queued* unless Gabe asks. The book already has a crash leg (the straddle), and the answer is
  UNDERPOWERED by construction.

**VIX calls as the tail leg:** not tested anywhere in the ledger. The closest review is AJ Brown's VIX double vertical
(`data/theta_profits/strategies/vix_crash_hedge.md`, 2/5), and its payoff is capped by $1-wide spreads. Low priority
for the same reason as above.
