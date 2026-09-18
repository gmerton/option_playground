# Covered Calls & Cash-Secured Puts on Momentum Stocks — Alan Ellman (Blue Collar Investor)

> **Verdict:** A clear, honest-sounding intro to option *income* selling, but "what actually works" is not
> demonstrated. The two strategies are **one payoff**: an in-the-money covered call is a short put at the same
> strike (put-call parity), so the "protection paid for by the option buyer" is just a lower-delta position.
> Evidence is **4 hand-picked winners, 0 losers**, with 5-day returns annualized ×52 (266%). Two of the four
> examples don't match the tape (APH, RMBS below). The parts that decide the outcome, the stock list and the
> 27 chapters of exits, are behind the paywall. **Tested 2026-09-17 (§9):** mechanised, his public method earns
> what holding the stock at the same delta earns, minus costs. His filters add nothing, and selling *through*
> earnings earned more on average, so the earnings rule shapes risk, not return. Liquidity/fills decide the sign.
> **Type:** income / short premium, weekly and 2–4-week · **Instrument:** US single stocks (+ ETFs)
> **Conviction:** 1/5 · **Risk:** 6/10 · **Tested?** **yes** (2026-09-17). His public method, mechanised, does not
> beat holding the stock at the same delta, and his filters add nothing. See §9.
> **Source:** [Dr. Ellman Has Traded Options for 30 Years, Here's What Actually Works](https://www.youtube.com/watch?v=J-I6iLGjp1Q),
> TraderLion, 2026-09-06, 1:37:45. [transcript](../videos/interviews/2026-09-06_J-I6iLGjp1Q/transcript.txt)

---

## 1. Who, and what's being sold

- **Dr. Alan Ellman**, former dentist (40 years), trading options since ~1995; founder of **The Blue Collar
  Investor (BCI)**, 20 years old in January; nine books (*Cashing In on Covered Calls*, 2007, onward), 700+
  articles, 600+ videos, expert witness in covered-call suitability cases, writes for AAII and OIC.
- Host: Richard Moglen (TraderLion).

**Commercial context:**
- The stock selection shown is a screenshot of **BCI's 9-page weekly premium-member report** [36:32].
- The **Trade Management Calculator** (2,400-formula spreadsheet) is a member product [48:08].
- Trade management/exits are deferred to his book and to a **January all-day TraderLion workshop** with
  Dr. Eric Wish and Les Masonson, pitched with a sign-up link [24:11], [27:05], [94:04].
- A **Deepvue sponsor read** runs mid-episode [20:09] ("DFW" in the captions).

## 2. Mechanics

**Strategies.** Covered calls (buy stock, sell a call) and cash-secured puts (sell an out-of-the-money put, set
aside strike minus premium). Weekly (Mon–Fri, "no weekend risk") and 2–4-week expirations. He sells 125–150
contracts a month [26:21]. Historically ~¾ covered calls. Lately he favors puts as more defensive [88:17].

**Stock selection (BCI list)** [36:45]–[45:44], [89:14]:
1. **Fundamentals first:** sales and earnings growth, **industry rank A**, **mean analyst rating** (1–5, his
   picks 1.42–1.69), **on-balance volume** arrow up (he accepted a down arrow on RMBS [80:31]).
2. **Implied volatility 30–60% absolute** = "sweet spot" [38:48]; open interest adequate; weeklies available.
3. **Technicals, all four bullish** (bold on the list):
   - 20-day EMA above a rising 100-day EMA, price at or above the 20 EMA
   - MACD histogram > 0
   - Stochastic oscillator **> 80 read as bullish, not overbought**; below 80 is a "slight red flag"
   - Volume holding, no negative divergence
   He prefers stocks **already trending** over fresh breakouts [44:31]. Each example was beating the S&P
   over 1–3 months.
4. **Common sense:** **never sell an option with earnings before expiry** ("the most important rule")
   [14:43]; watch ex-dividend dates; diversify by industry; cash allocation.

**Strike selection** [69:29]:
- Pre-state a target: **2–4% a month time value** (0.5–1% a week) on stocks. ETFs yield less. His mother's
  account uses 1–3%.
- **Out of the money** in normal/bull markets or for elite charts: premium plus room for the stock to rise.
- **In the money** when defensive or the chart is mixed. **~⅔ defensive in 2026** [66:41].
- **Ladder strikes** within one position (e.g. 1 ITM + 1 OTM on 200 shares) [33:06].
- Puts: out of the money only, deeper when defensive.

**Management:** "over 20 exit strategies", "27 chapters" — **not shown** [28:27], [49:31].

## 3. Claimed edge & returns

- "I've been beating the market… for 30 years" [02:09], [96:58]. "Beating the market significantly so far in
  2026" [65:42]. **No figures, no denominator, no drawdown.**
- ChatGPT named him the best covered-call teacher [22:41]. Social proof, not evidence.
- The four trades (all winners):

| trade | dates | structure | his result | our data |
|---|---|---|---|---|
| MRVL | 2026-04-20 → 04-24 | 200 sh, 1× 133C (ITM) @13.35, 1× 157.5C (OTM) @1.13 | **5.13% / 5 days = "266% annualized"** | ✓ closed 164.31. Stock +11–13% that week, so the position earned under half of holding |
| APH | 2026-06-29 → 07-17 | 200 sh @163.17, 2× 150C (ITM) @15.60 | 1.49% / 19 days = 28.6% annualized; "closed 157.60, 10.03 above break-even, didn't break a sweat" | ⚠ **pre-split** (2-for-1 on 2026-09-03): expiry close **151.20**, day's low **146.04**, *below* his 147.57 break-even. Result still stands (above the 150 strike) but the story doesn't |
| EQT | 2026-03-09 → 03-13 | 4× 59P @0.25 | 0.43% / 5 days = 31% annualized | ✓ closed 64.37 |
| RMBS | 2025-09-22 → 10-17 | 3× 90P @1.30 | 1.47% / 26 days = 20.5% annualized; "didn't break a sweat" | ⚠ stock fell 10% and traded **89.57, under the 90 strike**, before recovering to 96.26 |

## 4. Objective assessment

1. **The ITM covered call is a short put.** By put-call parity, long stock + short 133 call ≈ cash + short
   133 put. MRVL's "$12.35 intrinsic value = huge protection, paid for by the option buyer" is the intrinsic
   value of **his own shares** handed back. Nobody pays for insurance. He sold a 133 put for ~$1 (0.75% for 5
   days, 8.5% out of the money). The ITM covered call and the defensive CSP are the **same trade**, and so is
   the risk: a **capped gain and the full stock loss below break-even**.
2. **"Guaranteed 1.62% as long as it doesn't drop more than 8.07%"** [62:20] is true and is the whole problem.
   The payoff is short-tail: many small, near-certain gains; occasional large losses (earnings avoided, but
   not macro gaps, FOMC afternoons or guidance cuts). Four winners cannot show the tail. His own origin story
   (Taser, earnings hits) is that tail.
3. **Annualizing ×52 is marketing arithmetic.** 5.13% in 5 days on one hand-picked week → 266% says nothing
   about a year of 52 trades that includes the losers, idle cash, and weeks the list is empty.
4. **Winners only, with contradictions.** 4 of 4 winners. Two of the four happy narratives are contradicted by
   the price data (APH broke through break-even on expiry day; RMBS traded through the put strike).
5. **Upside truncation is the hidden cost on momentum names.** He selects stocks up 70% in three months, then
   caps them. MRVL: +11% stock week, 5.1% for him. On the trending cohort he picks, the forgone right tail is the
   price of the "income".
6. **The differentiator is paywalled.** Industry rank and the curated list are BCI products; mean analyst
   rating isn't in our data. The exits that decide loss size aren't shown.
7. **Absolute IV 30–60% ≠ rich premium.** It selects volatile names, not overpriced options. Our own-IV
   percentile work ([paid-to-wait](../../studies/paid_to_wait_study.md)) is the relevant measure, and on the
   index a high IV rank is a warning, not an edge.
8. **"Beating the market for 30 years"** is unsupported. As general background, systematic buy-write
   benchmarks (e.g. Cboe's BXM) are usually cited as lower-volatility, not higher-return, than the index over
   long bull runs. Any claim to beat the index needs numbers.

## 5. What's genuinely sound

- **No short premium through earnings**, as a *risk* rule. It trims the worst weeks (0.30Δ weekly worst 1%:
  −18% clear vs −22% through earnings). ⚠ The test found it **costs return**: selling through earnings earned more
  on average (§9).
- **Liquidity checks and working the mid** [60:26]. Our short-dated selling study says liquidity is *the*
  gate: on single names at 10 DTE, costs ate 136% of the gross premium.
- **Pre-stating a return target to pick the strike** is a sensible, IV-adaptive way to set moneyness.
- **Selling puts on stocks in strong uptrends, reading stochastic > 80 as strength.** Our RSI study (section F)
  found that on RSI ≥ 70 names, straddles are cheaper *and* the stock moves even less than that, with a slight
  upward drift; the put buyer loses ~20 pp. That is the **put seller's winning side**, on exactly the cohort his
  filter picks. A hypothesis for sellers, not a result: that data is 7-DTE long straddles with buyer costs.
- Honest framing where it counts: "low risk, not no risk" [26:49]; paper trade 3–4 months first [96:32].

## 6. Testability

| component | status |
|---|---|
| EMA 20 > rising EMA 100, price ≥ EMA 20, MACD hist > 0, stochastic > 80, volume | **EOD-testable now** (daily bars) |
| absolute IV 30–60%, earnings not before expiry, weeklies, open interest | **testable** (`options_daily_v3` bid/ask 2010 → 2026-02; earnings table) |
| strike at 0.5–1%/week or 2–4%/month time value, ITM/OTM | **testable** (chain) |
| industry rank A, mean analyst rating, the curated BCI list | **proprietary / not in our data** |
| 20+ exit strategies | **not disclosed** |

## 7. Recommended test (run 2026-09-17, see §9)

**"BCI-filter cash-secured puts vs holding the stock at the same delta."** Pool names, weekly Fridays 2018 →
2026-02:
- **Filter:** the four public technical rules + IV 30–60% + no earnings before expiry.
- **Trade:** sell the put at the strike paying ~0.75%/week (and a ~2%/month 3–4-week variant), hold to expiry,
  settle at intrinsic from the underlying.
- **Sizing:** cash-secured.
- **Benchmarks:** (a) the same put with no filter; (b) **stock held at the put's entry delta**, the beta check
  our [short-dated selling study](../../studies/vrp_shortdte_names_study.md) says every short-put result needs;
  (c) buy-and-hold of the filtered names.
- **Report:** mean, median, worst week, crash weeks (2020-03, 2022, 2025-04), and share of return lost to the
  capped right tail.
- **Costs:** entry at mid + ¼ spread.
- The ITM covered call does not need its own run (parity).
- **Pass bar:** beats (b) after costs, both halves.

## 8. Overlap with the existing book

- **Bull put spread (ETF, 45 DTE, 50% take, no stop)** survives at +5.7%/trade but is **substantially long
  beta**: the mirror bear call loses. A CSP is the same short put *without the wing*, so more tail.
- **Short-dated single-name selling** ([study](../../studies/vrp_shortdte_names_study.md)): at 10 DTE, net
  **negative** after costs except NVDA/AMZN/AAPL/V/SPY. The 30-DTE profit is probably direction, not premium.
  His weekly single-name sales sit in the cost-negative zone unless the names are that liquid. Holding to
  expiry halves the round-trip cost, which is untested.
- **Paid-to-wait put spreads:** own-IV ≥ 60th percentile gate +5.7% net; ungated −3.3% net.
- **RSI conditioning study** (section F): the overbought/extended cohort is where long vol loses and short
  puts *should* win.
- **Journal context:** Gabe's own book already sells a lot of put spreads (9/16: TWST, DELL, MSFT, USO, DINO,
  ANET). BCI's filters are close to the house entry stack, so the marginal new idea is **naked CSP instead of
  a spread**, which our evidence doesn't favor on single names.

## 9. Test result (2026-09-17)

Full study: [`data/studies/bci_csp_study_2026-09-17.md`](../../studies/bci_csp_study_2026-09-17.md). 326 pool
names, every Friday 2018 → 2026-02, real bid/ask, hold to expiry, settled at intrinsic.

- **The put ≈ the stock at the same delta, minus costs.** Weekly at his 0.75%/wk strike: +0.03%/trade vs +0.07% for
  a delta-matched stock position (excess t −1.7). Monthly: +0.26% vs +0.45% (t −1.4). At perfect mid fills the
  excess is about zero; at bid it is clearly negative (t −4.2).
- **His filters add nothing:** BCI full within-week t −0.5 (weekly), −1.4 (monthly). A weekly book compounds at
  **−1.4%/yr** with his filters (max DD −34%, worst week −29%) vs +1.2% unfiltered and +10.5% for SPY.
- **Earnings rule:** selling *through* earnings earned more (0.30Δ weekly within-week t +3.6), not beyond direction
  (t +1.3), and the tail is somewhat worse. A risk preference, not a return edge.
- **RSI ≥ 70 seller-side hypothesis:** right sign, t ≤ 1.8. Not confirmed.
- Verdict lowered 2/5 → **1/5**. Untested: the curated list, analyst rating and industry rank, and his exit rules.
