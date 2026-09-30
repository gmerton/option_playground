# Small caps: 12-1 momentum and the precision breakout outside our ADDV filter (2026-09-29)

**Pre-registration:** the docstring of `run_smallcap_tests.py`, frozen in 5636f56 (spec) before any data was built;
implementation + interpretation notes committed in 36b08d3 before the run. Panel: `data/cache/smallcap_panel_2009.parquet`
(1,236 names with 50d ADDV $5–50M and price ≥ $5 as of 2026-09; 563 present in 2009). Survivor-biased, as declared.

## Results (run 2026-09-29; `data/studies/smallcap_tests_2026-09-29.log`)

**Verdict: both primaries FAIL → NULL. Small caps are not a missing edge; if anything they are worse.**

**T1 momentum 12-1 (top vs bottom decile, monthly, net of turnover costs; bar NW t ≥ 3.2):**

| universe | spread %/mo | NW t | halves (2009–17 / 2018–26) | yrs + | long-only (top − band) | t |
|---|---|---|---|---|---|---|
| **S small caps** | +0.44 | **1.35** | +0.78 / +0.14 | 10/17 | +0.21 | 1.07 |
| M mid/large (reference) | +0.73 | 1.88 | +0.32 / +1.11 | 13/17 | +0.66 | 2.73 |
| X chain-spot incl. delisted (T3) | **−0.17** | −0.61 | +0.02 / −0.33 | 7/16 | +0.16 | 1.12 |

Momentum is weaker in small caps than in the mid/large reference, and on the series that includes delisted names the
spread turns negative — the survivorship direction the pre-registration warned about.

**T2 precision breakout on small caps (house trade, 20 bp/side; bar date t ≥ 3.2 vs same-date ADR-tercile names):**

| stat | n | mean %/trade | date t | halves |
|---|---|---|---|---|
| raw trade | 2,387 (575 names) | **−0.82** | −2.81 | −2.05 / −0.43 |
| vs same-date random small caps | | **−0.50** | −1.99 | −1.71 / −0.30 |
| vs the same name later | | −0.47 | −1.55 | −1.89 / −0.08 |

The house breakout loses money in small caps even on a survivor panel, and does worse than random small caps bought
the same day.

**What it means for the book now.** For a small-cap rebound play (IWM −8.8% from 8/14), none of our machinery transfers:
don't run the precision breakout below $50M ADDV, and don't expect the 12-1 sleeve to work better there. Keep the
momentum sleeve (launching 10/01) on its mid/large universe.
