# UVXY Reverse Wheel — Tested and REJECTED

**Run date:** 2026-08-10
**Verdict:** Rejected. Max drawdown exceeds total profit in every variant, including
defined-risk versions. The existing bear-call-spread playbook dominates it on every axis.
**Scripts:** `run_uvxy_reverse_wheel.py` · output `uvxy_reverse_wheel.csv`

---

## The idea

Harvest UVXY's structural decay by wheeling it short:

1. Sell a 50Δ call (~20 DTE)
2. If it expires ITM, accept assignment → **short 100 shares** at the strike
3. Write a put, collect premium, repeat
4. When the put is assigned, buy back the shares → flat → return to step 1

Directionally sound in premise. UVXY is 1.5× VIX futures with persistent contango roll,
so being short is the right side.

---

## Why the premise is right but the trade is wrong

UVXY 20-trading-day forward moves, 2012–2026, spot derived by put-call parity,
split-spanning windows excluded (n = 3,355):

| Statistic | Value |
|---|---:|
| **Median** | **−12.26%** |
| Down windows | 69.6% |
| p25 | −23.9% |
| p75 | +5.1% |
| **Mean** | **+12.82%** |
| p95 | +138.4% |
| p99 | **+525.6%** |
| Max | **+1,332%** |

**Median −12.26%, mean +12.82%.** The decay is real, but the right tail dominates the
expectation. A reverse wheel is short that tail at every stage — naked calls before
assignment, naked shares after — with nothing capping either.

Short 100 shares at $21 is $2,100 notional. A p99 move means covering near $131:
**~$11,000 of loss on a $2,100 position.**

---

## Backtest — 1 contract / 100 shares, 20 DTE legs, 2018-01 → 2026-02

Spot derived per date via put-call parity (UVXY's Tradier prices are not on the same
scale as historical Athena strikes, which is why other UVXY studies avoid underlying
prices entirely — parity sidesteps it). Reverse splits applied to the live position:
2018-09-18 1:5 · 2021-05-26 1:10 · 2023-06-23 1:10 · 2024-04-11 1:5 · 2025-11-20 1:5.

| Variant | Borrow | Cycles | Final P&L | Max DD | % time short |
|---|---:|---:|---:|---:|---:|
| **A** put @ short basis | 0% | 141 | **+$6,108** | **−$7,678** | 66.7% |
| A | 5% | 141 | +$5,582 | −$7,694 | |
| A | 15% | 141 | +$4,530 | −$7,726 | |
| **B** put @ 50Δ (normal roll) | 0% | 141 | **+$391** | **−$7,187** | 31.2% |
| B | 5% | 141 | +$123 | −$7,203 | |
| B | 15% | 141 | **−$415** | −$7,236 | |

### The mechanic that makes variant A look profitable is the one that makes it useless

Putting the put at the **short basis** means assignment always covers at the price you
shorted — **share P&L is exactly zero by construction.** Every dollar of the $6,108 is
premium; the share leg contributes only drawdown. It is not a wheel harvesting decay, it
is naked premium selling with an unbounded short attached, holding that short **66.7% of
the time**.

Variant B — put at the current 50Δ, so assignment covers *below* the basis — is the
version that could actually capture the decay. It earns **+$391 over eight years** and
goes negative at a 15% borrow rate.

### Variant B by year

| Year | P&L | Cumulative |
|---|---:|---:|
| 2018 | −$511 | −$511 |
| 2019 | +$3,115 | +$2,604 |
| 2020 | −$1,270 | +$1,334 |
| 2021 | −$474 | +$860 |
| 2022 | +$591 | +$1,451 |
| 2023 | −$403 | +$1,048 |
| **2024** | **−$3,040** | −$1,991 |
| 2025 | +$1,918 | −$74 |

Negative in five of nine years; 2024 alone erased three years of gains.

---

## Defined-risk variant — long protective call against the short shares

Buy an OTM call each cycle while short, capping the pair's loss at
`(K_protect − K_basis) × 100`. Variant A, 0% borrow:

| Protection | Final P&L | Max DD | Protection cost |
|---|---:|---:|---:|
| None | +$6,108 | −$7,678 | — |
| **0.10Δ** | **+$5,338** | **−$5,554** | $7,856 |
| 0.20Δ | +$3,392 | −$6,340 | $11,121 |
| 0.30Δ | +$852 | −$6,989 | $14,892 |

0.10Δ is the best setting — gives up $770 of profit to cut drawdown by $2,124. But
**even then max DD ($5,554) exceeds total profit ($5,338) over eight years.**

Note the perverse ordering: **richer protection produced worse drawdowns.** At 0.30Δ the
$14,892 spent on calls becomes its own slow bleed, so the drawdown stops being spike-driven
and becomes cost-driven. Variant B stays at or below zero under every protection setting.

---

## Not modelled (all would make results worse, none better)

- **Borrow cost beyond 15%.** UVXY is periodically hard-to-borrow; a genuine squeeze
  would exceed the swept range.
- **Early assignment.** American-style; short calls get assigned early precisely during
  spikes, when it hurts most.
- **Margin calls.** A −$7,678 drawdown on $2,100 of notional would very likely force
  covering at the worst available price. The realised outcome is worse than shown.

---

## Why the existing playbook wins

| | Reverse wheel (best case) | Current 0.50/0.40 bear call spread |
|---|---|---|
| Risk | unbounded (or capped only by paid protection) | **defined by construction** |
| Max loss/contract | −$5,554 realised drawdown | **~$117 median** |
| Short share exposure | 31–67% of the time | none |
| Borrow cost | yes | none |
| Assignment risk | yes | none |
| Return | +$5,338 over 8 years | **+5.06% ROC/trade, 74.6% win** |

The current playbook already harvests UVXY's decay through a structure with none of these
exposures. The reverse wheel takes on all of them to produce less.

---

## Related rejections

- **Naked short straddle** (`uvxy_short_straddle_20dte.md`) — 75.5% win rate *and*
  −370% annualised ROC in 2020. Same lesson: UVXY's right tail destroys unbounded shorts.
- **Put calendar** (tested 2026-03-04) — UVXY's moves destroy the ATM pin; −93% in 2021.

The pattern across all three: strategies that win most of the time on UVXY lose more than
they make when they lose, unless risk is defined at entry.
