# CSP vs stopped stock: is the put's edge over shares a stop artefact? (2026-09-23)

**Question** (Gabe, after the OneOption review): the BCI study found a cash-secured put ≈ the stock held at the put's
delta, minus costs, but both arms were unmanaged. In practice the share buyer runs a tight stop that breaches in
chop, and the put seller runs none. Is "sell puts instead of buying shares in a choppy market" really the whipsaw
cost of a tight resting stop?

**Script:** `run_csp_vs_stopped_stock.py`, pre-registered in its docstring before any stop arm was computed.
**Full output:** `csp_vs_stopped_stock_2026-09-23.log` / `.csv`.

## Design (as registered)

- **Sample:** the BCI trade cache. 0.30Δ OTM puts on the straddle pool, every Friday 2018-01 → 2026-02, real fills,
  settled at intrinsic. 100,644 M-tenor (~28 DTE) and 101,205 W-tenor (~7 DTE) trades, 326 names.
- **Arms:** same name, same date, same collateral:
  - **a PUT:** held to expiry.
  - **b REST:** |Δ| shares; the stop rests intraday and fills at min(open, stop).
  - **c CLOSE:** same stop, judged on the close.
  - **d HOLD:** no stop.
  - Stock arms pay 10 bp per side; a stopped arm sits in cash for the rest of the window.
- **Stops:** 0.5 ADR (primary); the entry-day low (house tight stop); 1.0 ADR (house disaster width).
- **Primary cell:** M tenor, 0.5 ADR, **a − b**, month-clustered t. The bar is |t| ≥ 3 with both halves positive.
- **Regime:** SPY 20-day efficiency ratio at entry, in terciles. The prediction was that a − b is larger in CHOPPY.
- **Multiple testing:** 24 secondary cells, Šidák |t| ≥ 3.07.

## Results

**Primary: NULL.** a − b = **+0.235% of collateral per trade, t 0.84** (98 months). By half: H1 2018–21 −0.005,
H2 2022–26 +0.441 (t 2.77). By year, a − b is positive in 6 of 9 years and **−0.97 in 2020**.

**Regime interaction: wrong sign.** CHOPPY minus TREND = **−0.26 (t −0.55)**. In choppy tapes the put is *no* better
than the stopped stock (+0.05). This holds for every stop width and both tenors (−0.06 to −0.29, all |t| < 0.7).

Levels, M tenor, % of collateral per trade:

| arm | mean | worst 1% | month-cluster Sharpe |
|---|---|---|---|
| **d HOLD** (no stop) | **+0.49** | −16.9 | **0.265** |
| a PUT | +0.36 | **−41.0** | **0.128** (worst) |
| c CLOSE 1.0 ADR | +0.29 | −9.5 | 0.256 |
| c CLOSE 0.5 ADR | +0.20 | −7.9 | 0.220 |
| b REST 0.5 ADR | +0.13 | −5.6 | 0.178 |

(The risk columns are exploratory and were added after the primary was read.)

**What happens to the stops:**
- A 0.5 ADR stop resting intraday is hit on **84%** of 28-day trades (70% on W). In **47%** of those, the stock
  finished above the entry by expiry. The whipsaw is real and large.
- It costs only ~0.37pp against holding, because the stop also exits the crashes. In 2020 the stopped stock made
  +0.72 while the put lost −0.26. Excluding 2020, a − b is +0.39.

**Close-judged beats resting, fourth replication:** c − b = **+0.076 to +0.083 (t 2.15–2.84)** on M, positive in
both halves at all three widths and in every regime. It's below the Šidák 3.07 and so not certified, but it
agrees with the entry study, the gap-share study and the stop definitions.

## Verdict: NULL · MECHANISM · METHOD

- **NULL on the hypothesis as registered.** The put does beat a tight resting stop on average, in the direction Gabe
  expected, but the gap is t 0.84 overall. The gap is *smallest* in choppy tapes, the opposite of the claim, and it
  lives in calm years.
- **MECHANISM:** the tight stop is not a chop tax. It's crash insurance: it costs in calm years and pays in
  selloffs (2018, 2020). The put's "advantage" is simply the absence of a stop, and **the unstopped stock at the
  same delta has more of it**: higher mean, less than half the tail, twice the month-level Sharpe. On a risk-adjusted
  basis the put is the *worst* of the six arms, because short gamma makes its left tail 2.4× the delta-matched stock's.
- **METHOD / practice:** the share buyer's cure isn't selling puts. It's to stop resting the tight stop intraday:
  judge it on the close (+0.08, consistent), or widen to 1 ADR and cut size. Both are already house rules
  (`stop_definitions.md`).

⚠ **Caveats:**
- Daily bars: the resting fill is min(open, stop), which is optimistic for intraday spikes through the level.
- The put arms can't be managed early (hold to expiry, as registered). Rolling or closing losers is a separate
  question.
- Survivorship: this is the current straddle pool.
