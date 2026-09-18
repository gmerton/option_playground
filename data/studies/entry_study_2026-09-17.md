# Entry study (2026-09-17): can the tight intraday stop be made to work with intraday execution + re-entry?

**Question.** Every earlier test judged a tight stop on the daily close, single shot, and it lost (alert funnel -1.5pp; pullback <= 3% recipe -0.74R; ORB low 73% "stopped" while the stock went +11%). Luk / Qullamaggie run it differently: enter at the trigger near the intraday low, exit the moment the level breaks, re-enter on the next trigger, accept a ~30% hit rate. Does that package beat buying the close?

**Data.** `run_entry_study.py`. 2,439 layer-2 name-days (ADDV >= $50M, ADR 4-7, within 15% of the 52wk high, stacked, prior close) among the 183 names with 1-min bars, 154 sessions 2026-02-02..09-11; 286 of them on the blind control set (`universe_study_extra.txt`; the curated list is hindsight). Entries on the same name-days: CLOSE (buy the close, stop = day low, daily management); ORB15 (first 1-min close over the 15-min opening-range high, stop = OR low); RECLAIM (flush >= 0.25 ADR under max(open, prior close), then first 1-min close back over VWAP, stop = session low). Execution: close-judged / intraday (exit at the first 1-min close under the stop) / intraday + re-entry (next trigger the same day, max 3 entries, result = sum). 0.06% per side each way. After the entry day everything is managed on daily closes (first close under the stop or the 20 EMA, 60 cap). SEs by date.

| entry (return per name-day) | ALL n | ret | t | win | stopped same day | control n | ret | t |
|---|---|---|---|---|---|---|---|---|
| **CLOSE, stop = day low (2.3% away)** | 2,439 | **+5.95%** | 7.0 | 33% | -- | 286 | **+3.89%** | 3.3 |
| ORB15 close-judged (stop 2.7% away) | 1,294 | +5.12% | 5.1 | 29% | 0% | 151 | +2.21% | 1.8 |
| ORB15 intraday stop | 1,294 | +4.87% | 5.1 | 27% | 23% | 151 | +1.51% | 1.3 |
| ORB15 intraday + re-entry | 1,294 | +5.07% | 5.2 | 28% | 23% | 151 | +1.89% | 1.7 |
| RECLAIM close-judged | 1,774 | +4.02% | 5.0 | 24% | 0% | 207 | +3.10% | 2.5 |
| RECLAIM intraday stop | 1,774 | +2.27% | 4.4 | 14% | **64%** | 207 | +1.96% | 2.0 |
| RECLAIM intraday + re-entry (57% of days re-enter, 2.0 entries) | 1,775 | +3.34% | 4.9 | 20% | 64% | 207 | +2.48% | 2.3 |
| paired: ORB intraday+re minus CLOSE | 1,294 | **-1.22pp** | -3.4 | | | 151 | -0.94pp | -1.8 |
| paired: RECLAIM intraday+re minus CLOSE | 1,775 | **-2.28pp** | -3.4 | | | 207 | -1.20pp | -1.6 |

Return per 1% initially risked: CLOSE +2.54 (all) / +1.75 (control) vs ORB +1.90 / +0.77. By month every entry is the same story: Mar-May 2026 carries everything; Feb, Jun-Sep flat or negative.

**Reading.**
1. **Buying the close beats every intraday entry, on every universe, paired on the same name-days** (-0.9 to -2.3pp, t -1.6 to -3.4). Not by a lot, but never the other way.
2. **Executing the stop intraday makes it worse, not better** (ORB 5.12 -> 4.87; RECLAIM 4.02 -> 2.27). The session-low stop is inside the noise: 64% of RECLAIM entries are stopped the same day, 23% of ORB entries.
3. **Re-entry repairs only part of that** (RECLAIM 2.27 -> 3.34; ORB re-entries almost never trigger -- price rarely re-clears the OR high the same day). With costs, two entries a day on 57% of days still lands below the close entry.
4. **The size lever is already in the close entry here.** On layer-2 name-days the day's low is a median 2.3% under the close -- as tight as the ORB stop (2.7%) -- and it wins on return per unit of risk too. Tightness came from the structure of the day, not from entering near the intraday low; same conclusion as the stop-distance finding on the breakout pool.
5. What this cannot test: their discretion about WHICH day and which trigger, and selling winners into strength intraday. What it does test -- the mechanical version of "tight stop + intraday exit + re-entry" on qualified names -- has no edge over the daily-close process. One regime (Feb-Sep 2026), 63 names.

**Verdict.** Close the entry study. The house process stands: buy the daily close (or a pivot buy-stop -- a wash), stop = the day's low judged on the close, manage on closes. Get tight stops by picking days whose low sits 1.5-3% under the close, not by moving the entry to the intraday low. Alerts stay information, not triggers.
