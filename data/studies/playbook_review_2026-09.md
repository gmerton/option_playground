# Option playbook review — September 2026

*2026-09-08. A fresh skeptical pass over the 30 option playbooks in `data/studies/` (mostly written March 2026), the allocation framework, and the Friday screener, using what this month's work established about fills, stale tables, and regime dependence. Purpose: decide which playbooks can carry surplus buying power today, which need rework, and which should be retired.*

## Headline findings

1. **No backtest engine models costs.** Every credit spread, condor, straddle and calendar is priced at the mid on entry and at mid or intrinsic on exit, with zero commission and zero slippage (`run_tlt_strategy_study.py`, `run_spx_strangle.py`, `run_put_spreads.py`, `run_calendar.py`). The one study that did model costs (`data/theta_profits/backtests/dc_time_machine/RESULTS.md`, $0.052/share commission plus 25% of each leg's quoted bid-ask, paid both ways) turned every tight-gap double-calendar configuration net-negative. The playbooks' 25% bid-ask entry filter is a gate, not a cost model; it does not haircut the reported ROC.
2. **The Tier A calendars are untradeable at today's quotes.** XLU, XLV and XLP put calendars (priority 347 / 286 / 239, the top of the framework) all failed the 25% short-leg bid-ask gate in this afternoon's screener run: 41%, 135% and 42%. Their backtested debits are $7 to $39 per contract with a 25% profit target, which is inside the quoted spread. The framework's ranking formula (ROC × win × 52/weeks) rewards exactly this profile: tiny debits, enormous ROC percentages, "annualized ROC +6,249%". Until these are re-run with the dc_time_machine cost model, treat their tier as unproven. The March live trades (XLU +17%, GLD calendar +22%) were closed early on discretion, so they do not test the rule either.
3. **The regime edges are concentrated in one or two years.** SPX bullish-high-IV condor: 24 of 47 trades in 2020, and the single 2022 trade lost 74.5%. XLE bearish-high-IV: 26 of 79 trades in 2020. SPY bearish-low-IV straddle: about 5 weeks a year, roughly 40 trades total. QQQ bearish-low-IV: 5 weeks a year. The 8-year window holds one crash, one bear, and five up years; the priority score has no penalty for a signal whose history is one episode.
4. **Per-regime parameter selection is in-sample for most tickers.** SPY, QQQ, XLF, XLE and TLT each carry a different delta pair and stop rule per regime, chosen from an "original vs optimized" table on the full sample. ASHR's 550% annualized-ROC profit target came from a 40-value sweep. Only TLT and ASHR report a walk-forward split (2018–22 in, 2023–26 out), and both hold up there. The others should be read as fitted until they get the same treatment.
5. **Annualized-ROC metrics are misleading on 5- to 11-day holds** and drive the priority order. TLT's "+616% OOS annualized" is +5.6% per trade on 410 trades; XLU's "+6,249%" is $12 a contract. Per-trade ROC on a max-loss basis and dollar P&L per contract should be the only figures in the tables.
6. **The screener's Sharpe-weighted sizing runs on invented inputs.** `strategy_registry.py` builds per-year ROC "estimated from annual win rates — actual values not tracked per year", then computes Sharpe from that. Today it printed QQQ at 4.49 and sized it to 28 contracts against 2 under the fixed model. Ignore the Sharpe column until the registry stores real per-year results.
7. **Backtests cannot be extended past July 2026.** `options_daily_v3` carries only trade prints after mid-July, so no playbook can be re-run on the last two months, and `fwd_vol_daily` (the straddle FVR source) stopped on 2026-02-20. Live gates are fine because they read Tradier chains; the history is frozen.
8. **Live results so far do not match the tables, but mostly because the live book is not the playbooks.** Playbook trade logs contain four 2026 rows in total. August's systematic structures were 33 long straddles (27 closed, 30% win, +$1,025), 29 bull put spreads and 4 condors (24 closed, 58% win, +$1,124), and the spread names were AAOI, PLTR, CBRS, SPCX, UNH, XLE — discretionary underlyings, not the roster. The +$4.3k systematic result is evidence that defined-risk structures are the better vehicle for this book, not evidence for any specific playbook.

## Playbook by playbook

| Playbook | Tier | Evidence | Concern | Verdict |
|---|---|---|---|---|
| XLU / XLV / XLP put calendars (FVF ≤ 0.90) | A | 62–93 trades, 82–94% win | mid fills on $7–39 debits, 25% target inside the spread, failed BA gate live today; correlated on FOMC weeks | **Suspend until re-run with costs.** Candidate for a cost-aware rebuild, since the FVF signal itself is sound |
| XLE bull put, bearish-high-IV only | A | 79 trades, 85% win; 2026 live +54% | 26 trades in 2020; 9 weeks/yr; gate is not live today (bullish-low-IV) | Keep; size as an episodic strategy, not a core |
| SPY long straddle, bearish-low-IV | A | ~40 trades, 58% win, +22.6% | tiny n; the IV-percentile gate from the long-straddle work is not applied here | Keep small; add gate 3 |
| QQQ bull puts by regime | A/B/C | 8-yr full sample, 80–92% win | per-regime deltas fitted in-sample; correlated with SPY/SPX/SOXX | Keep the bullish-low-IV variant (27 wks/yr, most data); walk-forward the rest |
| SPY double calendar 0.35Δ | B | after-cost backtest exists (+9.7% BuLO) | gains concentrated 2021/24/25; BHI leg small-sample | Keep; the only playbook with a cost model. Live today: ENTER |
| SPX iron condor by regime | A/B | 71 + 47 trades | BuHI is a 2020 story; 2022 single trade −74% | Keep BHI at Tier B; demote BuHI to provisional |
| SOXX bull put, always on | C | 8 yrs, 89% win, survived 2022 | 0.35/0.30 deltas = $5 wide, thin credit after costs; failed BA today | Keep; verify credit ≥ 2× commissions at entry |
| TLT regime switch | C | walk-forward OOS holds; 410 trades | 2024 −2.8%; tiny per-share P&L; annualized-ROC framing | Keep; report per-trade ROC only |
| ASHR condor | C | walk-forward holds both legs | 550% target from a 40-value sweep; 2025 put leg −2% | Keep; freeze the target |
| GLD bull put (VIX<25) | C | 87% win; live +22% | no walk-forward; today: ENTER | Keep |
| XLF regime, USO, INDA, BJ, SQQQ, UVXY, UUP | B/C | 8-yr full sample | XLF 2022 −13%; INDA/UUP chains sparse 2023+; BJ monthly-only; UVXY no stop by design | Keep as Tier C fillers; INDA/UUP/BJ need a liquidity re-check before any capital |
| TMF, CLS, GEV, YINN, XOP | P | ≤2 years | one regime of data | Provisional stays provisional; YINN already removed |
| Long straddle (pool 323, FVR + IV pct) | B | 5-yr walk-forward, 44% win, +13% | FVR table stale → live IV gate rebuilt from prints; Friday entry not observed in August (Tuesday entries) | Keep; the gate rebuild is done, the discipline is not |

## What to change before deploying surplus buying power through these

1. **Add the dc_time_machine cost model to `run_put_spreads.py`, `run_calendar.py` and `run_tlt_strategy_study.py`** and re-run the Tier A and B rows. Anything whose per-trade ROC drops below about 3% after costs leaves the funded list. This is the single highest-value task and it is mechanical.
2. **Replace annualized ROC with per-trade ROC and dollars per contract** in every table, and re-score the framework on those. Expect the calendars to fall and the index spreads to rise.
3. **Add a concentration penalty to the priority score:** share of trades in the single best year. A strategy with more than 40% of its trades in one year gets half weight.
4. **Walk-forward the per-regime parameters for SPY, QQQ, XLF, XLE** the way TLT and ASHR were done, and adopt the OOS-best, not the full-sample-best.
5. **Fix the registry:** store actual per-year ROC from each study's output; until then, sizing uses the fixed model only.
6. **Run the screener as written on Fridays** and log every entry in the playbook trade log. Four logged trades in six months is not a live track record.

## What can carry capital now, on the current evidence

Today's screener produced four entries at VIX 15.7: QQQ bullish-low-IV bull put 0.45/0.35, SPY double calendar, GLD bull put, and a UVIX bear call. Of those, the SPY double calendar is the only one with a cost-modeled backtest, QQQ bullish-low-IV is the most-sampled regime row, and GLD is a plain 87%-win spread on a liquid chain. The UVIX call spread carries a high-contango warning and Tier C weight. That is a reasonable place to start at framework size, with the 25% open-risk cap, while the cost-model re-run decides what else gets funded.

---

# Part 2 — After-cost re-run (2026-09-08, same day)

Cost model added to every engine (`src/lib/studies/costs.py`, copied from the dc_time_machine study): $0.0065/share per leg per side commission plus 25% of each leg's quoted entry bid-ask, paid on entry and again on any exit that trades. A leg that settles at expiry pays no exit cost. Entry bid-ask is the exit proxy (exit quotes are not stored). `--no-costs` reproduces the old mid-fill tables. Engines patched: `put_spread_study.py`, `calendar_study.py` (ROCnet/WinNet columns in every table), `run_tlt_strategy_study.py`, `run_tlt_regime_switch.py`, `run_spx_strangle.py`.

## Results, gross (playbook) vs net (after costs)

| Playbook | Framework tier | Gross ROC / win (playbook) | Net ROC / win | Cost per share | Verdict |
|---|---|---|---|---|---|
| XLU put calendar, FVF ≤ 0.90 | A (#1) | +78.8% / 93.5% | **−54.0% / 10.8%** | $0.136 on a $0.130 debit | dead |
| XLV put calendar, FVF ≤ 0.90 | A (#2) | +49.0% / 87.1% | **−94.8% / 8.1%** | $0.235 on a $0.208 debit | dead |
| XLP put calendar, FVF ≤ 0.90 | A (#3) | +54.7% / 82.1% | **−129.1% / 7.7%** | $0.135 on a $0.112 debit | dead |
| XLE bull put, bearish-high-IV | A (#4) | +35.5% / 84.6% | not reproducible (see data note) | | blocked |
| SPX condor 0.20c/0.40p, bullish-high-IV + 200MA | A (#7-equiv) | +11.2% / 95.7% | **+10.9% / 95.7%** | ~$0.30 on $74 credit | survives |
| SPX condor 0.20c/0.30p, bearish-high-IV | B | +10.4% / 78.9% | **+9.8% / 78.9%** | | survives |
| QQQ bull put, bearish-high-IV | B | +25.3% / 79.7% (this engine) | **+22.5% / 79.7%** | ~$0.05 | survives |
| QQQ bull put, bullish-high-IV | A | +11.6% / 76.5% | **+9.4% / 76.5%** | | survives |
| QQQ bull put, bullish-low-IV | C | +13.5% / 76.9% | **+10.6% / 76.5%** | | survives |
| SPY bull put, bearish-high-IV | B | +7.5% / 94.7% (playbook) | **+20.2% / 77.3%** (this engine's fixed deltas) | | survives |
| SPY bull put, bullish-low-IV | C | | **+4.1% / 76.9%** | | marginal |
| SOXX bull put 0.35/0.30, always on | C | +9 to +32% per year | **−31% (2018), +9, +3, −19, −6, −1, +7, +7, +27 (2026 partial)** | ~$0.12 on $1.50 credit | marginal, 4 of 8 full years negative |
| GLD bull put 0.30/0.25, VIX<25 | C | +2 to +17% per year | **−17, +7, 0, −12, +3, −4, +11, +9** | ~$0.05 | marginal, positive only 2024–26 |
| TLT regime switch | C | +5.6% / 87.6% overall | **−10.0% total; every regime negative (−3.7% to −16.7%), win 35–50%** | ~$0.075 on $0.24–0.49 credits | dead |
| XLF regime switch | B | +6.1% / 74.8% | **−4.6% total; bull put −8.8%, bear call −8.1%, strangles ≈ +1%** | ~$0.04 on $0.16–0.21 credits | dead |

Read the QQQ/SPY rows as the engine's fixed-delta strategy study rather than the playbook's regime-optimized deltas; the point is the *gap* between gross and net on the same trades, which is 2 to 3 points of ROC on QQQ and SPY, 10 to 17 points on TLT, XLF and SOXX, and more than 100 points on the calendars.

## What this means

- **The framework's top three strategies are artifacts of mid pricing.** On a $0.11 to $0.21 debit, the round-trip cost is $0.13 to $0.24. The FVF signal is real (win rate rises monotonically as the factor falls) but it cannot be monetized in these products at these sizes. Tier A rows 1 to 3 are removed.
- **TLT and XLF regime switching are dead after costs.** Credits of $0.16 to $0.49 a share against $0.04 to $0.08 of cost, exited early on an annualized-ROC target, leaves nothing. The 87.6% win rate becomes 35 to 50 percent.
- **SPX is the one Tier A that is unaffected.** Large-dollar options with tight spreads relative to premium. The remaining concerns from Part 1 stand (2020 concentration in the bullish-high-IV row, one −74% trade in 2022).
- **QQQ and SPY bull puts survive with a 2 to 3 point haircut**, which makes them the workhorses. SPY bullish-low-IV at +4.1% net is thin; QQQ bullish-low-IV at +10.6% net on 221 trades is the best-sampled positive row in the whole book.
- **SOXX and GLD are marginal**, positive in the AI-bull years and negative in most others. Keep only if credits at entry exceed roughly 3 times the modeled cost.
- **XLE cannot be evaluated**: `data/cache/XLE_stock.parquet` is split-adjusted (XLE 45.38 on 2024-06-03) while `options_cache` strikes are not, so every settlement in the engine is wrong (bull puts 2% win, straddles −974%). The March playbook numbers presumably came from an unadjusted cache; rebuild the stock cache on the strike basis before re-running.

## Framework changes applied

Tier A after costs: **SPX bullish-high-IV condor, QQQ bearish-high-IV bull put.** Tier B: SPX bearish-high-IV condor, QQQ bullish-high-IV and bullish-low-IV bull puts, SPY bearish-high-IV bull put, SPY double calendar (already cost-modeled). Tier C: SOXX, GLD, SPY bullish-low-IV. Removed: XLU/XLV/XLP calendars, TLT regime switch, XLF regime switch. Blocked pending data fix: XLE. The Friday screener still prints the old tiers; `strategy_registry.py` needs the same edit before its ENTER labels can be trusted.
