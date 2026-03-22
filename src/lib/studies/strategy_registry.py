"""
Confirmed strategy registry — single source of truth for Sharpe scores and metadata.

Both run_allocation.py and run_friday_screener.py import from here so that updating
per-year data in one place propagates everywhere.

To update after a new backtest cycle:
  1. Add or update the per_year_roc list for the relevant strategy.
  2. Sharpe scores recompute automatically at import time.

portfolio_alloc: fixed dollar allocation from the $100K portfolio model
  (run_portfolio_estimate.py). Per-trade risk = portfolio_alloc / avg_concurrent.
  This is the primary sizing recommendation shown in the screener.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class Strategy:
    name: str
    per_year_roc: list[float]   # per-year average ROC% (one value per calendar year)
    avg_trade_roc: float        # overall per-trade mean ROC (from playbook)
    win_rate: float             # overall win rate %
    avg_concurrent: int         # typical overlapping open positions
    freq_per_year: int          # qualifying entries/year after liquidity filter
    note: str
    portfolio_alloc: int = 0    # fixed $ allocation from $100K portfolio model
    caveats: list[str] = field(default_factory=list)

    @property
    def mean_annual(self) -> float:
        return statistics.mean(self.per_year_roc)

    @property
    def std_annual(self) -> float:
        if len(self.per_year_roc) < 2:
            return float("inf")
        return statistics.stdev(self.per_year_roc)

    @property
    def sharpe_annual(self) -> float:
        """Year-level Sharpe: mean(per-year ROC) / std(per-year ROC)."""
        s = self.std_annual
        if s == 0 or s == float("inf"):
            return 0.0
        return self.mean_annual / s

    @property
    def years(self) -> int:
        return len(self.per_year_roc)

    @property
    def losing_years(self) -> int:
        return sum(1 for r in self.per_year_roc if r < 0)

    @property
    def risk_per_trade(self) -> int:
        """Per-trade risk budget = portfolio_alloc / avg_concurrent."""
        if self.avg_concurrent > 0 and self.portfolio_alloc > 0:
            return self.portfolio_alloc // self.avg_concurrent
        return 0


ALL_STRATEGIES: list[Strategy] = [

    Strategy(
        name="UVXY combined",
        per_year_roc=[0.31, 6.19, 9.22, 8.22, 7.74, 3.48, 3.17, 10.08],
        avg_trade_roc=5.60,
        win_rate=74.6,
        avg_concurrent=4,   # 2 positions × 2 legs (call spread + put) each
        freq_per_year=40,
        note="Bear call spread always + short put when VIX<20. Equal-capital blend.",
        portfolio_alloc=10_000,
        caveats=["Put leg is naked short — undefined max loss; size conservatively"],
    ),

    Strategy(
        name="TLT calls",
        per_year_roc=[14.63, 30.99, 15.45, 17.69, 2.90, -7.94, 36.29, 18.97],
        avg_trade_roc=11.57,
        win_rate=81.4,
        avg_concurrent=2,
        freq_per_year=17,
        note="Regime-switch (4 regimes). $12.07 cum 2018–2026. Reg T ROC. 100% ann-target.",
        portfolio_alloc=5_000,
        caveats=["2019: only 1 trade (30.99%) — outlier that inflates mean", "Idle 60% of time"],
    ),

    Strategy(
        name="GLD puts",
        per_year_roc=[-5.71, 17.52, 7.84, -4.65, 10.41, 2.26, 16.88, 17.44],
        avg_trade_roc=7.98,
        win_rate=87.1,
        avg_concurrent=2,
        freq_per_year=40,
        note="Bull put spread 0.30Δ/0.05Δ. VIX<25 only.",
        portfolio_alloc=3_000,
        caveats=["2018 and 2021 losing years; GLD trended against short puts both years"],
    ),

    Strategy(
        name="GLD calendar",
        per_year_roc=[14.9, 3.4, 20.3, 15.9, -8.7, 38.3, 20.5, -1.8],
        avg_trade_roc=13.3,
        win_rate=75.4,
        avg_concurrent=2,
        freq_per_year=34,
        note="Put calendar 0.50Δ ATM. iv_ratio≥1.00 (backwardation) required. Net debit.",
        portfolio_alloc=3_000,
        caveats=["Debit strategy — ROC relative to net debit paid, not credit received"],
    ),

    Strategy(
        name="XLU calendar",
        per_year_roc=[27.7, 22.7, 15.4, 12.2, 51.9, 2.6, 79.4, 61.7],
        avg_trade_roc=78.8,
        win_rate=93.5,
        avg_concurrent=1,
        freq_per_year=12,
        note="Put calendar 0.50Δ ATM. fwd_vol_factor≤0.90. ~11 entries/year. Net debit.",
        portfolio_alloc=3_000,
        caveats=[
            "Per-year data from no-filter sweep (fwd≤0.90 per-year not available)",
            "Per-trade ROC (+78.8%) reflects highly selective entry — not every week",
        ],
    ),

    Strategy(
        name="USO puts",
        per_year_roc=[7.60, 8.75, 8.79, 8.39, 8.22, 15.71],
        avg_trade_roc=9.58,
        win_rate=92.3,
        avg_concurrent=2,
        freq_per_year=47,
        note="Bull put spread 0.25Δ/0.05Δ. 30 DTE. All VIX. Post-restructuring (Jul 2020+).",
        portfolio_alloc=3_000,
        caveats=["6 years of data (2020–2025); no losing year yet but history is shorter"],
    ),

    Strategy(
        name="XLF regime",
        per_year_roc=[20.7, -15.1, 22.9, 14.3, 9.3, 32.7, -12.5, 44.3],
        avg_trade_roc=6.1,
        win_rate=74.8,
        avg_concurrent=2,
        freq_per_year=42,
        note="Regime-switch (4 regimes). $23.79 cum 2018-2026. Reg T ROC. Strangles: 2–3%.",
        portfolio_alloc=4_000,
        caveats=[
            "per_year_roc uses credit as denominator for strangle years (inflated 10-13×); spread years are accurate",
            "Correct Reg T avg_trade_roc = +6.1% (strangles: $6-7/share margin vs $0.43-0.99 credit)",
            "2019: -15.1% — slow Bearish_LowIV grind, thin strangle premium",
            "2024: -12.5% — Bullish_HighIV strangle had a bad run (6 trades)",
            "Strangles are naked — size at 2-3% max; spread legs use 5%",
        ],
    ),

    Strategy(
        name="XLE puts",
        per_year_roc=[42.0, 50.0, 32.0, 34.0, 14.0, 14.0, 18.0, 26.0],
        avg_trade_roc=35.5,
        win_rate=84.6,
        avg_concurrent=1,
        freq_per_year=10,
        note="Bull put spread 0.35Δ/0.25Δ. Bearish_HighIV only (~9 wks/yr). $15.94 cum 2018-2025.",
        portfolio_alloc=3_000,
        caveats=[
            "Per-year ROC estimated from annual win rates — actual values not tracked per year",
            "Only active ~9 weeks/year; capital mostly idle",
            "2020: 26 qualifying weeks — concentration risk in prolonged energy bear market",
        ],
    ),

    Strategy(
        name="UUP straddle",
        per_year_roc=[18.2, 15.5, 21.0, 14.8, 16.3, 19.7, 12.1, 10.5],
        avg_trade_roc=2.3,
        win_rate=73.1,
        avg_concurrent=1,
        freq_per_year=13,
        note="ATM short straddle ~0.50Δ. No regime gate. ~13 entries/yr. $14.26 cum 2018-2026. Reg T ROC.",
        portfolio_alloc=2_000,
        caveats=[
            "per_year_roc uses credit as denominator (inflated); correct Reg T margin = 0.20×$28 + $0.44 = $6.04/share",
            "Correct Reg T avg_trade_roc = +2.3% (prior +17.4% used ~$0.44 credit as denominator)",
            "2024-2025: data sparse; verify chain liquidity in broker before each entry",
            "Naked straddle — size at 2-3% max",
        ],
    ),

    Strategy(
        name="ASHR puts",
        per_year_roc=[-1.43, 6.95, 20.44, 6.76, 1.92, 7.19, 21.27, -2.02],
        avg_trade_roc=6.6,
        win_rate=87.7,
        avg_concurrent=2,
        freq_per_year=24,
        note="Bull put spread 0.25Δ/0.15Δ (0.10Δ wing). All VIX. 550% ann-ROC profit target. Iron condor put leg.",
        portfolio_alloc=3_000,
        caveats=[
            "per_year_roc from original 0.05Δ wing / 50% fixed take study — shapes are representative",
            "Current params (0.10Δ wing + 550% target): IS 87.4% win +3.8% ROC; OOS 88.2% win +11.8% ROC",
            "Run alongside ASHR calls (condor) — correlation is negative",
        ],
    ),

    Strategy(
        name="ASHR calls",
        per_year_roc=[10.48, 11.15, -3.99, 7.51, 0.92, 15.63, 16.55, 6.56],
        avg_trade_roc=8.8,
        win_rate=90.2,
        avg_concurrent=2,
        freq_per_year=29,
        note="Bear call spread 0.20Δ/0.10Δ. All VIX. 50% fixed profit take. Iron condor call leg.",
        portfolio_alloc=3_000,
        caveats=[
            "Ann-target optimization rejected — exits at 7.7d with +1.5% OOS ROC vs 14d/+10.5% baseline",
            "Run alongside ASHR puts (condor) — correlation is negative",
        ],
    ),

    Strategy(
        name="TMF calls",
        per_year_roc=[25.00, 22.18, -1.95, -13.38, 1.86, 10.93, 21.34],
        avg_trade_roc=15.07,
        win_rate=87.3,
        avg_concurrent=2,
        freq_per_year=47,
        note="Bear call spread 0.35Δ/0.05Δ. All VIX. 50% take. 0.05Δ wing exception: 0.10Δ costs -5.4pp ROC.",
        portfolio_alloc=2_000,
        caveats=[
            "WATCH LIST — only 2 usable years post-split (2024–2025); pre-2024 has 1–7 trades/year",
            "2022 (worst rate year in 40yr) had only 3 trades — strategy is undertested in stress",
            "Ann-target rejected: all targets fire at 6.3d vs 11.5d baseline; OOS PnL drops $748→$508",
            "Correlated with TLT — do not run both at full size simultaneously",
        ],
    ),

    Strategy(
        name="INDA puts",
        per_year_roc=[-6.33, 10.57, 32.92, -4.30, 12.12, 12.89, 18.18],
        avg_trade_roc=12.79,
        win_rate=91.7,
        avg_concurrent=1,
        freq_per_year=7,
        note="Bull put spread 0.25Δ/0.05Δ. All VIX. Very thin option chain.",
        portfolio_alloc=2_000,
        caveats=[
            "Only 60 trades over 8 years; 2023–2025 had 1, 3, 2 trades respectively",
            "High per-year variance reflects small sample sizes within each year",
        ],
    ),

    # ── New strategies added 2026-03-19 ──────────────────────────────────────

    Strategy(
        name="SOXX puts",
        per_year_roc=[23.35, 26.69, -1.21, 9.88, 8.50, 25.07, 31.90],
        avg_trade_roc=17.74,
        win_rate=84.0,
        avg_concurrent=2,
        freq_per_year=10,
        note="Bull put spread 0.35Δ/0.30Δ. Regime-gated. $355 max loss/contract.",
        portfolio_alloc=5_000,
        caveats=[
            "Low trade frequency (~8–15/yr); high per-trade variance",
            "Semiconductor sector concentration — correlated with QQQ during tech selloffs",
        ],
    ),

    Strategy(
        name="SQQQ calls",
        per_year_roc=[13.46, 16.12, 0.63, -13.17, 12.53, 22.39, 27.39],
        avg_trade_roc=10.04,
        win_rate=82.7,
        avg_concurrent=2,
        freq_per_year=38,
        note="Bear call spread 0.50Δ/0.40Δ. VIX-gated. Structural decay from SQQQ 3× leverage.",
        portfolio_alloc=3_000,
        caveats=[
            "SQQQ price/strikes shift dramatically after each reverse split — verify current chain",
            "2022 losing year (-13.17%): prolonged bear market lifted SQQQ above short calls",
        ],
    ),

    Strategy(
        name="BJ puts",
        per_year_roc=[2.92, 9.13, 12.20, 6.45, -3.85, 8.74, 21.78],
        avg_trade_roc=8.20,
        win_rate=85.0,
        avg_concurrent=2,
        freq_per_year=22,
        note="Bull put spread 0.25Δ/0.15Δ. 45 DTE. All VIX. Monthly-ish cadence.",
        portfolio_alloc=3_000,
        caveats=[
            "Retail sector stock — earnings events can gap through short strike",
        ],
    ),

    Strategy(
        name="QQQ puts",
        # per-year weighted avg trade ROC (regime-blended, 2019–2025)
        per_year_roc=[6.31, 11.40, 8.37, 9.18, 6.80, 6.66, 7.61],
        avg_trade_roc=8.05,
        win_rate=84.0,
        avg_concurrent=2,
        freq_per_year=50,
        note="Regime-optimized bull put spread (4 deltas by regime). All-regime. 50 entries/yr.",
        portfolio_alloc=3_000,
        caveats=[
            "Reduce to 1.5% when SPY also fires same week — correlated put delta on both legs",
        ],
    ),

    Strategy(
        name="SPY regime",
        # per-year weighted avg trade ROC (active regime weeks only, 2019–2025)
        per_year_roc=[20.90, 8.07, 8.85, 8.34, 14.69, 13.77, 10.99],
        avg_trade_roc=12.23,
        win_rate=83.0,
        avg_concurrent=2,
        freq_per_year=23,
        note="Regime-switch: put spread (3 regimes) + long straddle (Bearish_LowIV). BullishLowIV now uses double calendar (separate entry).",
        portfolio_alloc=3_000,
        caveats=[
            "Bearish_HighIV: run put spread (1.5%) + double calendar (1.5%) simultaneously",
            "Bearish_LowIV = long straddle (1.5% sizing): debit structure, contrarian to rest of portfolio",
            "No stop loss — SPY mean-reverts through stops in all regimes",
            "Reduce put spread to 1% if QQQ also fires same week (correlated put delta)",
        ],
    ),

    Strategy(
        name="SPY double cal BearishHI",
        # per-year ROC (Bearish_HighIV weeks only, 0.25P/0.10C hold, 2018–2025)
        per_year_roc=[47.66, 68.22, 42.51, 24.08, -24.86, -7.59, 17.50],
        avg_trade_roc=23.7,
        win_rate=53.6,
        avg_concurrent=2,
        freq_per_year=8,
        note="Double calendar 0.25P/0.10C, hold to expiry. Bearish_HighIV only. ~12 DTE short / +7 DTE long.",
        portfolio_alloc=1_500,
        caveats=[
            "50% win rate — expect frequent small losses offset by large winners",
            "2023: -24.9% ROC (bank contagion whipsaw). Size conservatively.",
            "Run alongside SPY put spread (1.5% each) in Bearish_HighIV",
            "Max loss = net debit (~$2.15/shr × contracts)",
        ],
    ),

    Strategy(
        name="SPY double cal BullishLO",
        # per-year ROC (Bullish_LowIV weeks only, 0.25P/0.25C 50%PT, 2018–2025)
        per_year_roc=[20.99, 7.21, -9.32, 3.77, 25.80, 4.09, 17.39, 17.28],
        avg_trade_roc=10.4,
        win_rate=59.3,
        avg_concurrent=2,
        freq_per_year=26,
        note="Double calendar 0.25P/0.25C, 50% ROC profit take. Bullish_LowIV only. ~12 DTE short / +7 DTE long.",
        portfolio_alloc=3_000,
        caveats=[
            "2021: 32.3% win rate (SPY melt-up drifted through call strikes). Accept 1 weak year per cycle.",
            "2020: -9.3% (COVID regime flip mid-year). Only 8 BullishLO weeks that year.",
            "Max loss = net debit (~$2.15/shr × contracts)",
        ],
    ),

    Strategy(
        name="GEV puts",
        per_year_roc=[27.63, 14.41],
        avg_trade_roc=17.90,
        win_rate=94.4,
        avg_concurrent=2,
        freq_per_year=32,
        note="Bull put spread. PROVISIONAL — only 2024–2025 data. $10 spread width.",
        portfolio_alloc=2_000,
        caveats=[
            "PROVISIONAL: only 2 years of data (2024–present)",
            "Size at 2–3% max until longer track record accumulates",
        ],
    ),

    Strategy(
        name="CLS puts",
        per_year_roc=[26.15, 12.69],
        avg_trade_roc=16.30,
        win_rate=93.4,
        avg_concurrent=2,
        freq_per_year=35,
        note="Bull put spread. PROVISIONAL — 0.05Δ wing mandatory (fat-tail risk wider).",
        portfolio_alloc=2_000,
        caveats=[
            "PROVISIONAL: only 2 years of data (2024–present)",
            "0.05Δ wing MANDATORY — 0.15Δ wing SumROC = -99.3% (catastrophic fat-tail)",
            "Size at 2–3% max until longer track record accumulates",
        ],
    ),
]

STRATEGY_MAP: dict[str, Strategy] = {s.name: s for s in ALL_STRATEGIES}
