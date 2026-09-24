# OptionsPlay — "How to Find the Few Earnings Setups Worth Trading" (Tony Zhang, 2026-07-18, 33 min)

_Reviewed 2026-09-24. A Growth Lab session (week 2 of the July "idea generation" series) that demos the new
dashboard's **earnings calendar**. About 9 minutes of macro (03:28–13:04: an EPS-growth recap, the Q2
outlook, Middle East/inflation) are skipped as outlook. This is the 2026 version of the 2025 Earnings
Navigator ([3VVjDDJvu2s](../2025-05-02_3VVjDDJvu2s/notes.md),
[RokhF9v62HE](../2025-07-20_RokhF9v62HE/notes.md)). The **valuation leg is gone**, direction is now one
platform score, and an IV-rank "T-chart" chooses the structure. Transcript in this folder._

## Verdict: 2 / 5

This is a filter walkthrough rather than a strategy, and it is more honest than the 2025 sessions. He
defines the expected move correctly and says it is "not directional" (20:54). He puts liquidity first, and he makes no
"proven" claim. Nothing is priced beyond the platform's mid, and nothing is backtested. The two rules
that carry the weight are both answered on our data. (1) **"Strong bull / strong bear" = the highest
probability of an explosive directional move** (13:09–13:14): trend + RS alignment calls the reaction's
direction 50/50 on our 4,477 events, and aligned names realise *less* of their implied move (exploratory
check in 3VVjDDJvu2s). (2) **IV rank chooses debit vs credit**: tested NULL (t 0.68). Heading into a print, IV rank
largely measures the event ramp itself. The half point over the 2025 sessions is for dropping the untestable
"AI" valuation story and describing the options-implied inputs correctly.

## Data audit

| item | what he shows |
|---|---|
| Backtest / sample / track record | None. No claim of one either |
| Pricing | Platform auto-built structures at the mid (ISRG 400/450 call spread, NFLX call credit spread, TSLA 390/315 put spread) |
| Direction input | "Directional Edge" = proprietary 1-month and 6-month trend indicators plus an RS score out of 10 (12:14–14:25). Opaque, but close to the 2025 trend + RS legs |
| Statistic / control | None |

## Platform pitch vs testable rules

- **Pitch:** the new dashboard, the grid/card views, the slides download, the free trial, and next week's wheel
  sessions (roughly 00:45–03:02, 13:50–15:28, 29:15–end).
- **Testable:** (a) very-liquid names only; (b) strong-bull/strong-bear alignment → a directional earnings
  trade; (c) bigger expected move → a bigger opportunity; (d) the IV-rank T-chart: low IVR → a debit spread,
  high IVR → a credit spread; (e) for a big expected move on cheap options, go more aggressive (an OTM
  put/call, ~30 DTE).

## Claims against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:00 / 18:56, 17:01–17:47 | Cut hundreds of reporters to a handful: **very liquid only**, "somewhat liquid" only late in the season | ✅ **AGREES.** The earnings vol premium survives costs only in the top ~40% by volume (+0.284% at the bid, PARKED). Crossing the spread costs 171% of the gross premium unconditionally (`earnings_vol_premium_2026-09-20.md`) |
| 12:14–14:41, 20:25 | **Strong bull / strong bear** (1m + 6m trend and RS aligned) = "the highest probability of making … a directional move on earnings" | ❌ **Direction is a coin flip** (exploratory, 3VVjDDJvu2s): 21d trend + 21d RS ≥ 5% / 5pp in the same direction → hit rate 50.0% bull / 49.6% bear. An ATM option in the trend direction, at the ask, settled at the front expiry: −16.6% of premium, t −3.03. It is no better than the opposite-direction option (−2.2pp, t −0.15). ⚠ A proxy for his score, not the score itself |
| 20:04–21:34 | Expected move = what the options market implies, "not directional in nature"; the bigger it is, the more the market implies a big move | ✅ **Correct description.** On our events the move to the front expiry stays inside the ATM straddle price 61.9% of the time (`earnings_vol_events.parquet`) |
| 21:34 | "If you're looking for stocks that can make big moves, that's really where you want to focus" (names with the biggest expected moves) | ❌ **For a buyer, the wrong direction.** At mid the event premium sorts monotonically on implied-move size: the richest quintile is **+1.70% to the seller**, i.e. the most overpriced for the buyer. At the bid it is also the worst quintile for the seller (−0.718%) because its spreads are widest (`earnings_vol_premium_2026-09-20.md`). The biggest-expected-move names are the costliest to trade on both sides |
| 22:20–23:06 | **IV-rank T-chart:** strong bull + low IVR → call debit spread; + high IVR → put credit spread; strong bear mirrors it | ❌ **NULL.** IV rank as a vehicle chooser: DiD +15.4pp bullish, **t 0.68** (`run_ivrank_vehicle.py`, `ivrank_vehicle_2026-09-22.csv`). Per dollar at risk, the call debit spread beat the put credit spread in every IV-rank tercile, so the switch doesn't help. ⚠ **Earnings-specific:** front-expiry ATM IV rises **+40 to +57 vol points** into the print (`earnings_ramp_2026-09-20.md`), so ISRG's "IV rank 100" on report day (23:42) mostly measures the event. It says little about whether that name's options are cheap |
| 23:42–24:38, 24:38–25:24 | ISRG and NFLX report after the close with IVR ~100 → **sell a call credit spread through the print** (ISRG Aug-28 400/450) | **PARTIAL / untested for spreads.** Selling through the print on naked puts earned more than earnings-clear puts (within-week +0.19pp, t +3.6, but not beyond direction, excess t +1.3; worse tail −22.3% vs −17.8%; `bci_csp_study_2026-09-17.md` §3). The 3-DTE ATM straddle sold at the bid is −0.43% (`earnings_vol_premium_2026-09-20.md`). Bear-aligned names drifted **up** into the front expiry in the exploratory check (+0.97%), which works against a bearish call spread |
| 26:59–28:21 | TSLA: strong bear with cheap options → buy a put spread, or "more aggressive", a ~30-day ATM/OTM put: "risk $1,200 to make $3,200" | ❌ Exploratory: the bear-aligned trend-direction option was the **worst** cell, −26.9% of premium at the ask (front expiry, not his ~30 DTE). The $3,200 is the payoff **if** it tanks, not an expectation |
| 25:24–26:10 | Shorter-dated options are fine around earnings | Consistent with the timing finding: a long earnings option bought days early loses to theta (−3.4 / −6.9 / −14.3% at mid for −3/−5/−10 sessions, `earnings_ramp_2026-09-20.md`). A 30-DTE tenor for the ramp itself was queued 2026-09-20 and declined for now (TEST_INDEX §10 "Pre-earnings ramp on a 30–45 DTE tenor") |

## Not tested, could be

1. **Nothing new on the direction side.** Steps (b) and (d) are answered (the exploratory check in 3VVjDDJvu2s, and
   the IV-rank vehicle NULL). The platform's exact "Directional Edge" score is proprietary. Our 21d
   trend + RS proxy is the testable version, and its 1m + 6m variant is a threshold change on the same
   axis, not a new axis.
2. **The one new axis these three sessions raise** is written up in 3VVjDDJvu2s, "Not tested, could be" #2:
   **trend + RS alignment as a selector for the earnings vol-premium seller** (aligned names realise less
   of a larger implied move; seller −0.23% vs −0.56% of spot at the bid, exploratory). Not queued.
