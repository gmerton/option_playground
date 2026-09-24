# tastylive — "How Tom Sosnoff Trades 0DTE Vertical Spreads" (published 2024-01-27, recorded Tue 2024-01-23, 13:25, 34k views)

_Reviewed 2026-09-23. "Market Measures" segment (CBOE-sponsored): a research-team study of directional 0DTE SPX
verticals, read and annotated live. The segment opens with Sosnoff describing his own 0DTE trade from that morning.
Transcript in this folder._

**Who is speaking.** **Sosnoff, confirmed.** "I'm Tom S, he's Tony Battista" (01:10), with the date given as
"Tuesday January 23rd". The study is the research team's. The commentary, and the one trade he describes, are
his. ⚠ The title says he "trades 0DTE vertical spreads". **The trade he actually reports is not a vertical.** It's
a short ATM straddle with wings at the expected move, i.e. an **iron fly**.

## Verdict: 2 / 5

The segment is worth more than its study, because Sosnoff reveals his standing 0DTE structure: *"we like to go
[wings] at the expected move"* (03:06). Our data gives a sharp answer to that structure. **A 1-day SPY iron fly
with wings at 1× the implied move fails even on the favourable days (t 2.0), and loses on unfavourable ones
(−12.0%, t −3.7).** The same structure passes only with **2× wings on positive-dealer-gamma days**, and he
mentions no gamma filter.

The study itself has three problems:
- it splits results by whether the trade was "directionally right", which is **outcome conditioning**, so the
  "right" rows are tautologically 100% winners;
- it covers **10 months of a bull market**;
- it states no fills, n or costs.

Credit where due: Sosnoff flags the hindsight himself ("in hindsight... masters of the obvious"). He also draws
the one conclusion our data backs: **the premium is at the money** ("I sold a $6 call, that's what I like to
sell").

## His rules, in codable form

| dimension | rule as stated |
|---|---|
| instrument | SPX 0DTE (index, cash-settled) |
| his own structure | **Sell the ATM straddle; buy the wings at the expected move** (~±120 SPX points that day). When the strikes weren't available he bought what existed (4760 / 4950 around a 4850 body, about 0.75–0.8× EM) (02:56–03:32) |
| timing | Entered before ~9:11 CT, i.e. near the open (01:19) |
| strike preference | Sell near-the-money premium, not cheap OTM: "eat like a bird, poop like an elephant" is the failure mode; "today I sold a $6 call because that's what I like to sell" (08:24–08:35) |
| take profit | Study: **25% of max profit**, else expire (04:44–04:51). His own: closed part early for "a quick 70–80–90 bucks per contract" (12:18) |
| frequency | "50 trades already this morning... over 100 yesterday" (00:57–01:04) |
| directional overlay | If you pick a direction, pick a strike distance that fits your risk (11:46–11:55) |
| view on 0DTE | "Just like longer-dated options, just faster" (10:50–11:00). On 0DTE the tail risk is **upside** at all-time highs, the reverse of 45 DTE (10:25–10:37, 12:25–12:45) |

## Data shown: audit

| item | what the video gives | assessment |
|---|---|---|
| design | SPX 0DTE put and call verticals **sold at the open**, short strike ATM / $10 / $20 / $30 OTM, long strike $30 further out; closed at 25% of max profit or held to expiry; marked every 10 minutes | a clean mechanical rule set ✅ |
| sample | **10 months** to ~Jan 2024 | ⚠ one regime: a strong rally. Sosnoff says so himself at 05:42 |
| n | not stated (~200 sessions implied) | no t, no CI |
| fills / costs | not stated | ⚠ at $30 wide with 50c–$1 far-OTM credits (08:18–08:23), crossing four bid-asks is a large share of the credit. Our cost sweep killed nine strategies of exactly this small-credit shape (UVIX bear call +11.0% gross / 93% win → −8.8% net) |
| control | none: no unconditional short-premium arm, no random-day or straddle comparison | ❌ |
| ⚠ outcome conditioning | "right" = close > open for puts, and results are then reported **split by right/wrong** | ❌ "right" rows are **definitionally** 100% winners ("you never lost"). The split is not a strategy you can trade; only the "overall" rows are. It's the retracted-exhaustion-fade error in miniature (conditioning on the day's own close) |
| results quoted | puts overall: win rate "mid-90s", "P&L pretty damn strong". Puts when wrong: still high win rate, average P&L ~0, ATM lost. Calls overall: 94% win but **far-OTM average P&L negative**. Calls when wrong: "ugly across the board". Call-side CVaR (worst 5%) worse than put-side. Closer to ATM made up for the losses and "came out more profitable net" | direction matches ours at the one point we can check (ATM beats OTM); the rest is a 10-month bull-market artefact until shown otherwise |

## Claim by claim

| @ | Claim | Our evidence | new vs `data/more_tom` |
|---|---|---|---|
| 02:56–03:32 | **His 0DTE trade: short the ATM straddle, wings at the expected move** | ❌ **Contradicted unfiltered.** SPY 1-day iron fly, real fills on all four legs, 1,942 days (`gex_spy_ironfly_2026-09-21.md`). **1× wings: positive-gamma +6.8% on max risk (t 2.0, FAIL); negative-gamma −12.0% (t −3.7)**, which pools to about **−3% every day** (day-weighted from those two rows, not a separately reported cell). 2× wings: **0.0% every day**, **+5.8% (t 3.4, 14/17 yrs) on positive-gamma days only**, −5.4% (t −3.1) on negative. Fixed ±0.9% wings (~1.34× implied) unfiltered: **−3.79%/trade (t −1.85)**, 32-day losing run. ⚠ Ours enter at the prior close and his near the open (the overnight gap is ~half the day's variance), and SPY rather than SPX. **The gamma filter is the whole edge, and he mentions no filter** | ⭐ new: More Tom's 0DTE clip was policy only |
| 00:57–01:04 | 50 trades this morning, 100 yesterday | **Frequency multiplies an unsigned expectancy.** At 1× EM unfiltered, ours is negative. His brokerage earns on every one of those trades. That's the same cost conflict as OptionsPlay's "a penny or two" (measured 6.5% of mid, TEST_INDEX row 276) | dup (trade often) |
| 04:13–05:24 | Study design; "10-minute data gives the same results as 1-minute" | Plausible for a 25%-target rule. **Not replicable on v3** (EOD only), same limit as the Julia Spina 539-condor review (TEST_INDEX, 2.5/5) | — |
| 05:31–06:11 | Selling 0DTE put spreads every day for 10 months: win rate mid-90s, strong P&L | **Sample, not edge.** Our 1-day SPY 16/5Δ put spread over 2010–2026: **+0.7% all days**; on positive-gamma days +1.9% on risk (t 3.5, 94% win) but **only +0.7% in 2010–17 (t 0.6)**, and it lost to the 2× fly by ~4pp. The 94% win rate matches his. The return doesn't | new |
| 06:43–07:51, 09:34–09:54 | "When wrong" vs "when right" breakdowns | ❌ **Outcome-conditioned, so not evidence.** Splitting by the day's close vs open selects on the result. The only tradeable rows are "overall" | ⭐ new (method) |
| 07:57–08:35 | Far-OTM call spreads lose despite a 94% win rate; "eat like a bird, poop like an elephant"; **"I like to sell the $6 call"** | ✅ **Agrees. The edge is at the money.** SPY 1-day on positive-gamma days: **2× iron fly +5.8% vs 16/5Δ condor +1.8% vs 16/5Δ put spread +1.9%**. "OTM strikes win more often but collect little — the edge is AT the money" (`gex_spy_condor_putspread_2026-09-21.md`). Also the POP ≠ edge result: win rate falls as net ROC rises across credit/width quintiles | ⭐ new: strike preference, stated for 0DTE |
| 10:09–10:37, 12:25–12:45 | On 0DTE at all-time highs the tail is to the **upside**; at 45 DTE it's always the downside | **A sample-period statement, and he says so** ("based on the last 10 months"). Our longer-dated call side is consistently worse: ETF condor call side FAIL (+0.36%/trade, t 0.6), UVXY bear call −7.4% net (t −3.65). **Untested for 1-day call spreads** (our 1-day study didn't run call-side spreads) | new |
| 10:37–10:44 | Little skew in 0DTE | Untested descriptive. Our skew result is at ~30 DTE: a noisier VIX, t 1.44 | new |
| 10:50–11:00 | 0DTE "is just like longer-dated options, just faster" | **Partial.** The premium is strongest at the short end (10d VRP +1.75vp, t 8.93; 30d +0.78, t 2.08), so short tenors are not just faster. They're where the premium is. But at 1 day the premium is **regime-dependent to the point of sign-flipping** (fly +5.8% vs −5.4% by dealer gamma), which has no 45-DTE analogue we've measured | new |
| 11:33–12:07 | Taking the ATM risk "made up for the large losses" and was more profitable net; that's why the straddle/strangle swap works | ✅ Agrees ATM > OTM (above). ⚠ "Works" is unsupported unconditionally: SPY 1-day short straddle every day +5.4% of credit, but its worst day was **−604% of credit**, and the defined-risk version at 1× wings fails | partial dup |

## What I would take

1. ⭐ **His 0DTE trade is our paper trade, minus the part that works.** The live `run_gex_fly_paper.py` fly
   (2× implied-move wings, positive-gamma days only) is Sosnoff's straddle-with-EM-wings with two changes:
   **double the wing** and **add the gamma filter**. Each change is individually load-bearing in our data. That's
   the most concrete Sosnoff ↔ ledger link in any of the four videos.
2. **Sell near the money, not pennies.** It agrees with our 1-day result and with the retired small-credit filler.
3. **Reject the right/wrong breakdown as a method.** Worth citing when any creator reports "win rate when
   directionally correct".

## Not tested, could be

- **At-the-open vs prior-close entry for the 1-day SPY fly.** His entry is near the open; ours includes the
  overnight gap, which carries ~half the variance. Needs intraday option quotes we don't have in v3. The paper
  trade already logs a 0DTE-at-the-open variant as secondary evidence (TEST_INDEX, Live GEX + paper trade row).
  **No new queue item**: let the paper log answer it.
- **1-day SPY call credit spread by gamma sign.** The one side of his study we never ran. Prior: negative in a
  rising tape, noisy otherwise. Low value. **Not queued.**
