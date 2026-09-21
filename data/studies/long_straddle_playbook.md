# Long Straddle Playbook

**Strategy:** Buy ATM straddle (long call + long put, same strike)
**Perspective:** Buyer — profit when stock moves more than implied by premium
**Universe:** 323-ticker weekly-optionable pool — see *Approved-List Rebuild* below.
⚠ The 140-name approved list is **SUPERSEDED**; ticker qualification failed OOS testing.
**Last updated:** 2026-09-16
**Status:** Research complete. Trading, with two caveats added 2026-09-15 — see
*Independent VRP validation* at the bottom. The entry mechanism is now corroborated by a
measurement that shares no code with this backtest; the **magnitude is not statistically
resolved**, and the **tail concentration is a live sizing risk**.
**Revision 2026-09-16:** added an **RSI(14) < 70** entry gate (condition 5). Entries at RSI ≥ 70
lost ~12pp/trade; the walk-forward held in 7 of 8 years (within-week placebo p = 0.0002).
Sleeve +4.14% → +5.38%/trade, monthly t 1.78 → 2.17. See *RSI Gate* below.
**Revision 2026-08-08:** added an IV-percentile entry gate (condition 3). Single-leg
(call-only / put-only) variants tested and rejected. See *Gate Revision* below.
**Revision 2026-08-08 (b):** the 140-name approved list is **retired**. An honest
walk-forward showed ticker qualification performs WORSE than no ticker selection at all
(+14.72% vs +16.06% OOS). Trade the gates across the whole weekly pool instead.
**Revision 2026-09-10:** path simulation on daily bid/ask (see *Re-centering and the real stop*).
Re-centering REJECTED (every variant -3 to -7pp vs hold). The -50% stop's +7pp is a modelling artefact:
a real close-based stop adds nothing (-0.25pp). **Honest expectation: ~+4% per trade after costs, not +14-16%.**
**Revision 2026-08-11:** earnings tested — **flagged, not gated**. The IV-percentile
gate already removes 98% of earnings trades as a byproduct. See *Earnings* below.
**Correction 2026-08-08:** DTE relabelled 10 → **7**. Friday entry into the next Friday
expiry is a 7-day gap; the query targeted 10 DTE with ±5 tolerance, so 7 won ~always.
Observed: **88.0% of trades at DTE 7, 7.8% at 14, only 0.2% at an actual 10** (mean 7.71,
median 7). No result changes — every backtest in this document was already run on 7-DTE
trades. Only the label and the stop rationale were wrong. **Other DTEs are untested.**

---

## Strategy Structure

| Leg | Type | Delta | DTE | Action |
|-----|------|-------|-----|--------|
| Call | ATM call | ~+0.50Δ | ~7 DTE | Buy 1x |
| Put  | ATM put  | ~−0.50Δ | ~7 DTE | Buy 1x |

- Same strike for both legs
- Entry: Friday morning, **next Friday's expiry (~7 DTE)**
- Same expiry for both legs (weekly options)

**P&L:**
- Cost = call_mid + put_mid (debit paid)
- Payout = call_settlement + put_settlement at expiry
- Profit = payout − cost
- ROC = profit / cost × 100%

---

## Entry Conditions (all required)

1. **Ticker in the weekly-optionable pool** — `data/watchlist/straddle_pool_323.txt`
   - 323 names from the study universe carrying weeklies on ≥60% of days
     (proxied by `iv_put_10` availability in `silver.fwd_vol_daily`)
   - A 7-DTE straddle *requires* weeklies, so names without them are untradeable here
     regardless of how they would score. This is a structural filter, not a performance one.
   - ⚠ No per-ticker performance qualification. See *Approved-List Rebuild* for why.
2. **FVR ≥ 1.20** — forward vol ratio (30→90d) must be in contango
   - FVR = fvr_put_30_90 from `silver.fwd_vol_daily`
   - FVR ≥ 1.20 means 90-day implied vol > 30-day → market expects vol to expand
   - Check on the Friday morning of entry
3. **IV percentile ≤ 30** *(added 2026-08-08 — see Gate Revision below)*
   - `iv_put_10` ranked against that ticker's **own trailing 252 daily observations**,
     ending the day **before** entry. Not a cross-sectional rank — MSTR at 80% IV and
     KO at 15% are not comparable.
   - Tenor-matched on purpose: the trade is ~7 DTE, and iv_put_10 outperformed
     iv_put_30 and iv_put_90 as a predictor.
   - Requires ≥60 prior observations to compute; names without that history are skipped.
4. **Liquid chain** — verify bid > 0 / ask > 0 / OI > 0 on both legs in broker before entering
   - Approved list includes some thinly-traded names; always confirm fills are realistic
5. **RSI(14) < 70** *(added 2026-09-16 — see RSI Gate below)*
   - Wilder RSI on daily adjusted closes, read on entry day (the backtest read the entry-day close).
   - RSI ≥ 70 ≈ 2.8 ADR above the 21 EMA: the same "extended" flag in different units.
   - Checked by `run_straddle_screen.py` (column `RSI`, near misses say `RSI>=70`) and
     `run_straddle_iv_gate.py` (`passes_all`). Helper: `src/lib/commons/rsi.py`.
   - No RSI reading (thin history) → not blocked.

---

## Sizing

**Per-trade allocation is based on premium paid (= max loss).**

| FVR at entry | Size | Dollar amount ($100K account) |
|---|---|---|
| FVR ≥ 1.40 | Full | 1.5% = **$1,500 in premium** |
| FVR 1.20–1.39 | Half | 0.75% = **$750 in premium** |

**Example:** Straddle costs $3.00 ($1.50 call + $1.50 put) with FVR = 1.45
→ Buy 5 contracts ($1,500 ÷ $300/contract)

**Portfolio cap:** Maximum 3% of account in open straddle positions at any time.
Multiple signals may fire the same week; if total open premium would exceed $3,000,
skip the weakest FVR signals first.

> **Note on the IV-percentile gate and trade count.** Adding gate 3 cuts qualifying
> trades by ~56% (7,821 → 3,452 over 2018–2026). That is not a cost here: at 1.5%
> per full-size trade against a 3% cap you can fund roughly two positions at a time
> regardless, so you were already turning away more signals than you could take.
> The selectivity is effectively free.

---

## RSI Gate — added 2026-09-16

Full study: `data/studies/rsi_conditioning_study_2026-09-16.md` (sections B, D, E, F). Scripts
`run_rsi_conditioning_study.py`, `run_rsi_straddle_walkforward.py`.

**Finding.** On the 5,886 gated trades (2018-04 → 2026-02), entries with RSI(14) ≥ 70 averaged
**−6.1%** (median −29%) vs +5.4% for the rest. Within-week regression −12.8pp, t −3.4. RSI < 30 is
not a problem (only 63 trades); the gate is one-sided.

| check | result |
|---|---|
| each year, fixed 70 | skip helped mean, median and ex-top-1% in **7 of 8** full years (2020 lost: skipped tail winners) |
| expanding window 2020–26 | none +5.83% t_m 2.15 → **fixed 70 +6.95% t_m 2.51** |
| within-week placebo (5,000 shuffles) | real lift +1.24pp vs 95th pct +0.56, **p = 0.0002** |
| cutoff plateau | smooth from 60 to 80, no spike at 70 |
| breadth | 176 tickers; leave-one-ticker-out gap −10.9 to −12.7pp; 77% of tickers show it |

**Effect on the sleeve (in-sample):** n 5,886 → 5,250, mean +4.14% → **+5.38%**, monthly t 1.78 →
**2.17**, mean ex-top-1% +0.33% → +1.63%, top-1% share of return 92% → 70%.

**Why it works — it is NOT the call.** Within the same week, extended names' straddles are cheaper
(−0.39% of spot) but the stock moves even less (−0.86%), so the move beats breakeven 8pts less
often. The call leg is no worse (−5.5pp, t −0.7); the **put leg** takes the loss (−19.9pp, t −2.9)
because extended names drift slightly up.

**Why 70 and not 60.** Skipping ≥ 60 raises the mean more (+6.74%) but drops a third of trades for no
gain in monthly t. 70 is the textbook level and was set before any results were seen.

⚠ **Does not fix the strategy's core weakness.** The sleeve is still carried by its tail.

---

## Gate Revision — IV percentile added 2026-08-08

**Claim tested:** does an IV *level* gate beat, or complement, the FVR *term-structure*
gate? They measure different things (level vs shape) and are close to orthogonal.

**Method:** 140-name approved list, 2018-01→2026-02, ~7 DTE ATM straddle, Friday entry,
stop modelled as the house loss-floor `max(roc, −50%)`, $0.50 min straddle cost / $0.25
min leg. Date-clustered bootstrap (Friday entries across 140 correlated names are not
independent). Scripts: `run_track2_pull.py`, `run_track2_gates.py`.

**Result — straddle with stop:**

| Arm | n | Win% | Mean | Sharpe | 95% CI | vs A |
|---|---:|---:|---:|---:|---|---:|
| no gate | 25,001 | 42.3% | +11.04% | 0.140 | [+7.66, +14.76] | −5.21 |
| **A — FVR ≥ 1.20** (prior gate) | 7,821 | 44.5% | +16.25% | 0.192 | [+12.48, +20.52] | — |
| A+ — FVR ≥ 1.40 | 2,977 | 44.3% | +16.79% | 0.199 | [+11.98, +21.73] | +0.54 |
| B — IV pct ≤ 30 alone | 7,896 | 42.8% | +13.48% | 0.161 | [+9.19, +18.30] | −2.77 |
| **C — both** (current) | 3,452 | 44.9% | **+18.08%** | **0.209** | [+12.90, +23.45] | **+1.83** |
| C — IV pct ≤ 20 & FVR ≥ 1.20 | 2,473 | 44.7% | +18.65% | 0.214 | [+12.88, +24.42] | +2.40 |

The gates **stack**: FVR alone is the stronger single filter (+16.25 vs +13.48), but
combining them adds +1.83pp and lifts Sharpe 0.192 → 0.209. Arm A's Sharpe of 0.192
sits close to this playbook's original +0.170, which validates the pipeline.

⚠ **Absolute levels carry look-ahead** — the 140-name list was itself selected on
2021–25 data. The *arm comparison* is clean (identical trades, only the filter differs),
but do not read +18.08% as an expected return.

⚠ **The −50% stop is a loss clip, not a path-dependent simulation.** It rescues 30.7%
of straddle trades and adds +7.39pp to the mean. Defensible for a straddle — one leg
gains as the other loses, so the position decays toward the stop rather than gapping
through it — but it is an approximation, and the reported edge depends on it.

### Single legs were tested and rejected

Buying only the call or only the put was tested on the same entries. **No edge — it is a
directional bet.** Calls beat puts overall (+12.45% vs −4.67%) purely because 2018–2026
was a bull market; in 2022 puts returned **+69.41%** against calls' **+9.41%**. Neither
FVR nor IV percentile contains directional information, so there is no signal here to
select a leg with.

Single legs are also far more exposed to the stop approximation — the clip rescues
**54.8%** of call-only and **60.6%** of put-only trades (adding ~25pp), versus 30.7% for
the straddle. Their apparent outperformance is largely an artifact of assuming you always
fill at exactly −50%, which a 7-DTE single leg can gap straight through.

---

## Earnings — tested 2026-08-11, FLAGGED not gated

**Question:** should an earnings event inside the holding window disqualify a trade?

**Method:** 8,557 historical earnings dates for 275 pool tickers pulled from the Tradier
corporate calendar into `stocks.earnings_report` (previously empty). A trade is marked
`earnings` if any event falls in `[entry_date, expiry]`. Restricted to the 274 tickers
with earnings data, so absence means absence — the 48 without data are ETFs.
Scripts: `run_earnings_pull.py`, screen flag in `run_straddle_screen.py`.

### Earnings trades are materially worse

| Segment | n | Win% | Mean (stop) | Mean (hold-to-expiry) | 95% CI (hold) |
|---|---:|---:|---:|---:|---|
| No earnings in window | 38,768 | 41.8% | +11.75% | **+4.79%** | [+0.41, +10.07] |
| **Earnings in window** | 3,715 | 41.2% | +7.90% | **+0.13%** | **[−3.66, +4.14]** |

Stripped of the stop, earnings straddles earn **essentially nothing** — indistinguishable
from zero. Win rate barely moves (41.2% vs 41.8%) and p95 is *lower* (+148.5 vs +158.6).
You pay elevated IV for a move that on average does not exceed what was priced in. This is
the standard finding — implied earnings moves are fairly-to-over-priced — now confirmed
on our own data.

### But the IV gate already handles it

| | No earnings | Earnings in window |
|---|---:|---:|
| Median IV percentile | 45.6 | **90.1** |
| Share passing `IVpct ≤ 30` | 34.7% | **2.0%** |

Pre-earnings IV sits at the **90th percentile** of a name's own trailing range, so the
existing gate screens out **98%** of earnings trades without being asked to. Earnings
trades fall from **9.6% of all trades to 0.3% of arm C** (16 of 5,265).

**Decision: no earnings gate.** An explicit filter would remove ~16 trades in 5,265 — no
measurable effect, one more rule to maintain. Instead `run_straddle_screen.py` reports
days-to-next-earnings per qualifier and marks any that fall inside the holding window.

⚠ The ~2% that *do* pass the IV gate before earnings are the exception worth eyeballing.
A recently-listed or regime-shifting name can rank low against a stale reference window
even with earnings-elevated IV. Treat an `⚠ IN WINDOW` flag as a sizing input, not a veto.

⚠ The arm-C earnings cell is only **16 trades** — far too thin to say how *gated* earnings
trades perform. The finding above is about the unconditional population.

---

## Exit Rules

| Condition | Action |
|-----------|--------|
| Position value drops to ≤50% of premium paid | **Exit immediately (stop-loss)** |
| Expiry | Let expire (payout is settlement value) |
| No other take-profit rule | Do not exit early on winners — let them run |
| Stock moved far from the strike | **Do not re-center or flat-take** — tested 2026-09-10, −3 to −7pp per trade |

**Why no profit cap:** The long straddle is a right-skewed payoff. OOS testing showed
that any profit cap reduces Sharpe (Cap 100% drops Sharpe from +0.17 to −0.04).
The large wins are not anomalies — they are the strategy.

**Why stop at −50%:** Removing trades that lose >50% of premium improves OOS Sharpe
from +0.072 (hold to expiry) to +0.170 — a 2.4× improvement, positive in every
test year 2021–2025. On a ~7 DTE straddle a position down 50% is typically 2–4 days in,
with most remaining value being time premium that will decay before expiry.

⚠ The original wording of this rationale referenced "day 5–7 on a 10 DTE straddle" — that
was based on the mislabelled DTE (see header). On a 7 DTE trade, day 5–7 *is* expiry. The
stop's empirical support is unaffected; only the reasoning is restated.

---

## Re-centering and the real stop — 2026-09-10

**Question:** when the stock has moved away from the strike, does it pay to sell the moved pair and
buy a fresh ATM straddle (re-center), or to sell and go flat? And what does the −50% stop earn on a
real price path instead of the `max(roc, −50%)` clip?

**Method:** 19,270 gated trades, daily close bid/ask/delta from `options_daily_v3`, house cost model
(25% of bid-ask + $0.0065/sh/leg per trade), expiry settled by put-call parity. Triggers: net delta of
the held pair ≥ 0.35 / 0.50, or a move ≥ 0.5 / 0.75 / 1.0 × the entry straddle price; only with ≥2 more
trading days to expiry. Full tables: `data/studies/straddle_recenter_study.md`.

**Result — 7 DTE, both gates (n = 5,886), after costs unless noted:**

| Variant | Mean | Win% | vs hold (paired t) |
|---|---:|---:|---:|
| Hold, pool-file payout, mid (this playbook's basis) | +8.15% | 43.7% | |
| Hold, parity settlement, mid | +6.82% | 43.4% | |
| −50% clip (this playbook's model) | +14.23% | 43.4% | |
| **Hold, after costs** | **+4.14%** | 42.3% | |
| Real −50% stop on the daily close | +3.89% | 41.3% | −0.25pp (−1.37) |
| Re-center, move ≥ 0.75× implied, once | −0.25% | 40.6% | −4.40pp (−7.16) |
| Re-center, move ≥ 1.0× implied, once | +0.71% | 41.4% | −3.43pp (−6.60) |
| Re-center, net delta ≥ 0.35, unlimited | −2.87% | 38.4% | −7.01pp (−9.89) |
| Sell and go flat, move ≥ 1.0× implied | +1.38% | 48.7% | −2.76pp (−4.65) |

**1. Re-centering is rejected.** Every trigger, threshold and count loses 3.4–7.0pp per trade against
holding, t −6.6 to −9.9; more re-centers are worse. Flat-take loses 2.8–5.9pp. It raises the win rate
and median (the trade *feels* better) but cuts the mean — the same shape as the profit caps. Moves that
trigger a re-center tend to keep running, and the convex tail is the whole edge. Rejected in 7 of 9
years; the exceptions are 2018 (n=288) and 2026 (n=100, tie).

**2. The −50% stop earns nothing on a real path.** The clip adds +7.4pp because it assumes every trade
that ends below −50% was exited at exactly −50%. In practice 30% of trades finish below −50%, but most
get there on the last day, which a close-based stop cannot reach: it catches only a third of them, and
a third of the trades it does stop would have recovered (7.7% would have finished positive). Net
−0.25pp (t −1.4). **Keep the stop only as a disaster guard, not as a return source.**

**3. Settlement and costs.** The pool file's payout (`call_last_exp + put_last_exp`) counts a stale
print on the out-of-the-money leg: +1.3pp vs true settlement. Measured entry/exit costs: −2.7pp
(median entry bid-ask 5.9% of the straddle mid).

**4. The longer hold has no edge.** 14-DTE entries on the same signals: +1.28% after costs (t +1.19);
the real stop is worse (−1.08pp, 33% stopped) and re-centering is worse still. The edge lives at 7 DTE.
Discretionary 2–3 week straddles (e.g. PANW 9/2→9/18) are outside the tested strategy.

**Honest expectation, revised:** ≈ **+4% per trade after costs** (t +3.7), both gates, hold to expiry.
The FVR-only superset is +1.3% (t +1.8): the IV-percentile gate is doing most of the work.
⚠ Not tested: intraday re-centering (the data has closing marks only), rolling to a later expiry.

---

## Performance (OOS Walk-Forward, 2021–2025)

Walk-forward design: qualify tickers on IS data (2018→N−1), trade approved
list in test year N with FVR≥1.20 gate. Five folds: 2021, 2022, 2023, 2024, 2025.
Minimum straddle cost $0.50 (penny straddles excluded).

**With stop at −50% of premium:**

| Year | N trades | Win% | Avg ROC% | Sharpe |
|------|----------|------|----------|--------|
| 2021 | 1,932 | 41.7% | +10.1% | +0.125 |
| 2022 | 1,187 | 47.5% | +17.9% | +0.236 |
| 2023 | 1,608 | 44.4% | +13.8% | +0.176 |
| 2024 | 1,993 | 42.5% | +10.2% | +0.140 |
| 2025 | 2,116 | 44.5% | +13.6% | +0.175 |
| **OOS avg** | **1,767** | **44.1%** | **+13.1%** | **+0.170** |

Baseline (hold to expiry, no filter): Sharpe −0.003
Baseline (FVR≥1.20, all tickers, hold to expiry): Sharpe +0.036
This strategy (approved list + FVR gate + stop): Sharpe +0.170

---

## FVR Signal Interpretation

FVR = fvr_put_30_90 = (30→90d forward vol) / (spot 30d IV)

| FVR | Interpretation | Action |
|-----|----------------|--------|
| < 1.00 | Backwardation — vol term structure inverted | Skip (seller's market) |
| 1.00–1.19 | Neutral | Skip |
| 1.20–1.39 | Mild contango — some buyer edge | Half size |
| ≥ 1.40 | Strong contango — market expects vol to expand | Full size |

The FVR signal works because options at ~7 DTE are priced from the short-end of
the vol surface. When the term structure is in contango (FVR ≥ 1.20), the 7 DTE
options are relatively cheap vs the market's own 90-day implied vol forecast —
creating structural edge for the straddle buyer.

---

## Approved-List Rebuild — 2026-08-08 — ticker qualification REJECTED

**Question:** today's IV gate was bolted onto a list qualified under FVR alone — selected
under one rule, traded under another. Does rebuilding the list under *both* gates help?

**Method:** candidate pool = 323 weekly-optionable names (139 of the 140 published names
fall inside it; RVLV is the lone exception at 51% coverage — so this re-ranks within the
same eligible universe rather than redefining it). Published fold structure unchanged:
qualification sees only `year < N`, criteria `n≥15, avg_roc>0, sharpe>0`, folds 2021–25,
stop −50%. Scripts: `run_straddle_pool_pull.py`, `run_straddle_rebuild_wf.py`.

**Result — out-of-sample by fold:**

| Arm | 2021 | 2022 | 2023 | 2024 | 2025 | Mean | n | Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 published list + FVR only | +18.53 | +21.36 | +18.44 | +12.78 | +14.63 | +17.15 | 5,200 | 0.212 |
| 2 published list + both gates | +22.13 | +21.30 | +18.68 | +13.96 | +15.12 | +18.24 | 2,501 | 0.218 |
| 3 **rebuilt** list + both gates | +13.67 | +21.18 | +12.44 | +13.58 | +12.75 | **+14.72** | 1,449 | 0.187 |
| 4 **full pool, no list** + both | +14.97 | +18.02 | +15.25 | +13.19 | +18.88 | **+16.06** | 4,573 | 0.196 |

**The rebuilt list is the worst arm — worse than using no ticker list at all.** Arm 4 beats
arm 3 by +1.34pp on 3× the trades. Ticker qualification subtracts value.

**Why it broke — the qualification sample starves.** Requiring 15 in-sample trades that pass
*both* gates is brutal on early folds, and the resulting lists churn violently:

| Fold | Qualified | Overlap with prior fold |
|---|---:|---:|
| 2021 | **8** | — |
| 2022 | 43 | 18.6% |
| 2023 | 48 | 89.6% |
| 2024 | 81 | 50.0% |
| 2025 | 117 | 65.0% |

Eight tickers in 2021, and 18.6% overlap into 2022. That is noise, not skill.

**Arms 1 and 2 look best but are contaminated** — the published list was selected on 2021–25
and is being scored on 2021–25. Their apparent edge is look-ahead. **Arm 4 is the honest
configuration.** Its only look-ahead is the pool's weekly-coverage definition, which is a
liquidity criterion rather than a performance one.

### Honest expectations (arm 4) — corrected and cost-measured 2026-09-20

> ⚠ **The numbers previously in this block were the wrong population.** They read +5.76% / +12.61%,
> which is **full pool + FVR gate only** — no IV gate — not arm 4. Traced 2026-09-20 by reproducing
> every variant: FVR-only on folds 2021–25 gives +5.76 / +12.62, median −14.15, win 43.4%, matching
> the old block to rounding. The error dates to the block's first commit (2026-09-02) and made the
> honest configuration look **~2.9pp worse than it is**. The fold table above (+16.06 mean) was always
> right; this block disagreed with it.

Arm 4 = full pool + **both** gates, folds 2021–25, **n 4,573**. Entry costs are now **measured** from
real bid/ask on both legs of every entry (100% quote coverage) — see
[straddle_slippage_2026-09-20.md](straddle_slippage_2026-09-20.md). Cost is one-sided: the position
settles at expiry, so you only cross on the way in. Measured entry spread: **median 6.5% of mid**.

| Entry fill | Mean, no stop | **Mean, −50% stop clip** | Median | Win% |
|---|---:|---:|---:|---:|
| mid (the old basis) | +8.77% | **+15.46%** | −12.10% | 44.5% |
| **realistic — half the spread (2.2% over mid)** | **+6.73%** | **+13.57%** | −13.88% | 43.8% |
| full ask (4.4% over mid) | +4.79% | +11.78% | −15.45% | 42.7% |

**Measured slippage sensitivity: −0.86pp of ROC per 1% paid over mid** (this document previously
carried a parameterised guess of −0.95pp — close, and now retired). **Every fold stays positive at
every fill level**; the worst single cell is 2024 at the full ask, +9.69%.

⚠ **The stop clip contributes +6.69pp — 43% of the headline** — by rescuing 29.3% of trades. It is an
assumption that you always exit at exactly −50%, **not a path simulation**. Treat **+13.6%** as the
realistic expectation and **+6.7%** as the assumption-free floor. Replacing the clip with a real path
simulation needs daily marks on the specific contracts and is now the **largest remaining unknown in
this strategy**.

**Capacity is not binding:** median **37 qualifying signals per week** against ~2 fundable
positions under the 3% cap. You will always be choosing among far more signals than you can
take, which is why the IV gate's 56% trade-count cut costs nothing.

---

## Approved Ticker Lists (SUPERSEDED 2026-08-08 — retained for reference only)

> These lists are **no longer the entry universe**. See *Approved-List Rebuild* above:
> per-ticker qualification underperformed trading the gates across the whole weekly pool.
> Kept here because the names remain a useful liquidity-screened starting point.


### Core List — All 5 Folds (82 tickers)
*Qualified in every test year 2021–2025. Full-size eligible.*

AAL, AAOI, AAPL, AFL, AG, AMC, ANET, AVGO, BAC, BK, BKNG, BSX, CAT, CMG,
COF, COP, COTY, CSCO, CVNA, CVS, CYBR, EOG, ERX, ET, ETN, EW, FCX, FDX, FEZ,
GM, GS, HAL, HCA, HD, IBM, INTU, IYR, JNJ, JPM, KKR, LB, LLY, LOW, LRCX,
MCK, MET, MRK, MRVL, MT, MU, NOV, NTAP, NTES, NVDA, OIH, PAA, PBR, PSX,
RCL, RIG, RRC, SCHW, SLB, STX, SU, SYY, TECK, TEVA, TPR, TQQQ, TSM, UAL,
ULTA, UPRO, URI, VLO, VOD, WFC, WMB, XLK, XRT, YUM

### Extended List — 3–4 Folds (58 additional tickers)
*Qualified in 3 or 4 of 5 test years. Use at 0.5× the tier sizing above.*

ABBV, AGNC, AMAT, AMRN, ASML, AXP, BP, BURL, C, CF, CLF, COST, CVX, DAL,
DB, DE, ED, EPD, FAS, FSLR, FUTU, GD, HPE, INTC, JETS, KLAC, KR, LEN, LVS,
MAR, MARA, MDB, NET, NOK, NTR, NUE, NUGT, OXY, PLTR, PM, PNC, REGN, ROST,
RVLV, SIG, SLV, SMH, STEM, TAP, TJX, TNA, TXN, UNP, WDC, WPM, XHB, XOM, ZIM

---

## Top Performers (FVR≥1.20, full period, ≥3/5 folds)

| Ticker | N | Avg ROC% | Win% | Sharpe | Folds |
|--------|---|----------|------|--------|-------|
| OIH | 24 | +77.4% | 66.7% | 0.582 | 5/5 |
| NOV | 22 | +58.7% | 54.5% | 0.476 | 5/5 |
| AG | 30 | +84.6% | 66.7% | 0.397 | 5/5 |
| RRC | 37 | +32.8% | 54.1% | 0.363 | 5/5 |
| LOW | 86 | +30.7% | 61.6% | 0.361 | 5/5 |
| VLO | 103 | +32.3% | 53.4% | 0.309 | 5/5 |
| CAT | 209 | +24.9% | 52.6% | 0.265 | 5/5 |
| EOG | 76 | +23.7% | 59.2% | 0.266 | 5/5 |
| SU | 82 | +22.4% | 56.1% | 0.280 | 5/5 |

Energy and commodities dominate the top tier. Their options chronically underprice
realized moves due to commodity price sensitivity and geopolitical event risk.

---

## What Not To Do

- **Do not cap profits.** Every profit target tested (50%, 75%, 100%, 150%, 200%)
  reduced OOS Sharpe below baseline. The large wins are the edge, not anomalies.
- **Do not trade without the FVR gate.** Unfiltered straddle buying on all tickers
  has negative Sharpe (−0.003 OOS). The FVR filter is essential.
- **Do not trade tickers not on the approved list.** The per-trade ML model
  (LogReg + LGBM, 10 features) produced AUC ~0.50 across all 5 test years —
  individual trade prediction does not work. Ticker selection is the edge.
- **Do not exceed 3% total open straddle premium.** Simultaneous signals are
  correlated (they all win or lose in a vol spike week).

---

## Key Scripts

**Gate revision (2026-08-08):**
```bash
# pull ~7 DTE straddles + iv_put_10/fvr for the 140 approved names
AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_pull.py

# compare gate arms (no gate / FVR / IV-pct / both), pooled + walk-forward
AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_gates.py
```
⚠ `options_daily_v3` uses **99999.99 as a sentinel** in `last`. Only ~8 rows in 27k, but
they produced returns up to +7,272,627% and moved the sample mean from +3.98% to +1238%.
Filter on the sentinel itself — NOT on `payout > strike`, which would delete legitimate
large upside winners. Clustered in leveraged ETFs (TQQQ, UPRO).


| Script | Purpose |
|--------|---------|
| `run_long_straddle_study.py` | Full IS study, FVR bucket breakdown, per-ticker leaderboard |
| `run_straddle_ticker_walkforward.py` | Walk-forward ticker validation (generates approved lists) |
| `run_straddle_exit_analysis.py` | Exit rule simulation (cap/floor ROC analysis) |
| `run_long_straddle_model.py` | ML model (LogReg + LGBM) — AUC ~0.50, not actionable |

**Data source:** `silver.option_legs_settled` (3M rows, 987 tickers 2018–2026)
**FVR source:** `silver.fwd_vol_daily` → cached at `data/cache/fvr_daily.parquet`

---

## Research Notes

- **Individual trade ML model failed (AUC ~0.50):** Features (VIX, FVR, IVR, RV20,
  premium_pct) cannot predict whether a specific stock moves in a specific week.
  Straddle outcomes are event-driven and path-dependent at the trade level.
- **Ticker-level signal is real:** Structural alpha exists in tickers where IV
  chronically underprices realized moves. The walk-forward validates this signal
  persists OOS year-over-year.
- **OOS improves on IS for top names:** OIH, AG, VLO OOS Sharpe exceeds IS —
  no overfitting concern for the top tier.
- **2022 note:** High baseline ROC in 2022 reflects the market crash (straddles
  exploded in value across the board). The approved list showed lower 2022 ROC
  than the unfiltered baseline — it filters out high-RV crash-sensitive names,
  which is the correct behavior for a stable strategy.

*Playbook written: 2026-03-22*
*Based on: silver.option_legs_settled, 987 tickers, 2018–2026*

## Gate 3 reference source — rebuilt live off IBKR (2026-09-16)

`silver.fwd_vol_daily` ends **2026-02-20** and cannot be extended: the builder prices the ATM put from v3's
bid/ask, and v3 lost bid/ask in March 2026 (stored IV survives to mid-May, then prints only). So the live screen was
ranking today's IV against a window that stopped seven months ago.

**The staleness is material at the single-name level, even though the index regime is unchanged.** VIX over the stale
window vs the months since is flat (mean 19.0 vs 18.7, 30th pctile 16.4 both, today at the 24th pctile in each). But
ranking the *same* IBKR IV30 series in the pre-Feb-2026 window against the months since, on 20 names:

| window effect (old-window pctile − recent-window pctile) | median | mean | max | verdict flips at the ≤30 gate |
|---|---|---|---|---|
| 20 liquid names, 2026-09-15 | +27.5pp | +23.9pp | 55pp | **10 of 20** |

Sixteen of twenty are positive, i.e. single-name IV drifted **up** since February, so the stale reference makes names
look more expensive than they are and the ≤30 gate was too strict. Index vol is not a proxy for single-name vol here.

**What the screen does now** (`run_straddle_screen.py`, `--iv-source ibkr|athena`): gates 2 and 4 (FVR, liquidity) run
first, then IBKR `reqHistoricalData(OPTION_IMPLIED_VOLATILITY)` supplies a trailing-1y IV30 distribution for the
survivors only — typically ~10 names, far inside IB's 60-requests-per-10-minutes budget (capped at 50). Both
percentiles print side by side with the source per row; it falls back to the stale table when TWS is absent. The
live-port guard in `ibkr_bot/conn.py` is respected, not bypassed (the screen only calls reqHistoricalData).

**Effect on 2026-09-15 (full 331-name pool):** 54 passed FVR, 88 liquidity, 10 both; 7 qualified on the IBKR gate.
Four of those seven — WMT, MSFT, V, BROS — were blocked by the stale table (53 / 70 / 41 / 38%) and clear easily on
current data (26 / 18 / 19 / 24%). AMC has no fwd_vol_daily history at all and is only screenable this way.

⚠ **Not the identical metric.** IBKR publishes a 30-day composite IV; the study gated on ~10-DTE ATM put IV, chosen
because the trade is ~7 DTE. The +4.14%/trade result was measured on the 10-DTE metric, so the IBKR gate is the same
idea on a less event-sensitive tenor. Watch one consequence: the old gate removed ~98% of earnings trades as a
byproduct precisely because 10-day IV spikes into a print, and a 30-day composite will do that less. All seven
qualifiers on 2026-09-15 had earnings at T+43 or later, so nothing leaked that day, but if earnings-in-window
qualifiers start appearing, promote the earnings flag to a gate.

---

# Independent VRP validation (2026-09-15)

A new stage-one screen measures the variance risk premium directly, without simulating a
single straddle: `vrp = ATM implied vol − realized vol over the matching forward window`
(`run_vrp_panel.py`, `src/lib/studies/vrp_panel.py`). Because it shares no code, no cache
and no settlement logic with this playbook's backtest, it is a genuine outside check on the
entry mechanism. Joined to 128,447 trades from `data/cache/long_straddle_features.parquet`
via `run_vrp_straddle_reconcile.py`. Full write-up: `data/studies/vrp_straddle_reconcile.md`.

## The headwind this strategy trades into

On the 331-name straddle pool, 2018 to 2026, short-dated ATM implied vol is **rich by +4.13
vol points** (t 8.74, 82% of days positive). That is measured over the same 7 to 14 day
horizon this strategy buys. Unconditionally, a long straddle here is buying vol that is
systematically overpriced. Everything below is about how the gates escape that.

## The gates work, and they work for the stated reason

Each gate cuts the premium the trade faces. Monotonically, on both axes:

| cell | n | premium faced | winsorized mean ROC | ex-top-1% mean |
|------|---|---------------|---------------------|----------------|
| no gates | 72,272 | +2.29 vol pts | −0.21% | −3.03% |
| gate 2 only (FVR ≥ 1.20) | 23,227 | +1.37 | +2.54% | −0.24% |
| **gates 2+3 (this playbook)** | **13,167** | **+0.79** | **+3.74%** | **+1.00%** |
| gates 2+3 with IVpct ≤ 15 | 8,884 | +0.48 | +5.29% | +2.60% |

This is the strongest corroboration the strategy has. An independent estimator says the
entry conditions select vol that is genuinely cheap relative to what follows, and the
winsorized +3.74% lines up with the playbook's stated ~+4% per trade.

**Gate 2 is the workhorse, not gate 3.** FVR ≥ 1.20 alone moves the winsorized mean from
−1.31% to +3.06% and halves the premium faced. Gate 3 adds on top of it, but only at the
extreme: within the gate-2 population the ≤15 percentile bucket returns +5.29% while the
15–30 band returns +0.51%. An earlier read of this data called gate 3 useless; that was
measured on the **ungated** population and was wrong. Inside the population this playbook
actually trades, gate 3 helps.

## ⚠ Caveat 1 — the magnitude is not statistically resolved

Every name in the pool enters on the same Fridays. Pooling 13,167 trades therefore does
**not** give 13,167 independent observations; it gives about 331 dates. Collapsing each date
to a cross-sectional mean and correcting for that:

```
  cell                     trades   dates    mean    t_NW   boot 95% CI      hurdle
  gates 2+3 (playbook)     13,167     331   +2.97%   1.19   [-0.73, +8.78]    3.29
  gates 2+3, IVpct <= 15    8,884     290   +3.71%   1.53   [-0.54, +8.82]    3.29
  gate 2 only              23,227     369   +1.67%   1.02   [-0.94, +5.49]    3.29
```

None of these clear the multiple-testing hurdle, and every interval includes zero. This is
**not** evidence the edge is absent — the point estimates are positive, consistently ordered,
and the mechanism is independently corroborated above. It is evidence that the sample cannot
distinguish +4% from 0% with the confidence the "research complete" label implies. Trade it
as a promising position, not a settled one.

## ⚠ Caveat 2 — the return is almost entirely tail, and gating does not fix that

```
  share of total return from the top 0.1% of trades
    no gates              100.0%
    gate 2 only            98.8%
    gates 2+3 (playbook)   98.9%   <- gating does NOT reduce tail dependence
  playbook cell: median ROC -14.3%, win rate 42.9%, ex-top-1% mean +1.00%
```

The gates raise the average and leave the **shape** untouched. Roughly 13 trades out of
13,167 carry the result. The practical consequences:

- **Size for the distribution, not the mean.** An expectancy that needs one trade in a
  thousand is not carry and must not be sized like carry.
- **Breadth is not optional.** Taking a handful of gated entries per month gives a high
  chance of never touching the tail that produces the return.
- **Never cut the tail.** Any profit-take or stop that truncates the top of the distribution
  removes the edge itself. This is consistent with the 2026-09-10 revision, which already
  rejected re-centering and found the −50% stop to be a modelling artefact.

## Proposal (NOT applied — needs Gabe's yes)

**Tighten gate 3 from IV percentile ≤ 30 to ≤ 15.** It improves every metric monotonically
(premium faced +0.79 → +0.48, winsorized mean +3.74% → +5.29%, ex-top-1% +1.00% → +2.60%,
win rate 42.9% → 43.4%) at the cost of about a third of the entries. Given caveat 2, fewer
entries is a real cost, so this is a judgement call between per-trade quality and the breadth
needed to catch the tail. Not applied.

## Note on gate 2's data source

Gate 2 reads `fvr_put_30_90` from `silver.fwd_vol_daily`, which is **stale since 2026-02-20**
and cannot be rebuilt from `options_daily_v3` (no stored IV after mid-May 2026). The live
screen already works around this by sourcing the trailing distribution from IBKR. Since gate
2 is now shown to be the workhorse of the entry logic, that workaround is load-bearing and
should not be allowed to silently degrade.

## Live check of the exit rules (2026-09-18)

The journal summary now carries a **"Held to expiry"** column (original legs settled at intrinsic on their expiry). Across the 25 closed Aug–Sep 2026 straddles whose expiries had passed: **held to expiry −$3,359 vs +$1,040 realized** — the early exits were worth ~+$4.4k in this sample, almost all of it three spike sales that reverted by expiry (RDDT 8/12 +$1,622 realized vs −$983 held; PLTR 8/26 +$228 vs −$1,016; RDDT 8/21 +$59 vs −$898). This does NOT overturn hold-to-expiry (the backtest's edge is the rare monster the hold captures; n here is 25 in one mean-reverting month) — it is the **spike rule** doing its job. The journal's exit grading now encodes all three rules (`run_build_reviews.py: straddle_exit_verdict`): held to expiry → good; **spike = structure ≥ +100% within 5 sessions → good** (≈3x on the winning leg, the other leg being near dead); −50% stop → good; anything else closed early → too_soon (early profit take / early loss exit). 22 of 32 closed-straddle exit verdicts changed on re-grading; RDDT 8/12 went too_soon → good. Borderline: PLTR 8/31 (+93% in 3 days) grades too_soon under the 100% line and was right in hindsight (+$1,050 vs +$647 held) — the threshold is a parameter, not a finding.
