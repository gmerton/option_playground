# 45-Day Put Selling Strategy | Tom Sosnoff's Proven Trade

**Video:** `0f2kr2iOXzg` · **Channel:** Freedom Income Options (Casey Stubbs) · **Watched:** 2026-09-26 ·
**Published:** 2025-10-29 · 15:24. The strategy explainer behind the 3-month test (`JMso3dDSg5A`, 2/5).

> **1.5/5 · one test worth queuing (not new to the KB: its "Gap" line).** The rule set is complete and the sizing
> warning is the best advice in the video. Everything else is a one-year, winners-only sales pitch: a "96% win rate"
> that is mostly the 50% take inflating win rate (not EV), "$28,500 a year per contract", and "recoup losses
> instantly" when the VIX is up. The testable question it leaves open is the one the KB already names: an always-on
> naked index put at 45 DTE / 50% take / 21 DTE, at real fills, has never been run.

## Rules
- [00:01] Sosnoff's "one trade": sell a **45-DTE, 12-delta put on /ES**, take profit at **50%**. (The 3-month-test
  video used a 10Δ; the description and captions differ across the channel. Read the transcript.)
- [02:12] Steps: ES → 45-DTE expiry → 12Δ → sell the put → 50% profit order.
- [06:27] **Close at 21 DTE regardless of profit or loss** ("protects from big losses... protects from assignment").
- [08:33] ⚠ **Sizing**: use ~20–25% of capital, up to 50% "when the VIX goes up"; never go all in. /MES (1/10 size,
  ~$1,200 buying power) for small accounts.
- [11:42] Live example: ES 6,400 put (spot ~6,939), Dec-19 expiry, credit $1,735, buying power ~$12,000.

## Claims
- [00:01] "Just with one contract, one a week, is $28,500 in profit... over the last year a 96% win rate." One year
  (2024-10 → 2025-10), a bull tape, source not shown.
- [09:36] "12–14% in a 45-day period" on buying power, "you can do it again and again".
- [13:50] "If you let it expire... 88%. If you take profit early, it bumps it... to 96%."
- [07:30] After a loss, the next credit is bigger because the VIX is up, so "we could recoup our losses almost
  instantly".

## Critique
- **Win rate ≠ edge.** Taking profits at 50% raises the win rate by construction and cuts the average win; the
  tastylive doctrine review (rule 14) and our own tests treat POP as priced, not an edge. The 88 → 96% jump is that
  mechanism, not extra expectancy.
- **One bull year.** No 2018-02, 2020-03 or 2022 in the sample. For a naked put those are the whole question.
- **"Recoup losses instantly"** is martingale framing: the bigger post-crash credit comes with bigger risk, and
  "up to 50% of capital when the VIX goes up" is the doubling-down case.
- Return on buying power ignores that SPAN margin expands in a selloff (queued Breitstein test 5: margin expansion
  in the cost model).

## Against the ledger
- **21-DTE close** (the rule's risk manager): tested on 45-DTE 20Δ strangles, 14,367 trades: close at 21 − hold
  **−$0.52/share, t −2.42 → NULL on return, leaning INVERTED; a risk reducer only** (sd $9.33 vs $17.09, worst −$291
  vs −$617). It does what he says on risk and costs return.
- **Certified cell:** the SPY put sale is certified only in the **bearish-high-IV** regime (t 6.07; SPX condor
  t 5.21 = one bet). The always-on version is untested.
- The paid-to-wait/IV-gate and VRP results say the put's premium is real at 10 days, weaker at 30 (t 2.08).
- ⭐ **Queued test (TEST_INDEX §10):** SPY as the /ES proxy (same index, penny-wide quotes, v3 has bid/ask
  2010 → 2026-03): every Friday sell the ~45-DTE put nearest −0.12Δ; 50% take at the real closing cost, else close at
  21 DTE at the ask (arm B: hold to expiry at intrinsic). Primary = always-on net P&L per trade (month-clustered t),
  compared with the same trade restricted to the certified bearish-high-IV days, i.e. does the always-on version add
  anything beyond the regime that already certifies? Report crash weeks explicitly (2018-02, 2020-02/03, 2022),
  settle at intrinsic, and the pull window must cover the largest move (house rule). Local if the SPY put chains are
  cached (`reference_spy_caches_2026_09`), else one Athena pull.
