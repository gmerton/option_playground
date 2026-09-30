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
