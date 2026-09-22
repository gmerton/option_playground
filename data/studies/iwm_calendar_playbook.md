> **2026-09-16:** the ETF structure is now the SAME-EXPIRY IRON CONDOR at the same strikes (0.35Δ shorts, ~2% wings, ~20 DTE, hold to expiry, size on width − credit): +31.8 / +41.4% on max risk vs the diagonal's +19.1 / +27.0% on paired entries, every ticker / regime / year. See `double_calendar_playbook.md` (step 11).

> **2026-09-15 evening:** IWM entries are now DOUBLE DIAGONALS -- long legs 2% of spot wider than the 0.35-delta shorts (rev from 1% the same evening, width sweep), sized on max risk = net debit + wing width. See `double_calendar_playbook.md` (structure update) and `calendar_path_study.md` step 7.

# IWM double calendar playbook (2026-09-15)

> ## ⚠ NO t ON FILE — 2026-09-22. One of the last acted-on claims without a test statistic.
> The clean calendar path re-run (`calendar_path_study.md`, after the 2026-09-16 truncation erratum) found **no edge in any ETF calendar**. This was added Tier B on the pre-erratum evidence. Treat as unsupported until measured.


Source: `data/studies/calendar_path_study.md`, double-calendar step (real daily bid/ask 2018-11 → 2026-07, house cost
model on four legs). The single ATM put calendar (+9% / +14%) was replaced the same day by the symmetric 0.35-delta
double calendar.

| sym 0.35Δ double, hold | n | ROC | Win | 2018–mid-2022 | mid-2022–2026 |
|---|---|---|---|---|---|
| Short ~20 DTE / long ~27 (the screener's structure) | 335 | +25.6% | 64% | +22.9% | +28.1% |
| Short ~12 DTE / long ~19 | 342 | +15.4% | 63% | +12.9% | +17.7% |

**Entry:** Friday. Short put at 0.35Δ and short call at 0.35Δ on the ~20-DTE expiry, long put and long call at the same
strikes on the next weekly (gap 5–9 days). Each leg's bid-ask ≤ 25% (screener gate); the whole structure's bid-ask was
6–13% of the debit in the study. No term-structure or IV gate. Regime: enter in every regime; Bear_LoVIX is the weak
cell (+16%, small n) and Bull_LoVIX was NEGATIVE before mid-2022 (−4.7%) and +25% after -- size the bull-low-VIX
entries smaller if you want to respect that.

**Management:** HOLD to the short expiry. Paired against hold: profit takes −2 to −8pp (they raise the win rate to
70%+ and cut the mean), stops rarely trigger, re-centering −4pp, closing the far side when a strike is tested −10pp,
closing a side at half its debit −3pp, the term-structure-inversion exit −16pp. At the short expiry both short legs
settle at intrinsic; sell both long legs at the close.

**Size:** Tier B; the debit is the max loss (~1.2 on IWM). Win rate ~60%, right tail fat.

**Caveats:** 2019 was the one negative year (−11%); overlapping weekly entries mean the trade-level t overstates
independence (monthly-mean t 6.3). bid/ask data end July 2026; re-cut when it extends. Not tested: rolling the short
legs at expiry; unequal deltas other than 0.35/0.10 (which was much worse).
