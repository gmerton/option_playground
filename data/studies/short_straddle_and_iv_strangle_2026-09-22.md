# Two unread studies, read — 2026-09-22

`run_short_straddle_study.py` and `run_iv_condor_study.py` were committed, had caches on disk, and had
**no result doc and no TEST_INDEX row**. Run today. One is a clean null that strengthens the long
straddle; the other is **invalid** and its output has been quarantined.

⚠ **Neither wires `costs.py`.** Both are mid-priced (`grep costs|slippage|commission` → no hits;
the delta-hedged engine uses `(bid+ask)/2`). A mid-priced result **can kill a cell, never certify one** —
so the negative findings below stand and the positive ones do not.

---

## 1. Short 7-DTE ATM straddle — NULL, and a mirror-image confirmation of the long side

41,757 trades, 317 tickers, 2018-04 → 2026-02. Pre-registered H1/H2/H3.

| arm | n | win% | mean% | 95% CI |
|---|---|---|---|---|
| **all trades, no gate** | 41,757 | 58.3 | **−1.83** | [−5.26, +1.52] |
| FVR ≤ 0.80 | 6,086 | 60.1 | +1.89 | [−2.55, +6.09] |
| **FVR ≥ 1.20** | 13,459 | 57.3 | **−5.04** | **[−8.81, −1.25]** |
| **IV pct ≤ 30** | 13,172 | 57.4 | **−4.51** | **[−9.02, −0.47]** |
| IV pct ≥ 85 | 6,752 | 60.7 | +3.19 | [−2.86, +8.57] |
| FVR ≤ 0.80 AND IVpct ≥ 70 | 2,986 | 60.8 | +3.72 | [−2.58, +9.72] |

**Verdict: NULL as a strategy.** Ungated selling loses (−1.83%) *at mid*, before costs. H1 and H2 are
directionally right but **every positive cell's CI includes zero, while the negative cells' CIs exclude
it.** Walk-forward on the best cell is unstable: 2021 +3.4, 2022 −3.8, 2023 +12.0, 2024 −2.3, 2025 +11.3.
Worst single trade in the best cell = **−1,193% of credit** (unbounded downside).
⚠ The CIs are per-trade; all names enter on the same Fridays, so effective n is ~the date count, not
41,757 — the true intervals are wider still (same trap as `vrp_straddle_reconcile.md`).

**⭐ The real value — it independently confirms the long straddle's two gates by inverting them.**
The long straddle is half the certified pair, and its gates were only ever validated on the long side:

| gate | long straddle | short straddle (this study) |
|---|---|---|
| FVR ≥ 1.20 | the workhorse gate | **seller's worst FVR cell, −5.04, CI excludes 0** |
| IV pct low (≤20/≤30) | the most robust gate in the repo | **seller's worst IV cell, −4.51, CI excludes 0** |

Both gates flip sign for the opposite side of the same trade, on the same pool, at significance. That is
a genuine out-of-sample-in-direction check the book did not previously have.

## 2. IVP-gated short strangle — **INVALID: path truncation via missing marks**

Reported 94–99% win rates and 86–100% average ROC on 0.25Δ short strangles across 2018–2026 **including
2020 and 2022, with zero stops ever triggering.** Not credible. Cause, from the trade log:

**`mark_cov` = share of holding days with a usable option mark. Median 14.3%. 67% of trades below 25%.**
With no path visible, the engine cannot fire the 50% take or the 2× stop and books the trade as
`expiry_win` at the full credit.

| mark coverage | n | mean ROC | win% | share booked `expiry_win` |
|---|---|---|---|---|
| <10% | 4,581 | **+62.9%** | 83.9 | **83.9%** |
| 10–25% | 2,483 | +58.7% | 83.7 | 82.8% |
| 25–50% | 695 | −0.4% | 65.8 | 31.5% |
| 50–75% | 2,773 | **+14.1%** | 76.8 | **2.8%** |
| >75% | 0 | — | — | — |

**The return is a pure function of how much of the path the engine could see.** No trade anywhere in the
sample has >75% coverage. The best-observed subset gives +14.2% on credit at 77% win — still mid-priced,
still upward-biased, and not a result.

⚠ **Same failure mode as the 2026-09-16 calendar erratum** (path truncation hid losses) — an independent
instance in a different engine. Any study reading `data/cache/iv_*` parquets (built 2026-07-27) inherits it.

**Actions taken:** output quarantined as `INVALID_strangle_trades_2026-09-22.csv`. The script needs a
minimum-coverage guard (skip or flag trades below ~50%) before it produces anything quotable.

## 3. Delta-hedged straddle — not a study

`run_delta_hedged_straddle.py` is a **single-ticker, 30-DTE, 3-month inspector**, mid-priced, and returns
0 rows for any recent window because v3 greeks end ~2026-05. It cannot test the positive-gamma mechanism
as written; that would need a panel build.

## How to apply

- Don't re-propose short strangle/straddle premium on this pool. Ungated selling is negative at mid.
- **Do** cite this as support for the long straddle's FVR and IV gates — it is the mirror test.
- Before any further use of `run_iv_condor_study.py`, add the coverage guard.
- Standing rule reinforced: **mid-priced output kills, never certifies.**

Related: [[project_vrp_straddle_reconcile]], [[project_calendar_path_study]],
[[feedback_price_at_real_fills]], [[project_what_survives_2026_09]].
