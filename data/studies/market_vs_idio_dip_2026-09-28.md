# Market-driven vs stock-specific dips in uptrend names — primary NULL, survivorship check uninterpretable (2026-09-28)

**Prompt (Gabe):** "a lot of times it's just down on market over-reaction". Split the 9/25 dip-in-uptrend effect (PARKED on survivorship) by the dip's cause.
**Script:** `run_market_vs_idio_dip.py`, pre-registration in the docstring. **Log:** `logs/market_vs_idio_dip.log`. Table: `market_vs_idio_dip_2026-09-28.csv`. Panel events: `logs/market_vs_idio_dip_events_panel.csv`.

## Design
- **Population and event:** P2 uptrend names (measured at t−10), dipping ≥ 1.5 ADR below their 10-day high close.
- **Split:** 252-day beta, ending before the peak. MKT = beta × the SPY move explains ≥ 2/3 of the drop; IDIO ≤ 1/3.
- **Outcome and control:** 20-day forward return vs same-date non-pullback P2 names in the same ADR × beta tercile cell. Event-weighted, month-clustered SE.

## Result
| run | arm | n | 20d excess | t | halves |
|---|---|---|---|---|---|
| **A panel (OHLC ADR) — PRIMARY** | **MKT** | 564 | **+1.64pp** | **0.95** | +2.35 / +1.59 |
| A | IDIO | 9,698 | −0.20 | −0.55 | |
| A | MKT − IDIO (monthly) | 64 mo | +1.13 | 0.93 | |
| A | MKT, residual outcome (beyond the market's own rebound) | 564 | +1.58 | 0.91 | |
| B panel, close-only ADR | MKT | 689 | −0.12 | −0.08 | |
| C chain-spot SURV (today's liquid names) | MKT | 700 | +1.17 | 1.32 | |
| C chain-spot **NONSURV** (delisted / not liquid today) | MKT | 519 | **−3.33** | **−3.06** | −0.43 / −4.01 |
| C chain-spot ALL | MKT | 1,219 | −0.75 | −0.88 | |

**Primary: FAIL** (|t| 0.95; halves positive; 8/12 years positive). It is **UNDERPOWERED**. Market-explained dips are rare: 565 of 12,224 dips, SE ≈ 1.7pp, so only an effect of about 5pp per month would clear the bar.

**Method check: FAILED**, so the pre-registered survivorship read is **uninterpretable**. The close-only ADR proxy flips the panel MKT cell from +1.64 to −0.12. That is the same failure as 9/25: the close-only translation doesn't reproduce the OHLC event set.

**Exploratory, not bar-bearing:** the pattern across groups is the survivorship shape. MKT dips earn +1.2 to +1.6pp on survivors and **−3.3pp (t −3.06; 60d −5.7pp, t −3.36) on names that are not liquid today**. ⚠ Deviation from the 9/25 convention: events whose series ended inside the forward window were dropped rather than exited at the last close. That biases NONSURV *upward*, so the negative is if anything understated.

## Verdict
**NULL (primary, UNDERPOWERED) · survivorship UNINTERPRETABLE by pre-reg · YIELD MECHANISM.**
- Splitting by cause does not rescue the dip trade. The market-driven dip is directionally positive on survivors but far too rare to certify.
- The stock-specific dip, which is 82% of all dips, is flat vs control.
- On names that did not survive to today, the market-driven dip was clearly *bad*. That is the opposite of "the market over-reacted". Some of what looks like a market over-reaction was the start of the name's decline.
- **The dip-in-uptrend row stays PARKED, now leaning toward artefact.**
- Next step (not queued): an OHLC survivorship-free panel. Polygon daily bars for delisted names need the paid tier, which is the same blocker as the value/quality test.
