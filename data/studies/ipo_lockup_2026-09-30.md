# IPO lockup expiry event study, survivorship-free (2026-09-30)

**Verdict: NULL · YIELD MECHANISM.** Stocks do not underperform other recent IPOs around the standard 180-day lockup expiry. Shorting into it loses money after borrow.

- Pre-registered in the docstring of `run_ipo_lockup.py` and committed before any return was computed (6e7af79).
- IPO dates: the first 424B4 per CIK from the EDGAR quarterly indexes (`run_sec_424b4_index.py`, 7,940 filings), with SPACs excluded.
- Prices: chain_spot, including delisted names. 639 events; 408 have prices over the full primary window (options usually list about 31 days after the IPO). 283 of the companies later delisted.
- Control: other IPOs that are 60–400 days old on the same dates and not near their own lockup (median 39 per event).

| window | n | raw | control | excess | t | halves (<2018 / ≥2018) |
|---|---|---|---|---|---|---|
| **PRIMARY [E−5, E+5]** | 408 | +0.71% | −0.19% | **+0.90pp** (median +0.08) | **+0.58** | −0.69 / +2.47 |
| [E−1, E+1] | 406 | +0.50 | −0.17 | +0.68 | +1.83 | +0.22 / +1.14 |
| [E, E+10] | 413 | +1.65 | +0.06 | +1.59 | +2.42 | +0.75 / +2.44 |
| [E+1, E+20] | 411 | +0.98 | −0.20 | +1.18 | +1.41 | −0.43 / +2.81 |

- **Sign flips with the era.** 2011–2014 is negative every year (−1.1 to −4.3pp), matching the published effect. 2021–2026 is positive in every year. Negative years: 8/16.
- **Not tradeable:** an absolute short over the primary window, net of costs and 30%/yr borrow, averages **−2.10%** (41% win rate).
- **Survivorship at work:** names that later delisted show −1.10pp (t −1.21), while survivors show +2.40pp (t +2.07). A survivor-only panel would have told a different story.
- Caveat: a fixed 180-day proxy misses staged or early releases (CBRS has 11 waves). That dilutes the result; it does not flip it.

**MECHANISM.** The lockup is a scheduled, public event. By the late 2010s it was priced in advance, and after 2018 the window even leans positive (relief once the overhang clears). This agrees with the house finding that scheduled events carry no edge once public (earnings, FOMC).

**What it means for the book now.** No rule to short lockups. For CBRS specifically, the 10/14 and 10/28 unlocks are not a tested reason to short or to avoid it. Today's drop came with a news item (the OpenAI/Nvidia report), which a scheduled-supply rule does not capture.
