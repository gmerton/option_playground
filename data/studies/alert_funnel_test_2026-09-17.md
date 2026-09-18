# Alert-funnel test (2026-09-17): do intraday alerts add anything once a name has passed layer 2?

**Question.** The top-down funnel is regime (size only) -> layer 2 stock state (the measured edge) -> today's precision entry. The alert study scores every alert as a day trade and finds nothing sorts outcomes. Held the validated way instead (stop on the daily close, exit on the first close under the 20 EMA, 60-session cap), does an intraday alert on a layer-2 name (a) beat the daily-close entry, and (b) beat the same name on a day with no alert?

**Data.** `run_alert_funnel_test.py`. Replayed long alerts (UR / ORB9 / LVL), 153 sessions 2026-02-02..09-10, first alert per name-day: 8,191, of which 1,153 were on a name in the layer-2 state at the prior close (ADDV >= $50M, ADR 4-7, within 15% of the 52wk high, 10>20>50 with the house slack). Controls: every layer-2 name-day in the same sessions bought at the close. Three universes: all 1,400 liquid names; the names the monitor was streaming (**hindsight: replays use TODAY's curated list**); and the study's 40-name no-hindsight control set.

| cell (multi-day hold, % return per trade) | n | ret | win |
|---|---|---|---|
| all liquid layer-2 name-days, close entry | 15,097 | +0.37% | 26% |
| watched (hindsight) layer-2 name-days, close entry | 2,495 | +5.90% | 33% |
| -- with a long alert that day | 1,150 | +6.90% | 37% |
| -- with no alert that day | 1,345 | +5.04% | 31% |
| **no-hindsight control names**, layer-2 name-days, close entry | 285 | **+4.01%** | 35% |
| -- with a long alert that day | 134 | **+3.85%** | 36% |
| -- with no alert that day | 151 | **+4.14%** | 35% |
| alerted name-days: **alert-price entry** (stop = session low) vs same-day **close entry** (stop = day's low) | 1,150 | **+5.38% vs +6.90%**, paired -1.53%, t_day -3.2 | |
| same, control names only | 134 | +1.73% vs +3.85% | |
| layer-2 + daily breakout day: alert entry vs close entry | 75 | +23.5% vs +24.2%, paired -0.67%, t -0.6 | |

By month (watched names): Feb 0 / Mar +7 to +14 / **Apr +20 to +30 / May +8 to +12** / Jun 0 / Jul -1 to -2 / Aug +0.3 to +1.4 / Sep +1 to +2. The whole positive result is April-May 2026.

**Reading.**
1. **The alert carries no information beyond the state.** On the no-hindsight names an alert day (+3.85%) and a no-alert day (+4.14%) are the same; on the watched names the gap (+6.9 vs +5.0) is inside month-to-month noise and flips sign in 4 of 8 months.
2. **The intraday entry is worse than waiting for the close**: -1.5pp per trade (t -3.2), -2.1pp on the control names. The alert's tight session-low stop (1.8% away vs 5.7% for the day's low) is hit on the daily close far more often than the wider stop, and the ~1.75% better price does not pay for it. Same conclusion as the stop study (intraday stop halves the result) and the ibkr_bot finding ("trigger can't buy precision").
3. **The day-trade framing understated the state.** The same in-state alerts score +0.36R as day trades and +5.4% held the validated way. The alert study cannot see the layer-2 edge because it closes every trade the same day.
4. **The monitor's daily in-play gate is not layer 2.** Only 290 of the 1,153 in-state alerts were shown (grade B/C); the shown ones did worse (+2.4%) than the hidden ones. Whatever the gate measures, it is not the state with the edge.
5. **Universe hindsight is large**: +6.1% on today's curated list vs +0.37% on all liquid names vs +4.0% on the blind control set. Any alert statistic computed on the replayed curated universe is inflated; the control set is the only honest read.
6. **Regime**: everything positive here is April-May 2026. Jun-Sep is flat to negative on every cut.

**Verdict.** Intraday alerts do not earn a place as entry signals, even on names that passed layer 2. The entry that tests best is the one the funnel already had: the daily close (or a buy-stop at the pivot, which is a wash against the close on breakout days). Alerts, if kept, are information about plan names, never a trigger, and the daily gate that decides show/hide should be replaced by plan-list membership.
