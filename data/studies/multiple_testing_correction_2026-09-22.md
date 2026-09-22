# Ledger-wide multiple-testing correction

_2026-09-22 · `run_multiple_testing_correction.py` · data `multiple_testing_correction_2026-09-22.csv` · method-upgrades queue item 1_

## Verdict

**Of the 36 claims we act on, 11 are CONFIRMED, 5 SUPPORTED, 2 WEAK, 11 NOT CERTIFIED, and 7 have no test statistic
on file at all.** What survives is lopsided: the confirmed POSITIVE edges are all **index options + dealer gamma**
(the SPY 1-day short straddle / 2× fly / put spread on positive-gamma days, the gamma→realised-vol link, the 10-day
VRP). Most of the other confirmed results are **vetoes** (things that lose). The book's own legs do worse:

- **7-DTE straddle: SUPPORTED** (t 3.7, 8 variants → survives BH 5% at M=125, not at M=400).
- **Precision-tier breakout: WEAK** (t 3.3 trade-weighted, 10 variants → BH 10% only; and month-weighted it is −0.04).
- **Straddle + bull put PAIR: NOT CERTIFIED** (t 2.5, 3 variants). Neither leg alone gets there (bull put t 1.2).
- **Every PARKED near-miss is NOT CERTIFIED** after the within-row charge: HYB-B (t 2.6, k 4), earnings drift
  good+MUTED (t 2.65, k 6), PEAD tape (1.89), retrace (0.48), gap share (1.71). They stay parked for the forward
  lockbox; none may be promoted on current evidence.
- **Seven claims we act on have no t on file:** the size lever (exclusion), the SPX condor / QQQ-SPY bull put regime
  playbooks (Tier A/B, ~30 regime×ticker cells), the SPY/IWM calendars, event-convexity calls vs random dates,
  Sleeping Giants, paid-to-wait IV gate, and the straddle-stop removal (0/20 variants, no single t). The Tier A/B
  playbooks are IN BOOK with no certifiable statistic — the biggest gap this pass exposes.

## Method

- **Unit = one research question** (a TEST_INDEX row). M = 125 at row level (§1–§9 rows that ran a test); **stress
  M = 400** at cell level (every recorded cell incl. the 69-row pattern ledger). The ~90 null/fail rows enter with
  p = 1 — they were tested and count against the rest.
- **Within-row search charged with Šidák:** a row that tried k variants and reports its best t gets
  p_k = 1 − (1 − p)^k. k is from the row text (e.g. breakout tier chosen among ~10 validation cuts).
- **Lenses:** Benjamini–Hochberg FDR at 5% / 10% (share of false discoveries among what is kept), Holm familywise 5%,
  Harvey–Liu–Zhu raw |t| ≥ 3. For one claim with k = 1, Bonferroni needs t ≥ 3.54 (M=125) / 3.84 (M=400).
- **Verdicts:** CONFIRMED = BH 5% at both M; SUPPORTED = BH 5% at M=125 only (or 10% at both); WEAK = BH 10% at
  M=125 only; NOT CERTIFIED otherwise; NO t ON FILE where no statistic exists.

⚠ Caveats: k is a judgement from the row text (undercounts are likely → the correction is if anything lenient);
t-stats mix clustering schemes (date / month / trade); related claims (straddle → fly → put spread) are dependent,
which BH tolerates; two-sided p throughout.

## Table

| group | claim | t | k | Šidák p | BH 5% M125 | BH 10% M125 | BH 5% M400 | Holm M125 | |t|≥3 | verdict | use |
|---|---|---|---|---|---|---|---|---|---|---|---|
| book | Straddle + bull put PAIR (50/50 blend, monthly) | +2.50 | 3 | 3.7e-02 | · | · | · | · | · | **NOT CERTIFIED** | in book |
| book | 7-DTE straddle, both gates, after costs (hold) | +3.70 | 8 | 1.7e-03 | ✓ | ✓ | · | · | ✓ | **SUPPORTED** | in book |
| book | Bull put spread leg alone (monthly) | +1.20 | 1 | 2.3e-01 | · | · | · | · | · | **NOT CERTIFIED** | in book (pair leg) |
| book | Precision-tier breakout, close entry, cap 20 (date-clustered) | +3.30 | 10 | 9.6e-03 | · | ✓ | · | · | ✓ | **WEAK** | in book |
| book | same, MONTH-weighted (2026-09-22) | -0.04 | 1 | 9.7e-01 | · | · | · | · | · | **NOT CERTIFIED** | caveat |
| book | Size lever = exclusion (A+B only, +0.29R OOS) | — | 3 | — | · | · | · | · | · | **NO t ON FILE** | in book |
| book | SPX condors / QQQ-SPY bull puts by regime (Tier A/B) | — | 30 | — | · | · | · | · | · | **NO t ON FILE** | in book |
| book | SPY double calendar / IWM put calendar (Tier B) | — | 6 | — | · | · | · | · | · | **NO t ON FILE** | in book |
| index | SPY negative dealer gamma -> +8% realised vol beyond VIX | +7.70 | 3 | 4.1e-14 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | vol input |
| index | SPY 1-day SHORT straddle on positive-gamma days | +5.60 | 2 | 4.3e-08 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | -> fly paper trade |
| index | SPY 1-day 2x iron fly on positive-gamma days | +3.40 | 2 | 1.3e-03 | ✓ | ✓ | ✓ | · | ✓ | **CONFIRMED** | paper trading from 9/22 |
| index | SPY 1-day put credit spread on positive-gamma days | +3.50 | 2 | 9.3e-04 | ✓ | ✓ | ✓ | · | ✓ | **CONFIRMED** | logged, not traded |
| index | Gamma edge holds on weekdays only (not a weekend artefact) | +3.90 | 1 | 9.6e-05 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | robustness |
| index | 10-day variance risk premium (IV > realised) | +8.90 | 3 | 0.0e+00 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | mechanism |
| index | QQQ noise-band momentum, negative-gamma days | +2.92 | 2 | 7.0e-03 | · | ✓ | · | · | · | **WEAK** | UNDERPOWERED near miss |
| parked | HYB-B universe (TT at $100M + ADR>=4) | +2.60 | 4 | 3.7e-02 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | Earnings drift good+MUTED (ledger) | +2.65 | 6 | 4.7e-02 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | PEAD tape signal on the straddle pool | +1.89 | 2 | 1.1e-01 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | Earnings vol premium, liquid names, at the bid | +1.10 | 3 | 6.1e-01 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | Retrace entry vs breakout | +0.48 | 6 | 1.0e+00 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | Gap-share selection sort (edge vs same-name control) | +1.71 | 9 | 5.6e-01 | · | · | · | · | · | **NOT CERTIFIED** | PARKED |
| parked | Event-convexity 0.12d over 0.25d at real fills | +0.29 | 2 | 9.5e-01 | · | · | · | · | · | **NOT CERTIFIED** | strike choice |
| parked | Event convexity calls vs random dates | — | 4 | — | · | · | · | · | · | **NO t ON FILE** | lottery sizing |
| parked | Sleeping Giants cheap LEAPs | — | 3 | — | · | · | · | · | · | **NO t ON FILE** | MARGINAL |
| parked | Paid-to-wait put spreads, IV >= 60th pct gate | — | 4 | — | · | · | · | · | · | **NO t ON FILE** | MARGINAL |
| veto/mech | Buy the CLOSE, not an intraday entry (paired) | +3.40 | 4 | 2.7e-03 | ✓ | ✓ | · | · | ✓ | **SUPPORTED** | house process |
| veto/mech | ORB9 stop floor 0.6 ADR | +3.40 | 4 | 2.7e-03 | ✓ | ✓ | · | · | ✓ | **SUPPORTED** | adopted |
| veto/mech | Alert-price entry worse than the close entry | +3.20 | 2 | 2.7e-03 | ✓ | ✓ | · | · | ✓ | **SUPPORTED** | alerts = info only |
| veto/mech | Tightening a stop when extended INVERTS (10-EMA) | +4.80 | 8 | 1.3e-05 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | veto |
| veto/mech | Leading-group filter INVERTS (bottom-3 > top-3) | +2.60 | 3 | 2.8e-02 | · | · | · | · | · | **NOT CERTIFIED** | veto / context only |
| veto/mech | Closing a put spread on the break costs | +5.80 | 1 | 6.6e-09 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | never close on the break |
| veto/mech | Earnings calendar loses at every back leg (liquid, limit fill) | +3.30 | 3 | 2.9e-03 | ✓ | ✓ | · | · | ✓ | **SUPPORTED** | veto |
| veto/mech | Event call as a debit spread: 2nd leg friction | +5.51 | 2 | 7.2e-08 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | veto |
| veto/mech | Intraday alert arms lose (Stage A stop-close) | +4.30 | 5 | 8.5e-05 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | no day-trading book |
| veto/mech | VWAP double-rejection short worse than random | +6.20 | 2 | 1.1e-09 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | veto |
| veto/mech | Straddle -50% stop is a cost (0/20 variants beat hold) | — | 20 | — | · | · | · | · | · | **NO t ON FILE** | stop removed |

## What changes

1. **Book status** — keep the pair and the breakout at fixed small size (they are the best we have), but the index
   now labels them SUPPORTED (straddle), WEAK (breakout) and NOT CERTIFIED (the pair / bull put), not "IN BOOK" alone.
2. **Compute a t for the seven uncertified claims**, starting with the SPX condor / QQQ-SPY bull put regime
   playbooks (IN BOOK, Tier A/B, no statistic, ~30 cells searched) and the size-lever exclusion.
3. **Forward lockbox** (queue item 5) is now the only route for every PARKED row: data from 2026-09-22 on,
   untouched, one confirmation run ~2027-03.
4. **Where to look next:** the confirmed positive edges cluster in index options conditioned on dealer gamma. The
   SPY 2× fly paper trade is the live test of that family.
