# QQQ 1-day iron butterfly on positive-gamma days — replication of the SPY result (2026-09-22)

## Pre-registration (written BEFORE the QQQ engine was run; do not edit this section after the results)

**Why.** The SPY 1-day 2× iron fly on positive-GEX days passed (+5.8% on max risk, t 3.4, both halves,
14/17 years; `gex_spy_ironfly_2026-09-21.md`) and the gamma filter is the whole edge (the same fly on
every day earns 0.0%). The single cheapest way to raise confidence in a t 3.4 result is to replicate the
**pre-specified cell on a second underlying**, not to search for a new one. QQQ is the only candidate
that already clears the prerequisites:

- The gamma→realized-vol mechanism **already passes on QQQ**: +4.0% excess realized vol on negative-GEX
  days beyond VIX(t−1)+RV(t−1), t 4.1, and RV 1.05% vs 0.67% (t 17) (`gex_regime_pin_2026-09-21.md`).
- QQQ option spreads are SPY-class. The mega-cap version of this trade **failed on costs** (straddle
  bid-ask 4.4% of mid = 4× SPY; `gex_stock_ironfly_2026-09-21.md`), so cost parity is the binding
  prerequisite and QQQ is the only other name that has it.

**This is a replication, not a sweep.** One underlying, one pre-specified primary arm. No new thresholds
are searched, so it carries a single test's multiple-testing charge.

**Trade (identical to the SPY spec, ticker swapped).** Entry at day t−1 close, expiry day t (only days
whose next listed expiry is exactly the next trading day). ATM strike K = call delta nearest 0.50 in that
expiry. Sell the K call and K put; buy a call at K + W and a put at K − W where W = w × the ATM straddle
mid, rounded to the NEAREST LISTED strike on each side. GEX sign from day t−1, computed by the same
`gex_series` code path over strikes within ±20% of spot.

**Primary arm fixed in advance: w = 2.0** (the arm that passed on SPY). w = 1.0 is reported as secondary
only, because it failed on SPY (t 2.0) — it is not eligible to become the headline.

**Fills.** Shorts at mid − 25% of bid-ask, longs at mid + 25%, $0.0065/share/leg, four legs; settle at
expiry with no exit cost. Skip a day if a wing strike has no two-sided quote or the net credit ≤ 0.

**Data.** `data/cache/gex/QQQ_short_expiry_quotes.parquet`, built today by the newly committed
`run_gex_quotes_pull.py` (1,059,776 rows, 2010-11-22 → 2026-02-20, DTE 1–4) — same schema and same DTE
mix as the existing SPY cache. QQQ GEX strikes from `QQQ_gex_strikes.parquet` (2010-11 → 2026-02).

**Pass bar (positive-gamma days, w = 2.0, return on max risk at the real fill).**
Mean > 0, **|t| ≥ 3 on days**, **both halves positive**, and positive-gamma > negative-gamma.
Anything less is a FAIL and the trade stays SPY-only.

**Stated prior.** QQQ's gamma→RV effect is about half SPY's (+4.0% vs +8.1%; t 4.1 vs 7.7), so a
**smaller** effect than SPY's +5.8% is expected. A result materially *larger* than SPY's should be
treated as suspicious rather than encouraging. QQQ's quote history also starts 2010-11 and its
daily-expiry era differs, so the first half will be thinner than SPY's.

**What would falsify the extension.** t < 3 on positive-gamma days; either half negative; or
positive-gamma ≈ all-days (the gamma filter carrying nothing on QQQ, which would undercut the SPY
mechanism rather than merely failing to extend it).

---

## Results (run 2026-09-22 after the pre-registration above; `run_gex_spy_ironfly.py --ticker QQQ`, log `.log`, table `.csv`)

**Verdict on the pre-registered arm (w = 2.0, positive-gamma days): FAIL. The trade stays SPY-only.**
It misses on two of the four conditions: **t 2.55 < 3**, and the **first half is negative (−5.05%)**.

1,512 QQQ 1-day flies, 709 positive-gamma days, 2011 → 2026-02, real fills on all four legs.

| w | gamma | n | ret on max risk | t | 2010–17 | 2018–26 | win | $ mean / worst | pos months |
|---|---|---|---|---|---|---|---|---|---|
| **2×** | **positive** | 709 | **+5.24%** | **2.55** | −5.05% (t −1.16) | +8.12% (t 3.50) | 59.8% | +$24.6 / −$1,004 | 53% |
| 2× | negative | 803 | −6.67% | −3.28 | −6.24% | −6.77% | 50.1% | −$21.9 / −$1,839 | 44% |
| 2× | all | 1,512 | −1.08% | −0.74 | −5.63% | +0.05% | 54.6% | −$0.1 | 49% |
| 1× | positive | 709 | +6.96% | 1.79 | −19.78% | +14.44% | 48.2% | +$12.6 / −$354 | 50% |

**The mechanism replicates; the tradeable claim does not.**
- Gamma still sorts on QQQ: positive +5.24 vs negative **−6.67 (t −3.28)**, an 11.9pp gap, with all days
  at −1.08 — the same shape as SPY, where the filter was the whole edge.
- The *level* on positive days is close to SPY's (+5.24 vs +5.82), so this is not a weaker effect; it is
  a **noisier** one — 709 days vs 928, with wider dispersion.
- ⚠ My stated prior (expect a *smaller* effect than SPY's, because QQQ's gamma→RV coefficient is half
  SPY's) was **wrong in level and right in significance**. Worth recording: the RV coefficient did not
  translate proportionally into fly return.

### Diagnostic — where the half-failure lives (POST-HOC; not a rescue)

| | QQQ n | QQQ ret | SPY n | SPY ret |
|---|---|---|---|---|
| pre-2016 | **110** | **−10.17%** | **71** | **+10.40%** |
| 2016+ | 599 | +8.07% | 857 | +5.44% |

QQQ's entire failure sits in a **110-day pre-2016 sample** (7–33 qualifying days a year, when QQQ barely
had 1-day expiries). From 2016 on — the era in which this trade actually exists — QQQ runs **+8.07%,
better than SPY's +5.44%**.

⚠ **This does not rescue the result.** The halves were pre-registered at 2018; re-cutting at 2016 to make
it pass is precisely the move this book forbids. A 2016+ version is a **new** hypothesis needing its own
pre-registration and its own multiple-testing charge. Recorded as a diagnostic only.

### ⭐ What this says about the SPY trade (the more valuable finding)

**SPY's "both halves positive" rests on 71 pre-2016 days at t 1.96 — not significant.** The replication
put sample depth on both tickers side by side for the first time, and SPY's first-half pass is as thin as
QQQ's first-half failure; the two thin samples simply landed on opposite signs. So this exercise should
move confidence in the SPY fly **slightly down, not up**: an independent underlying failed the bar, and
the leg of SPY's pass that looked strongest turns out to be its thinnest.

What does survive on both: the **gamma filter itself** (SPY all-days 0.0%, QQQ all-days −1.08%; negative-
gamma significantly negative on both, t −3.06 / −3.28), and the modern-era level (SPY +5.44, QQQ +8.07).

## How to apply

- **Do not trade the QQQ fly.** It failed its pre-registered bar.
- **Do not size the SPY fly up** on the strength of "it replicated" — it did not.
- The live SPY paper trade continues as built; review at ~100 flies as planned.
- If the 2016+ cut is ever pursued, it is a new pre-registered test on both tickers, with the daily-expiry
  era as the stated reason for the cut — decided *before* seeing the split again.

Related: `gex_spy_ironfly_2026-09-21.md`, `gex_regime_pin_2026-09-21.md`, `gex_stock_ironfly_2026-09-21.md`.
