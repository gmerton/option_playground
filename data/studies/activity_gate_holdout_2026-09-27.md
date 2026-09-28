# Breakout-activity gate on the 2010–19 holdout (2026-09-27)

`run_activity_gate_holdout.py` (pre-registered; frozen from `run_breakout_activity_gate.py`). Log
`logs/activity_gate_holdout.log`. AUDIT STEP 3 item 2.

## Verdict: FAILS OUT OF TIME — it reverses sign · the 2019–26 PARKED result is RETRACTED

390 precision-tier trades, 2010-01 → 2019-09 (the survivor panel is thin before 2019), pooled mean −0.64R.

| cnt_pct (trailing-252 percentile of the prior N-session breakout count) | Q1 → Q5 mean R | top − bottom | t |
|---|---|---|---|
| **cnt5 (PRIMARY)** | −0.42 … −1.10 | **−0.69R** | **−2.59** (halves −0.78 / −0.32, 1/6 yrs +) |
| cnt10 | −0.70 … −0.80 | −0.10R | −0.32 |
| cnt20 | −0.39 … −0.57 | −0.18R | −0.50 |

vs xname −0.14 (t −0.48); vs post −0.74 (t −1.64); % return −2.21pp (t −1.70). Plateau fails.

## Read
- The in-sample finding (2019–26: busiest weeks +0.81R better, t 2.59) is the same size **with the opposite sign**
  out of time. Together with the missing plateau in both samples, the best reading is noise: the gate doesn't know
  when to press. PARKED → RETRACTED.
- Consistent with every market-state gate tried (index 10/20 filter, breadth deferral, distribution days) and with
  the adaptive-trader sim: neither the market's recent activity nor your own recent results tell you when to press.
- ⚠ Side note: the precision tier itself averages −0.64R on this holdout (390 trades; thin, survivor-biased
  panel). The tier's WEAK in-sample status and its freeze-forward NULL already said it isn't certified; this is
  another out-of-time data point in the same direction.
