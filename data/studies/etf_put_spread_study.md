# Pooled ETF bull put spreads: when does a one-sided put credit spread pay? (2026-09-10)

Script: `run_etf_put_spread_regression.py`; trades in `data/studies/etf_put_spread_trades.csv`.

**Setup.** 21 unleveraged ETFs from `options_cache` (SPY QQQ IWM GLD TLT XOP XBI XLK XLE XLV EEM GDX
USO XLU FXI XLP XLF ASHR SOXX UUP INDA). Every Friday, 2018-07 .. 2026-02 (7,170 trades after
warm-up): sell the ~30-delta put and buy the ~15-delta put at the expiry nearest 30 days (median
credit 18% of width). Return on max loss, net of the house cost model (median cost 9% of credit).
The entry price comes from put-call parity (unadjusted, matches the strikes); later prices use
split-adjusted closes. Exits: **hold** to expiry, or **managed** (take profit at 50% of credit, stop
when the spread is worth 2× the credit). Train 2018-22, test 2023-26. t-stats use the equal-weight
weekly portfolio (Newey-West).

## 1. No unconditional edge after costs

| Hold to expiry | Trades | Mean/trade | Win % | Worst | Weekly t |
|---|---|---|---|---|---|
| All | 7,170 | +0.6% | 77.6% | −207% | +0.3 |
| Train 2018-22 | 4,169 | −0.9% | 76.7% | −207% | −0.3 |
| Test 2023-26 | 3,001 | +2.7% | 78.8% | −131% | +1.0 |

## 2. The managed exit destroys value everywhere
The 50%-take / 2×-stop version lost −4.3% per trade (t −5.4), and was negative in both halves, for
almost every ETF and under every filter. Stopping out on daily marks turns temporary losses into
permanent ones. This is the third study to agree: straddle stops earn nothing on a real path, and
converting paid-to-wait spreads on the break loses. **Hold put credit spreads to expiry; size to the max loss.**

## 3. The model (log IV/RV, IVP, skew, FF, trend, VIX) has no out-of-sample skill
Train corr 0.13, test −0.05. Its top-tercile picks scored worse than the trades it skipped.

## 4. What does work: selling puts into stress
Hold to expiry, UUP excluded (38 trades, 7-cent credits, costs 35% of credit).

| Condition | Train trades | Train mean | Test trades | Test mean |
|---|---|---|---|---|
| All | 4,143 | −0.9% | 2,989 | +2.4% |
| **VIX ≥ 25** | 1,123 | **+4.5%** | 51 (3 weeks) | +17.3% |
| VIX ≥ 30 | 470 | +8.1% | 31 | +14.7% |
| **VIX ≥ 25 and uptrend** | 441 | **+10.1%** | 10 | +10.9% |
| VIX < 20 | 2,028 | −4.0% | 2,423 | +2.1% |
| **Near-term vol above later months (ff > 0)** | 990 | +1.6% | 1,405 | **+4.4% (t 2.2)** |
| Rich put skew (skew_z > 1) | 679 | +1.9% | 460 | +5.1% |

- **VIX ≥ 25 by year:** 2018 +22%, 2020 +10.5%, 2021 +7%, **2022 −3%** (the grinding bear market
  is the failure mode), 2023 +21%, 2025 +15%.
- **It's an equity-ETF effect.** At VIX ≥ 25: IWM +14.6%, QQQ +13.9%, XBI +13.1%, XOP +10.6%,
  XLV +9.6%, SPY +9.5%, XLK +8.7%. But **TLT −14.9%**, FXI −4.0%, ASHR −3.4%, XLU −3.0%.
- **IV percentile:** the lowest quintile was the worst in both halves, and higher IVP was better in
  the test period.
- **IV/RV:** the highest quintile was the worst in the train period, the opposite of the VRP story.

## Reading
Put credit spreads on ETFs aren't a steady premium harvest after costs. They're a bet that fear is
overpriced. The one consistent edge is selling equity-ETF put spreads when VIX is 25 or higher (best
with the ETF still above its 50-day average), or when the term structure is inverted or put skew is
rich. Hold to expiry. This agrees with the IWM study (paid only in "Bullish HighIV" and washouts),
the paid-to-wait IV gate, and the QQQ result that high own-IV is not an edge in calm tapes.
⚠ The high-VIX test sample is tiny: 2023-26 had 3 such weeks. The out-of-sample case rests on the
year-by-year record, with 2022 negative. The rule is in-sample.

**Candidate rule:** SPY, QQQ, IWM, XLK, XLV or XBI; VIX ≥ 25; ETF above its 50-day average (or VIX
≥ 30 without the trend condition); sell the 30-delta put, buy the 15-delta, ~30 DTE; hold to
expiry; size to max loss; no bond or China ETFs. On 9/10 VIX was ~18, so the rule is inactive.
