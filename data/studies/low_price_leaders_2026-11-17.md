# Low share price among fresh leaders, volatility held fixed (2026-11-17)

> ## ⛔ RETRACTED 2026-11-17 (same day): look-ahead through future splits
> `logpx` was computed **after** split-adjusting chain_spot, so a 2012 "price" reflects every split through 2026.
> Later splitters are disproportionately later winners, so a low adjusted price encodes the future. On the
> **nominal** (raw) price at the event: **2011-18 LOW − HIGH +2.2%, t 0.89; 2019-25 −0.1%, t −0.02**, and low-priced
> names halve MORE (5.3% vs 2.3%). No price effect. The veto test was not run. Re-score:
> `low_price_leaders_2026-11-17_nominal.csv`. Everything below is the contaminated original, kept for the record.

**Verdict: PASS on the pre-registered spread (DISCOVERY) · as a long selector ≈ SPY · actionable as a VETO, untested
as one.** Low-priced fresh 52w-high names beat high-priced ones by ~10%/yr with volatility held fixed, and they
blow up no more often. The edge is mostly the **high-priced leg lagging**, not the low-priced leg winning.

| check | LOW − HIGH 12m excess | t_NW | halves |
|---|---|---|---|
| **PRIMARY 2011-18 (unseen), chain_spot incl. delisted** | **+10.0%** | **+4.20** | +14.0% / +6.4%, 8/8 yrs; halving gate z −0.55 |
| excluding forward-break events | +8.3% | +2.85 | — |
| yfinance split-adjusted where alive, chain_spot otherwise | +9.9% | +4.26 | +13.3% / +6.9% |
| yfinance only (alive names, survivor-biased) | +11.6% | +3.10 | +17.2% / +6.2% |
| 2019-25 (SEEN, reference only) | +7.8% | +2.15 | 6/7 yrs |

- **Artefact check (missing splits make high-priced names look like they crashed):** chain_spot vs yfinance
  split-adjusted forward returns, median gap 0.3% in every price tercile; high tercile mean gap −0.6%. Not the cause.
- **Levels (2011-18, yfinance, alive):** LOW +12.9% mean / +8.6% median, MID +7.8%, HIGH **+3.5% / +2.3%**,
  SPY +12.9%. 45% of high-priced fresh leaders were down after a year, vs 38% of low-priced ones. Median price
  LOW ≈ $18, HIGH ≈ $90.
- **Strongest where volatility is high:** LOW − HIGH +14.6% in the top ADR tercile, +3.1% in the bottom. LOW
  doubled 3.1% vs 0.9% with equal halving (3.8% vs 4.3%).
- **Read:** among fresh 52w-high names, a low nominal price buys the right tail without extra left tail. A high
  nominal price marks names that lag. This runs against the literature's nominal-price illusion (low-priced
  stocks overvalued; Birru–Wang 2016), so the mechanism is open. Caveats: one sample, price-only returns (no
  dividends; high-priced names pay more, which is worth ~1–2%/yr against HIGH), 10 bp costs not applied (equal in
  both legs).
- **Next:** this is a selection result on a broad event set. The test that matters for the book is a **high-price
  veto on the house breakout** (precision tier): new, pre-register before running.

Pre-registration: docstring of `run_low_price_leaders.py`. Graded sample 2011-18; 2019-25 is SEEN.

## 2011-18 (GRADED)

- LOW − HIGH xs **+10.03%/event, t_NW +4.20**; halves 2011-14 +14.01% / 2015-18 +6.39%; years same sign 8/8; halving gate z -0.55 → **PASS**
- n LOW 924 / HIGH 933; median price LOW $17.5 vs HIGH $90.3

| group | mean xs | median fwd | P(double) | P(halve) | n |
|---|---|---|---|---|---|
| LOW | -0.6% | +5.4% | 3.1% | 3.8% | 924 |
| MID | -6.3% | +5.5% | 1.4% | 3.5% | 919 |
| HIGH | -10.0% | +1.7% | 0.9% | 4.3% | 933 |

| ADR tercile | LOW − HIGH xs | LOW P(double) / P(halve) | HIGH P(double) / P(halve) |
|---|---|---|---|
| low | +3.1% | 1.0% / 0.6% | 0.0% / 1.0% |
| mid | +10.7% | 2.9% / 2.3% | 0.6% / 2.3% |
| high | +14.6% | 5.5% / 8.4% | 1.9% / 9.6% |

| year | LOW − HIGH xs |
|---|---|
| 2011 | +10.2% |
| 2012 | +22.1% |
| 2013 | +17.9% |
| 2014 | +1.7% |
| 2015 | +7.5% |
| 2016 | +11.0% |
| 2017 | +3.8% |
| 2018 | +1.4% |

## 2019-25 (seen, reference)

- LOW − HIGH xs **+7.82%/event, t_NW +2.15**; halving z -1.25
- n LOW 610 / HIGH 612; median price LOW $21.2 vs HIGH $139.3

| group | mean xs | median fwd | P(double) | P(halve) | n |
|---|---|---|---|---|---|
| LOW | -1.5% | +7.7% | 4.8% | 4.6% | 610 |
| MID | -2.3% | +4.9% | 4.1% | 4.5% | 603 |
| HIGH | -8.2% | +5.7% | 2.8% | 6.2% | 612 |

| ADR tercile | LOW − HIGH xs | LOW P(double) / P(halve) | HIGH P(double) / P(halve) |
|---|---|---|---|
| low | +0.7% | 1.0% / 0.5% | 1.5% / 2.0% |
| mid | +0.7% | 2.5% / 3.4% | 1.0% / 2.9% |
| high | +18.8% | 10.8% / 9.8% | 5.9% / 13.7% |

| year | LOW − HIGH xs |
|---|---|
| 2019 | -5.6% |
| 2020 | +8.7% |
| 2021 | +15.1% |
| 2022 | +16.7% |
| 2023 | +0.8% |
| 2024 | +8.2% |
| 2025 | +16.8% |

## 2011-18 excluding forward-break events

- LOW − HIGH xs **+8.34%/event, t_NW +2.85**; halving z +0.29
- n LOW 898 / HIGH 904; median price LOW $17.6 vs HIGH $90.1

| group | mean xs | median fwd | P(double) | P(halve) | n |
|---|---|---|---|---|---|
| LOW | -1.9% | +5.3% | 2.9% | 3.6% | 898 |
| MID | -5.9% | +5.7% | 1.3% | 3.0% | 898 |
| HIGH | -9.6% | +1.9% | 0.6% | 3.3% | 904 |

| ADR tercile | LOW − HIGH xs | LOW P(double) / P(halve) | HIGH P(double) / P(halve) |
|---|---|---|---|
| low | +2.9% | 1.0% / 0.7% | 0.0% / 1.0% |
| mid | +5.4% | 2.3% / 2.3% | 0.7% / 1.0% |
| high | +14.9% | 5.4% / 7.7% | 1.0% / 8.1% |

| year | LOW − HIGH xs |
|---|---|
| 2011 | +2.9% |
| 2012 | +21.9% |
| 2013 | +17.5% |
| 2014 | -1.4% |
| 2015 | +6.8% |
| 2016 | +11.3% |
| 2017 | -0.5% |
| 2018 | +1.0% |

