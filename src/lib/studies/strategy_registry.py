"""
Confirmed strategy registry — single source of truth for Sharpe scores and metadata.

Both run_allocation.py and run_friday_screener.py import from here so that updating
per-year data in one place propagates everywhere.

To update after a new backtest cycle:
  1. Add or update the per_year_roc list for the relevant strategy.
  2. Sharpe scores recompute automatically at import time.
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


ALL_STRATEGIES: list[Strategy] = [

    Strategy(
        name="UVXY combined",
        per_year_roc=[0.31, 6.19, 9.22, 8.22, 7.74, 3.48, 3.17, 10.08],
        avg_trade_roc=5.60,
        win_rate=74.6,
        avg_concurrent=2,
        freq_per_year=40,
        note="Bear call spread always + short put when VIX<20. Equal-capital blend.",
        caveats=["Put leg is naked short — undefined max loss; size conservatively"],
    ),

    Strategy(
        name="TLT calls",
        per_year_roc=[14.63, 30.99, 15.45, 17.69, 2.90, -7.94, 36.29, 18.97],
        avg_trade_roc=11.57,
        win_rate=81.4,
        avg_concurrent=2,
        freq_per_year=17,
        note="Bear call spread 0.35Δ/0.05Δ. VIX≥20 only — ~40% of Fridays active.",
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
        caveats=[
            "Per-year data from no-filter sweep (fwd≤0.90 per-year not available)",
            "Per-trade ROC (+78.8%) reflects highly selective entry — not every week",
        ],
    ),

    Strategy(
        name="XLV puts",
        per_year_roc=[4.99, 11.31, 3.59, -1.99, 2.86, 7.07, 14.04, 15.71],
        avg_trade_roc=6.82,
        win_rate=92.5,
        avg_concurrent=2,
        freq_per_year=47,
        note="Bull put spread 0.25Δ/0.05Δ. All VIX.",
    ),

    Strategy(
        name="USO puts",
        per_year_roc=[7.60, 8.75, 8.79, 8.39, 8.22, 15.71],
        avg_trade_roc=9.58,
        win_rate=92.3,
        avg_concurrent=2,
        freq_per_year=47,
        note="Bull put spread 0.25Δ/0.05Δ. 30 DTE. All VIX. Post-restructuring (Jul 2020+).",
        caveats=["6 years of data (2020–2025); no losing year yet but history is shorter"],
    ),

    Strategy(
        name="XLF regime",
        per_year_roc=[20.7, -15.1, 22.9, 14.3, 9.3, 32.7, -12.5, 44.3],
        avg_trade_roc=16.7,
        win_rate=75.0,
        avg_concurrent=2,
        freq_per_year=42,
        note="Regime-switching: 4 strategies by XLF 50MA × VIX. $21.74 cum 2018-2025.",
        caveats=[
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
        caveats=[
            "Per-year ROC estimated from annual win rates — actual values not tracked per year",
            "Only active ~9 weeks/year; capital mostly idle",
            "2020: 26 qualifying weeks — concentration risk in prolonged energy bear market",
        ],
    ),

    Strategy(
        name="UUP straddle",
        per_year_roc=[18.2, 15.5, 21.0, 14.8, 16.3, 19.7, 12.1, 10.5],
        avg_trade_roc=17.4,
        win_rate=73.1,
        avg_concurrent=1,
        freq_per_year=13,
        note="ATM short straddle ~0.50Δ. No regime gate. ~13 entries/yr. $14.26 cum 2018-2025.",
        caveats=[
            "Per-year ROC estimated — actual per-year breakdown not tracked",
            "2024-2025: data sparse; verify chain liquidity in broker before each entry",
            "Naked straddle — size at 2-3% max",
        ],
    ),

    Strategy(
        name="ASHR puts",
        per_year_roc=[-1.43, 6.95, 20.44, 6.76, 1.92, 7.19, 21.27, -2.02],
        avg_trade_roc=8.49,
        win_rate=86.6,
        avg_concurrent=2,
        freq_per_year=24,
        note="Bull put spread 0.25Δ/0.05Δ. All VIX. Iron condor put leg.",
        caveats=["Run alongside ASHR calls (condor) — correlation is negative"],
    ),

    Strategy(
        name="ASHR calls",
        per_year_roc=[10.48, 11.15, -3.99, 7.51, 0.92, 15.63, 16.55, 6.56],
        avg_trade_roc=8.19,
        win_rate=90.1,
        avg_concurrent=2,
        freq_per_year=29,
        note="Bear call spread 0.20Δ/0.10Δ. All VIX. Iron condor call leg.",
        caveats=["Run alongside ASHR puts (condor) — correlation is negative"],
    ),

    Strategy(
        name="INDA puts",
        per_year_roc=[-6.33, 10.57, 32.92, -4.30, 12.12, 12.89, 18.18],
        avg_trade_roc=12.79,
        win_rate=91.7,
        avg_concurrent=1,
        freq_per_year=7,
        note="Bull put spread 0.25Δ/0.05Δ. All VIX. Very thin option chain.",
        caveats=[
            "Only 60 trades over 8 years; 2023–2025 had 1, 3, 2 trades respectively",
            "High per-year variance reflects small sample sizes within each year",
        ],
    ),
]

STRATEGY_MAP: dict[str, Strategy] = {s.name: s for s in ALL_STRATEGIES}
