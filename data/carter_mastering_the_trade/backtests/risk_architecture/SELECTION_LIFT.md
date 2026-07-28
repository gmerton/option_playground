# Selection Lift — what the breakout scorecard is actually worth

**Run:** 2026-07-26 · `arch_lib.py` + `run_selection_lift.py`
**Universe / window / sim:** identical to [RESULTS.md](RESULTS.md) — 299 names, 2006–2026,
10 stops × 6 exits, 0.3% risk, 30% position cap, 10 slots, no leverage, 10 bp round trip.
**Only the entry varies.** 8 tiers, from the dumb control up through the production scorecard.

Pivot detection is the repo's own `_detect_pivot`, vectorized — **validated to zero mismatches
across 2,400 randomly-sampled bars on 6 tickers** against the production function.

## Headline

> **Selection is worth roughly 3× on per-trade return, and it buys the right tail, not the hit
> rate. But it cannot be spent: the gates are so restrictive that the portfolio sits 77–92% in
> cash, and not one of the 480 entry × architecture combinations beat SPY buy-and-hold.**
>
> **The binding constraint is universe breadth, not signal quality.**

---

## 1. ⚠ The first reading was an artifact — architecture must be matched to the selection

At a fixed **3% stop**, the scorecard tiers looked terrible (CAGR falling monotonically from
GATES 9.16% down to POTENT 0.74%). That comparison is invalid. The ADR ≥ 3.5% gate *selects for
names whose ordinary daily range exceeds 3%*, so a 3% stop is far tighter for the gated tiers
than for the control. Median hold collapsed to 2–3 days and stop-out rates hit 88%.

Re-run with a volatility-scaled stop (**2.0 ATR**, mean width 9.2% for gated tiers vs 4.6% for
the control), the ordering reverses:

| entry tier | n | win % | **mean %/trade** | p90 | **p99** | med hold | t |
|---|---:|---:|---:|---:|---:|---:|---:|
| DUMB | 22,624 | 31.1 | +1.04 | 11.6 | 49.0 | 18 | 11.3 |
| REQ-only | 25,601 | 31.7 | +1.23 | 11.8 | 50.7 | 18 | 14.0 |
| **GATES** | 2,872 | 32.1 | **+2.92** | 24.6 | **101.0** | 19 | 6.3 |
| BREAKOUT | 1,665 | 31.5 | +2.89 | 28.0 | 100.4 | 20 | 4.8 |
| CONFIRMED | 884 | 30.4 | +1.83 | 25.2 | 99.4 | 20 | 2.3 |
| POTENT | 584 | 28.6 | +0.95 | 20.5 | 88.7 | 20 | 1.0 |
| LEADER | 493 | 30.0 | +2.63 | **30.6** | **107.2** | 21 | 2.1 |
| BOTH | 319 | 31.0 | +2.77 | 24.1 | 103.4 | 22 | 1.8 |

**Win rate is flat at ~31% across every tier.** Selection does not improve how often you are
right. It roughly **triples the mean and doubles the right tail** — p99 goes from +49% to
+101/107%. The convexity these traders monetize comes from *which names*, not from the stop.

This is the direct complement to RESULTS.md: architecture cannot create convexity, selection can.

**Stable across eras**, mean %/trade at the matched architecture:

| tier | 2006–11 | 2012–18 | 2019–26 |
|---|---:|---:|---:|
| DUMB | −0.01 | +1.02 | +1.54 |
| GATES | +0.62 | +3.15 | +3.91 |
| BREAKOUT | +0.59 | +2.21 | +4.04 |
| LEADER | +1.43 | +1.60 | +3.45 |

No decay — the gate advantage is largest in the most recent era.

## 2. The ADR gate is doing nearly all of the work — and it is marked "optional"

Isolating it (2.0 ATR architecture, mean %/trade):

| | gates applied | mean %/trade |
|---|---|---:|
| DUMB | — | +1.04 |
| REQ-only | Stage 2 + $10M dollar volume (**both "required"**) | +1.23 |
| GATES | the above **+ ADR(20) ≥ 3.5%** (**"optional"**) | **+2.92** |

**The two required gates add almost nothing over the dumb control (+0.19 pp). Adding the
optional gate more than doubles the result (+1.69 pp).** Same story on capital efficiency
(CAGR per unit deployed): DUMB 7.5, REQ-only 10.1, GATES 20.6.

⟹ **`GATE_TIERS` has the tiering backwards.** Stage 2 and dollar volume are hygiene; ADR is the
edge. Volatility selection is the gate that pays.

## 3. POTENT is the one tier that actively destroys value

POTENT (= CONFIRMED + EMA lead + prior bar green + within ±8% of pivot) is the worst tier in the
study: +0.95%/trade, below even REQ-only, and the lowest mean CAGR across all 60 architectures
(0.23%). Every other scorecard tier beats it. The suspects are the two ad-hoc conditions it adds
over CONFIRMED — `prev_green` and the ±8% pivot-distance window. Worth isolating and probably
deleting.

Note LEADER (+2.63) and BOTH (+2.77) are fine — the damage is specific to POTENT's filters.

## 4. ⚠ The edge is real and cannot be spent

Portfolio results, 2.0 ATR + close<50EMA:

| tier | avg exposure | CAGR | max DD | **CAGR per unit deployed** | MAR |
|---|---:|---:|---:|---:|---:|
| DUMB | 60.4% | 4.52% | −19.6% | 7.5 | 0.23 |
| REQ-only | 63.9% | 6.46% | −23.3% | 10.1 | 0.28 |
| GATES | 23.2% | 4.77% | −16.7% | 20.6 | 0.29 |
| BREAKOUT | 18.9% | 3.89% | −15.5% | 20.6 | 0.25 |
| CONFIRMED | 14.1% | 1.79% | −12.4% | 12.7 | 0.14 |
| POTENT | 10.8% | 1.19% | −9.2% | 11.0 | 0.13 |
| LEADER | 8.5% | 2.18% | −7.0% | **25.7** | 0.31 |
| BOTH | 6.2% | 1.80% | −5.2% | **29.3** | **0.35** |

Per dollar actually at work, the top tiers earn **3–4× the dumb control**. But GATES fills only
23% of the account and BOTH only 6%, so the raw CAGR never materialises.

**Not one of the 480 combinations beat SPY (~10.7%) on raw CAGR.** The best in the study was
GATES at a 3% stop, 9.16%.

⚠ The "per unit deployed" column assumes linear scaling. Levering a 6%-exposure strategy to 60%
scales drawdowns too and compounding is not linear — read it as a ranking, not a forecast.

## 5. What follows

The edge per trade is real, robust across eras, concentrated in the right tail, and largest for
exactly the gates the scorecard emphasises. The failure is **capacity**: 299 mega-caps cannot
generate enough qualifying setups to fill a portfolio.

That is a fixable problem and it names the next test precisely:

1. **Run the same tiers against the full ~5,300-name Minervini cache.** ~18× the universe should
   produce enough signals to lift exposure from 23% into the 60–80% range, which is the only way
   the measured per-trade edge converts into CAGR. **Blocker:** the cache stores close/high/low/
   dolvol but *no open* (`lib.minervini.scan`), so it needs either a broader OHLC fetch or a
   switch to close-based entry.
2. **Re-tier the gates** — promote ADR to required, demote or drop POTENT's `prev_green` and
   ±8% pivot-distance conditions.
3. **Pair selection with an ATR-scaled stop, never a fixed %.** The whole first reading of this
   test was an artifact of that mismatch, and it is the same mistake in live trading.

## 6. Limitations

All of RESULTS.md §5 still applies (survivorship growing with hold length, mega-cap universe
wrong for the style, realized-only drawdown marking, sell-into-strength untested, EOD
resolution). Additionally:

- **Deep tiers are statistically weak.** LEADER t=2.1 (n=493), BOTH t=1.8 (n=319), POTENT t=1.0.
  Directional, not settled. Only GATES (t=6.3) and BREAKOUT (t=4.8) are firm.
- **Survivorship hits the gated tiers hardest.** They hold longest (med 19–22 days) and
  concentrate in high-ADR momentum names, which is exactly where the "still liquid today" filter
  removes the most casualties. The per-trade lift is overstated by an unknown amount.
- **The exposure result is universe-conditional**, and that is the point of next step 1.
