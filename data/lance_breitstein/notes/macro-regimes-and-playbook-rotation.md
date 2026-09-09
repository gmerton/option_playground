# Macro regimes and playbook rotation

> **Verdict:** A slow-regime version of the repo's own "condition on current conditions" rule, with one useful distinction it lacked.
> **Type:** regime
> **Source:** `9EEUa618xQw` — How Macro Market Conditions Make or Break Your Trading Strategies (2026-01-31)

---

## The mapping he gives [00:39–05:03]

| Regime | What pays, per him |
|---|---|
| Lower rates | long momentum, speculative small caps / OTC (2021: GME, AMC) |
| Inflation | the CPI-release trade (2022: multi-percent index moves); otherwise poor for long momentum, traders shift short-biased |
| Elections / headline density | breaking-news trades (2018 and 2025 tariff headlines "moved global markets by significant percentages every time"; the April 2025 tariff delay = +10% in a session); regulatory stance sets the M&A headline supply |
| Strong economy | breakouts, an open IPO window (CoreWeave, Circle 2025), hot-theme small caps |
| Weak economy / panic | **mean reversion** ("some of what I do best"): the Aug 2024 Nikkei panic = his $10M+ trade; capital-raise headlines |

Framing [00:28–00:39]: "not about predicting the economy... recognizing what kind of tape you're in and aligning your trading with the opportunities that are actually showing up." Application [05:03–05:32]: many playbooks, not one; know which environment each one wants; rotate and size accordingly.

## ⚠ Where this meets the repo

- The repo's rule (`feedback_weight_current_conditions`) conditions setup expectancy on the **trailing 30-day** state, and `run_regime_validation.py` found that state has **no persistence** — it describes, it does not forecast. Breitstein's regimes are **slower** (a rate cycle, an inflation year, a presidency) and defined by the *kind of opportunity* they produce (headline density, IPO supply, panic frequency), not by trailing returns or breadth. That is a different object and might persist where the 30-day one did not; nobody has tested it.
- His claim that "your strategy stopped working" is usually "the environment stopped paying that strategy" is the same conclusion as the August retrospective, arrived at from the other side.
- No numbers, no dates beyond the anecdotes, course-free. Filed as a framing, not a finding.
