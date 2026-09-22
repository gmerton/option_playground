# 1-day iron butterfly on large liquid stocks, by stock gamma and by SPY gamma (2026-09-21)

## Pre-registration (written BEFORE any data was pulled; do not edit this section after the results)

**Why.** The SPY 1-day 2× iron fly on positive-GEX days passed (+5.8% on max risk, t 3.4;
gex_spy_ironfly_2026-09-21.md). Does the same trade work on the largest single-stock option markets?

**Names (fixed):** AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD, NFLX, AVGO. META from 2021-07 only (older
history sits under FB in the table; not merged). Window 2010-01 → 2026-02-27, `silver.options_daily_v3`.

**Trade.** Single stocks have Friday (and rare holiday-Thursday) expiries only, so entry = any day d whose nearest
listed expiry is exactly one calendar day later (in practice Thursday close → Friday expiry). Same structure as the
SPY fly: ATM = call delta nearest 0.50 in that expiry; sell the ATM straddle, buy wings at K ± 2 × the straddle mid
(nearest listed strike each side). Fills: shorts at mid − 25% of the bid-ask, longs at mid + 25%, $0.0065/share/leg.
Held to expiry. **Prices from put-call parity, not bars** (v3 strikes are unadjusted, and NVDA/TSLA/AAPL/AVGO split):
S_entry and S_settle = K + C − P at the strike with the smallest |C − P| mid, on the entry day and on the expiry day.

**Earnings screen (fixed rule, no look-ahead):** skip an entry whose implied move (straddle mid / S) is more than 2×
the median implied move of that name's previous 8 entries (needs ≥ 4 prior entries).

**Two gamma conditions, each tested separately:**
- **A. The stock's own GEX** at d's close: Σ over every expiry and strikes within ±20% of S of (call OI × γ − put OI × γ),
  naive sign as in the SPY test. ⚠ Covered-call writing may make the naive sign less meaningful for single stocks.
- **B. SPY's GEX** at d's close (the cached series from the SPY tests).

**Pass bar (per condition, positive-gamma entries, return on max risk at the real fill).** Mean > 0 with |t| ≥ 3 where
t is computed across ENTRY DATES (mean per date over the names traded that day, then t across dates), positive in
both halves (2010–2017 / 2018–2026-02), AND higher than the same fly on negative-gamma entries. All-entries baseline,
bid-ask cost and per-name results reported.

**Not tested:** other names, other wing widths or structures, multi-day holds, entries on non-expiry-eve days,
the FB history, sizing.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_gex_stock_ironfly.py`, log `.log`, table `.csv`)

**Verdict: FAIL on both conditions. The SPY fly does not carry over to single stocks.** 5,952 flies on 741 entry
dates (296 screened out as earnings weeks); median ATM straddle bid-ask **4.4% of mid, 4× SPY's 1.1%**.

| condition | gamma | flies | entry dates | return on max risk | t (dates) | 2010–17 | 2018–26 | win | $ mean / worst |
|---|---|---|---|---|---|---|---|---|---|
| A. own-stock GEX | positive | 4,415 | 728 | −1.9% | −1.9 | −2.7% | −1.5% | 55% | −$11 / −$4,883 |
| A. own-stock GEX | negative | 1,241 | 496 | −1.5% | −0.7 | +1.9% | −3.0% | 55% | −$24 / −$6,059 |
| B. SPY GEX | positive | 2,728 | 334 | +0.9% | 0.6 | −1.2% | +1.8% | 57% | +$15 / −$5,519 |
| B. SPY GEX | negative | 2,912 | 402 | −4.4% | −2.3 | −2.4% | −5.7% | 54% | −$40 / −$6,059 |
| all entries | — | 5,656 | 738 | −1.8% | −1.4 | | | 55% | −$14 |

- **Own-stock gamma carries no information:** the naive sign reads positive on 78% of entries (covered-call writing
  likely makes dealers net long calls in single names) and positive vs negative barely differ.
- **SPY gamma points the same way as in SPY** (positive +0.9% vs negative −4.4%, a 5.3pp gap) but the positive side
  is ~zero and not positive in 2010–17: the market regime helps, but not enough to pay 4× SPY's costs.
- **Costs explain most of it.** Per name, the cheapest option markets did best on SPY-positive days (AAPL 2.5% bid-ask
  +5.1%, META 2.8% +10.0%, TSLA 3.1% +7.9%, AMD 3.0% +4.6%) and the widest did worst (AVGO 11.1% −4.5%, GOOGL 7.9%
  −2.9%). ⚠ That's a post-hoc read of per-name results, NOT a finding; a "cheap-spread names only" version would be a
  new pre-registered test with its own multiple-testing cost. Parked, low priority.
- The tails are larger than SPY's (worst −$6,059 per fly on the highest-priced names).

**Decision: SPY only.** The live paper trade stays as built.
