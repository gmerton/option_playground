# Paid-to-wait put spread: the IV >= 60th-percentile gate with full IV coverage + a delta-matched stock control (2026-09-29)

## Pre-registration (written BEFORE the IV pull or any gated number; do not edit this section after the results)

**Why.** Audit step 3 item 5 (`audit_top_down_2026-09-25.md` List A #5). The gate "sell the SETUP-name 30/15Δ put spread
only when the name's 30-day IV is ≥ its own 60th percentile" was the whole edge in `paid_to_wait_study.md` (+5.7% net
on max loss) but was known for only 382 of 1,548 spreads (129 gated); gated t 1.53, gated − ungated t 2.29. No
delta-matched stock control was ever run. It is live-adjacent (`run_putspread_scan.py`, paper only, NOT CERTIFIED).

**Trades (frozen).** The existing 1,548 spreads in `data/studies/paid_to_wait_events.csv` (SETUP Fridays 2019-10 →
2026-02, 30/15Δ put spread ~35 DTE from v3 bid/ask, house costs, **hold to expiry**, `roc_hold_net` on max loss).
No new trades are built. (Extending events to 2010 needs a v3 leg pull → separate, needs Gabe's OK.)

**New IV gate.** `silver.options_iv_daily.call50_iv` (≈ ATM 30-DTE IV, quoted legs) for the event's ticker; percentile
of the entry-date value within that ticker's trailing 252 sessions ending on the entry date (min 126 observations).
**Gated = percentile ≥ 0.60.** Events with no percentile are dropped from both arms and counted.
Sanity (reported): agreement with the original `iv_pct` gate on the events where both exist.

**Delta-matched stock control.** Per spread, a long stock position of the spread's nominal net delta (+0.15 share per
spread share: short −0.30Δ, long −0.15Δ), entry close → the close on expiry (the panel prices the spread already
settles on), 5 bp/side, return on the same max-loss capital: `0.15 × (S_exp − S_entry) / max_loss`, minus costs.

**Primary (both required; month-clustered t on entry-month means).**
1. **Gate effect:** gated − ungated `roc_hold_net`: > 0, **t ≥ 3.2**, both halves positive (split 2023-01-01).
2. **Beats its stock:** gated events, `roc_hold_net − stock_dm`: > 0, **t ≥ 3.2**, both halves positive.
**Charge:** second look at the same gate on overlapping events (k = 2) → 3.2.

**Reported, not in the bar:** gated `roc_hold_net` alone (mean, t, win), per year, by regime state; the put25_iv
version of the gate; the 0.13-of-spread slippage calibration is NOT applied (house 0.25 stays, as in the original).

**Read.** Pass both → the gate is SUPPORTED (paper trade with the correct gate, still no size until forward data).
Fail 1 → the gate does not separate outcomes → the paid-to-wait put spread goes NULL. Pass 1, fail 2 → the gate works
but the spread is not better than holding 0.15 delta of stock → NULL as a *vehicle* (stock instead).

---

## Results (run 2026-09-29, after the pre-registration above was committed in a0b69fa; `run_paid_to_wait_iv_gate.py`, `.log`, `.csv`)

**Verdict: NULL. With full IV coverage the gate does not separate outcomes, and every version of the spread loses to
holding 0.15 delta of the same stock. The paid-to-wait put spread is closed.**

IV percentile now known for 98.8% of events (was 24.7%); new gate agrees with the old one on 80% of the 382 overlap
events (rank corr 0.71). Gated 468 / ungated 1,062.

| cell | mean (% of max loss) | month t | halves (2019–22 / 2023–26) |
|---|---|---|---|
| gated `roc_hold_net` | **−1.45%** (win 75%) | −0.93 | −6.09 / −1.33 |
| ungated `roc_hold_net` | −4.27% | −1.65 | −5.20 / −6.32 |
| **P1 gated − ungated** | +4.92pp | **1.33** (bar 3.2) | +6.36 / +3.53 |
| **P2 gated spread − Δ-matched stock** | **−9.08pp** | **−3.21** | −10.06 / −9.85 |
| put25 gate: gated − ungated | +0.71pp | 0.15 | |

- The original +5.7% on 129 gated events does not survive coverage: on 468 gated events the spread **loses −1.45% net**.
  The gate's lead over ungated (+4.9pp) is the same sign but t 1.33, and the put-25Δ version of the gate is ~0.
- **The stock beats the spread significantly** (t −3.2, both halves, 7 of 8 years): the SETUP names went up (+7.6% of
  max-loss capital for 0.15Δ of stock) and the short put spread's capped credit, costs and gap losses gave that away.
- Only the bear states were positive for the gated spread (bear/B+ +8.4%, n 106; bear/B− +15.2%, n 19) — exploratory.

**What it means for the book now.** Stop the paper paid-to-wait put spread: as a way to "get paid while waiting" for a
SETUP name it is worse than simply owning a small stock position. `run_putspread_scan.py` (Thu) has no tested edge
behind it; per the working rule it should be treated as retired unless Gabe wants the bear-state lead pre-registered.
