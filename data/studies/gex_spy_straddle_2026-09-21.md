# SPY 1-day straddles by dealer-gamma sign: long on negative-gamma days, short on positive (2026-09-21)

## Pre-registration (written BEFORE any data was pulled; do not edit this section after the results)

**Why.** The GEX regime test passed (gex_regime_pin_2026-09-21.md): negative-GEX days carry ~8% more realised
volatility than the prior day's VIX and realised vol predict (SPY, t 7.7). The VIX is a 30-day implied vol, so that
doesn't say the 1-day option was mispriced. This asks the tradeable question on both sides: **are 1-day SPY options
under-priced on negative-gamma days (buy) and over-priced on positive-gamma days (sell)?**

**Trade.** On day t−1's close, the ATM SPY straddle (call delta nearest 0.50) in the expiry that settles on day t
(only days where such an expiry is listed: mostly Fridays early on, daily from 2022). Held to expiry, settled at
|S_t − K| with S_t = SPY's day-t close. GEX sign from day t−1's close (same series and naive convention as the regime
test). Data: `silver.options_daily_v3` SPY bid/ask/delta, 2010-01 → 2026-02-27.

**Pricing.** Mid = bid/ask midpoint of both legs. Real fill = house cost model: buy at mid + 25% of the combined
bid-ask, sell at mid − 25%, $0.0065/share/leg commission; no exit cost at expiry. Straddles under $0.10 mid skipped.

**Measures.**
- Mechanism: realised / implied move ratio = |S_t − K| / straddle mid (fair ≈ 1 before the risk premium). Regression
  ratio_t = a + b·NEG + c·log VIX(t−1) + e, Newey-West t (5 lags).
- Item 2 (LONG on negative-gamma days): long straddle return on premium at the real fill.
- Item 1 (SHORT on positive-gamma days): short straddle return on premium at the real fill; worst day reported. Also
  vs shorting on EVERY day (does the gamma filter add?).

**Pass bars (SPY; both halves = 2010–2017 and 2018–2026-02).**
- Item 2: mean long return at the real fill > 0, |t| ≥ 3 (days), positive in both halves.
- Item 1: mean short return at the real fill > 0, |t| ≥ 3, positive in both halves, AND beats shorting on all days
  (difference > 0).
- Mechanism: b > 0 with t ≥ 3 (realised/implied higher on negative-gamma days beyond the VIX).

**Not tested:** strangles, wings, condors or other strikes; entries intraday; other tickers; stops or early exits;
sizing. One structure, one run.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_gex_spy_straddle.py`, log `.log`, table `.csv`)

**Verdicts: Item 1 (SHORT on positive-gamma days) PASS · Item 2 (LONG on negative-gamma days) FAIL (fairly priced) ·
Mechanism PASS.** 1,943 SPY 1-day straddles (2010-03 → 2026-02; 413 in 2010–17 when day-t expiries were mostly
Fridays, 1,530 in 2018–26), median bid-ask 1.1% of mid.

| gamma | days | implied move (median) | realised / implied | LONG at real fill | t | SHORT at real fill | t | short win | worst short day |
|---|---|---|---|---|---|---|---|---|---|
| **positive** | 928 | 0.53% | **0.85** | −15.7% | −6.6 | **+13.7%** | **5.6** | 67% | −604% of credit |
| negative | 1,015 | 0.84% | 1.01 | −0.05% | −0.02 | −2.1% | −0.9 | 55% | −510% |

Halves (short on positive / long on negative, at real fill): 2010–17 **+16.0% (t 2.2, n 172)** / −11.7%; 2018–26
**+13.2% (t 5.2, n 756)** / +3.6% (t 1.3). By year the positive-day short is up in 13 of 17 years (down 2016, 2018,
2022, 2026; 2022 n 27, 2026 n 12).

- **Mechanism:** realised/implied is higher on negative-gamma days beyond the VIX (b +0.169, NW t 4.7; 2018–26 t 5.5,
  2010–17 t 0.9 on 413 days).
- **Short on EVERY day** (the plain 1-day volatility premium): +5.4% (t 3.1). **Filtering to positive-gamma days adds
  +8.2pp**; positive vs negative days differ by 15.8pp (Welch t 4.6). On negative-gamma days the short earns nothing.
- **Long on negative-gamma days fails:** the extra volatility found in the regime test IS priced into the 1-day
  straddle (0.84% vs 0.53%), realised ≈ implied (ratio 1.01).
- **$ per straddle** (short, positive days): mean +$36.9, worst −$1,060. Unlimited-risk structure.

## What it means / before trading it

Passes the pre-registered bar comfortably, and survives the day's multiple-testing load at t 5.6. It is NOT ready to
trade as run:
1. **Naked ATM straddle = unlimited risk**, worst day −6× the credit. Needs the defined-risk version (iron butterfly)
   tested, pre-registered, before any live use. Queued.
2. **The first half is thin** (172 positive-gamma trades, t 2.2, mostly Fridays). The edge lives mainly in the
   daily-expiry era.
3. **Live GEX** must be rebuilt from Tradier chains at the close (the v3 feed lost OI/gamma in 2026); the entry is at
   the close into the next day's expiry, which also carries after-hours pin/assignment risk on American SPY options.
4. **Forward check:** the lockbox rule (data from 2026-09-22 on) applies; paper-trade before sizing.
