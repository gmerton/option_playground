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

## Addendum 2026-09-18 — the "disaster stop" (Gabe's live setup on SNDK / CRM / NOW)

Variant added to `run_entry_study.py`: a WIDE resting stop X ADR below the entry executed intraday; the tight level (session low) judged at the close; optionally a same-day exit if the close is back under the reference level (PDL for a reclaim, OR high for an ORB break); then daily-close management with the stop at the session low. Same 2,450 layer-2 name-days, Feb–Sep 2026.

| execution (return per name-day) | RECLAIM all | RECLAIM control | ORB all | ORB control | stopped same day (all) |
|---|---|---|---|---|---|
| tight stop executed intraday | +2.27% | +1.96% | +4.85% | +1.51% | 64% / 23% |
| tight stop judged at the close | +4.01% | +3.10% | +5.11% | +2.21% | 0% |
| **disaster 1.0 ADR** | **+4.21%** | +3.10% | **+5.41%** | +2.13% | 6% / 4% |
| disaster 1.0 ADR + same-day exit if close < PDL / OR high | +4.01% | +3.20% | +3.97% | +1.75% | 6% / 4% |
| disaster 1.5 ADR + same-day rule | +4.05% | **+3.33%** | +3.97% | +1.74% | 1% |
| disaster 0.5 ADR | +3.57% | +3.20% | +5.05% | +2.21% | 29% / 23% |
| CLOSE entry (baseline) | +5.94% (all) / +3.89% (control) | | | | |

Tail: p5 of the tight-intraday reclaim −5.1% vs −6.9% with the 1-ADR disaster stop; worst cases (−18 to −24%) are identical across variants — they are multi-day gap losses the day-one stop never touches.

**Reading.** (1) The disaster-stop package recovers what the tight intraday stop gives away: +4.2% vs +2.3% on reclaims, +5.4% vs +4.9% on ORB, and it matches or slightly beats judging the tight stop at the close. It is the best intraday-executed variant on both universes. (2) The wide stop almost never fires (4–6% of days at 1 ADR) — its job is the crash, not the noise, and it costs ~1.8pp of p5 tail for ~2pp of mean. (3) **The same-day "back under the OR high" exit HURTS ORB entries** (+5.41 → +3.97%): breaks that close back inside the range recover often enough that closing them is a mistake. For reclaims the PDL rule is neutral (+4.21 → +4.01 all, +3.10 → +3.20 control) — keep it as a discipline rule, not an edge. (4) None of this beats buying the close (+5.94%); it closes most of the gap. "Cut losses early" survives at the daily level (stop at the session low, judged on the close) — what does not survive is executing that stop on 1-minute bars.

**Rule for the three live positions:** SNDK (ORB): resting stop ~1 ADR below entry (1,595), judge 1,686.50 at the close, do NOT auto-exit on a close back under 1,669. CRM / NOW (reclaims): resting stop ~1 ADR below (230 / 131), judge the session low at the close, PDL rule optional.
