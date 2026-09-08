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
