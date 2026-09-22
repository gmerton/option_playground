# Ledger-wide multiple-testing correction

_2026-09-22 · `run_multiple_testing_correction.py` · data `multiple_testing_correction_2026-09-22.csv` · method-upgrades queue item 1_

## Verdict

> **Updated same day** — the Tier A/B regime playbooks now have a t (see the Update section at the end): 14 CONFIRMED · 5 SUPPORTED · 1 WEAK · 15 NOT CERTIFIED · 6 NO t. Only the bearish-high-IV SPY bull put and SPX condor certify; both Tier A labels and QQQ bullish-low-IV fail. The counts directly below are the first pass.

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

---

## Update (same day): Tier A/B regime playbooks now have a t — `run_tierab_significance.py`

The seven IN-BOOK regime cells, run through their own engines with the 2026-09-08 cost model, exactly as the
playbooks / registry / Friday screener trade them (option history ends 2026-02-20). t is on MONTHLY means of net
ROC (weekly entries overlap), Newey-West lag 2 alongside; k = the delta × wing × stop sweep each cell was picked
from (QQQ/SPY 54, SPX 49). Trades in `tierab_trades_2026-09-22.csv`, stats in `tierab_significance_2026-09-22.csv`.

| cell | trades / months | net ROC per trade | win | month-weighted | t (month) | t (NW) | halves (pre / post Jul-2022) | years + | top-year share | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **SPY bull put, bearish high-IV** 0.25/0.15 | 75 / 37 | +6.8% | 95% | +8.7% | **6.07** | 6.36 | +2.6 / +12.3 | 8/9 | 43% | **CONFIRMED** |
| **SPX condor, bearish high-IV** 0.20c/0.30p | 71 / 36 | +9.8% | 79% | +9.6% | **5.21** | 5.32 | +11.6 / +7.3 | 7/8 | 42% | **CONFIRMED** |
| QQQ bull put, bearish high-IV 0.25/0.15 (Tier A) | 78 / 36 | +6.2% | 92% | +7.9% | 3.53 | 3.50 | +2.4 / +12.5 | 8/8 | 45% | NOT CERTIFIED (k 54) |
| SPX condor, bullish high-IV + 200MA 0.20c/0.40p (Tier A) | 47 / 22 | +10.9% | 96% | +8.7% | 2.26 | 2.44 | +10.7 / +11.7 | 5/6 | **51%** | NOT CERTIFIED |
| QQQ bull put, bearish low-IV 0.35/0.15 (not tiered) | 42 / 22 | +7.7% | 90% | +7.1% | 1.74 | 1.84 | +5.7 / +11.0 | 6/8 | 26% | — |
| QQQ bull put, bullish high-IV 0.45/0.35 2× stop (Tier B) | 68 / 29 | +11.8% | 81% | +7.1% | 1.04 | 1.04 | +10.7 / +13.6 | 5/6 | 44% | NOT CERTIFIED |
| **QQQ bull put, bullish low-IV 0.45/0.35 (Tier B)** | 220 / 69 | +3.4% | 80% | **−4.8%** | **−0.87** | −0.86 | −0.2 / +6.7 | 5/9 | 19% | NOT CERTIFIED |

**Reading it:**
- **Two cells certify, and they are the same trade:** sell index put risk after a selloff when VIX ≥ 20 (SPY bull put,
  SPX condor, bearish high-IV). The QQQ version of the same regime (t 3.5) misses only because it was picked from a
  54-cell sweep. These three fire in the SAME stress episodes (2018-Q4, 2020, 2022, 2025-04) — one bet, not three;
  ~43% of trades sit in one year.
- **Both "Tier A" labels fail:** QQQ bearish-high-IV (search penalty) and the SPX bullish-high-IV + 200MA condor
  (t 2.3, 51% of trades in one year — the 2020 concentration flagged on 9/8).
- ⚠ **QQQ bullish-low-IV — the regime that fires most (~27 wks/yr) and the one the screener entered live on 9/8 — has
  no edge:** +3.4% per trade but −4.8% month-weighted (t −0.87); the positive half is post-2022 only.
- The ledger re-run with these seven cells (M 131 / 406) moves two borderline verdicts upward, because BH's line rises
  as more strong p-values enter: the 7-DTE straddle to CONFIRMED (was SUPPORTED) and QQQ noise-band to SUPPORTED
  (was WEAK). Treat both as borderline — their raw evidence did not change.

### Ledger table after the update (M = 131 / 406)

| group | claim | t | k | Šidák p | BH 5% M131 | BH 10% M131 | BH 5% M406 | Holm M131 | |t|≥3 | verdict | use |
|---|---|---|---|---|---|---|---|---|---|---|---|
| book | Straddle + bull put PAIR (50/50 blend, monthly) | +2.50 | 3 | 3.7e-02 | · | · | · | · | · | **NOT CERTIFIED** | in book |
| book | 7-DTE straddle, both gates, after costs (hold) | +3.70 | 8 | 1.7e-03 | ✓ | ✓ | ✓ | · | ✓ | **CONFIRMED** | in book |
| book | Bull put spread leg alone (monthly) | +1.20 | 1 | 2.3e-01 | · | · | · | · | · | **NOT CERTIFIED** | in book (pair leg) |
| book | Precision-tier breakout, close entry, cap 20 (date-clustered) | +3.30 | 10 | 9.6e-03 | · | ✓ | · | · | ✓ | **WEAK** | in book |
| book | same, MONTH-weighted (2026-09-22) | -0.04 | 1 | 9.7e-01 | · | · | · | · | · | **NOT CERTIFIED** | caveat |
| book | Size lever = exclusion (A+B only, +0.29R OOS) | — | 3 | — | · | · | · | · | · | **NO t ON FILE** | in book |
| book | QQQ bull put Bearish_HighIV 0.25/0.15 (Tier A) | +3.53 | 54 | 2.2e-02 | · | · | · | · | ✓ | **NOT CERTIFIED** | in book |
| book | QQQ bull put Bullish_HighIV 0.45/0.35 2x stop (Tier B) | +1.04 | 54 | 1.0e+00 | · | · | · | · | · | **NOT CERTIFIED** | in book |
| book | QQQ bull put Bullish_LowIV 0.45/0.35 (Tier B) | -0.87 | 54 | 1.0e+00 | · | · | · | · | · | **NOT CERTIFIED** | in book |
| book | SPY bull put Bearish_HighIV 0.25/0.15 (Tier B) | +6.07 | 54 | 6.9e-08 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | in book |
| book | SPX condor Bullish_HighIV+200MA 0.20c/0.40p (Tier A) | +2.26 | 49 | 6.9e-01 | · | · | · | · | · | **NOT CERTIFIED** | in book |
| book | SPX condor Bearish_HighIV 0.20c/0.30p (Tier B) | +5.21 | 49 | 9.3e-06 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | in book |
| book | SPY double calendar / IWM put calendar (Tier B) | — | 6 | — | · | · | · | · | · | **NO t ON FILE** | in book |
| index | SPY negative dealer gamma -> +8% realised vol beyond VIX | +7.70 | 3 | 4.1e-14 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | vol input |
| index | SPY 1-day SHORT straddle on positive-gamma days | +5.60 | 2 | 4.3e-08 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | -> fly paper trade |
| index | SPY 1-day 2x iron fly on positive-gamma days | +3.40 | 2 | 1.3e-03 | ✓ | ✓ | ✓ | · | ✓ | **CONFIRMED** | paper trading from 9/22 |
| index | SPY 1-day put credit spread on positive-gamma days | +3.50 | 2 | 9.3e-04 | ✓ | ✓ | ✓ | · | ✓ | **CONFIRMED** | logged, not traded |
| index | Gamma edge holds on weekdays only (not a weekend artefact) | +3.90 | 1 | 9.6e-05 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | robustness |
| index | 10-day variance risk premium (IV > realised) | +8.90 | 3 | 0.0e+00 | ✓ | ✓ | ✓ | ✓ | ✓ | **CONFIRMED** | mechanism |
| index | QQQ noise-band momentum, negative-gamma days | +2.92 | 2 | 7.0e-03 | ✓ | ✓ | · | · | · | **SUPPORTED** | UNDERPOWERED near miss |
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
