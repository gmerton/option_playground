# Alert detectors over 20 sessions: what fails, what survives (2026-09-10)

Replayed the current (9/10) detector rules over every session with Tradier 1-min bars on file, 2026-08-13 .. 2026-09-10 (20 sessions, 68-name long+short universe, 1,073 alerts). Each alert scored identically: alert price -> stop hit before the close (-1R) or the close, R = |price - stop|. No management, no costs (median UR risk 1.69% of price, so a 0.10% round trip = ~0.06R). Filters were judged on the first 10 sessions (A: 8/13-8/26) and checked on the last 10 (B: 8/27-9/10).

## Baseline by detector

| Detector | n | avg R | t | stopped | A | B |
|---|---:|---:|---:|---:|---:|---:|
| UR (VWAP reclaim, long) | 494 | +0.00 | +0.01 | 36% | +0.04 | -0.03 |
| ORB9 (opening-range break, long) | 97 | +0.40 | +1.07 | 75% | +0.90 | -0.05 |
| ORB9 without its top 3 winners | 94 | -0.14 | -0.67 | 78% | -0.25 | -0.05 |
| BIR (bounce into resistance, short) | 238 | -0.15 | -2.76 | 31% | -0.03 | -0.23 |
| FBO (failed breakout, short) | 244 | -0.07 | -1.76 | 15% | -0.03 | -0.10 |

No detector has an edge on its own. ORB9's mean is three trend-day outliers (DE 8/21 +21.6R, CRM 8/19 +18.7R, IBIT 8/19 +11.7R). The shorts that looked good on 9/8-9/10 are negative over 20 sessions.

## What survives both halves (UR only)

| UR filter | n | avg R | t | stopped | A | B |
|---|---:|---:|---:|---:|---:|---:|
| all | 494 | +0.00 | +0.01 | 36% | +0.04 | -0.03 |
| alert before 10:00 | 232 | negative | | 50%+ | 09:40 -0.26, 09:41-10:00 -0.11 | 09:40 -0.37, 09:41-10:00 -0.11 |
| **alert after 10:00** | 262 | **+0.16** | **+2.54** | 22% | +0.18 | +0.14 |
| after 10:00, SPY below VWAP | 109 | +0.24 | +2.53 | 17% | +0.14 | +0.34 |
| after 10:00, SPY above VWAP | 153 | +0.10 | +1.18 | 25% | +0.20 | +0.01 |
| SPY below VWAP (any time) | 191 | +0.17 | +2.03 | 28% | +0.21 | +0.14 |
| SPY above VWAP (any time) | 303 | -0.11 | -1.82 | 42% | -0.07 | -0.13 |
| 10+ names reclaiming in the same minute | 35 | -0.73 | | 76% | -1.00 | -0.63 |

- The whole UR loss is the first 30 minutes. After 10:00 it is positive in both halves (t 2.5), ~+0.10R after costs.
- The index gate is INVERTED for UR: a reclaim while SPY is still under its VWAP is relative strength and does better. Same shape as the Part III rotation finding (leading-group filtering inverted).
- The same-minute flood filter is real (-0.73R) but redundant once the floor is 10:00 (every flood minute was before 10:00).
- ORB9 late-fire artifact (alerts released when the hard index gate opens, 25-65 min after the break) is real in the code but did NOT hurt: late alerts scored better than fresh ones. Not a priority fix.
- Profit targets (+0.5R/+1R/+2R) do not rescue any detector. RS vs SPY and level type (MA vs PDH/OR) do not separate outcomes. The relative-strength short gate is not supported either way.

## Caveats
One 20-session period (late Aug to early Sep 2026). The universe was assembled from names that had recently moved (hindsight). Replays use bar VWAP, the live monitor uses all-prints VWAP. Hold-to-close scoring with no management. +0.16R is modest: keep scoring live before sizing up.

Scripts: scratchpad score_all.py / eval_filters.py (log-based scorer), replay logs data/watchlist/logs/universe_alerts_<date>_replay.log.

## Daily in-play gate (added 2026-09-10, after Gabe's INTC 9/10 critique)

Every universe name gets a daily state from its chart at the prior close
(`src/lib/alerts/daily_state.py`, carried on `DailyCtx`, cache `alert_ctx_v5_<date>.parquet`):

- **LONG**: within ±1 ADR of the 21 EMA, not a falling-EMA downtrend, not "over the 9 but still
  under the 21", and at least 0.5 ADR under the nearest prior swing high. In practice, a pullback
  into rising EMAs or a base near the 21.
- **SHORT**: a trend-down (under falling 9/21 EMAs, not stretched more than 1.5 ADR under), or
  exhaustion (2+ ADR over the 21 and within 1 ADR under / 0.5 ADR over the nearest prior swing high).
- **OUT**: everything else.

Alerts against the name's state are dimmed as "out of play" (`--no-day-gate` turns this off).
SHORT-state names also get BIR, and the swing high is a named BIR/FBO level ("prior high").

INTC is the reference case. On 9/9 and 9/10 it's SHORT: 2.5 ADR over the 21 and under the 8/13-8/17
highs, 106.9-107.6. The 9/10 VWAP-reclaim long is out of play.

| Long alerts (UR + ORB9), 20 sessions | n | avg R | first half | second half |
|---|---:|---:|---:|---:|
| no gate | 591 | +0.07 | +0.20 | −0.03 |
| state LONG, first version | 256 | +0.17 | +0.19 | +0.16 |
| **state LONG, shipped** (no unconfirmed reclaim, room ≥ 0.5 ADR) | 176 | **+0.34** | +0.35 | +0.33 |
| blocked by the shipped gate | 415 | −0.05 | +0.12 | −0.17 |
| UR after 10:00, no gate | 262 | +0.16 | +0.18 | +0.14 |
| UR after 10:00, shipped gate | 92 | +0.28 | +0.24 | +0.32 |

Rejected sub-states (both halves negative): "reclaiming the 9 under the 21" −0.48R (n=22; mostly
early-morning UR failures) and bases within 0.5 ADR of a prior high −0.11R (n=60). A cap on
extension at alert time adds little for UR and removes nearly every ORB9, so it's not used.

Shorts: restricting to SHORT-state names cuts the worst losers. BIR on LONG-state names was −0.23R
(t −2.7) and on OUT names −0.42R (t −3.2). The kept shorts are still −0.06R (n=197), so shorts stay
informational. FBO exhaustion n=10, not enough to judge.

⚠ The sub-state choices were made on these same 20 sessions. Both halves agree, but it's still
in-sample. Keep scoring the live alerts.
Not built: a daily-21-EMA reclaim trigger, which is the kind of move INTC made on 9/4.
