# Event convexity on the unseen 2010-01 → 2019-09 holdout (2026-09-29)

## Pre-registration (written BEFORE the pull; do not edit this section after the results)

**Why.** Audit List A #3 (`audit_top_down_2026-09-25.md`). OTM calls bought the session before a scheduled event (FOMC
decisions, US elections) beat the same purchase on control dates (`event_convexity_2026-09-18.md`: 55 FOMC + 3 elections,
2019-10 → 2026-09), but only Welch t 1.96 on 53 event dates, and the 0.12Δ preference was a mid-price artefact.
v3 reaches back to 2010: 78 more FOMC decisions and 5 more elections, none seen. Relevance now: the 2026-11-03 midterms.

**Design (frozen from `run_event_convexity_pull.py` / `_score.py`; only the window, panel and dates change).**
- Events: 78 scheduled FOMC decision days 2010-01 → 2019-09 (`data/fomc_dates_2010_2019.json`; 2010/2012/2018 checked
  against federalreserve.gov) + elections 2010-11-02, 2012-11-06, 2014-11-04, 2016-11-08, 2018-11-06.
- Entry: the session before each event; the 40 highest-ADR names with ADR ≥ 4 and ADDV ≥ $50M on `liquid_panel_2009`.
- Control: every Wednesday in the same months with no event within 3 calendar days, same name rule.
- Contracts: calls 10–45 DTE, the rows nearest 0.12Δ and 0.25Δ; fills at mid ± 25% of spread; daily paths for exits.

**Primary (all required).** Bucket **0.25Δ** only (the audit: 0.12Δ's lead was a mid artefact), exit **sell after 5
sessions** (the original's best arm). Stat = event minus control mean return, **Welch t on date-level means ≥ 3**,
both halves positive (2010–2014 / 2015–2019-09).
**Reported, not in the bar:** 0.12Δ; hold-to-expiry and sell-10d; P(≥ 5x); FOMC-only vs election-only (5 events =
anecdote); the pooled 2010–2026 Welch t with the original trades.

**Known limits.** Survivor panel (today's liquid names) for the name pick — shared by event and control. The event set
is FOMC-heavy; a pass says "scheduled macro events", not "elections".
**Cost.** Athena: entry chunks (~150 name-dates each) + path pulls, cached under `data/cache/event_convexity_2010/`.
Approved by Gabe 2026-09-29 ("go").

---

## Results (run 2026-09-29, after the pre-registration above was committed in 5442ca0; `run_event_convexity_holdout_score.py`, `.log`, `.csv`)

**Verdict: FAIL → NULL. On 83 unseen event dates, calls bought the session before FOMC decisions and elections do no
better than the same calls bought on ordinary Wednesdays. The 2019–26 lead (Welch t 1.96) does not replicate.**

12,388 purchases (2,851 event / 9,537 control; 83 event dates, 270 control dates).

| bucket | exit | event mean | control mean | diff | Welch t | halves (2010–14 / 2015–19) |
|---|---|---|---|---|---|---|
| **0.25Δ** | **sell after 5 sessions (PRIMARY)** | −10.3% | −6.0% | **−1.7pp** | **−0.24** | +1.4 / −4.9 |
| 0.25Δ | sell after 10 | −18.1% | −3.5% | −9.2pp | −0.93 | |
| 0.25Δ | hold to expiry | −6.3% | −8.1% | +0.8pp | 0.07 | |
| 0.12Δ | sell after 5 | −23.1% | −12.7% | −6.8pp | −0.96 | |

- P(≥ 5x) is the same on event and control dates (1.35% vs 1.28% at 0.25Δ, 5-day exit): no fatter right tail.
- **FOMC** (78 dates): 5-day mean −12.7%, median −46%.
- **Elections** (5): mean +19.1% but median −64.5%, and it is two events: 2010 (+109%) and 2016 (+237% mean, carried by
  a few names); 2012 −79%, 2014 −9%, 2018 −72%. With 2020/2022/2024 (all risk-on) that is 5 of 8 elections positive
  in mean, 8 events — still anecdote.
- Pooled 2010–26 Welch t: **not computed** — the original trade cache (`data/cache/event_convexity/`) no longer
  exists; rebuilding it needs a second Athena pull and cannot change the holdout verdict.

**What it means for the book now.** Retire "buy convexity into scheduled events" (MARGINAL → NULL). For the
2026-11-03 midterms: the evidence for pre-election OTM calls is 8 events with a median loss in the unseen five; if
Gabe plays it, it is a thesis bet sized as a lottery ticket, not a tested edge.
