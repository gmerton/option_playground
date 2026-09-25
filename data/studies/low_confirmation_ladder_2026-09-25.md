# Buying great stocks at a discount: the confirmation ladder off a pullback low (2026-09-25)

Script: `run_low_confirmation_ladder.py` (pre-registered 6f778f1). Log: `data/studies/logs/low_confirmation_ladder.log`;
entries `logs/low_confirmation_ladder_entries.csv`; table `low_confirmation_ladder_2026-09-25.csv`.

⚠ **Post-registration fix, disclosed.** The first run cut the control's ADR terciles on the *population's* own names
and required ≥ 30 per date. That left most precision-tier entries with no control (P1 halves = NaN, 2 years of data).
Terciles are now cut on the full liquid cross-section, falling back to all same-date population names if a cell has
fewer than 5. Coverage: P1 64%, P2 96%. The design is otherwise unchanged, but the passing numbers below exist only
after that fix.

## Verdict: PRIMARY FAIL · the confirmation ladder adds NOTHING · P2 "buy the dip in an uptrend" passes the bar → PARKED (survivorship) · MECHANISM

3,478 precision-tier (P1) and 18,947 broad-uptrend (P2) pullbacks of ≥ 1 ADR from a 10-session high, 2010→2026.
Control = same-date names in the same population and ADR tercile, not themselves pulling back.

**The curve (P1; P2 is nearly identical):**

| rung | fires | low holds 20d | premium over the low | fwd20 | P1 excess (t) | P2 excess (t) |
|---|---|---|---|---|---|---|
| K0 buy the 1-ADR dip | 100% | 13% | 0.35 ADR | +1.88% | −0.36 (−0.37) | **+1.07 (+4.16)** |
| **K1 close > low-bar high (PRIMARY)** | 76% | 38% | 1.24 | +2.09% | **+0.58 (+0.67)** | +1.10 (+3.94) |
| K2 + 2-bar higher low | 69% | 42% | 1.33 | +2.06% | +0.57 (+0.71) | +1.39 (+5.16) |
| K3 close > 5 EMA | 87% | 33% | 1.02 | +1.96% | +0.84 (+0.98) | +1.33 (+5.50) |
| K4 close > 21 EMA | 87% | 28% | 0.84 | +2.01% | +0.21 (+0.27) | +0.98 (+3.27) |
| K5 close > prior high | 69% | 59% | 2.28 | +2.17% | +1.51 (+1.08) | +0.69 (+2.53) |

- **The "reliably exiting the low" signal does not exist on daily bars.** Confirmation raises the hold rate from 13% to
  59%, but it charges almost exactly for it: forward returns are flat across the ladder (+1.9 to +2.2%), and every rung
  vs simply buying the dip has t ≤ 2.5 (P1) and ≤ 1.7 (P2). You pay for certainty in price, one-for-one. This
  confirms the 9/23 reclaim-vs-pullback result from the other side.
- **The primary (precision tier, K1) fails:** +0.58pp, t 0.67.
- **What passes is the DIP, not the confirmation.** In the broad uptrend (P2), every rung from K0 up beats same-date
  uptrend names that did *not* pull back by +0.7 to +1.4pp over 20 sessions, at t 2.5–5.5, 15–16 of 17 years, both
  halves positive. That is short-term reversal inside an uptrend: *given an uptrending name, one that just dipped
  1 ADR beats one that didn't, over the next month.*
- ⚠ **Why PARKED, not ADOPTED: survivorship.** The panel holds only names liquid in 2026. Uptrend names whose dip turned
  into a collapse (and later a delisting) are missing, and that bias flatters exactly this test: dip vs no-dip (see
  DATA_CATALOG §7). A +1pp/month edge is the same order as a plausible survivorship lift, so it cannot be told apart
  here.
- ⛔ **RETRACTED 2026-09-25 (look-ahead: the support tag used the episode's final low). Fixed numbers: P1 +1.71pp t 1.75, P2 +0.45 t 1.08 (below non-support +1.50). See dip_survivorship_2026-09-25.md.** Original text: **Global-minimum bonus (exploratory, not bar-bearing):** lows at support (within 0.5 ADR of the 50 SMA, 200 SMA or
  prior base high) at K1: P1 **+3.47pp t 3.63** (n 838) vs −0.78 elsewhere; P2 +2.00 t 4.75 vs +0.81. Hold rates are the
  same (39–41% vs 36–38%), so support does not make the low hold *more often*; the ones that hold go further. This is
  the most interesting lead, and it is exploratory: it would need its own pre-registration and a holdout.

## Next (candidates, not run)
1. **Survivorship check** for P2 K0/K3: rebuild spot for delisted optionable names from `options_daily_v3` chains
   (`chain_spot.py`), or a forward lockbox from 2026-10. No adoption before one of these.
2. **Support-low pre-registration.** ⚠ Corrected 2026-09-25: an earlier draft proposed 2010–2017 as a holdout. That is
   wrong, because the exploratory look pooled ALL years, so no in-panel holdout exists. The holdout is the names NOT in
   the panel. Both follow-ups are pre-registered in `run_dip_survivorship.py` on `silver.chain_spot_daily`.
