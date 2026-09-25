# Archived scripts

Moved here on 2026-09-24 (housekeeping) from the repo root. **Nothing here is run by any orchestrator, scheduled job,
or other script** — each was checked for imports and shell/CI references before moving. They are kept so a
result can be reproduced; the conclusions live in `data/studies/TEST_INDEX.md`, not in these files.

What was moved: study/backtest scripts last committed before 2026-08, the `scratch_*` probes, one-off data
migrations, and scripts that look operational but are retired or superseded (see OPERATIONS.md).

**To re-run one:** from the repo root, `PYTHONPATH=src:. .venv/bin/python3 scripts/archive/<file>`.
⚠ 15 of them locate files relative to their own path (`__file__`) and will look in the wrong place from
here — `git mv` the script back to the root to re-run it: `option_chart_app.py`, `run_bulk_filter.py`, `run_combined.py`, `run_grid_study.py`, `run_iv_condor_study.py`, `run_standard_put_spread_bulk.py`, `run_straddle_study_full.py`, `run_strangle_study_full.py`, `run_tlt_naked_calls.py`, `run_tlt_ratio_calls.py`, `run_tlt_strangle_study.py`, `run_tlt_structure_sweep.py`, `run_vrp_analysis.py`, `scratch_fade_trigger.py`, `upsert_put_spread_from_csv.py`.

Deliberately NOT archived (still useful, or imported by another script): `run_build_fwd_vol.py`,
`run_build_option_legs.py`, `run_backfill_options_v3.py`, `run_reversal_monitor.py`, `run_sleeping_giants.py`,
`run_breakout_scorecard.py`, and six that other scripts import (`run_fvr_straddle_regression.py`,
`run_long_straddle_study.py`, `run_refresh_preferred.py` [called by `deploy_breakout_lambda.sh`],
`run_sleeping_giants_backtest_stage3.py`, `run_straddle_ticker_walkforward.py`, `run_uvxy_combined_sweep.py`).

| file | last commit | what it is |
|---|---|---|
| `dedup_v3.py` | 2026-02-22 | Deduplicate options_daily_v3 for Sep 2025 onwards. |
| `migrate_to_v3.py` | 2026-02-22 | One-off migration script: options_daily_v2 → options_daily_v3 |
| `option_chart_app.py` | 2026-09-02 | GOOG option vs. underlying intraday chart. |
| `premarket_check.py` | 2026-06-17 | Pre-market scan of the breakout roster: gap, position vs trigger, pre-market volume. |
| `premarket_defense.py` | 2026-06-17 | Pre-market DEFENSE check: for each held position, show the gap and distance to its |
| `run_adhikary_breakout_backtest.py` | 2026-06-21 | Backtest Archetype A (Technical VCP Breakout) against Tito's 15 Breakout trades. |
| `run_adhikary_fade_universe_validation.py` | 2026-06-21 | Fade strategy universe validation: Archetype C (Exhaustion) detector. |
| `run_adhikary_universe_validation.py` | 2026-06-21 | Universe validation: Run Archetype A detector on S&P 500 + Nasdaq 100. |
| `run_allocation.py` | 2026-03-09 | Capital allocation calculator for confirmed option strategies. |
| `run_batch.py` | 2026-03-03 | Batch put sweep + put spread sweep for multiple tickers. |
| `run_bulk_filter.py` | 2026-03-09 | Filter the February bulk put spread study to identify candidates for deep analysis. |
| `run_calendar.py` | 2026-03-09 | Put calendar spread backtest — short ATM put (~20 DTE) + long put (~27 DTE) at same strike. |
| `run_call_spreads.py` | 2026-03-09 | Generic bear call spread backtest — short delta × wing width × VIX regime sweep. |
| `run_combined.py` | 2026-03-03 | Generic combined strategy analysis: bear call spread + short put. |
| `run_compound_sim.py` | 2026-05-28 | Compounding simulation for any ticker. |
| `run_correlation.py` | 2026-03-03 | Three-strategy simultaneous failure analysis. |
| `run_csp_screen.py` | 2026-07-27 | CSP candidate screen over the low-ADR 'just right' cohort. |
| `run_delta_hedged_straddle.py` | 2026-03-03 | Delta-hedged ATM straddle study — CLI runner. |
| `run_eod_scan.sh` | 2026-06-21 | cron entrypoint for run_preferred_breakouts.py; the crontab was never installed (superseded by the preferred-breakout-eo |
| `run_grid_model.py` | 2026-05-28 | Grid Structure Lookup Table Builder |
| `run_grid_screener.py` | 2026-05-28 | Live Grid Screener — Lookup Table |
| `run_grid_study.py` | 2026-05-28 | Grid Structure Study |
| `run_iron_butterfly_filtered.py` | 2026-03-22 | Iron Butterfly — filtered universe analysis. |
| `run_iron_butterfly_study.py` | 2026-03-22 | Iron Butterfly Study — delta sweep + FVR regression |
| `run_iv_condor_study.py` | 2026-05-28 | IV Percentile (IVP) Short Strangle Study |
| `run_iv_crush_screener.py` | 2026-05-28 | IV-Crush Far-OTM Strangle Screener |
| `run_long_straddle_model.py` | 2026-03-22 | Long Straddle — multi-feature walk-forward model. |
| `run_luk_analyzer.py` | 2026-03-09 | Analyze Martin Luk's livestream stock picks to reverse-engineer his methods. |
| `run_minervini_scan.py` | 2026-07-27 | Minervini Trend Template scan over the full US common-stock universe — local CLI. |
| `run_optimizer.py` | 2026-03-03 | Generic Optuna Bayesian optimizer for the combined strategy (bear call spread + |
| `run_portfolio_backtest.py` | 2026-03-09 | Portfolio backtest — simulate all confirmed strategies for a given year. |
| `run_portfolio_estimate.py` | 2026-03-21 | Portfolio annual P&L estimate based on playbook data. |
| `run_profit_sweep.py` | 2026-03-21 | Profit-Target Optimization Sweep for put_spread / call_spread strategies. |
| `run_put_spreads.py` | 2026-03-09 | Generic bull put spread backtest — short delta × wing width × VIX regime sweep. |
| `run_puts.py` | 2026-03-03 | Generic short put backtest — delta sweep with VIX regime filter. |
| `run_short_dte_put_spreads.py` | 2026-03-18 | Short-DTE bull put spread backtest — 0-5 DTE, Thursday entry, trend-filtered sweep. |
| `run_sleeping_giants_backtest.py` | 2026-06-21 | Sleeping Giants backtest — STAGE 1: historical episode sweep. |
| `run_sleeping_giants_backtest_stage2.py` | 2026-06-21 | Sleeping Giants backtest — STAGE 2: entry resolution. |
| `run_sleeping_giants_backtest_stage4.py` | 2026-06-21 | Sleeping Giants backtest — STAGE 4: exit-rule study. |
| `run_spy_double_calendar.py` | 2026-03-21 | SPY Double Calendar Spread Backtest |
| `run_standard_put_spread_bulk.py` | 2026-03-09 | Re-run the top ~1,000 tickers from the February bulk put spread study using |
| `run_stock_dcal_screener.py` | 2026-09-15 | Stock double-calendar / double-diagonal screener (playbook: data/studies/double_calendar_playbook.md, rule 3). |
| `run_straddle_exit_analysis.py` | 2026-03-22 | Long Straddle — Early Exit Rule Analysis |
| `run_straddle_study_full.py` | 2026-02-24 | Full re-run of the 50-50 straddle study with delta/DTE guardrails. |
| `run_strangle_study_full.py` | 2026-02-24 | Full re-run of the 25-25 strangle study with delta/DTE guardrails. |
| `run_thursday_screener.py` | 2026-09-18 | Thursday short-DTE bull put spread screener. |
| `run_tlt_naked_calls.py` | 2026-03-18 | TLT Naked Short Call backtest. |
| `run_tlt_profit_sweep.py` | 2026-03-19 | TLT Profit-Target Optimization Sweep (Walk-Forward) |
| `run_tlt_ratio_calls.py` | 2026-03-18 | TLT 2:1 Call Ratio Spread backtest. |
| `run_tlt_strangle_study.py` | 2026-03-19 | TLT Short Strangle Study — Bearish_LowIV regime |
| `run_tlt_structure_sweep.py` | 2026-03-19 | TLT Per-Regime Structure Sweep |
| `run_uvxy_calls.py` | 2026-03-03 | UVXY short call backtest — delta sweep with VIX regime filter. |
| `run_uvxy_stop_loss_test.py` | 2026-03-03 | Stop-loss sensitivity test for the UVXY bear call spread. |
| `run_uvxy_straddle.py` | 2026-03-03 | UVXY 20-DTE ATM short straddle backtest. |
| `run_vrp_analysis.py` | 2026-03-19 | VRP (Volatility Risk Premium) predictiveness analysis. |
| `scratch_adhikary.py` | 2026-05-28 | Adhikary_Options.csv analysis: per row, sweep all strikes that traded on the |
| `scratch_adhikary_dte.py` | 2026-05-28 | DTE-ladder study for the Adhikary CALL setups, mirroring the NVDA multi- |
| `scratch_adhikary_exits.py` | 2026-06-17 | True P&L for the 6 EARLY-EXIT trades: pull the inferred contract's price on Tito's actual |
| `scratch_adhikary_holdpath.py` | 2026-06-17 | 'When to hang tight' — path analysis of the HELD-to-expiry winners. |
| `scratch_adhikary_qa.py` | 2026-06-17 | QA pass on Adhikary_Options.csv: verify each trade was directionally profitable. |
| `scratch_adhikary_reconcile.py` | 2026-06-17 | Reconcile Tito's own Setup_Type / Days_In_Trade labels against my A/B/C/D calls. |
| `scratch_adhikary_returns.py` | 2026-06-17 | Tito's actual Return column is now ground truth. Compare to my two estimators: |
| `scratch_adhikary_strikes.py` | 2026-06-17 | Infer the STRIKE Tito bought from his recorded Entry_Price (option premium), using the |
| `scratch_adhikary_trailtest.py` | 2026-06-17 | Pressure-test the 20-EMA-close trail against Tito's actual intraday-strength exits, on the |
| `scratch_crash_leader_bias.py` | 2026-09-02 | Is the crash-leader "edge" real, or is it survivorship? |
| `scratch_crash_leader_regime.py` | 2026-09-02 | Is the crash-leader edge a real effect or one regime episode? |
| `scratch_entry_dates.py` | 2026-06-21 | Reconstruct the CURRENT open lot's entry date(s) per name from stocks.trades. |
| `scratch_fade_detector.py` | 2026-06-21 | Archetype C (climactic-exhaustion fade) — daily-bar detector / gate calibration. |
| `scratch_fade_trigger.py` | 2026-06-21 | Archetype C — intraday entry-trigger + invalidation analysis (1-min bars). |
| `scratch_local_pivot.py` | 2026-06-17 | Recipe #5 fix — anchor the breakout pivot on the LOCAL base, not the multi-month high. |
| `scratch_nvda_calls.py` | 2026-05-28 | (no docstring) |
| `scratch_sg_data_probe.py` | 2026-06-21 | Probe Athena options coverage for the sleeping-giants LEAP backtest. |
| `upsert_put_spread_from_csv.py` | 2026-02-22 | One-off: upsert put spread study from saved CSVs into MySQL. |
