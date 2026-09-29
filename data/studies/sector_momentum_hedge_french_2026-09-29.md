# Industry-momentum 12-1 spread as a bear-market HEDGE, Ken French industries 1927→2026 (2026-09-29)

## Pre-registration (written BEFORE any spread return was computed; do not edit this section after the results)

**Why.** Audit List A #6 (`audit_top_down_2026-09-25.md`), audit step 3 item 3. The SPDR-sector 12-1 spread
(`run_sector_momentum_spread.py`, 2026-09-24) has ~zero return but paid in 3 of 4 bears (2008 +25%, 2020 +16%,
2022 +31%; 2000–02 −10.3%) and survived de-meaning as a book overlay (`run_sector_overlay_test.py`). Four episodes is
anecdote. Ken French's industry returns reach back to 1926 and give ~10 episodes. Breadth is OFF right now; this is
the only bear-leg candidate left in the ledger.

**Data.** `data/cache/french/10_Industry_Portfolios.csv` (value-weighted monthly, 1926-07 → 2026-08, CRSP 202608)
and `F-F_Research_Data_Factors.csv` (Mkt = Mkt-RF + RF), downloaded 2026-09-29; loader `src/lib/studies/french_data.py`.
10 value-weighted industries ≈ the 9–11 SPDR sectors, so K = 3 keeps the same breadth as the ETF test.

**Spread (fixed; the ETF test's primary cell).** For holding month h: rank industries on cumulative return over
months h−12 … h−2 (12-1, skip the latest month); long the top 3, short the bottom 3, equal weight, dollar-neutral.
Net of 20 bp/month + 0.25%/yr borrow, as in the ETF test. First holding month 1927-07.

**Bear episodes (defined from the market series only, listed before any spread return was seen).** Drawdowns of
the monthly Mkt total-return index of ≥ 20%, peak → trough, where an episode ends when the index regains its peak:

| # | peak | trough | market DD | seen before? |
|---|---|---|---|---|
| 1 | 1929-08 | 1932-06 | −83.7% | new |
| 2 | 1946-05 | 1947-05 | −24.3% | new |
| 3 | 1961-12 | 1962-06 | −23.1% | new |
| 4 | 1968-11 | 1970-06 | −33.6% | new |
| 5 | 1972-12 | 1974-09 | −46.5% | new |
| 6 | 1987-08 | 1987-11 | −29.9% | new |
| 7 | 2000-08 | 2002-09 | −45.0% | ETF test (−10.3%, failed) |
| 8 | 2007-10 | 2009-02 | −50.3% | ETF test (+) |
| 9 | 2020-01 | 2020-03 | −20.2% | ETF test (+) |
| 10 | 2021-12 | 2022-09 | −24.8% | ETF test (+) |

Episode window = holding months peak+1 … trough (the months the market was falling). ⚠ 1937–38 sits inside
episode 1's underwater period and is not a separate episode under this rule.

**Primary (both required).**
1. **Pays in bears:** the spread's cumulative net return over the episode window is **> 0 in ≥ 7 of 10** episodes.
   (Since 3 of the 4 seen episodes were positive on ETFs, this effectively needs ≥ 4 of the 6 new ones.)
2. **De-meaned drawdown cut:** host = the market; sleeve = the spread with its full-sample mean subtracted, scaled to
   50% of the market's full-sample volatility (the overlay test's primary size). Host + sleeve has a **smaller
   max drawdown inside the episode window than the host alone in ≥ 7 of 10** episodes.

**Label condition (required to call it more than a beta hedge).** The spread beats its **beta-equivalent market
short** (−β × market, β from the full-sample OLS of spread on Mkt) over the episode window in ≥ 7 of 10 episodes.
Pass 1+2 without this → "hedge, but no better than a cheaper index short".

**Reported, not part of the bar:** full-sample mean / t / β / alpha; per-decade mean (the carry); the 12 months after
each trough (momentum crashes happen in rebounds, e.g. 1932, 2009); the 6-new-episode count on its own.

**Caveats stated up front.** 20 bp/month is optimistic for the 1920s–70s (no ETFs; industry portfolios are not
tradeable instruments); the test is about the *hedge property*, not a live cost. Monthly data understate intra-month
drawdowns (1987 is one month). One cell, no grid.

---

## Results (run 2026-09-29, after the pre-registration above was committed in d34e706 / 87747e0; `run_sector_momentum_hedge_french.py`, `.log`, `.csv`)

**Verdict: PASS on the primary (the hedge property replicates on 6 new episodes), FAIL on the label → per the
pre-registered reading: "a hedge, but no better than a beta-equivalent index short" by episode count.**
⚠ The first run had the beta-equivalent short's sign flipped (it showed 8/10 on the label); caught before recording,
fixed in the script, and every number here is from the corrected run. The primary conditions did not change.

| # | episode | mkt | spread | β-equiv short | DD host → overlay | next 12 m | peak → trough+12 |
|---|---|---|---|---|---|---|---|
| 1 | 1929-08 → 1932-06 | −83.7 | **+81.2** | +21.1 | −83.7 → −74.7 | −53.5 | −15.6 |
| 2 | 1946-05 → 1947-05 | −24.3 | +0.3 | +3.3 | −24.3 → −24.8 ✗ | +4.5 | +4.9 |
| 3 | 1961-12 → 1962-06 | −23.1 | +6.1 | +3.1 | −23.1 → −20.1 | +5.7 | +12.2 |
| 4 | 1968-11 → 1970-06 | −33.6 | **−13.0** | +4.8 | −33.6 → −40.9 ✗ | −12.2 | −23.6 |
| 5 | 1972-12 → 1974-09 | −46.5 | +4.7 | +7.5 | −46.5 → −45.7 | −10.4 | −6.1 |
| 6 | 1987-08 → 1987-11 | −29.9 | **−14.7** | +4.0 | −29.9 → −38.6 ✗ | −2.1 | −16.5 |
| 7 | 2000-08 → 2002-09 | −45.0 | +19.0 | +7.0 | −45.0 → −36.8 | −28.2 | −14.5 |
| 8 | 2007-10 → 2009-02 | −50.3 | +44.4 | +8.3 | −50.3 → −35.7 | −25.0 | +8.2 |
| 9 | 2020-01 → 2020-03 | −20.2 | +5.4 | +2.6 | −20.2 → −17.2 | +24.9 | +31.7 |
| 10 | 2021-12 → 2022-09 | −24.8 | +12.6 | +3.3 | −24.8 → −21.6 | −6.2 | +5.6 |

- **Cond 1 (pays):** 8/10 → YES; **4/6 on the new episodes** (exactly the implied need). **Cond 2 (de-meaned DD cut):**
  7/10 → YES, only 3/6 new. **Label (beats the β-equiv short):** 6/10, 2/6 new → no.
- **It fails in the two ways that matter most for a hedge:** the fast crash (1987, −14.7% while the market fell 30%)
  and the rotating bear (1968–70). Where it works, it works big (1929–32 +81%, 2008 +44%) — the label is lost on the
  small episodes (1946, 1973), not the large ones.
- **Rebound give-back:** negative in 7/10 of the 12 months after the trough (1932 −53.5%, 2001–02 −28%, 2009 −25%).
  Held peak → trough + 12, only 5/10 are positive. The hedge pays in the fall and gives much of it back in the turn.
- **Carry (exploratory):** full sample +0.17%/mo (t 1.48), β −0.12, alpha +0.29%/mo (t 2.72) — but per decade it is
  ~0 since 1960 except the 1990s and 2020s, and the SPDR version was −0.17%/mo. The pre-reg's "cheaper index short"
  wording assumed a costlier spread; over the century the spread is not the costlier leg, but on ETFs since 1999 it is.

**What it means for the book now.** Breadth is OFF. The sector-momentum spread is a real, century-tested bear leg in
slow bears (8/10 pay, 7/10 cut drawdown with the mean removed), but it does **not** protect against a 1987-style
crash, it gives back much of its gain after the low, and by count it is not clearly better than simply
running ~0.12 beta short. Adopting it as a standing sleeve is still Gabe's preference call (the 9/24 overlay: maxDD −4
to −5 pts for ~0.12 Sharpe); this test removes "4 episodes is anecdote" as the objection, not the cost objection.
