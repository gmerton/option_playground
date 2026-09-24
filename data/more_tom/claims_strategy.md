# More Tom — claim ledger, STRATEGY / MECHANICS half

Channel: **More Tom** (`@MoreTom-w2t`), 496 subs, 26 videos uploaded 2026-09-01 → 2026-09-22.
Speaker is **Tom Sosnoff** (tastytrade / thinkorswim co-founder, 40+ yrs CBOE market maker) with rotating
co-hosts; every video is a clip from a long-form Q&A or interview, so the channel is tastytrade doctrine
delivered conversationally rather than a structured course. Sign-off is identical on all 13: a funnel to
"my new portfolio / career optimization tools / financial forecasting / prediction engine".

This file covers the **13 strategy/mechanics videos** only. A parallel review covers the process/psychology
half; the session owner merges and sets the final score.

**My half-score: 2.5 / 5.** Reasoning at the bottom.

Transcripts: `data/more_tom/videos/shorts/<date>_<id>/transcript.txt` (+ `meta.json`). All 13 pulled clean,
no failures.

---

## The ledger — one row per video

| # | video | core claim (one sentence) | his mechanism | verdict vs OUR evidence |
|---|---|---|---|---|
| 1 | **Stop Trusting Spread Scanners. Do This Instead.** `pZm-y3oxzIQ` (3:43, 09-22) | A spread scanner is worthless unless you first restrict the universe to high option volume / top-liquidity underlyings — you cannot trade spreads in illiquid names at all. | Illiquid chains have no OI or volume, so every "efficient" spread the scanner surfaces is untradeable; the scan wastes your time and the fills take the edge. | ⭐ **AGREES — strongest agreement in this half, and it is our own hardest-won result.** 10-DTE single-name premium selling: **FAIL, net negative, costs = 136% of gross, "liquidity is the gate", tradeable set = SPY + NVDA/AMZN/AAPL/V** (`vrp_shortdte_names_study.md`). Credit/width rescue 2026-09-22: 13 of 15 screener spreads stay negative even in their high-credit half — "credit/width discriminates within a LIQUID universe, not within a bad one" (`cw_rescue_2026-09-22.csv`). UVIX bear call was +11.0%/trade and 93% win gross → **−8.8% net** because the round trip costs about the whole $0.25 credit. |
| 2 | **Don't Roll a Losing Put Until You Do This** `qo9466KD_u8` (3:15, 09-21) | Do **not** roll a losing put spread out in time and wider (a $3 spread became a $9 spread) — instead sell the corresponding call spread above your short put strike, which needs no extra capital and reduces basis. | "Don't throw good money after bad": rolling multiplies max loss to defend a thesis that is already wrong; the call spread collects premium inside margin you have already posted. | **AGREES on don't-roll · UNTESTED (negative prior) on the call-spread patch · CONTRADICTED on the wheel** (co-host's defence at the end). See cross-ref §5 — this is the row that matters most to the owner, who rolls spreads across expiries. |
| 3 | **What Nobody Tells You About Implied Volatility** `wR5M8Z6qhcI` (3:23, 09-21) | Implied vol is structurally above realized — realized is higher only ~15% of the time — and that spread is the whole reason to sell premium; tails happen more often than models say but playing for them is a stupid way to trade. | "The future cannot be more certain than the past", so IV is priced at a premium to fair value and you sell it hoping to stay inside the range. | **AGREES on direction · CONTRADICTED on magnitude, tenor and the "15%".** VRP panel measures `iv − realized` directly: 10d **+1.75 vol pts, t_NW 8.93, 17/17 years**, all 10 tickers clear Bonferroni — but **30d +0.78 (t 2.08) and 90d +0.84 (t 1.30) clear nothing, "not one IV-percentile bucket, not one VIX regime, not one year."** Positive share is **75% at 10d, 71% at 30d/90d** → realized wins 25–29% of the time, not 15%. See §2. |
| 4 | **Do This Every Time IV Rank Spikes** `s9JYik5DV7k` (5:33, 09-04) | When IV rank spikes (crude 20 → 130) sell options, go out to roughly **one** standard deviation (two SD is "too cheap"), and cover when IVR falls back to 30–50; you can't call the vol peak and don't need to. | Vol is fenced at 100 and mean-reverts; it rises ~10% of the time, falls ~20%, sits quiet 70%. "Fear is the only friend you've got" — the spike is the opportunity window. | **PARTIALLY AGREES — the gate is real, the structure and the numbers are not.** Paid-to-wait, 7 yrs of real quotes: the generic rule is **−3.3% net**, an **IV ≥ 60th own-percentile gate gives +5.7% net / 78% win** (gated − ungated +16pp, t 2.29, 37 months, n 129 → NOT CERTIFIED after Šidák). Against him: the own-IV gate **FAILS on QQQ/IWM bull puts** (≥80th pct is a mild VETO). His 10/20/70 vol-cycle split is sourced to nothing. See §3. |
| 5 | **The Only Trading Signals You Need to Watch** `7oqOCrL7TJk` (5:13, 09-02) | The only inputs he uses are the **level of implied vol** (which selects the strategy), plus occasional price extremes and **skew extremes**; open interest carries no information in liquid names; trend following doesn't exist and he fades trends for a living. | Different IV levels call for different structures; skew shows how much upside/downside the market is pricing; "multiple days in a row" is a random run, not a trend. | **CONTRADICTED on both named signals · AGREES on open interest · CONTRADICTED on "no such thing as a trend."** IV as a vehicle chooser tested at real fills 2026-09-22: right sign, **no significance — DiD +15.4pp bullish, t 0.68**, halves +38.3/+8.3. Skew as a signal: **NULL** (see §4). OI: we use OI + bid/ask% as a *tradability* gate and never as a signal — agrees. Trend: see §7. |
| 6 | **The Real Reason Puts Cost More Than Calls** `DviI9IZkfTU` (4:43, 09-21) | Skew did not exist before 1987 — calls and puts were priced the same — and it appeared because the crash proved downside **velocity** was unpriced; today's put premium is the price of that velocity. | War story: in Oct 1987 there was no way to price the move, and the real fear was counterparty/clearing failure (Continental Bank, First Options), not the tape. | **AGREES on mechanism · CONTRADICTED as a tradeable signal.** The history is correct and the "velocity of risk" framing is the right one. But we tested skew directly and it is **a noisier VIX** — see §4. We compute 25Δ skew in `credit_spread_finder` as an *indicator only*; there is no tested claim behind it, and the one test we ran said there shouldn't be. |
| 7 | **Stop Buying Short-Term Calls. Do This Instead.** `1itwTWKGVyM` (4:17, 09-05) | Buying short-dated calls is gambling; premium selling is the professional side — and he has not bought premium in 26 years, because once you're retail you're paying someone else's offer. | As a market maker he had no choice of side; as retail, buying on the offer removed his edge, so he flipped to selling — but only in **high vol**, since he is measurably worse as a *directional* premium seller than as a *volatility* one. | **CONTRADICTED on the headline · AGREES on the cost argument and on his own self-assessment.** Our two surviving option strategies are a **long 7-DTE straddle** (buying short-dated premium, +6.7%/trade unstopped at realistic fills, SUPPORTED t 3.7) and a bull put, and only as a PAIR. The straddle's gate is the **inverse of his rule** — buy when the name's own IV percentile is **≤20–30** (mid +9.19 at ≤20 vs +5.05 ungated, clean monotone dose-response). His directional/vol split matches our finding that the put credit spread has **no edge over its own delta (+$7/contract, t 0.26)**. ⭐ His paying-the-offer point is exactly what killed 9 strategies in our 2026-09-22 cost sweep — full credit. |
| 8 | **How Much Theta You REALLY Need in Your Portfolio** `Co1-RL9AKp8` (3:12, 09-22) | Portfolio theta should run **0.1–0.2% of net liq** (up to 0.3 on a small account); 0.5% is far too much gamma risk and impossible to sustain. Secondary: ATR ≈ the 16-delta option, so read expected move off deltas instead. | "All the research we've done over the years"; above 0.2 you are chasing your tail on gamma. | **UNTESTABLE as stated · CONTRADICTED in premise.** No P&L claim, no research cited — it is a risk-budget convention. The premise fails for us: after the 2026-09-22 multiple-testing correction exactly **ONE** short-premium bucket certifies (bearish-high-IV index put sale, **SPY t 6.07 + SPX t 5.21 = the same stress episodes = one bet**); everything else is Tier U, **0 of 13** non-regime screener spreads certify, UVXY **net −3.46% (t −2.65)**, UVIX −8.8%, UUP straddle t −0.31. A daily theta target makes you hold premium you have no measured edge in. ATR ≈ 16Δ **AGREES** and matches `ema_strike_breach_study`: breach odds depend only on cushion in ADR (2 ADR ≈ 21%, 3 ≈ 13%). |
| 9 | **Stop Guessing Risk. Use Two Standard Deviations.** `9jSWuibhGTw` (1:22, 09-02) | He views every position inside a ±2 SD envelope because beyond 2 SD nothing is quantifiable — and broker **buying-power reduction already approximates a 2 SD move**, so BPR is a usable risk read. | Reg-T margin on short premium is sized to carry roughly a 2 SD move, so the number is already on your screen. | **AGREES mechanically · CONTRADICTED as a sizing philosophy.** BPR ≈ 2 SD is a genuinely useful shortcut. But it contradicts his own video #3 (tails happen far more often than the model) — and >2 SD is where short-premium P&L is actually decided: our SPY 1-day naked straddle's worst day was **−604% of credit**. Our sizing is not a probability envelope at all: `risk ÷ (entry − stop)` with the stop at ~1 ADR, and the size-lever study found the lever is **EXCLUSION (A+B grades only, +0.29R OOS)**, not a graded risk spread (+0.08R, more drawdown), with the stop-distance cell failing outright as a grade. See §8. |
| 10 | **Everyone Is Wrong About Zero-DTE Options** `FWo8H2s60UY` (5:21, 09-03) | 0DTE has produced **no systemic risk** — the market is at record highs — and its value is the liquidity it brought to US exchanges, not what any single trader extracts; regulators sunsetting weekly expiries (India) make things worse. | Volume attracted to listed US exchanges keeps the US the deepest liquidity pool "ten times over", which funds the innovation; partial product bans protect nobody. | **UNTESTABLE (market-structure / policy) — and it contains no trading claim at all.** Worth recording what our 0DTE evidence says anyway, because it is the opposite shape to anything he offers: see §1. ⚠ The one 0DTE-family structure that passed for us is conditioned on **dealer gamma**, a variable he never mentions in 13 videos. |
| 11 | **What Nobody Tells You About the Cash in Your Portfolio** `FZfndYs_nXc` (4:33, 09-22) | Hold a real cash sleeve in T-bills / BIL / SGOV, stay **non-correlated by product AND by strategy**, don't over-allocate, **under-hedge** — but always "reduce basis" by selling premium against a loser. | Non-correlation cuts risk "about 30%", rotating strategies another "10, 20 or 30%"; hedging costs more than it returns, so hedge 25–50 of every 100 deltas at most. | **AGREES qualitatively · UNTESTED on every number.** "Diversify by strategy" is literally our book: the straddle + bull put **PAIR, corr −0.25, blend clears t 2.5 where neither leg does alone (1.8 / 1.2)**. "Don't over-hedge" matches the cheap-convexity overlay **NULL** — carry −20…−34%/month on premium, ΔSharpe −0.05…0.00, and the **2022 must-pass FAILS**; the straddle is already the bear leg (worth ~13pp of drawdown), book corr with SPY only 0.22. The 30% / 10-20-30% figures have no source. "Reduce basis" = video #2's patch → §5. |
| 12 | **How to Build a Modern Portfolio When Rates Are High** `YF9BKb-aCOU` (6:15, 09-22) | **30 / 30 / 40** — 30% trading, 30% long-term, 40% cash & treasury equivalents at current rates — plus **selective market timing**: he will not buy index funds at all-time highs. | At 2% rates his cash sleeve would be zero; at today's rates cash pays you to wait. Public markets have "already realized" the move, so he is putting money into private companies instead. | **UNTESTABLE as an allocation · CONTRADICTED in its one testable form.** "Don't buy at all-time highs" runs against our breakout book (buys names **within 15% of the high**) and against the crash-leader veto (**never buy deep drawdowns in a healthy tape, median −20%/252d**). Every regime-timing rule we have tested has failed: FTD as a regime switch FAILS, trailing-30d rules from August fail 2019–26, HMM/regime-switching CONTRADICTED 5×. Half the runtime is Pokémon and baseball cards. |
| 13 | **What Everyone Gets Wrong About At-the-Money on Futures** `BZTNRODp7qk` (3:42, 09-22) | With spot 6,000 and the future 6,100, ATM is **6,100** — the option settles into the future, so the future is the underlying, not cash. Second half: platforms deliberately hide far-dated futures series because only the front few are liquid. | The option's deliverable defines the underlying; showing untradeable strikes gets retail filled $10 away on an unbreakable trade. | **AGREES (definitional) · UNTESTABLE as an edge.** Correct and uncontroversial; zero strategy content for us (no futures in the book). ⚠ Our own analogue of this error is live and expensive: **raw v3 strikes vs split-ADJUSTED price panels, median 3.1% mismatch** — the same "which underlying are you pricing against" trap, which produced a fake −38% on bull puts before the parity-spot fix. The liquidity half is video #1 again. |

---

## Cross-references — the depth

### §1. 0DTE — we have results; he has a policy opinion

`FWo8H2s60UY` makes no tradeable claim, so there is nothing to falsify. But the channel's silence on
*how* to trade 0DTE is worth contrasting with what we actually measured:

- **Adhikary archetype C (0DTE fade): FAILED** on the 1-min cache 2026-09-22 — and its headline
  "17 of 17, median +7%" was **RETRACTED as outcome-selected** (the detector required the trade day to
  close in its bottom 20% and red, then shorted that same day). The honest re-run: 608 trades, 131 dates,
  **−0.26%/day, 41% win, t −0.59**, edge vs a random minute in the same name-day **−0.02 (t −0.15)**.
- **Theta Profits' 0DTE long strangle: −26%/trade** at an EOD floor.
- ⭐ The **only** 0DTE-family structure that passed for us is conditioned on a variable Tom never mentions:
  the **SPY 1-day 2× iron fly on positive dealer-gamma days — +5.8% on max risk, t 3.4, both halves,
  61% win, 14/17 years**. The same fly on *every* day is **0.0%**, and on negative-gamma days it is
  **−5.4% (t −3.1)**. The gamma filter *is* the entire edge. Live paper trade started 2026-09-22.

**Takeaway for the merge:** "0DTE is fine / 0DTE is gambling" is the wrong axis. Our data says 0DTE pays
only when the dealer-gamma regime is right, and nothing in this channel gets near that.

### §2. IV > RV — right sign, wrong tenor, wrong frequency, and the premium is not the trade

`wR5M8Z6qhcI` is his central thesis and it is the one place we can mark him precisely.

| tenor | mean premium (vol pts) | t_NW | clears Bonferroni t 3.29 | share positive |
|---|---|---|---|---|
| 10d | **+1.75** | **8.93** | **yes** (17/17 years, all 10 tickers) | 75% |
| 30d | +0.78 | 2.08 | no | 71% |
| 90d | +0.84 | 1.30 | no | 71% |

Three corrections:

1. **His "15%" is wrong.** Realized beats implied **25% of the time at 10 days and 29% at 30 and 90 days**.
   He is understating how often the seller is on the wrong side by roughly a factor of two.
2. **The premium dies past 10 days.** At 30d and 90d "there is no cell anywhere in the report that clears
   the hurdle — not one IV-percentile bucket, not one VIX regime, not one year." He sells 30–45 DTE
   structures. Our panel says the thing he is harvesting is not measurably there at his tenor.
3. **His reasoning is wrong even where the conclusion is right.** "The future cannot be more certain than
   the past" is not why IV > RV — it is a risk premium paid to a seller, which is exactly why it can be
   (and in our data, at 30d+, is) arbitrarily small. Single-name at his horizon: 10-DTE selling is
   **net negative, costs = 136% of gross**.

Where he is right and unusual: **"you're not going to sell at fair value, you're going to sell at a premium
and hope you stay inside the range"** is the correct mental model, and he volunteers that the tails are
under-modelled rather than hiding it.

### §3. IV rank spikes — our closest analogue, and it half-agrees

`s9JYik5DV7k` ("crude IVR 20 → 130, sell it") maps onto **paid-to-wait**, the only study we have where an
IV gate is the whole edge (7 years, real quotes, 1,548 spreads, our cost model):

- generic rule: **−3.3% net** (+3.2% gross — the credit is 23% of width and two legs cost ~12% of it)
- **IV ≥ 60th own-percentile gate: +5.7% net, 78% win**, positive in every regime state except up/B+
- gated − ungated **+16pp, t 2.29** over 37 months — ⚠ **NOT CERTIFIED** after the 2026-09-22 Šidák charge
- by year: 2019 +15%, 2020 +13%, **2021 −17%, 2022 −19%**, 2026 −45% on 46 events

And our one certified bucket has the same shape he describes: **bearish-high-IV index put sale** after a
selloff. So the instinct is right where it is right.

Two places the data pushes back:
- The own-IV gate **FAILS on QQQ/IWM bull puts** — high own-IV is a mild **VETO** (≥80th pct), not a green
  light. High IV is not uniformly a sell.
- His **1 SD vs 2 SD** strike rule is untested as stated, but our nearest measurements point his way:
  breach odds depend only on cushion in ADR (2 ADR ≈ 21%, 3 ADR ≈ 13%), and the cross-sectional
  credit/width bull put — keep only the top quintile by credit ÷ width — runs **+6.52% net ROC, 78% win,
  t 2.40** vs +2.66 for all names and −1.06 for the bottom quintile. ⚠ It still loses to delta-matched
  stock by **2.43pp**, i.e. picking the rich strike does not stop the put spread from being stock exposure
  with the upside cut off.

⚠ **He never prices a fill, anywhere in 13 videos.** He describes a naked crude strangle (short the 140
call / 65 put) with no cost, no size, no stop and undefined risk. Our nearest naked leg, UVXY's 0.40Δ put,
was +4.2% net but **t 1.82 and below the bar before its 140-cell sweep charge**.

### §4. Skew — the mechanism is right, the signal is NULL

He offers skew twice: as history (`DviI9IZkfTU`, "no skew before '87, it prices velocity of risk") and as
one of the two inputs he watches (`7oqOCrL7TJk`, "I look for extreme situations in skew").

We had only the indicator — 25Δ skew computed in `credit_spread_finder` — until **2026-09-22**, when we ran
it as a signal (`run_skew_signal.py`, pre-registered, 25Δ put−call IV at ~30 DTE, 1,796 SPY sessions
2018-11 → 2026-02, percentile vs trailing 252d):

- forward 21d by skew quintile, **Q5−Q1 +1.72%, NW t 1.44** (bar was t 3); 10d +0.85 (1.07); 5d +0.49 (1.16)
- forward realised vol Q5−Q1 +8.2pp (t 2.06) — but halves **+15.7 / +1.0**
- in a joint regression **skew adds nothing beyond the VIX level**: return t 1.23; vol t −1.22 while
  vix_pct t **+6.54** (R² 0.215)

**Verdict: skew is a noisier VIX.** The GEX regime result is the same idea done properly — negative dealer
gamma buys **+8% realised vol beyond VIX, t 7.7, both halves**. Separately, `momentum_skew_vertical_study`
found the skewness premium is measurable (~15pp/unit move) but **the realised P&L does not pay**.

So: keep his §6 mechanism as the explanation for why puts cost more. Do not act on "extreme skew".

### §5. Rolling a losing put — ⭐ the row the owner should read

Three separable claims in `qo9466KD_u8`:

**(a) "Don't roll out and wider" — AGREES in direction only; the measurement below is ADJACENT, not direct.** ⚠ *(corrected 2026-09-24: that 69.8% is the LONG 7-DTE straddle's −50% stop (`straddle_stop_path_2026-09-20.md`), not a short-premium roll — rolling a losing short put/strangle out and wider is UNTESTED here)*
Our 2026-09-22 test of "roll at −50% if it requalifies" split it into a stop half and a re-entry half:
the **stop is a cost** (−3.84pp on the book, **−9.51pp on the breach cohort, 69.8% of stopped trades were
better held**) and the **re-entry is NULL** (+4.8% after a ≥50% loser, n 879, 198 dates, **t 1.55**, vs
+3.8% with no prior trade). The written verdict was literally *"don't roll; let it expire and re-buy if it
requalifies."* Different structure, same conclusion: **rolling to defend a loser is a cost, not a repair.**
His "$3 spread became a $9 spread" is the cleanest one-line statement of why.

**(b) "Sell the corresponding call spread above instead" — UNTESTED, with a negative prior.**
No test on file. But every call-side premium result we have is negative:
- ETF condor call side: **FAIL — "nothing on the call side", +0.36%/trade, t 0.6**
- UVXY bear call 0.50/0.40: **−7.4% net, t −3.65, 1 of 9 years positive** (costs $20/contract on a $158 max loss)
- UVIX bear call: **−8.8% net**, 93% win gross → 46% win net

⚠ And note the shape of his argument: *"it doesn't require any additional capital"* is a **margin**
argument, not an **edge** argument. It adds a second round trip on a small credit to a position that is
already wrong. That is exactly the failure mode our cost sweep keeps finding.
→ **Queued as test candidate #1 below** — it is cheap and it is live for the owner.

**(c) The wheel (co-host, closing 40s) — CONTRADICTED.**
"Some of my better trades have been the wheel… typically stocks below $40." BCI CSP study, **326 names,
8 years**: cash-secured puts and covered calls are **stock at the same delta minus costs**; filters add
nothing; selling *through* earnings earned more. Independently reproduced 2026-09-22: put credit 30/20Δ has
**no edge over its own delta anywhere (+$7/contract, t 0.26)** and is significantly **worse at low IV rank
(−$62, t −2.14)**.

Tom's own answer to the co-host is the sharper one: *"That's what everybody says until they get assigned —
that is the option trader's paradox."*

### §6. Theta / short-premium sizing — the number answers a question our data says not to ask

`Co1-RL9AKp8` prescribes 0.1–0.2% of net liq in daily theta. Read against the **2026-09-22 multiple-testing
correction** (BH-FDR + Holm + |t| ≥ 3 over M = 125 research questions, best-of-k charged with Šidák):

- **Exactly one** short-premium bucket certifies: **bearish-high-IV index put sale — SPY bull put t 6.07,
  SPX condor t 5.21 — and those are the same stress episodes, so it is ONE bet, not two.**
- QQQ bearish-high-IV t 3.53 fails on its 54-cell sweep; SPX bullish-high-IV+200MA t 2.26 fails;
  QQQ bullish-high-IV t 1.04; **QQQ bullish-low-IV — the most frequent cell, entered live 9/8 — is
  −4.8% month-weighted, t −0.87.**
- **0 of 13** remaining non-regime screener spreads certify. Net negative: ASHR −5.1%, XOP −3.1%,
  SQQQ −2.3%, TMF −1.7%.
- The bull put only survives **as half of the PAIR** with the long straddle (blend t 2.5; the pair itself is
  NOT CERTIFIED).

A portfolio theta target is a *budget*, and a budget assumes there is somewhere to spend it. On our
evidence there is one place, it is index-level, it is regime-conditioned, and it is small. **Running theta
at 0.1–0.2% of net liq would require manufacturing short premium in cells we have already priced as
negative.** Mark this UNTESTABLE-as-stated but flag it as the single most dangerous number in the channel,
because it is concrete, memorable, and implies a book size.

### §7. Signals, scanners and "trend following doesn't exist"

**Scanners/signals (`7oqOCrL7TJk` + `pZm-y3oxzIQ`).** He reduces the whole search to: liquid universe first,
IV level second, nothing else. Our Stage A result is the same shape from the other direction —
**11,227 intraday alerts, every arm −0.10 to −0.13R, and a random later minute in the same name beats the
trigger on every arm.** Re-scored with honest controls: every arm within **±0.03R of both controls**.
Regime-conditioned alerts, 2026-09-22: **NULL** (edge vs control within ±0.07R every month). So "your
scanner is not the edge, your universe is" **AGREES** with the most expensive negative result in the repo.
He gets there by instinct; we got there by 11,227 trades.

**Open interest — AGREES.** "No advantage to OI in liquid underlyings; only useful to check whether anyone
is trading an illiquid name." That is exactly how we use it: OI + bid/ask% is the **second universe gate**
in the top-down pipeline, a tradability condition, never a signal. Compare the queued EP9M diagnostic,
where an absolute-volume floor turned out to be **59.2% a size proxy** rather than an event filter.

**"There's no such thing as a trend" — CONTRADICTED, and he has it exactly backwards by arena.**
- Single-name momentum: our precision-tier breakout is **WEAK but positive — t 3.3, honest +0.4R**, and the
  **universe carries the return** (universe test: selection +0.56 to +1.79 per arm, trigger edge ≈ 0).
- Single-name fading — *his* stated business — is what our data kills: bouncy-ball short **−0.11 to −0.34R
  vs control +0.34 to +0.48**; Breitstein capitulation scorecard **FAIL on both sides**, score 5+ the worst
  bucket; Tito exhaustion fade **−0.26%/day with its 17/17 retracted**; counter-trend long −0.15…−0.33R.
  Our reversion section is **0 for 5 on single names**.
- **Index** reversion — what he actually trades — is our one certified bucket.

He is right about his own arena and wrong about the one he dismisses, and he asserts both with equal
confidence and zero evidence ("I think that's just actually a statistical exactly what's supposed to happen").

### §8. Two standard deviations vs how we actually size

`9jSWuibhGTw` is 82 seconds and contains one useful fact (**BPR ≈ a 2 SD move**, true for Reg-T short
premium and a legitimate screen-level shortcut) wrapped in a philosophy that does not survive contact with
our sizing work:

- We size from **`risk ÷ (entry − stop)`** with the stop at ~**1 ADR** — a *structural* distance, not a
  probability envelope. And we quote it two ways: `stop/ADR` (under ~0.5 → widen and cut size) and the
  execution mode. ⚠ **Corrected 2026-09-23:** this line previously paired the 1-ADR level with "judged on
  the CLOSE, not intraday", which is the wrong combination. The **1-ADR disaster stop RESTS intraday**
  (its job is the crash; it fires 4–6% of days); the **close-judged** rule belongs to the **tight**
  session-low stop. Canonical: `data/studies/stop_definitions.md`.
- The **size lever is EXCLUSION**: trading A+B grades only = **+0.29R OOS** vs flat 0.00; scaling risk by
  grade = **+0.08R with more drawdown**. ⚠ And the 2026-09-22 t-run found "A+B only" **IS** the precision
  tier re-counted (A+B OOS R = precision-only R = +0.286; A+B minus C = +0.083R, **t 0.57**).
- The **stop-distance cell fails as a grade** outright.

A 2 SD envelope tells you how much a position can move. It tells you nothing about **which trades to skip**,
which is the only sizing lever that measured positive for us. And his own §2 video says the tail is
under-modelled — the >2 SD region he declares unquantifiable is where the naked-premium P&L is decided
(SPY 1-day naked straddle worst day: **−604% of credit**).

### §9. ⚠ Costs — the channel-wide omission

Per the standing rule, this must be stated plainly: **across 13 videos there is not one fill, one bid/ask,
one commission, one slippage figure or one net-of-cost return.** Every structure he describes is quoted at
the idea level. He *does* make the cost argument once, correctly and memorably (`1itwTWKGVyM`: he stopped
buying premium because as retail he was "buying it on the offer" and the edge wasn't there) — which makes
the omission everywhere else harder to excuse, not easier.

Our 2026-09-22 cost sweep killed **nine** strategies that looked good at mid. The two most relevant to his
doctrine: **UVIX bear call +11.0%/trade and 93% win at mid → −8.8% and 46% win at real fills**, and
**UVXY combined +5.60% (t 3.60) gross → −3.46% (t −2.65) net, 1 of 9 years positive.** Both are "sell
premium in high IV" trades of exactly the kind this channel recommends. Anything in this ledger marked
AGREES should be read as agreeing *about direction*, never *about return*.

---

## Worth queueing

1. ⭐ **The "reduce basis" adjustment — does selling the call spread above a losing put spread beat doing
   nothing?** (`qo9466KD_u8`). Pre-register: on the paid-to-wait event set (real v3 bid/ask, house cost
   model), when a 30/15Δ put spread is ≥50% underwater, arms = (a) hold to expiry, (b) sell the
   corresponding call spread at/above the short put strike, (c) close and re-enter, (d) roll out and wider
   (his straw man). ~30 lines on the existing harness. **Prior: LOW** — call-side premium is 0-for-3 in our
   tests and this adds a round trip to a position that is already wrong — but it is **live for the owner**,
   who rolls spreads across expiries, and a clean null is worth having in writing. Likely yield: a
   MECHANISM/REFRAME (margin ≠ edge), not an edge.

2. **1 SD vs 2 SD short strike on the ONE certified bucket** (`s9JYik5DV7k`: "two standard deviations is too
   cheap"). We already have the pointer — credit/width top quintile +6.52% net ROC (t 2.40), and breach
   odds sorting only on ADR cushion — so this is a strike sweep on a structure we already trade rather than
   a new idea. ⚠ It is a **best-of-k charge on an already-certified cell**: pre-register the strike grid
   and Šidák it, or it will manufacture a false improvement on the one thing that survived.

3. ❗ **Data gap, not a queue item: we have never tested futures options.** His actual book is crude/gold/
   silver strangles, where the liquidity objection that sinks our single-name selling does **not** apply.
   Our whole VRP panel is equities + GLD/TLT. This means his central claim is **UNTESTED in the arena he
   trades it**, and we should say so rather than transfer the single-name null onto it. Do **not** fund
   futures data for this — just stop treating "10-DTE single-name selling fails" as a refutation of him.

**Explicitly declined** (settled; do not re-test on a creator's say-so): skew as a directional or timing
signal (NULL, 2026-09-22); IV rank as a vehicle chooser (NULL, same day); the wheel (BCI CSP FAIL);
rolling out and wider (settled by the straddle roll test); OI as a signal (his own answer agrees it is not
one); regime/market-timing rules of the "don't buy at highs" family (contradicted 5×).

---

## Score — 2.5 / 5 (my half only)

**Why it clears the 1.5–2.0 band.** Three of his claims independently reproduce results we paid real
compute for, and he reaches them by trading experience rather than by measurement: **the liquidity gate on
spread scanning** (our 136%-of-gross cost result, and the credit/width finding that a rich spread in a junk
name is more risk, not more edge); **don't roll a loser out and wider** (our roll test, −9.51pp on the
breach cohort, 69.8% better held — adjacent evidence only: a long-straddle stop, not a short-premium roll); and **the paying-the-offer argument** that is the whole reason our cost
sweep killed nine strategies. His skew mechanism is correct, his VRP sign is correct at the short end, his
under-hedge instinct matches our put-overlay null, and his "you're not selling at fair value, you're hoping
to stay inside the range" is a more honest statement of short-premium risk than most creators manage. He
also volunteers his own weakness (worse as a directional than a volatility seller), which matches our
finding that the put spread has no edge over its own delta.

**Why it is capped below 3.0.** Not one claim in 13 videos carries a number we can check — no sample, no
win rate, no t, no fill, no net return anywhere. The three numbers he does state from memory are: a
risk-reduction figure (30% / 10-20-30%) with no source, a vol-cycle split (10/20/70) with no source, and
**"realized is higher 15% of the time" — which we can check, and which is wrong: 25% at 10d, 29% at 30d and
90d.** His central thesis is measurably true at 10 days and **measurably absent at the 30–90 day tenor he
actually trades**. The two signals he names as sufficient both test **NULL** in our data (skew adds nothing
beyond VIX, t 1.44; IV rank as a vehicle chooser t 0.68). His theta prescription is a concrete, memorable
number that implies a book our correction says should not exist. And "there's no such thing as a trend" is
asserted flatly while the family he substitutes — single-name fading — is the one our tests kill hardest.

**Format penalty.** These are clipped Q&A answers, not instruction. Two of the thirteen are portfolio
chat with substantial runtime spent on Pokémon and baseball cards; one is a definitional futures answer
with no strategy content; one is a policy opinion on Indian regulators. The strategy density is low even
where the strategist is good.

Net: **2.5** — a genuinely expert operator whose instincts repeatedly match our measured results, packaged
with zero evidence and one checkable number that is wrong. Without `pZm-y3oxzIQ` (the liquidity video) this
would be a 2.0.
