# OptionsPlay: "Lose MORE than your Max Loss on a Credit Spread & How to Avoid it" (2021-03-19, 7 min)

_Reviewed 2026-09-24. Scripted explainer. It is the short version of the Biogen webinar (`2025-05-04_m2-bo0kxMu0`)._

## Verdict: 2.5 / 5

Accurate settlement mechanics and no edge claims. It is useful risk hygiene, and it makes no claim we could score as
a strategy. The one rule it prescribes (exit 2–3 weeks before expiry) is the 21-DTE rule, whose only test (re-run
2026-09-24, FIX-1) says it cuts risk but earns less than holding.

**Selection rule:** none. This video is about exits only.

| @ | Claim | Tag | Our evidence |
|---|---|---|---|
| 01:12–02:13 | **Pin risk.** Expiring between the strikes gets the short assigned and the long left unexercised, so you hold naked stock over the weekend | AGREES (mechanics) | Standard physical settlement |
| 00:12–01:24, 23:21* | Doesn't apply to cash-settled index options | AGREES (mechanics) | The SPX half of our certified bucket is exempt; the SPY half is not (*timestamp from the Biogen webinar) |
| 02:16–03:48 | **After-hours exercise of an OTM option** on Friday-evening news (Nike example). Check for post-close events before letting a spread expire | AGREES (mechanics) · Nike example UNVERIFIED | Same mechanism as the Biogen $625k case |
| 03:48–04:31, 06:01 | **Early assignment** doesn't change max risk if you close both the stock and the long leg; it only does if you carry the stock past the long's expiry | AGREES (mechanics) | Correct |
| 04:57–05:28 | **Exit or roll 2–3 weeks before expiry**: you will "never" be pinned and "rarely" be assigned early | AGREES (on assignment and risk) · **NULL, leaning INVERTED (on return)** | This is the 21-DTE rule. `run_21dte_exit_test.py` (TEST_INDEX §1), re-run 2026-09-24 after FIX-1 (the original dropped worthless-expiry winners): 21-DTE close − hold **−$0.52/share, month-clustered t −2.42** (halves −0.63/−0.40; hold +$0.23, 74% win; 21-DTE −$0.29, 64% win) → PASS: NO; risk only (sd $9.33 vs $17.09, worst −$291 vs −$617) |
| 05:28–05:50 | For 1–2-day spreads, close by 3:30–3:45 pm on expiration day | UNTESTED · sensible for physically settled | Our 1-day SPY structures are scored held to expiry at intrinsic (§55, §58). The closing cost vs the pin risk has not been measured |

**What's new / test candidates.** Nothing new. The only testable rule is FIX-1, already queued first for 2026-09-24.
