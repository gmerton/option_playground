# Ch. 7 — The Opening Gap

**Edition:** 3rd (2019) · **Pages:** _–_ · **Read:** 2026-07-26

## Raw notes

_(yours — capture freely)_

## Named setups appearing here

- [x] **Opening gap fade** → promoted to [`setups/opening-gap-fade.md`](../setups/opening-gap-fade.md)

## Claims to verify

- [x] **"Index gaps fill same-session at a high rate."** ✅ TESTED — see the write-up.
      True in aggregate (SPY 67.4%, 1993–2026), but the number is carried by gaps under 0.25 ATR,
      which are 53% of all days and untradeable. Fill rate by gap size: 85% / 56% / 35% / 27% / 11%.
- [ ] **His actual quoted fill percentages, per index** — ⚠ NEED FROM YOUR COPY. Once you have
      them I can check each index against its own number rather than the generic claim.
- [ ] **Min/max tradeable gap size, in index points** — ⚠ NEED FROM YOUR COPY. These are stale by
      construction (SPX ~2x since 2019); I want them to convert his points into 2019 ATR units and
      see which bucket he was actually pointing at.
- [ ] **Does he condition on the open being inside vs. beyond the prior day's range?** Tested
      anyway — 76.0% vs 52.7% fill, but the *lower*-fill group has the better expectancy.
- [x] **"Don't fade the day after a big trend day."** ✅ TESTED — appears to be **backwards**.
      +11.91 bp (t=6.53) on days after a ≥1 ATR move vs +0.84 bp (t=1.05) otherwise.
- [x] **"Don't fade the first trading day of the month."** ✅ TESTED — directionally consistent
      (−1.06 bp vs +2.78 bp) but n=402, t=−0.29. No evidence either way.

## Quotable rules

_(verbatim rules + page refs — yours)_

## Reactions / conflicts

- The chapter's core move — quoting a fill *frequency* as if it were an *edge* — is the failure
  mode the repo's precision-over-recall rule exists to catch. The data shows the two coming apart
  explicitly: the gap class with the higher fill rate has the lower expectancy.
- The fill-rate decline in the data starts ~2010, **not 2022**, so the KB's standing 0DTE-decay
  hypothesis does *not* explain it. Better candidate: more complete overnight price discovery.
  Worth remembering before reaching for 0DTE as the explanation on the next intraday setup.
- Same shape of result as `run_pullback_shorts.py`: an intuitive arrival signal that is near-zero
  in raw form and only useful as a conditioning variable.
