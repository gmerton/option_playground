# Retail call-buying bursts → next-days stock returns [A1] — 2026-09-23

**Verdict: NULL, leans negative (lottery-demand side, not the dealer-hedge side) · YIELD MECHANISM.**

The idea came from Gabe's "who is forced or predisposed to buy?": a burst of short-dated OTM call buying leaves dealers
short calls, and their delta hedge is mechanical buying. On 38,769 bursts in 1,254 liquid names (2010-02 → 2026-04),
the stock does **no better** over the next week than same-date names with the same day-t move and ADR: **−0.04pp,
t −1.24**. Every horizon is slightly *negative*, which is the retail-lottery story (call frenzies mark overpricing),
though none clears the bar. The one GEX split goes the "wrong" way for a hedging-flow story too: negative-gamma days
−0.08pp (t −1.84), positive-gamma +0.01pp.

Script: `run_call_burst.py` (pre-registered in the docstring before any return was computed). Log:
`data/studies/logs/call_burst.log`. Events: `logs/call_burst_events.csv`. Data: `silver.options_flow_daily`
(new, built 2026-09-23) → local cache `data/cache/options_flow_liquid.parquet`; prices `liquid_panel_2009.parquet`.
Local, minutes.

## Spec

- **Burst on day t:**
  - short-dated OTM call volume ≥ 3× its own 20-day mean, and ≥ 1,000 contracts;
  - ≥ 2× the matching put volume (directional call buying, not a volatility event);
  - liquid-eligible, and the first burst per name in any 10 sessions.
- **Entry:** the **next open** (flow is only known after the close), 0.10% slippage a side.
- **Primary control:** eligible **non-burst names on the same date, in the same quintile of day-t return and the same
  ADR tercile**, so a big news day can't pass for the flow.

## Results

| horizon | burst | matched control | diff | t (date-clustered) | halves (<2018 / ≥2018) |
|---|---|---|---|---|---|
| **+5 sessions (PRIMARY)** | +0.001% | +0.058% | **−0.039pp** | **−1.24** | −0.017 / −0.059 |
| +1 | −0.238% | −0.198% | −0.035pp | −2.75 | 0.000 / −0.067 |
| +10 | +0.279% | +0.358% | −0.073pp | −1.67 | −0.057 / −0.089 |

- **By SPY dealer-gamma sign (prior day):** positive +0.009pp (t 0.20); negative −0.083pp (t −1.84).
- **Same-name pre-window control** (a random non-burst day 20–60 sessions earlier): −0.108pp (t −1.71).
- **Per year (+5d):** 11 of 17 years negative, no run of either sign.
- **Median day-t return of burst names:** +0.30%. Bursts are not simply big up days, and the control matches the day's
  move anyway.

## Reading

- **No tradeable dealer-hedge lift.** Hedging, if it happens, happens on day t and overnight, before an entry based on
  day-t flow is possible. What is left from the next open on is flat to slightly negative.
- **The lottery side is slightly visible** (−0.03 to −0.07pp across horizons), but it's economically tiny and below
  every bar. Not a short signal.
- The market-level gamma split doesn't support the mechanism: the effect is *more* negative when dealers are short
  gamma, the reverse of what forced hedging predicts. A per-name GEX would be needed to test the mechanism properly,
  and the new flow table has the delta-weighted volumes to build one.

## New data asset

`silver.options_flow_daily` (Glue catalog), 19.2M ticker-days, all tickers, 2010 → 2026. See CLAUDE.md →
Historical data. Reusable for any options-flow / positioning work (put/call skew, per-name GEX proxies, premium
surges).
