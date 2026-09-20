# How to Sell Options Like a Wall Street Trader (My 4 Golden Rules)

**Video:** `eWeGAYvjxh4` · **Type:** talks · **Watched:** 2026-09-19 · 11:55, solo talk

Written up as [`principles/selling-options-four-rules.md`](../../../principles/selling-options-four-rules.md).

## Raw notes

Opens with a claim that matters for the whole KB: **"Selling options has become my favorite
trading strategy"** [00:00]. Every other video in this KB is intraday momentum equities. This is
the first time he names a *different* book as his primary one — worth noting that the trader
whose edge we opened this KB to study says his favourite strategy is now short premium.

Framing [00:54]–[01:45]: the insurance analogy. High win rate lulls sellers into false security →
they get progressively more aggressive → "and sure enough, boom, the catastrophe finally strikes."
He credits a prior options video with the "influencers wrongfully pitch selling options as income"
argument.

Four rules, then two worked examples, then a bonus rule and a closing risk list.

- **Rule 1** [01:45]–[03:18] — sell only after vol has blown out; never in "no man's land."
  California wildfires 2025 analogy: the best time to write insurance is right *after* the
  catastrophe, when the remaining writers get astronomical rates. "Sky-high implied volatility is
  actually offering you more risk cushion" [02:29].
- **Rule 2** [03:18]–[04:14] — sell only at a strike you'd genuinely want to be assigned.
  ⭐ Concrete technique: **annotate the net-of-premium breakeven on the chart** and look at what
  the move to get there would have to look like. $100 put sold for $5 → circle $95.
- **Rule 3** [04:14]–[07:25] — size only for shares you'd truly take. This is the longest section
  and the best-argued. Non-linearity: "a 1 to 2% move in the stock can even turn into a 30 to 50%
  or more loss in the option very quickly, especially with short-dated contracts" [05:17].
  ⚠ **Margin expansion** as a distinct risk [05:28]: CME repeatedly raised requirements during the
  gold/silver moves of early 2026, forcing traders out. "Even if your idea is right longer term,
  you may not survive the path." Then the psychology (freeze / hope / panic), then liquidity
  ("there's often no clean exit… spreads, liquidity can disappear").
  ⭐ **The sizing rule of thumb** at [06:51], verbatim below. Plus the sleep test [07:00].
- **Rule 4** [07:25]–[08:18] — expiry must match the window of the thesis. "Most of the options I
  sell tend to expire the same week, often with only even just a few days left" [07:37]. Exception
  he names: leveraged-ETF decay justifies going further out. Explicit warning against reaching for
  duration to collect more premium.
- **Example A — TIGR, 2024-10-07** [08:18]–[09:44]. China stimulus melt-up, TIGR (Chinese broker)
  had "nearly quadrupled" and gapped up hard. Stock at $14; he sold the **2024-10-18 $16 call for
  almost $2**. Cushion to the $18 breakeven = ~29% above spot, ~11 calendar days. Names it as "one
  of my favorite exhaustion gap technical patterns" [09:26] and shows the rule-2 breakeven
  annotation on the chart.
- **Example B — Bitcoin, Dec 2025–Jan 2026** [09:44]–[10:29]. $80k–$100k range = no man's land;
  bored traders sell puts into the range; range breaks, −$15k; *then* IV explodes and *then* you
  sell the puts. A clean statement of rule 1 as a negative and a positive.
- **Bonus rule** [10:29] — shorting calls is "infinitely more dangerous" than selling puts, no
  upper bound. Cites silver and the quantum-computing names. Same for shorting stock.
- **Closing risk list** [10:50]–[11:33] — don't average into a loser; keep your normal loss
  limits; don't concentrate; assigned margin is higher than you expect, "especially to the
  upside"; ⭐ "High win rate means nothing if your losers are fatal."

## Named setups appearing here

- [x] **The 4 golden rules for selling naked premium** — promoted to
      [`principles/selling-options-four-rules.md`](../../../principles/selling-options-four-rules.md).
      Rules 1 and 4 are mechanical (an IV-state gate and a tenor rule) and both collide with
      finished repo studies. Rules 2 and 3 are risk-acceptance rules, not edge rules.
- [ ] **Exhaustion gap → sell the call into it** — the *short-premium expression* of the same
      exhaustion-gap pattern that appears as an ORB fade in
      [`opening-range-break.md`](../../../principles/opening-range-break.md) and as a 0DTE *long*
      in `U9UZ2U6bozQ`. ⭐ Note that in this video he wants to be **short** premium into the
      exhaustion gap and in `U9UZ2U6bozQ` he wants to be **long** premium into it. He never
      reconciles the two; the reconciliation is presumably "long if you expect the expansion, short
      after it has happened," which is just rule 1 again.

## Claims to verify

- [ ] ⭐⭐ **Rule 1: selling is better after IV has blown out than in calm ranges.** ✅ **Already
      tested here and it holds** — see reactions.
- [ ] ⭐⭐ **Rule 4: "most of the options I sell expire the same week, often with only a few days
      left."** ⚠ **Already tested here and it fails on single names** — see reactions.
- [ ] **The sizing tolerance: "even if the option premium doubled against me and doubled against
      me again, I would still be okay."** ⭐ Directly calibratable against the short-straddle tail
      distribution already on disk. Done below — his rule of thumb is roughly right for *liquid*
      names and catastrophically insufficient for illiquid ones.
- [ ] **"Shorting calls is infinitely more dangerous than selling puts."** Checkable, and our
      1-DTE short tail is one-sided enough to be suggestive (worst cases SMCI +35.9%, NVAX +98.7%
      — both up moves). Not measured directly; a put-side vs call-side tail comparison off v3 is
      cheap.
- [ ] **"A 1 to 2% move in the stock can turn into a 30 to 50% or more loss in the option,
      especially with short-dated contracts"** [05:17]. Plausible and easy to confirm from the
      same 153k-row panel.

## Quotable rules

> "Rule number one, only sell options after volatility has blown out, not in no man's land where
> we are range bound and volatility is calm." [01:45]

> "Sell options during times of extreme moves and extreme sentiment. Never, ever sell options
> during times of complacency. That is by far the most common mistake people make." [03:04]

> "Rule number two, only sell options at a price you'd actually want to be assigned the
> underlying… Not, 'I guess I could survive it,' or not, 'I would hope it bounces.' Actually happy
> and salivating over how good the opportunity would be." [03:18]

> "I graph out on the chart where the stock would be net of the premium should I be assigned… if I
> sell a $100 strike put for $5, I will circle on the chart the $95 range and imagine what the move
> would look like for the stock to get there." [03:49]

> "A bad trade will not kill you. Being too big when you're wrong will." [04:28]

> "I try to always size so that even if the option premium doubled against me and doubled against
> me again, I would still be okay with it." [06:51]

> "If you are losing sleep or constantly checking quotes nonstop, you are probably oversized."
> [07:00]

> "Rule number four, only sell options with expirations within the window you actually want to see
> the move occur… your option expiration should always match the window of your thesis. Don't fall
> for the trap of thinking you want to go further out to collect more time value." [07:25]

> "Shorting calls is infinitely more dangerous than selling puts. Because there's no lower bound
> of zero." [10:29]

> "High win rate means nothing if your losers are fatal." [11:22]

## Reactions / conflicts

### ⭐⭐ Rule 1 independently corroborates a finished repo statistic

This is the second time in this KB a practitioner has confirmed a repo result rather than
contradicted one (the first was ORB vs the gap study). The paid-to-wait put-spread study, seven
years of real quotes, found:

- the **generic** rule (sell the spread on any signal): **−3.3% net**
- the same rule gated on **own-IV ≥ 60th percentile**: **+5.7% net, 78% win**
- the SPY 10-DTE pilot: **+1.16%/trade net**, and ⚠ **VIX < 20 is NEGATIVE**

That is rule 1, measured. "Never, ever sell options during times of complacency" is the same
sentence as "VIX<20 is negative" and "the generic ungated rule is −3.3%." Independent arrival at
a number we already own. Also consistent: the BCI covered-call test (TraderLion KB, 2026-09-17)
found selling **through** earnings earned *more* than avoiding earnings — i.e. sell when the
premium is genuinely rich, which is rule 1 applied to an event rather than to a regime.

### ⚠ But rule 1 does NOT generalize across instruments, and he states it as universal

The same paid-to-wait study found the own-IV gate **does not transfer to QQQ**, where ≥80th
percentile is a **veto, not an edge**. So "sell after vol blows out" is an instrument-conditional
rule that he states as a law of nature, with two anecdotes (TIGR, Bitcoin) as support. The repo's
version is stricter and better: *test the gate per instrument; do not assume it ports.*

### ⚠⚠ Rule 4 is the direct conflict — his preferred tenor is the one our data says is net negative

He sells "the same week, often with only even just a few days left." The repo's stage-2 result on
exactly that trade:

- **Short-dated single-name premium selling at 10 DTE is NET NEGATIVE — costs = 136% of gross.**
  The gross premium is real; the bid/ask eats more than all of it.
- **Liquidity, not premium, is the gate.** The tradeable set shrinks to SPY plus roughly
  NVDA / AMZN / AAPL / V.
- The 10-day variance risk premium itself is real and large (+1.75 vol points, t 8.93, 17/17
  years; +4.13 vol points on single names, t 8.74) — **the premium exists and you still cannot
  collect it on a single name.**

And at the extreme short end, from `data/studies/one_day_straddle/logs/short_side_2026-09-19.log`
(the short side of the same 152,995-trade panel, settled at the close, house cost model):

| cut | n | gross/prem | **net/prem** | win% | loss>2x prem |
|---|---|---|---|---|---|
| ALL | 152,995 | −23.4% | **−51.3%** (t −13.5) | 48% | 8.2% |
| bid/ask <5% | 10,768 | +2.6% | **+1.1%** (t +0.6) | 59% | 2.0% |
| 5–10% | 20,084 | +2.2% | −1.1% | 59% | 2.5% |
| 10–20% | 37,224 | −0.9% | −6.3% (t −4.0) | 56% | 2.8% |
| >20% | 84,919 | −42.5% | **−89.5%** (t −17.1) | 40% | 12.7% |

Selling the 1-DTE ATM straddle nets **+1% of premium on the most liquid decile and −89.5% on the
widest**, per-trade Sharpe −0.004 on liquid single names. **Gross is positive and net is not,
because the spread is the whole trade.** His TIGR example is an 11-day option on a $14 Chinese
micro-broker that had just quadrupled — the single widest-spread cell imaginable — and he quotes
the credit ("almost $2") without ever quoting what he had to cross to get it.

⭐ **The synthesis is clean and it is his rule 1 plus our liquidity gate:** the tenor rule is not
wrong about *thesis alignment*, it is wrong about *net*. Short-dated is where his conviction is
sharpest **and** where the spread tax is proportionally largest. Those two pull in opposite
directions and only the spread is measurable in advance.

### ⭐ Rule 3, calibrated against our tail — his rule of thumb is about right for liquid names

"Premium doubled and doubled again" = tolerating a loss of ~3× the credit received. Against the
short 1-DTE straddle distribution:

- **liquid (bid/ask <10%)**: `loss > 2× premium` on **2.0–2.5%** of trades (~1 in 40–50); p1 is
  −240% to −270% of premium; **worst observed −914%** (SMCI 2024-01-19, a 35.9% move against a
  3.6% implied).
- **illiquid (bid/ask >20%)**: `loss > 2× premium` on **12.7%** of trades, worst **−17,410%**.

So on liquid names his tolerance is breached roughly 1 time in 100–200, which is a *sane* rule of
thumb — and the worst case is still **3× past his tolerance**. On illiquid names it is breached
one trade in eight. **His rule is correct and under-specified: it needs a liquidity condition
attached, and he does not attach one.** Worth noting he does name the mechanism ("liquidity can
disappear, and you're going to be forced into closing the position at worst prices", [06:20]) —
he just never converts it into a gate.

### ✅ Rule 2 agrees with the BCI result, arrived at from the other direction

The BCI covered-call/CSP test (TraderLion KB, 2026-09-17, 1/5) found weekly and monthly
single-name short puts are **equivalent to holding the stock at the same delta, minus costs**, and
that BCI's screening filters added nothing. If short puts *are* stock-minus-costs, then the only
coherent reason to sell them is that you want the stock — which is precisely rule 2. He arrives at
the correct framing without the data. ⭐ **And it is the correct framing that kills the "income"
pitch**: he says so himself at [01:04] ("options influencers wrongfully pitch selling options as a
way of making income").

### ⚠ Margin expansion is a risk the repo's cost model does not carry at all

[05:28], the CME gold/silver margin hikes of early 2026. Every backtest in this repo sizes off a
static margin assumption. `net/margin` appears in the short-straddle log as a column but the
denominator never moves. **This is a genuine gap he identified that we have not modelled**, and it
bites precisely in the high-IV regime his rule 1 tells you to sell into. Rules 1 and 3 are in
tension for exactly this reason and he does not notice.

### ⚠ The same omission, third video running

No bid/ask, no slippage, no commission anywhere in 11:55 on a video about selling premium. He
gestures at liquidity twice as a *stress* phenomenon and never as a *cost*. Our cost model
(IBKR $0.65/contract + 25% of the bid/ask per traded side) turns +2.6% gross into +1.1% net in the
best decile and −42.5% gross into −89.5% net in the worst.

### House rules that apply

- "Precision over recall": rule 1 + a liquidity gate is a *much* smaller tradeable set than he
  implies, and that is the correct direction.
- The four rules are all **veto rules**, not selection rules. None of them identifies a trade; all
  of them reject one. That is the right shape for a short-premium book and worth saying out loud —
  it means the video contains no edge claim at all, only survival claims.

---

**Rating: 3.5/5** — the best options content reviewed in any KB so far, and the highest rating
given to a video that contains zero data. Rule 1 independently lands on a finished repo statistic
(paid-to-wait: ungated −3.3% → IV≥60th-pct +5.7%; VIX<20 negative), rule 2 is the correct framing
of what a short put actually is (which our BCI test proved the hard way), rule 3 is a sizing
tolerance that calibrates to within a factor of ~3 of our measured tail on liquid names, and he
identifies margin expansion as a path risk we do not model. Marked down for: no numbers, no
bid/ask, rule 1 asserted as universal when our own test shows it inverts on QQQ, and rule 4
pointing squarely at the tenor where our data says costs are 136% of gross on single names.
The export is **rules 1+2+3 kept, rule 4 kept only with a liquidity gate bolted on.**

**Course-marketing content present: yes, but light** — one soft plug at [09:26] ("those that
follow my trading course will recognize this as one of my favorite exhaustion gap technical
patterns"), plus cross-promo to his prior options video at [01:04] and the closing subscribe ask.
No hard pitch, no "link in description" course CTA.
