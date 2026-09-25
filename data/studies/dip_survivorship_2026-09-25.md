# Dip-in-uptrend survivorship check + support-low holdout (2026-09-25)

Script: `run_dip_survivorship.py` (pre-registered b070627). New data: `silver.chain_spot_daily`
(`run_build_chain_spot_daily.py`): raw daily spot for **10,836 optionable tickers incl. delisted**, 2010→2026, from
put-call parity (median of the 3 nearest-the-money strikes, expiry nearest 30 DTE); spot-checked within ~0.4% of real
closes. Log: `data/studies/logs/dip_survivorship.log`.

## Verdict: support-low lead RETRACTED (look-ahead bug) · survivorship question UNRESOLVED (method check failed) · METHOD

**1. The "low at support" lead was a look-ahead artefact. RETRACTED.** Both this script and the ladder tagged support
using the episode's *final* low, including lows made after the entry. With the tag judged on the low known at entry:
- ladder P1 K1 at support: **+3.47pp t 3.63 → +1.71pp t 1.75**; P2: **+2.00 t 4.75 → +0.45 t 1.08**, now *below*
  non-support lows (+1.50);
- holdout (non-panel names, T3): **+2.15pp t 5.01 → +0.25pp t 0.58, FAIL**; P1 −0.57 t −0.55.
- With the fix, lows at support hold no more often (37–40% vs 38%) and earn no more.

**2. The survivorship test is uninterpretable, per its own pre-registration.** T1, the method check, was required to
reproduce the ladder's +1pp dip effect on the survivor names with the close-only translation. Instead it gave
**−0.88pp (t −3.79)** on SURV, and −0.77 on ALL, −0.68 on NONSURV. Because the survivor result flips sign, the
translation (closes-only ADR proxy × 1.88, close-based peaks and lows, option-volume liquidity, a chain-spot price
source) does not measure the same thing. So the ALL/NONSURV comparison cannot answer the survivorship question.
(The automatic "SURVIVORSHIP ARTEFACT" line in the log is overridden by the pre-registered T1 rule.)

**What it does say:** the ladder's +1pp "dip in an uptrend" effect is **fragile to definition**. A close-only version
of the same idea is −0.9pp on the same names. An edge that flips sign under a reasonable re-specification is not
adoptable, whatever the cause. The ladder's P2 result stays **PARKED**, now with a fragility note as well as the
survivorship caveat.

## What it taught
- **METHOD:** look-ahead can hide in a *tag*, not only in an entry. Any label computed after an episode ends ("was the
  low at support?") must use only what was known at the entry bar. The ladder's exploratory lead passed t 3.6 on
  exactly this bug, which is the house rule (a clean result is a bug until proven otherwise) earning its keep.
- **Reusable data:** `silver.chain_spot_daily` is the first price series that includes delisted names (optionable
  only, closes only, raw; adjust splits with `pit/splits.parquet`). It is the partial fix for DATA_CATALOG §7's
  survivorship blind spot.
- **Next, if pursued:** isolate the T1 failure by running the close-only definitions on the survivor panel's own
  adjusted closes. That separates "the price source differs" from "the definitions differ". Only after T1 reproduces
  can survivorship be judged.
