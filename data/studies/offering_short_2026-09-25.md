# Follow-on equity offerings as a single-name SHORT (2026-09-25)

Script: `run_offering_short.py` (pre-registration in the docstring, committed as fe26d47 before the scoring run).
New data: `data/cache/offerings/offering_filings.parquet` from EDGAR full-text search (424B4/B5/B7, 2010Q1→2026Q2;
25.7k primary-issuer hits, 15.8k secondary, 7.7k at-the-market exclusions, no 10k-cap truncation).
Log: `data/studies/logs/offering_short.log`; events `logs/offering_short_events.csv`; table `offering_short_2026-09-25.csv`.

## Verdict: NULL (short) · 0 of 6 cells pass · every short loses in absolute terms · MECHANISM (the SEO lag is real but small)

4,843 deduped offerings on 1,023 panel names; **2,450 scored** (liquid on the file date), 535 names. Short at the next
open after the 424B file date. Control = same-date names in the same prior-5-session-return quintile × ADR tercile.
t is clustered by month.

| cell | n | event fwd | excess | t | halves | short P&L after costs |
|---|---|---|---|---|---|---|
| **ALL +20 (PRIMARY)** | 2,450 | +1.08% | **−0.21pp** | −1.23 | −0.09 / −0.32 | **−1.36%** (t −3.01) |
| Primary-issuer +20 | 2,083 | +1.02% | −0.37pp | −1.95 | −0.23 / −0.50 | −1.30% |
| Secondary +20 | 367 | +1.43% | +0.36pp | +0.85 | −0.14 / +0.79 | −1.71% |
| ALL +60 | 2,446 | +3.61% | −0.67pp | −1.85 | −0.58 / −0.75 | −4.04% |
| Primary-issuer +60 | 2,081 | +3.39% | −0.68pp | −1.56 | −0.65 / −0.70 | −3.83% |
| Secondary +60 | 365 | +4.82% | +0.22pp | +0.25 | −0.71 / +1.01 | −5.26% |

- **The direction matches Loughran–Ritter, but the size is too small.** Issuers lag matched names by about 0.2pp at 20
  sessions and 0.7pp at 60 sessions, with both halves negative and 12/17 years negative at +60. That is a consistent
  lean with t < 2, nowhere near the bar.
- **The stocks still rise.** Offering names gain +1.1% in 20 sessions and +3.6% in 60, so the short loses 1.4–4.0% per
  trade after costs. This is the fourth time the absolute return has killed a single-name short.
- **Secondary (insider or holder) sales carry no signal:** positive excess, and the halves disagree.
- **Exploratory:** "issuer sells into strength" (a prior 60-session run-up ≥ 30%, n 214) shows +1.17pp excess, the
  wrong way. A big file-day drop (≤ −3%, n 220) also shows +0.45pp, i.e. a rebound, not a drift. Neither supports the
  liquid-name analogue of the Veprek dilution fade.

## What it taught
- **MECHANISM:** on liquid names, dilution is priced by the time the prospectus is filed. The residual underperformance
  (~0.7pp per quarter) is a lean, not a trade. At best it is a weak "don't add" note for long-book names that just
  issued, and it has not earned even that.
- **The pattern across four single-name short tests** (short universes, breakdowns, IV skew/CW, offerings): every
  signal finds *relative* weakness of 0.2–0.7pp, and none finds an *absolute* decline. On this liquid, survivorship-biased
  panel, the market's drift beats every short signal we have found. What remains untested needs data we do not have:
  small caps, delisted names (§7 of DATA_CATALOG), and borrow.
- **Reusable data:** the offering-filing table (with CIKs, forms and file dates) is cached for any future event study.
