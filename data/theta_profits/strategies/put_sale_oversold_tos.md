# Single-Name Put Sales on Oversold Watchlist Names: "TOS" (The Option Seller)

Source: `2026-09-27_zA9Do0qLlOg` ("Inside Her 5-Step Put Selling Strategy: 90% Wins in 502 Trades", 46 min).
Reviewed 2026-09-30. Guest: the anonymous "TOS / The Option Seller", **the same guest as the 0DTE NQ/ES review**
([futures_strangle_nq_es.md](futures_strangle_nq_es.md), 2026-01-11_pP-gZCJq9aY). Host: John. Option Omega affiliate
read @06:31. **Sales motive: direct** (Discord alerts, theoptionseller.com @44:29).

## Verdict box

**Conviction 2 / 5 · Risk 5/10 (mostly defined-risk spreads on high-beta AI names; naked puts when "light"; no
stop) · Tested? PARTIAL: every testable component is already in our ledger.** It is a clearer process than her NQ
episode, and the record is better than most on this channel: a public alert log with a stated denominator (502 closed
trades, 452 winners) instead of screenshots. But the log is **one year (Aug 2025 →), one regime, on a discretionary
watchlist of the year's leading themes**. Its headline numbers (90% win, $137k "per contract alerted") have **no
risk denominator**. Mechanically, it is a dip-buy expressed as a put spread, and our ledger rejects both halves: the
dip event is NULL, and the spread is stock at its delta minus costs.

## Mechanics (as stated)

| step | rule | @ |
|---|---|---|
| 1 watchlist | stocks she has researched and "would genuinely be happy to own": business model, balance sheet, management, earnings-call tone. Rebuilt **twice a year** "like an index reconstitution". An AI bot monitors negative news. Shown: semis (AMD, TSM, INTC, DELL, MRVL), memory (MU, SNDK, STX), data centre (NBIS, CRWV, WULF, IREN), photonics (AXTI, COHR, LITE) | 08:24–11:21 |
| 2 trigger | **proprietary band indicator**: volatility-based bands around a **slow moving average**. Alert when price crosses into the lower band = "below its mean, relatively oversold". Then check whether the drop is sector-wide or a company-specific "broken thesis". DIY proxy offered: a longer MA plus the stock's own volatility, or RSI | 11:29–14:12, 26:02–26:52 |
| 3 GEX | Tanuki/MenthorQ levels: short strike **below a major put wall** | 14:23–17:22 |
| 4 volume profile | 6-month volume profile: short strike **below the point of control**, ideally below a tested support low ("I want the sale price") | 17:39–19:48 |
| 5 flow | Unusual Whales: **large ITM put SALES** (premium > $100k) or concentrated short-dated call buying. May copy the flow's expiry with her own, more conservative strike | 19:57–22:11 |
| tenor | no fixed DTE; monthlies for liquidity; **typically 2–3 months**; avoids events | 22:49–24:18 |
| structure | naked put if she "truly wants" the shares and is under-concentrated; **put credit spread** if the stock is expensive or the tape uncertain. Mostly spreads (@37:56) | 24:33–25:22, 37:56 |
| profit | discretionary: trim/close at the next monthly's **first call wall**, or **≥ 40% profit with > half the time left** | 31:10–32:14 |
| loss | **no stop-loss** ("option prices jump"). Close when the thesis breaks or portfolio risk is unacceptable | 32:20–33:08 |
| management | hands-off until expiry week; act if P(ITM) ≥ ~70%: close, roll, or take assignment | 33:20–33:59 |
| hedge | buys puts / put debit spreads when she "feels" vol coming | 36:50–37:30 |
| example | AMD 2026-09-14, spot ~487 after the AI-slowdown weekend: **Jan-15-2027 400/300 PCS for $17.45** (≈ 123 DTE, short strike ~18% OTM, below the July low and the 480 POC; expiry copied from ITM 500-put sales). Closed 09-17 at $9.45 = **+46% in 3 sessions** | 25:39–30:47 |

## Claims and data audit

| claim | @ | denominator / audit |
|---|---|---|
| **90% win, 452 of 502 closed trades, $137k profit "per contract alerted"** | 39:19–39:50 (also 01:21, where the caption reads "52") | ✔ a real denominator for the WIN RATE. ✖ **no risk denominator for the $**: one contract of a $100-wide AMD spread risks ~$8,255, while a small-cap spread risks a few hundred. Summing $ across them weights the result by underlying price. $137k / 502 = **$273 per trade**, which says nothing until it is divided by risk. ✖ **alerted ≠ filled** (her own account is "a lot bigger"; no fills shown) |
| "alerted with $100k capital in mind" | 40:04–40:38 | a sizing intent, not a capital series. No concurrent capital used, no ROC, no drawdown, no NAV curve |
| log started **Aug 2025** | 39:19 | **one regime**: the AI / semis / memory / neocloud tape that led the market Aug 2025 → Sep 2026. Her watchlist *is* that tape, and it is **rebuilt twice a year**, so names that broke were removed (look-back selection). No bear-tape trade exists in the record |
| 90% win rate as evidence | — | a win rate on OTM spreads closed at 40–50% of credit is structural. AMD example: win ≈ +$8.00, max loss $82.55, so **breakeven win rate if losers run to max = 91%**. Her losers are discretionary early closes, so the true breakeven is lower, but the 50 losses' sizes are not given. A 90% win rate is uninformative without them |
| NQ book: 94% win, 500+ alerts, $216k "per contract" | 02:44–03:01 | the futures book we already scored 1.5/5 (Jan: "91% / $77k on 100k in 4 months"). Same metric problems |
| risk 3/10 | 37:52–38:41 | honest qualifier: "not automatically low risk"; the rating comes from selection + sizing |

## Claims against our ledger

| claim | verdict | evidence |
|---|---|---|
| **sell puts on an oversold dip in a name you want to own** | ❌ **the event is NULL** | Dip-in-uptrend is **definition-fragile**: −0.79pp, t −4.22 under one reasonable spec vs +0.7…+1.4pp under another on the same names → no effect (`dip_price_source_2026-09-29.md`). "Buy great stocks at a discount" confirmation ladder: PRIMARY FAIL (P1 +0.58pp t 0.67; `low_confirmation_ladder_2026-09-25.md`). Reversal long at a fresh low: NULL (2026-09-30) |
| **check that the drop is sector-wide, not company-specific** (@26:37–26:52) | ❌ **NULL, and survivorship cuts the wrong way** | Market-driven vs idiosyncratic dips: MKT +1.64pp **t 0.95**. On names that did not survive, the "market over-reaction" dip was the start of the decline (−3.33pp, t −3.06) (`market_vs_idio_dip_2026-09-28.md`). Her twice-yearly watchlist pruning hides exactly those names from her log |
| **a put credit spread is the vehicle** | ❌ **beta** | OptionsPlay's 50/25Δ spec vs stock at its net delta **−2.68pp, t −2.21**, 7/8 years negative (`optionsplay_spec_2026-09-24.md`). Paid-to-wait 30/15Δ spreads − 0.15Δ stock **−9.1pp, t −3.21** (`paid_to_wait_iv_gate_2026-09-29.md`). ~30 DTE 30Δ/20Δ single-name bull put vs its own delta +$7, **t 0.26**. Naked single-name puts: BCI CSP ≈ stock at delta minus costs, book +1.2%/yr vs SPY +10.5% (`bci_csp_study_2026-09-17.md`) |
| post-dip premium is rich (implicit: the 46% in 3 days) | ❌ **FAIL** | Post-shock IV richness is the VIX level: POST − VIX-matched 10d −10.8pp, t −1.8 (TEST_INDEX §1). The AMD +46% is delta (a +5% rebound on a ~0.2Δ short) plus vega crush on the bounce: the dip-reversal bet, collected through an option |
| strike below the GEX put wall | ❌ **pin/support NULL** | Expiry pin to the largest-\|GEX\| strike +0.6 bps, t 0.3. Intraday revert to the GEX strike NULL (t −1.14). Only the GEX **regime** (sign → realised vol) passes (t 7.7). That is a sizing input, not a strike |
| strike below the 6-month POC / prior support | ⚠ **untested as such; support tag RETRACTED** | The "lows at support" lift (+3.47pp t 3.63) was a look-ahead artefact; fixed +1.71 t 1.75 (ladder doc). A strike chosen below support is a delta choice: further OTM = lower delta. Our delta results already cover it (the far-OTM spread is still beta) |
| copy large ITM put-sale flow | **untestable here** | v3 is daily prints + OI with no aggressor side, so a "sale" cannot be identified. Unsigned-flow proxies: call bursts NULL (A1), put bursts NULL, wrong sign for a veto |
| 40–50% take with > half the time left | ⚠ **NULL at house fills** | ETF bull puts: the old +5.70% (50% take vs held) was GROSS from `options_cache`, which drops zero-bid quotes. On unfiltered v3 at house fills, take −2.78%/trade vs hold −1.37%, **take − hold −1.42pp, t −1.77** (`putspread_exit_capital_time_2026-09-24.md`, corrected 2026-09-24). A take rule only changes the holding period of a vehicle that is beta at entry |
| no stop on short premium | ✔ **agrees** | 50% take + 2× credit stop −4.3%/trade, t −5.4 on ETF spreads (gross, the pre-correction engine; direction not in doubt) |
| monthlies for liquidity; avoid events | ✔ **agrees** | liquidity is the single-name gate (10-DTE costs 136% of gross); pre-earnings placement is the worst for short vol |
| she hedges with puts "when she feels" vol coming | discretionary | tail-hedge overlays on short premium were negative carry (WL-5f) |

**Red flags (checklist):** heavy sales motive ✔ (Discord alerts); record with no risk denominator ✔; winners-only
example ✔ (one AMD trade, closed at +46%, chosen "since we've been talking about it"); discretionary "proprietary"
trigger ✔; one-regime record ✔. **Not present:** "risk-free" language. She volunteers that oversold can get more
oversold, that flow can be wrong "with more money", and that the strategy is "not automatically low risk".

## What's genuinely sound

Defined risk by default, monthlies for liquidity, no stop on short premium, avoiding events, and an explicit
concentration check. These are all hygiene our data agrees with. The edge she attributes to the
process (watchlist + oversold + levels + flow) is the part our data says is either NULL (the dip), beta (the
vehicle) or untestable (the flow and the discretionary watchlist).

## Backtestability

The skeleton is codable: lower volatility band of a slow MA, a 60–90 DTE monthly put spread with the short strike
below the 6-month volume POC, 40% take with more than half the time left, no stop. The watchlist is not codable
point-in-time: it is discretionary and pruned twice a year, and any proxy built from today's names re-creates her
survivorship. **No new test proposed** (only-new-ideas rule). Every axis maps to a row:
- the event → dip-in-uptrend NULL (definition-fragile) + market-vs-idio NULL;
- the vehicle → OptionsPlay spec t −2.21, paid-to-wait t −3.21, 30Δ/20Δ t 0.26;
- the premium → post-shock FAIL.

The nearest untouched cell (a single-name 60–90 DTE spread with an early 40% take, vs delta-matched stock) has a
low prior. The spread is beta at entry, and a take rule only changes the holding period.
