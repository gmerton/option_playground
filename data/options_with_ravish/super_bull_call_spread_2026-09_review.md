# Options With Ravish — "Super Bull Call Spread" (2026-09-19) — reviewed 2026-09-20

Video: https://www.youtube.com/watch?v=VZ1MbM3UQ5Q (11:05, 15.4k views at review time)
Captions: yt-dlp auto-subs, clean pull. Transcript ~2,000 words.

**Score: 2.5/5.** The mechanics are taught correctly and the risk framing is better than most of
this cohort. It is nonetheless a *vehicle* tutorial sold as a *strategy*: the only input that
decides whether it makes money — which stock to be bullish on — is assumed, never addressed.

## What he actually proposes

Buy a ~30-delta call, sell a call 10 points further OTM, same expiry, any duration (he demos 30 DTE
on NVDA). Target paying ~1/4 of the width (~$2.50 on a $10 spread) for a ~3:1 max payoff. Exit
either at a 40–50% profit target, or hold toward 100%+ and sell half to take the principal off.
No stop loss; risk is controlled purely by position size — "position for zero," only commit what
you are willing to lose entirely.

## Verified against the live chain

My first suspicion was that his two entry rules contradict each other — that "30 delta" and "pay
25% of width" could not both hold. **That was wrong, and the data says so.** NVDA Oct-16 chain,
spot 222.52, 26 DTE (Tradier, last session):

| long K | delta | 10-wide cost | % of width | max R:R | move to max |
|--------|-------|--------------|-----------|---------|-------------|
| 220 | 0.579 | 4.60 | 46.0% | 1.17x | +3.4% |
| 225 | 0.466 | 3.52 | 35.2% | 1.84x | +5.6% |
| **230** | **0.358** | **2.51** | **25.1%** | **2.99x** | **+7.9%** |
| 235 | 0.270 | 1.73 | 17.3% | 4.78x | +10.1% |
| 240 | 0.203 | 1.11 | 11.2% | 7.97x | +12.4% |

At ~30 delta the spread costs ~25% of width and pays ~3:1. His two rules are the same rule stated
twice, and they are internally consistent. Credit where due.

## But that table is also the whole critique

**The 3:1 is a coordinate, not an edge.** Read the table as a dial: 0.58 delta buys 1.17x, 0.20
delta buys 7.97x. You can manufacture any advertised payoff by sliding the strike. The "300%
upside" in the title is not something the structure generates — it is the market's price for a
~25% chance, and cost/width ≈ the risk-neutral probability of reaching max profit (the 240 call's
delta is 0.203). By no-arbitrage the expected payoff of a spread costing 25% of width **is** 25% of
width: EV is zero before costs and negative after them. Advertising the odds as the prize is the
central sleight of hand, and he never once discusses probability beyond a passing line that it is
"low."

Everything therefore rests on the direction call being better than the market's — which the video
does not touch. "If I'm super bullish on a stock" is the entire selection rule. That is exactly
what [[feedback_conviction_selection_is_the_strategy]] and the August vehicle study already say:
no vehicle fixes entries.

**Costs are not the problem here, on this name.** Mid-to-mid debit 2.51; paying the full spread
both legs, 2.59 — 3% of the debit each way, ~7% round trip, on 50–60k OI per strike. That is
genuinely cheap. It will not hold on the mid-caps where a 3:1 lottery ticket is most tempting;
option liquidity stays the second universe gate.

**The management advice contradicts the thesis.** The structure is justified by a capped 300%
tail that requires roughly +8% in 26 days. Selling half at 100% — his stated preference — caps
realised profit far below the max the low probability was paid for. If the tail is the reason to
own it, systematically cutting before the tail arrives removes the reason. This is the same early-
take-profit instinct our double-calendar work already inverted in his 2026-07 video; it recurs here
against a structure where it bites harder.

**The opener is winners-only.** NVDA +348%, SNDK +231%, TSM +43%, no losses, no sample, no date
range, straight into a Discord/coaching funnel at 3:20. Standard for this cohort.

## What he gets right

- The mechanics are accurate, including the non-obvious one: a debit spread is theta-negative while
  OTM and flips theta-positive once price is through the long strike. Correctly explained.
- **No stop loss on a defined-risk convex position is correct**, and he argues it well. A stop on a
  lottery ticket ejects you from the right tail that is the only source of P&L. This agrees with our
  own exit-timing finding that same-day exits are the negative bucket, and with the lottery-sizing
  conclusion of the event-convexity study. His "position for zero" sizing is the right lever.
- He does say the trade loses if the stock goes sideways, and that a 400% winner can halve just as
  fast. Not hidden.

## Where this touches our validated book

The one place buying OTM calls has a measured edge here is **event convexity**: 0.12-delta calls
bought before a scheduled event, sold within 5 sessions, +30.7% vs −3.6% on random dates. His
structure is a cheaper expression of that same convex bet — but the short leg caps precisely the
large move that produced the +30.7%, he has no event condition, and he holds toward expiry rather
than exiting in 5 sessions. **For the one setup where we know call-buying works, the spread is
probably the wrong vehicle**, and that is a testable claim rather than a rhetorical one.

## Queued tests

1. **Vehicle extension** — the August vehicle study compared calls / short puts / put spreads on
   identical entries but never tested a *debit call spread*. Same entries, 30-delta 10-wide, vs
   naked call. Hypothesis from that study's shape: the spread cuts the loss like the put spread did
   and forfeits the right tail, so it follows entry quality like everything else.
2. **Does capping hurt the event trade** — re-run the event-convexity winner with the 0.12-delta
   call replaced by a 30-delta debit spread. Hypothesis: materially worse, because that result is a
   right-tail result.

Neither is a test of "does the bull call spread work" — that question is not well posed without a
selection rule, which the video does not supply.
