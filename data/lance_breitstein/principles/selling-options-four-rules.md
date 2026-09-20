# The 4 golden rules for selling options

> **Verdict:** ⭐ **Rule 1 independently lands on a finished repo statistic** — the paid-to-wait
> IV gate (ungated −3.3% net → own-IV ≥60th percentile +5.7% net, 78% win). Rules 2 and 3 are the
> correct risk framing and rule 3's tolerance calibrates to within a factor of ~3 of our measured
> tail on liquid names. ⚠ **Rule 4 is the conflict:** his preferred tenor (same week, a few days
> left) is exactly where our data says costs are **136% of gross** on single names. All four are
> **veto rules, not selection rules** — the video contains no edge claim, only survival claims.
> **Type:** regime gate + sizing + tenor (short premium)
> **Conviction:** 3/5 (4/5 for rule 1, 1/5 for rule 4 as stated) · **Testability:** EOD ⭐⭐ · **Tested?** partial — rules 1 and 4 both have direct repo tests
> **Source:** `eWeGAYvjxh4` — "How to Sell Options Like a Wall Street Trader (My 4 Golden Rules)" (2026-05-09)

⚠ Context worth recording: at [00:00] he says **"selling options has become my favorite trading
strategy."** Every other document in this KB is intraday momentum equities. The trader this KB was
opened to study for *entry precision* says his primary book is now short premium.

---

## 1. Mechanics

- **Instrument / universe:** naked short options — single-name calls and puts, plus index/crypto
  proxies. Both of his worked examples are single names / BTC, not ETFs.
- **Session / timeframe:** swing, days to ~2 weeks.
- **Setup condition — Rule 1, the only *entry* rule of the four:**
  > "Only sell options after volatility has blown out, not in no man's land where we are range
  > bound and volatility is calm." [01:45]
  > "Sell options during times of extreme moves and extreme sentiment. Never, ever sell options
  > during times of complacency. That is by far the most common mistake people make." [03:04]

  Mechanism he gives: the insurance analogy — the best time to write is right *after* the
  catastrophe, when the remaining writers get astronomical rates. "Sky-high implied volatility is
  actually offering you more risk cushion" [02:29].
- **Strike — Rule 2:**
  > "Only sell options at a price you'd actually want to be assigned the underlying… Not, 'I guess
  > I could survive it,' or not, 'I would hope it bounces.' Actually happy and salivating over how
  > good the opportunity would be." [03:18]

  ⭐ **Operational technique:** annotate the **net-of-premium breakeven** on the chart and look at
  what the path to get there would have to be. "If I sell a $100 strike put for $5, I will circle
  on the chart the $95 range and imagine what the move would look like for the stock to get there"
  [03:49].
- **Size — Rule 3:**
  > "Only sell options for the amount of shares you're truly willing to be assigned." [04:14]
  > "I try to always size so that even if the option premium doubled against me and doubled
  > against me again, I would still be okay with it." [06:51]
  > "If you are losing sleep or constantly checking quotes nonstop, you are probably oversized."
  > [07:00]

  = tolerate a loss of roughly **3× the credit received**. Reasons given: delta is non-linear and
  accelerates ("a 1 to 2% move in the stock can even turn into a 30 to 50% or more loss in the
  option very quickly, especially with short-dated contracts" [05:17]); ⚠ **margin requirements can
  be raised mid-trade** (CME, gold/silver, early 2026 — "even if your idea is right longer term,
  you may not survive the path" [06:05]); psychology; and liquidity disappearing at the exit.
- **Tenor — Rule 4:**
  > "Only sell options with expirations within the window you actually want to see the move occur…
  > Most of the options I sell tend to expire the same week, often with only even just a few days
  > left." [07:25]
  > "Your option expiration should always match the window of your thesis. Don't fall for the trap
  > of thinking you want to go further out to collect more time value." [08:08]

  Stated exception: leveraged-ETF decay justifies longer-dated shorts.
- **Directional veto (bonus rule):**
  > "Shorting calls is infinitely more dangerous than selling puts. Because there's no lower bound
  > of zero." [10:29]
- **Closing risk list** [10:50]–[11:33]: never average into a loser; keep normal loss limits; never
  concentrate; assigned margin is higher than expected "especially to the upside";
  ⭐ "**High win rate means nothing if your losers are fatal.**"

### The one worked trade

**TIGR, 2024-10-07** [08:28]–[09:44]. China stimulus melt-up; TIGR had "nearly quadrupled" and
gapped up hard. Stock ~$14, he sold the **2024-10-18 $16 call for almost $2** — breakeven $18,
~29% above spot, ~11 calendar days. He calls it "one of my favorite exhaustion gap technical
patterns" [09:26] and shows the rule-2 breakeven annotation.
**Counter-example: Bitcoin** [09:44] — $80k–$100k through Dec 2025/Jan 2026 is "no man's land";
selling puts into the boredom is the error; the range breaks −$15k, IV explodes, **then** you sell.

## 2. ⚠ The sizing-lever question

Not an entry-location principle, but rule 3 is a sizing rule and it calibrates:

- **Stop distance as % of entry:** no stop. The analogue is **loss tolerance = 3× the credit.**
- **Does he state a stop-out rate?** No. ⭐ **We can supply it.** From the short side of the
  152,995-trade 1-DTE panel (`data/studies/one_day_straddle/logs/short_side_2026-09-19.log`),
  share of trades losing **more than 2× premium**:

| liquidity cell | n | loss > 2× prem | p1 (on prem) | worst |
|---|---|---|---|---|
| bid/ask <5% | 10,768 | **2.0%** | −240% | −776% |
| 5–10% | 20,084 | 2.5% | −269% | −914% |
| 10–20% | 37,224 | 2.8% | −272% | −1,519% |
| **>20%** | 84,919 | **12.7%** | −1,254% | **−17,410%** |

  On **liquid** names his 3× tolerance is breached on roughly 1 trade in 100–200 — a sane rule of
  thumb — and the worst observed case (**−914%**, SMCI 2024-01-19, a 35.9% move against a 3.6%
  implied) is still **3× past his tolerance**. On **illiquid** names it is breached one trade in
  eight. **⚠ His rule is right and under-specified: it needs a liquidity condition and he does
  not attach one**, even though he names the mechanism at [06:20] ("liquidity can disappear, and
  you're going to be forced into closing the position at worst prices").
- **What would settle it:** already settled for 1-DTE; the same tail cut at 7–30 DTE off v3 would
  generalize it.

## 3. Claimed edge & evidence

**One trade, no numbers.** TIGR is a single winning example with the credit quoted and neither the
fill nor the spread nor the outcome stated. The BTC example is a *hypothetical* error, not a trade
of his. No win rate, no P&L, no trade count, no base rate anywhere in 11:55.

⚠ **Course marketing: light but present.** [09:26] "those that follow my trading course will
recognize this as one of my favorite exhaustion gap technical patterns" — the pattern that
*selects* the trade is name-dropped and withheld, while the four rules that are given are all
vetoes. The selection logic is again behind the paywall; the risk management is free.
Cross-promo to his prior options video at [01:04]. No hard CTA.

## 4. ⚠ Prop-infrastructure dependency

- **Depends on:** margin capacity and the ability to absorb assignment. Rule 2 and rule 3 both
  presuppose an account that can *take the stock* — "the margin utilized once you get assigned can
  be far higher than you expect, especially to the upside" [11:12]. Naked calls in a retail account
  require the highest approval tier and, on assignment, a **short stock position requiring
  locates** — which is the one genuinely prop-dependent piece and he does not flag it.
- **Retail-viable as stated?** **Puts yes, calls partly.** The put side is fully retail-viable
  (cash-secured or margin). The naked call side as he trades it (TIGR, wanting to be assigned
  short) assumes borrow availability on a quadrupled small-cap squeeze candidate — precisely the
  name where retail borrow disappears.

## 5. Decay risk

**Low for rules 1–3** — they are structural statements about the shape of the payoff and the
behaviour of vol, not flow niches. **Rule 1's specific magnitude does decay/vary**: our own test
shows the IV gate works on single names and ETFs but **inverts on QQQ**, so the *level* of the
edge is instrument- and era-conditional even where the direction holds. The TIGR-style
exhaustion-gap call sale in Chinese small caps is a 2024 flow condition, not a law.

## 6. Objective assessment

- **All four rules are vetoes.** None identifies a trade; each rejects one. That means the video
  contains **no edge claim at all** — it is a survival framework bolted onto a selection process
  that is never shown. Honest, but it means the rules cannot be "tested" for profitability in the
  usual sense; only the gate (rule 1) and the tenor (rule 4) can.
- **Rule 1 is stated as universal and is not.** Two anecdotes, zero base rates, and our own test
  shows the gate inverts on QQQ.
- **⚠⚠ No bid/ask, no slippage, no commission in 11:55 on short premium.** Third video running
  (see `U9UZ2U6bozQ` and `sxjsqauWE9E`). He treats liquidity as a stress phenomenon, never as a
  standing cost. Our cost model turns +2.6% gross into +1.1% net in the best decile and −42.5%
  gross into −89.5% net in the worst.
- **He never reconciles this video with `U9UZ2U6bozQ`.** There he wants to be **long** premium
  into an exhaustion gap; here he **sells** calls into one (TIGR). The reconciliation is rule 1
  itself — long *before* the expansion, short *after* — but he states neither the tension nor the
  resolution, and it is the entire difference between the two signs.

## 7. What's genuinely sound

- **⭐ Rule 1 is the single most-corroborated claim in this KB** (see §8). It is also the one rule
  in the options-education space that most sellers get backwards, and he leads with it.
- **⭐ Rule 2 is the correct ontology of a short put** and it destroys the "income" pitch — which
  he says outright at [01:04]. A short put *is* a levered long in the stock; the only coherent
  reason to sell one is that you want the stock at that price. Our BCI test proved exactly that
  the hard way.
- **The breakeven-annotation habit** [03:49] is a cheap, copyable technique with no downside and
  it forces the path question rather than the probability question.
- **⭐ Margin expansion as a distinct path risk** [05:28] is a genuine gap in this repo's cost
  model (see §8) — and it bites precisely in the high-IV regime rule 1 tells you to sell into.
  Rules 1 and 3 are in tension for that reason and he does not notice.
- **"High win rate means nothing if your losers are fatal"** [11:22] is the short-premium version
  of the repo's own finding that the straddle's P&L is 99.9% in the top 0.1% of trades — the same
  distributional point from the other side of the trade.

## 8. Overlap / conflict with the rest of the repo

### ⭐⭐ Rule 1 — corroborated, with a magnitude

The **paid-to-wait put-spread study** (7 years, real quotes):

| rule | net |
|---|---|
| generic, ungated | **−3.3%** |
| gated on own-IV ≥ 60th percentile | **+5.7%, 78% win** |
| SPY 10-DTE pilot | +1.16%/trade net · ⚠ **VIX < 20 is NEGATIVE** |

"Never, ever sell options during times of complacency" and "VIX<20 is negative" are the same
sentence. Also consistent: the **BCI covered-call test** (TraderLion KB, 2026-09-17, 1/5) found
selling **through** earnings earned *more* than avoiding them — rule 1 applied to an event instead
of a regime. And the **VRP panel**: the 10-day premium is real and large (**+1.75 vol points,
t 8.93, 17/17 years** on ETFs; **+4.13 vol points, t 8.74** on single names), and the gates do
sort it — the faced premium falls 2.29 → 0.79 vol points as the gates tighten, i.e. the richness
is concentrated where he says it is.

⚠ **But the gate does not port.** The same paid-to-wait study found the own-IV gate **fails on
QQQ, where ≥80th percentile is a VETO, not an edge**. Repo version of rule 1, stricter and better:
*test the IV gate per instrument; never assume it transfers.*

### ⚠⚠ Rule 4 — the direct conflict

His preferred tenor is where our data says the premium is uncollectable:

- **Short-dated single-name premium selling at 10 DTE is NET NEGATIVE — costs = 136% of gross.**
  **Liquidity, not premium, is the gate**; the tradeable set shrinks to **SPY + NVDA/AMZN/AAPL/V**.
  (The 30-DTE version is positive but is likely *direction*, since no 30-day premium exists in the
  VRP panel — beta check outstanding.)
- At 1 DTE, selling the ATM straddle nets **+1.1% of premium in the tightest decile, −1.1% at
  5–10%, −6.3% at 10–20%, −89.5% above 20%**; **−51.3% across all 152,995 trades**. Per-trade
  Sharpe on liquid single names: **−0.004**. ETFs +3.8% net (t 2.1) vs single names −0.7% (t −0.5).
  **Gross is positive and net is not, because the spread is the trade.**

**His TIGR example is the worst cell in that table**: an 11-day option on a $14 Chinese
micro-broker that had just quadrupled. He quotes the credit and never the spread he crossed.

⭐ **Synthesis:** rule 4 is right about *thesis alignment* and wrong about *net*. Short-dated is
simultaneously where his conviction is sharpest and where the spread tax is proportionally
largest. Only one of those two is measurable in advance. **Keep rule 4 only with a liquidity gate
bolted on** — which, combined with rule 1, is close to the repo's existing confirmed book (SPX
condors, QQQ/SPY bull puts).

### ✅ Rule 2 — the BCI finding, arrived at from the other end

BCI (TraderLion KB, 2026-09-17): weekly/monthly single-name short puts = **holding the stock at
the same delta, minus costs**; BCI's filters added nothing. If that is what a short put *is*, the
only coherent selling rule is rule 2. He gets the framing right without the data.

### ⚠ Margin expansion — a real gap he found in our cost model

[05:28], the CME gold/silver hikes of early 2026. Every backtest here sizes off a static margin
assumption; `net/margin` exists as a column in the short-straddle log but the denominator never
moves. **Unmodelled, and it bites in exactly the regime rule 1 selects for.**

### Conflicts with other KB documents

- ⚠ **Rule 3 (very conservative, uniform) vs
  [`stops-and-sizing.md`](stops-and-sizing.md) and [`risk-framework-longform.md`](risk-framework-longform.md)**
  (risk varies **10×** by A/B/C/D grade, $10k B → $100k A). He applies a flat conservatism to
  options and a 10× conviction spread to equities. The **size-lever study** (2026-09-18) backs the
  options treatment over the equity one: the lever that worked out of sample was **exclusion**
  (A+B only, +0.29R OOS vs 0.00 flat), **not** a 10× risk spread (+0.08R with more drawdown).
- ✅ **Rule 1 vs [`bollinger-bands.md`](bollinger-bands.md) and
  [`no-mans-land-and-process.md`](no-mans-land-and-process.md)**: "no man's land" is the *same
  term* he uses for contracting-volatility equities. In both books contraction = stand aside.
  Fourth independent statement against the Carter Squeeze, now in a different asset class.
- ⚠ **`U9UZ2U6bozQ`** — opposite sign on the same pattern; see §6.

### Testable extraction, ranked

1. ⭐⭐ **Rule 1 × liquidity, per instrument.** Re-run the own-IV percentile gate across the
   tradeable set (SPY/QQQ/IWM + the ~5 liquid mega-caps) with the house cost model, and record
   *per instrument* whether the gate helps, does nothing, or inverts (QQQ already inverts). This
   is the cheapest high-value test in the batch and it settles his only universal claim.
2. ⭐ **Rule 3's tolerance at 7–30 DTE.** Extend the `loss > 2× premium` tail cut beyond 1 DTE,
   split by spread decile. Gives a defensible sizing constant instead of a rule of thumb.
3. **Rule 4 head-to-head:** same-week vs 30-day short premium on the *same* names with the same
   IV gate, net of costs. Our 10-DTE and 30-DTE results were produced under different setups.
4. **The bonus rule:** put-side vs call-side tail asymmetry off v3. Our 1-DTE worst-10 list is
   suggestive (SMCI +35.9%, NVAX +98.7% — both up moves) but was never cut by side.
