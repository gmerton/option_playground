# MEIC (Tammy Chambless) — Skeleton Backtest Results

**Run:** 2026-07-05 · `run_backtest.py` · SPX 1DTE iron condor, 2016-01→2025-09 (her window ends
2025-09-05) · 4,783 condor-trades · fresh Athena pull `spx_dte2.parquet` (1.27M SPX dte-0-2 rows).

## TL;DR

**We cannot faithfully backtest MEIC** (it is 0DTE with 6 intraday entries and intraday per-side
stops; our data is EOD-only, so the intraday entry credit and stop-outs are unobservable). What we
*can* test is the **raw VRP skeleton** — a 1DTE SPX iron condor held to expiry with real EOD entry
prices — bracketed by two scenarios. The result is sharp:

> **The premium does not carry this strategy. The per-side stop does.**
> - **Held to expiry, NO stop (Scenario A): net-NEGATIVE** in almost every year and every delta
>   (full-sample −$0.21 to −$0.81 per 1-lot; even her benign 2023–25 window is slightly negative).
>   High win rates (69–85%) are swamped by trend-day losers — textbook negative-skew premium selling.
> - **Per-side loss capped at 2× credit (Scenario B ≈ the MEIC stop): strongly POSITIVE every year,
>   including the 2022 bear** (+$2.27 to +$4.92 per 1-lot).
>
> So MEIC's edge is **not** premium-harvesting or strike/delta selection — it is **loss-capping via
> the intraday stop.** That reframes the strategy and explains why Tammy obsesses over broker
> stop-handling: the stop *is* the alpha. It also means the edge is **an execution property we
> cannot reproduce or improve on our EOD stack** — it needs 1-min data.

## What A and B are (and why the truth is between them)

| | Scenario A — no stop | Scenario B — 2×-credit cap |
|---|---|---|
| Loss per side | up to (width − credit) | capped at 2× that side's credit |
| Represents | naked short IC held to expiry (pessimistic floor) | idealized per-side stop (optimistic) |
| Missing vs real MEIC | no loss protection at all | **does not charge for whipsaw stop-outs** — days that spike past the stop intraday then revert to a settle-inside "win." Real MEIC eats those. |

Real MEIC sits **A < MEIC < B**, and B is meaningfully optimistic because it only caps the loss on
days that *settle* beyond the short — it never simulates the stop firing on an intraday spike that
later reverts. Her own **live ~20.7% CAR vs 33.3% backtest (~37% haircut)** is exactly that
whipsaw + slippage leak that B cannot see. So: the edge is real and positive (her live proves it),
but it is entirely stop-dependent, and a third of it evaporates in real intraday execution.

## Numbers (per 1-lot, SPX points; ×100 = $). Width 50, slip $0.075/leg.

| Short Δ | Net credit | **A** win% | **A** avg PnL (full) | **A** avg PnL (2023-25) | **B** win% | **B** avg PnL (full) | **B** 2022 |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 0.10 | $3.09 | 84.6% | **−$0.21** | −$0.03 | 87.3% | **+$2.27** | +$3.22 |
| 0.12 | $3.89 | 81.1% | **−$0.29** | −$0.19 | 85.2% | **+$2.77** | +$3.76 |
| 0.15 | $5.12 | 76.0% | **−$0.47** | −$0.25 | 82.2% | **+$3.40** | +$4.64 |
| 0.20 | $7.30 | 69.4% | **−$0.81** | −$0.61 | 78.0% | **+$4.35** | +$5.99 |

- **Scenario A is negative at every delta**, and *less* negative the further OTM (0.10Δ ≈ breakeven
  in calm years) — consistent with premium-selling negative skew: further OTM = fewer breaches but
  thinner premium, net still ≤ 0.
- **Scenario B is positive at every delta and every single year 2016–2025**, including 2018, 2020
  (COVID), and 2022 — the loss-cap neutralizes the exact tail that sinks Scenario A.
- Lower delta (0.10–0.12, matching her stated 10–16Δ shorts) is the sweet spot: closest-to-flat
  Scenario A means the stop adds nearly pure positive EV, with the smallest tail.

## Caveats / what this is NOT

1. **NOT MEIC.** 1DTE overnight (proxy) vs her 0DTE intraday; single daily entry vs her 6 staggered
   (her averaging cuts variance we don't model); held-to-expiry with a settlement-based cap vs true
   intraday stops. Treat magnitudes as directional, not as her returns.
2. **Credit scale differs.** 1DTE-at-close collects more extrinsic than 0DTE-intraday. Per-side, the
   2020s high-IV 1DTE 0.10–0.12Δ credit (~$1.5–2/side) does land in her stated $1–1.75/side range;
   the low-IV 2016–17 years run thinner. So the mapping is decent in high-IV regimes, looser in calm.
3. **Settlement = SPX close (^GSPC).** Correct for PM-settled daily SPXW (the vast majority of 1DTE
   expiries); the occasional third-Friday AM-settled monthly is mismodeled (minor).
4. **Costs understated for MEIC.** Skeleton winners cash-settle with no exit fill (only 4 opening
   legs pay slippage). Real MEIC pays exit slippage on every stopped side — another reason B is
   optimistic.

## Verdict update

Skeleton confirms there IS a positive book here **but the edge is 100% the per-side stop**, not the
premium — so the strategy's viability rides entirely on intraday stop execution, which our EOD stack
cannot evaluate further. `Tested: partial` (skeleton only; MEIC proper needs 1-min SPX data →
BYOB/Option Omega, as Tammy herself uses). Conviction stays **2.5/5**: the backtest neither vindicates
a premium edge (there isn't one) nor refutes the strategy (her live proves the stop-edge is real) —
it *locates* the edge and confirms it's un-improvable here.

## Next steps (only on command)
- Tighten the A↔B bracket with a **Scenario C** that uses SPX intraday High/Low to approximate
  whipsaw stop-outs (requires pricing the short spread at the intraday extreme — adds model/IV error;
  the honest gain is small vs just trusting her live 20.7%).
- If MEIC is ever to be truly evaluated/optimized: 1-min SPX 0DTE data (CBOE/ORATS) in BYOB or Option
  Omega — out of scope for `options_daily_v3`.
