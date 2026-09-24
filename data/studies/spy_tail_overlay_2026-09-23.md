# Deep-OTM SPY put overlay on the certified bearish-high-IV bucket [WL-5f] — 2026-09-23

**Verdict: primary NULL / NEGATIVE CARRY (as pre-registered likely) · secondary UNDERPOWERED, modestly helps the tail.**

- **The primary overlay loses its whole premium on every trade.** Arm B is a 5Δ SPY put at the spread's own ~20-day
  expiry, budget 10% of credit. It lost the premium on **all 75 trades**, including the three spread wipe-outs
  (2018-12, 2020-03, 2022-06), because each crash had bounced back above the 5Δ strike by that Wednesday's expiry.
  - **Cost:** −1.94pp net ROC per trade.
  - **Tail:** it also makes the worst month (−1.3pp) and CVaR-5% (−1.6pp) slightly *worse*, since it adds premium
    and pays nothing back.
- **The ~60-day 3Δ put (arm C, sold after 20 sessions or at the spread's exit) is the only version that touches the
  tail.** At 10% budget:
  - **Cost:** −0.77pp mean.
  - **Tail:** worst month **+0.90pp**, CVaR-5% **+1.52pp**, with the improvement surviving every leave-one-episode-out.
  - **Caveat:** that's only 2 real episodes (2018-Q4, 2020-03). The 2022-06 wipe-out has no ~60-DTE quote, so it's
    excluded.
  - **Rule check:** the CVaR gain exceeds its cost and the worst-month gain about equals it, which is the pre-registered
    UNDERPOWERED-helps-the-tail cell. It's not a verdict to act on at n = 2 episodes.

Script: `run_spy_tail_overlay.py` (pre-registration in the docstring, from the tail-hedging review). Log:
`data/studies/logs/spy_tail_overlay.log`. Trades: `logs/spy_tail_overlay_trades.csv`.
Local run. The bucket was rebuilt from **silver.options_daily_v3**: `run_spy_puts_v3_pull.py` pulled SPY puts
2018 → 2026-04 at DTE 0–35 and 50–70 (4.0M rows, 9 Athena queries), plus DTE 36–49 (0.5M). It goes through the
unchanged engine and **reproduces the recorded 75 trades exactly**: net ROC +6.70% vs +6.76%, per-trade correlation
1.000.

## Results (ROC on spread max loss + overlay premium, per spread contract)

| arm @ budget | priced | Δ mean ROC | Δ worst month | Δ CVaR-5% (months) | overlay return on premium | overlay wins |
|---|---|---|---|---|---|---|
| **B 5Δ same expiry, held @10% (PRIMARY)** | 75 | **−1.94pp** | −1.30pp | −1.55pp | **−100%** | **0%** |
| B @5% / @20% | 75 | −0.98 / −3.81 | −0.65 / −2.55 | −0.78 / −3.04 | −100% | 0% |
| B′ sold at the spread's exit @10% | 75 | −1.58 | −1.20 | −1.37 | −79% | 0% |
| **C 3Δ ~60 DTE, 20 sessions @10%** | 61 | **−0.77** | **+0.90** | **+1.52** | −36% | 3% |
| C @5% / @20% | 61 | −0.39 / −1.51 | +0.46 / +1.77 | +0.77 / +2.99 | −36% | 3% |

- **Leave-one-episode-out (C @10%, Δ worst month / Δ CVaR):** without 2018-Q4 +2.15 / +0.86; without 2020-03
  +0.90 / +0.24; without 2022-H1 +0.90 / +1.52. Every cut stays positive. The 2020-03 cut shrinks the CVaR gain most.
- ⚠ **The month-clustered t (−32 for B, −7 for C) is not meaningful.** The overlay loses almost exactly its premium
  every time, so the difference has near-zero variance. The effective sample is the stress episodes, as pre-registered.
- **Wipe-out trades (A ≤ −50%):** 2018-12-07 −100.7% → B −100.7% / C −97.1%; 2020-03-06 −99.8% → B −99.8% / C −91.1%;
  2022-06-03 −100.3% → B −100.3% / C not priced.
- **Per year:** B costs 1.5–2.1pp in every year.

## Control and carry (overlay return on its own premium)

| Fridays | n | 5Δ same expiry, held | 3Δ ~60 DTE, 20 sessions |
|---|---|---|---|
| bucket Fridays | 75 | −100% (0% win) | −36% (3%) |
| **non-bucket, VIX ≥ 20** | 72 | −100% (0%) | −35% (3%) |
| all VIX ≥ 20 | 147 | −100% (0%) | −36% (3%) |
| all VIX < 20 | 263 | −74% (1%) | −13% (6%) |

The bucket signal makes no difference to the overlay (−36% vs −35%). The overlay is purely a function of the vol
state, and at VIX ≥ 20 its carry is 3× worse than in calm tapes. That's the "richest skew of the cycle" prior, measured.

## Reading

- **Same-expiry deep-OTM puts are useless as a hedge for a 20-day spread.** Over 2018–26, SPY crashes big enough to
  wipe out the 0.25/0.15 spread had always bounced back above the 5Δ strike by the Wednesday expiry. The spread's own
  long leg already caps the loss.
- **A longer-dated 3Δ put sold into the drop does cushion the two measured crashes,** at a cost of ~0.8pp of ROC per
  trade (about 11% of the bucket's +6.7% edge). With two episodes that's a risk-preference call, not a finding. The
  bucket stays as is. Revisit only if a live stress episode says otherwise.

## Infrastructure fixed / found along the way

- `run_qqq_regime_put_sweep._load_options_cache` crashed on an **empty** `data/cache/SPY_options.parquet` (0 rows,
  written 2026-09-22 14:54). **Fixed:** an empty cache is now treated as missing. Refetching it from MySQL needs
  ~13 GB RAM, so it can't run on this machine (8 GB).
- ⚠ **`data/cache/SPY_stock.parquet` was overwritten outside this study.** The working copy has 65 rows in a different
  schema (date index, no `trade_date`), which breaks `_load_stock_cache` and therefore `run_tierab_significance.py`.
  The committed version (2,271 rows, 2017-09 → 2026-09-17) is correct. This study reads it from git; the working copy
  was left untouched.
- New caches: `data/cache/SPY_puts_v3_2018_2026.parquet` (+ `_dte36_49`), SPY puts from v3, reusable for any SPY
  put-spread work.
