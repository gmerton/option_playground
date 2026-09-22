# VWAP double-rejection short (2026-09-21) — FAIL

**Verdict: NULL / worse than random. The 2nd-touch rejection short loses −0.26R held to the close (t −6.2) vs a random
minute in the same name-day at −0.17R; the 1st touch is no better than random either. Negative in both halves and on
both universe sets. YIELD: the 2nd rejection is WORSE than the 1st, the opposite of the idea.**

Prompted by SNDK 9/21 (open +1.9%, flush to 1785 in 5 min, lost VWAP 09:55, stalled under / poked VWAP 10:20–10:40,
slid to 1737). Script `run_vwap_rejection_short.py`, log `vwap_rejection_short_2026-09-21.log`, 2 ledger rows.

## Rule (pre-registered, ADR units, not fitted to SNDK)

Setup: by 10:30 the session low ≥ 0.3 ADR under the open; VWAP falling vs 30 min earlier. Touch: after ≥10 1-min
closes under VWAP−0.15%, a 1-min high within 0.15% of VWAP. Rejection = first close ≤ VWAP − 0.1 ADR. Killed by any
5-min close > VWAP + 0.1 ADR. Signal = rejection ending touch #2 (or #1), 10:00–14:30; entry next bar open; stop =
touch high + 0.1 ADR. Harness `run_intraday`: control = same name-day, random minute 09:45–15:30.
Cached 1-min bars, 192 names, 2026-02-02 → 09-18 (165 sessions).

Under this rule SNDK 9/21 is ONE touch (price never pulled 0.1 ADR ≈ $10 off VWAP between its two pokes), rejected at
10:43; it would have been a 1st-touch winner. Left as is: loosening the rule to catch the example is fitting.

## Results (R; the harness arms)

| arm | n | per session | hold to close | t | control | edge | cover on VWAP reclaim | halves (close) |
|---|---|---|---|---|---|---|---|---|
| **2nd touch** | 1,900 | 11.5 | **−0.258** | −6.21 | −0.174 | **−0.084** | −0.258 (ctrl −0.268) | −0.32 / −0.20 |
| 1st touch | 2,703 | 17.0 | −0.215 | −5.47 | −0.204 | −0.011 | −0.208 (ctrl −0.247) | −0.25 / −0.18 |

By universe set (hold to close): 2nd touch curated −0.233 / no-hindsight control set −0.320; 1st touch −0.195 / −0.269.
Every exit arm is negative (take +1R, +2R, 30 min, VWAP reclaim, next close); win rate 20–45%.

## Why it fails

It isn't selective: ~12–17 fires per session across the universe. The pattern describes most weak days after their
first hour, and by the time a name has failed at VWAP twice it's already extended down, so the remaining move is
shorter than the stop is wide. The random-minute control is negative too (shorting in a 2026 tape that mostly rose),
and the signal still loses to it. Consistent with the earlier short work: BIR −0.15R over 20 sessions, shorts ~0 or
negative over 153, and no intraday trigger that beats a random minute (Stage A).
