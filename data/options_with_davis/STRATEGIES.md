# Options With Davis — Strategy Index

Conviction 0–5 (independently tested edge) · Risk 1–10 · Tested = has our own backtest.

| Strategy | Conviction | Risk | Tested | Verdict |
|---|---|---|---|---|
| [XSP Put Condor](strategies/xsp_put_condor.md) | 1/5 | 6/10 | **yes** | **Refuted.** Matched credit spread wins 12/12 configs net of costs (XSP 2018–2026, n up to 335/config). The two extra legs cost ~3× the friction, exceeding the entire claimed edge. Structure also unbuildable at a net credit on 26–87% of Fridays, and his wider-debit demo on ~95%. |

**Reviewed: 1 video. Backtested: 1.**

## Settled

1. ~~**Condor vs put credit spread at equal max risk**~~ — **done 2026-08-08, claim refuted.**
   `run_davis_condor_study.py` → `davis_condor_study.csv`. The credit spread wins every DTE ×
   delta combination once realistic fills are applied; the condor only competes at mid, which is
   the basis on which the video presents it.

## Open backtest queue

1. **Decompose the two legs** — confirm the ATM put debit spread is the drag (strongly implied by
   the cost sensitivity, not yet isolated).
2. **Does anything rescue it?** The structure needs fills better than half-spread on all four legs.
   Worth one check of realised XSP spread widths at the four strikes involved before spending more.

## Channel-level patterns to watch

- POP quoted as if it were expectancy. Recurring; check the payoff distribution every time.
- DTE omitted. Check whether this is systematic across videos.
- Evidence is always a broker analyzer screenshot, never a backtest or trade log.
- Everything funnels to a free PDF and a 12-month paid mentorship.
