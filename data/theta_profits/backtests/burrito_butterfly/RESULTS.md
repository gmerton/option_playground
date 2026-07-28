# Burrito Butterfly — Backtest Results

**Run 2026-06-25.** Mechanical EOD backtest, SPX 2-DTE, **bullish** (his stated default), 2023-01 → 2026-02
(~385 trades). Data: Athena `silver.options_daily_v3` (EOD) + `^GSPC` spot for intrinsic settlement.
Script: `run_backtest.py`. Marks at **mid**; settle at **intrinsic**; costs = $0.65/leg + a slippage
fraction of the quoted bid-ask per leg.

Structures (ATM K, call delta ≈ 0.50): **A_FLY** `+C(K-15) -2C(K) +C(K+15)` · **B_BURRITO**
`+C(K-15) -2C(K) +2C(K+15) -C(K+20)` (fly + upper 5-wide call spread — our reading of an ambiguous
transcript) · **C_SPREAD** `+C(K) -C(K+5)` (plain bullish debit spread, the null).

## Headline: hold-to-expiry EV (% of risk), by slippage assumption

| Structure | win% | EV @ mid (his rosy fills) | EV @ 25% of spread | EV @ ½ spread (pessimistic) |
|-----------|:----:|:------------------------:|:------------------:|:---------------------------:|
| **A_FLY** (plain butterfly) | ~16% | **−12.2%** | **−24.9%** | **−34.0%** |
| **B_BURRITO** | ~54% | **−1.1%** | **−10.6%** | **−18.2%** |
| **C_SPREAD** (plain debit spread) | ~54% | **+6.8%** | **+1.5%** | **−3.1%** |

Losses are correctly bounded by the debit (worst single trade ≈ −1× risk). n ≈ 385 each.

## What the data says

1. **The plain butterfly is a clear loser** (−12% to −34% EV across all cost levels). A 2-DTE ATM
   15-wide fly needs SPX to pin within ±15 (~±0.3%) at expiry; it rarely does. It's a negative-EV
   theta lottery ticket — exactly what his "love/hate with butterflies" hints at, quantified.
2. **The burrito is negative-EV** at realistic (−10.6%) and pessimistic (−18.2%) costs; only ~breakeven
   (−1.1%) under his *rosiest* mid-fill assumption. The ~54% win rate is the trap — **positive win rate,
   negative mean**: the losers outweigh the winners. This is the statistical signature of a strategy
   that *feels* consistent while bleeding.
3. **Adding the butterfly DESTROYS expectancy.** The decisive head-to-head: C_SPREAD (+1.5%) → B_BURRITO
   (−10.6%) at realistic costs. The butterfly "free theta" is a **drag**, not a gift — you'd be strictly
   better off buying just the debit spread.
4. **Even the best piece has no real edge.** C_SPREAD's small positive EV is **SPX drift** — it's a
   permanently-bullish bet during the 2023–2026 bull market. Flip costs to ½-spread, or run it in a flat/
   down regime, and it's negative. There is no theta/structure edge here; there's beta.
5. **His advocated management made it WORSE.** The "managed" run (take +10% / cut at −10%) lowered EV for
   all three (e.g. B: −10.6% → −26.6%) — the tight stop locks losses that often recover by expiry.

## Honest caveats

- **EOD only.** His core claim is *intraday* hand-management (5–10% same-day exits, clawbacks). That is
  not testable here and the managed run is coarse (one intermediate mark). But the **hold-to-expiry
  structural EV is the cleaner read, and it's negative** — the burden of proof for an intraday edge is on
  the claim, and "risk-free / can't lose" is already falsified (losses are real and routine).
- **Always-bullish + bull market** inflates C_SPREAD; it's drift, not edge.
- **Strike interpretation** is one reading; magnitudes shift, but the *ranking* (C > B > A), the
  *butterfly-as-drag* finding, and the *bounded-but-negative* EV are robust to it and to slippage.
- 2-DTE, 2023–2026 only. Other DTEs (≤14) and longer history (daily expirations sparse pre-2022) untested.

## Verdict update

The marketing is refuted by the data. "Risk-free magic money rainbow" is false: the structure has real,
bounded losses and **negative expectancy** at any realistic cost; the elaborate "burrito" is **worse than
its simplest component**; and the only ~breakeven piece is undifferentiated market beta. **Conviction → 1/5,
Tested: yes.** Not a diamond.
