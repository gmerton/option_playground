# tastylive — "The Real Reason Why Tom Sosnoff Won't Trade Stock" (2025-07-01, 8:39, 13k views)

_Reviewed 2026-09-23. Studio segment: a research-team slide ("stock returns are static, options are strategic")
read aloud and annotated, with a co-host interjecting ("Yes we have", "Right. Right."). Transcript (auto-captions,
no speaker labels) in this folder._

**Who is speaking.** **Probably Sosnoff, not confirmed from the transcript.** The captions carry no names. The
lead voice speaks in the first person the way Sosnoff does ("we've said that a couple times before in our life",
"I don't think so"). He riffs on a live headline (Trump threatening to deport Musk, which dates the recording to
about 2025-07-01) and refers to "Pete this morning" (Pete Mulmat, a tastylive host). No clip self-identifies him.
Most of the content is the research team's slide text, which he reads and then comments on, so the list of
"rules" below is the house's as much as his.

## Verdict: 2 / 5

The mechanics are right and one line is unusually honest: *"you can set it up so you're right 80% of the time...
doesn't mean you make money"* (05:38). But the headline is contradicted by our data. The claim is that options
beat stock because you can shape the distribution: its skew, tail, width and mean. On our data, **shaping the
distribution does not move its mean.** A short put or put spread earns what stock at the same delta earns, minus
costs, and on the widest test the unstopped stock at the same delta beats the put on both return and tail. He
contradicts himself in the same clip. He says stops and smaller size are "not the definition of reducing risk"
(04:01). In the More Tom clips he says size is the *only* defence against outliers. There is no data anywhere in
the segment.

## His rules, in codable form

| dimension | rule as stated |
|---|---|
| instrument | Options on anything, never the static asset alone. Stocks, futures, spot FX, crypto, real estate and collectibles are all "static" (00:00–01:13) |
| what he looks at | Implied volatility of the underlying, the delta of the options, the legs, DTE, and the correlation between underlyings (02:20–02:40) |
| strike and size | Pick a delta to set the probability ("80% chance of winning" on an OTM put, 06:12) and the commitment ("delta 25 = committing 25% of a share position", 06:50) |
| vol regime | **High IV: collect larger credits. Low IV ("like it is now", July 2025): reduce risk** (05:16–05:35) |
| tail | Choose wings or no wings; "reduce some / mostly all of the tail risk — up to you" (03:14–03:28) |
| management | Change duration, manage early, hedge against the position (04:42–05:00) |
| explicitly rejects | **Stop orders as risk reduction, and cutting size as risk reduction** (04:01–04:15); passive investing (02:47) |

## Data shown

None. The segment is a conceptual slide. There is no sample, no fills and no control.

## Claim by claim

| @ | Claim | Our evidence | new vs `data/more_tom` |
|---|---|---|---|
| 00:00–02:07 | Stocks are "static": the return distribution is fixed by the underlying, near-normal with some skew and positive drift, so the only lever is picking the price | **Mechanically true, and irrelevant to expectancy.** The 30-day distribution of a stock is fixed; a static position in it is still the benchmark every option vehicle must beat, and mostly doesn't (next row) | new framing |
| 02:18–02:40, 08:01 | With options **you choose the skew, the tail, the width and the mean** via IV, delta, legs, DTE and correlation | ❌ **Contradicted on "the mean."** Put credit 30/20Δ vs delta-matched stock: **+$7/contract, t 0.26**, "no edge over its own delta anywhere", and **−$62 (t −2.14) at low IV rank** (TEST_INDEX, Vehicle vs delta-matched stock, 2026-09-22). BCI cash-secured puts, 326 names: stock at the same delta minus costs, **FAIL**. CSP vs stopped stock (2026-09-23, 201,849 trades): the **unstopped stock at the same delta beats the put, +0.49 vs +0.36, worst 1% −16.9 vs −41.0** (exploratory). The only structure that beat its own delta was the call **debit** spread, +$97 (t 2.29), which failed its own bar. You can shape the distribution. You can't choose its mean for free | new |
| 03:14–03:28 | Wings or no wings are a free choice of how much tail to cut | **Partly.** Wing width is not free. On single-name bull puts, the narrowest wing earns about 3pp less net ROC than any wider wing, paired on the same name and date (see the `C6vrj2zu6Hc` notes). Buying far-OTM tail is negative carry: 5Δ same-expiry SPY puts lose −100% on every trade ([WL-5f]) | new |
| 04:01–04:15 | "You can't say a stop order is risk reduction. You can't say reducing size is necessarily risk reduction" | **Mixed, and it contradicts his own More Tom clip `LJl1N4VuJnQ`** ("I don't know another way around outlier risk other than trade size"). Our data: stops on **short premium** are a cost, not a rescue. The straddle −50% stop is INVERTED: 69.8% of stopped trades would have done better held. On stock, a resting 0.5-ADR stop is **crash insurance costing ~0.37pp**, not a chop tax (CSP vs stopped stock). Size is the only non-inverted tail lever we have, and the lever is *exclusion*: A+B grades only +0.29R OOS | ⭐ new: internal contradiction |
| 04:42–05:00 | You can change duration, manage early, hedge | **One form certified, the rest don't.** 21-DTE management on 45/20Δ strangles: paired **+$1.53, t 4.26, sd halved**, but both arms are negative (TEST_INDEX §1, verified at `exit_21dte_2026-09-23.csv`: A −2.55, B −1.02 per share, n 6,558 resolved). Every management rule that conditions on P&L is INVERTED (BE+1R −0.08R; "extended→tighten" −0.19R t −2.8; roll test 69.8% better held) | dup of OptionsPlay 21-DTE |
| 05:16–05:35 | High IV: sell bigger credits. **Low IV: reduce risk** | ✅ **Agrees in direction.** The only certified short-premium bucket is **bearish-high-IV index put sale** (SPY bull put t 6.07, SPX condor t 5.21, one bet). The most frequent low-IV cell, QQQ bullish-low-IV, runs **−4.8% month-weighted (t −0.87)**, and put credit at low IV rank is −$62 (t −2.14). Paid-to-wait: ungated −3.3% net vs IV≥60th pct +5.7% (not certified). ⚠ The own-IV gate fails on QQQ/IWM bull puts (≥80th pct is a mild veto) | dup of More Tom `s9JYik5DV7k` / process #6 |
| 05:38–05:49, 06:12 | "Set your probability to whatever you want... **doesn't mean you make money**"; an OTM put on a stock you like at 80% | ✅ **Agrees, and it is the right caveat.** Across credit/width quintiles, **win rate falls 79.6 → 75.7 while net ROC rises −2.96 → +4.07 (t 3.74)**. POP is priced | dup (More Tom #11 / OptionsPlay) |
| 06:33–07:12 | Pick a delta that is a fraction of the share position; capital-efficient | **True as capital efficiency, not as edge**: same vehicle benchmark as above. The short-put version is the worst arm on risk | new |
| 07:45–07:59 | Platforms make any strategy available: "almost inexcusable not to use it" | Promotional, and the speaker's firm is a broker. Every extra leg is a round trip: our cost model is $0.65/contract/leg/side + 25% of the quoted spread, and the 2026-09-22 cost sweep killed nine strategies that looked good at mid | — |

## What I would take

1. **"Probability is a dial, not an edge."** It's the cleanest statement of the rule our credit/width result proves.
   Use it verbatim.
2. **"Low IV → reduce risk"** agrees with the one certified bucket and the low-IV decertification. It's already
   the book's practice (Tier U token sizing on QQQ bullish-low-IV).
3. **Nothing on "options beat stock."** Our vehicle benchmark says the opposite for every short-premium structure
   we measured.

## Not tested, could be

- **Nothing new is needed.** The one testable claim ("options let you choose a better distribution than stock")
  is already answered by the delta-matched stock benchmark and the CSP-vs-stopped-stock test.
- The stop/size contradiction is a **documentation** item for the doctrine file (`data/tastylive/sosnoff_doctrine.md`,
  rule 19), not a test.
