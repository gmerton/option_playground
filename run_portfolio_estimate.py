#!/usr/bin/env python3
"""
Portfolio annual P&L estimate based on playbook data.

Formula: Annual_$$ = N_trades × risk_per_trade × avg_ROC_per_trade
  risk_per_trade = allocation / max_concurrent

For TLT/XLF (which have $/share annual P&L):
  Annual_$$ = (allocation / avg_margin_per_share) × annual_P&L_per_share

For SPY/QQQ (regime-distribution + per-regime ROC):
  Annual_$$ = Σ_regimes(n_weeks × risk_per_trade × regime_ROC)

All allocations sum to ~$90K deployed.
"""

STRATEGIES = {
    # ── UVXY ──────────────────────────────────────────────────────────────────
    # Bi-weekly, 2 legs per entry (call spread + short put when VIX<20).
    # allocation=$10K, max_concurrent=4 legs → risk_per_leg = $2,500
    "UVXY": {
        "allocation": 10_000,
        "max_concurrent": 4,
        "years": {
            # year: (n_trades, avg_roc)
            2018: (45, 0.0031), 2019: (51, 0.0619), 2020: (48, 0.0922),
            2021: (46, 0.0822), 2022: (50, 0.0774), 2023: (41, 0.0348),
            2024: (46, 0.0317), 2025: (33, 0.1008),
        },
    },

    # ── TLT ───────────────────────────────────────────────────────────────────
    # Weekly regime-switch. Use $/share annual P&L directly.
    # avg margin = $0.87/share → at $5K: ~57 contracts
    "TLT": {
        "allocation": 5_000,
        "avg_margin_per_share": 0.870,
        "method": "pnl_per_share",
        "years": {
            # year: annual_P&L_per_share (sum of all trades that year, per 1-contract position)
            2019: 0.76, 2020: 0.49, 2021: 2.45, 2022: 4.26,
            2023: 1.83, 2024: -0.80, 2025: 1.19,
        },
    },

    # ── XLF ───────────────────────────────────────────────────────────────────
    # Weekly regime-switch (spreads + strangles). Use $/share annual P&L.
    # avg margin = $1.16/share (weighted across regimes) → at $4K: ~34 contracts
    # Use $4K allocation (blended: 5% for spreads, 2-3% for strangles)
    "XLF": {
        "allocation": 4_000,
        "avg_margin_per_share": 1.160,
        "method": "pnl_per_share",
        "years": {
            2019: -0.69, 2020: 5.57, 2021: 8.67, 2022: 1.62,
            2023: 3.98, 2024: -2.63, 2025: 4.84,
        },
    },

    # ── SQQQ ──────────────────────────────────────────────────────────────────
    # Weekly bear call spread (gated). allocation=$3K, max_concurrent=2
    "SQQQ": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            2019: (8,  0.1346), 2020: (36, 0.1612), 2021: (36, 0.0063),
            2022: (46, -0.1317), 2023: (51, 0.1253), 2024: (33, 0.2239),
            2025: (49, 0.2739),
        },
    },

    # ── XLU Calendar ──────────────────────────────────────────────────────────
    # Weekly put calendar (fwd_vol ≤ 0.90). allocation=$3K, max_concurrent=1
    "XLU_CAL": {
        "allocation": 3_000,
        "max_concurrent": 1,
        "years": {
            2019: (51, 0.227), 2020: (48, 0.154), 2021: (50, 0.122),
            2022: (51, 0.519), 2023: (51, 0.026), 2024: (49, 0.794),
            2025: (33, 0.617),
        },
    },

    # ── GLD Calendar ──────────────────────────────────────────────────────────
    # Weekly put calendar (iv_ratio ≥ 1.0). Estimate 30 trades/year.
    # allocation=$3K, max_concurrent=2
    "GLD_CAL": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            # (estimated_n_trades, avg_roc)
            2019: (41, 0.034), 2020: (27, 0.203), 2021: (19, 0.159),
            2022: (30, -0.087), 2023: (38, 0.383), 2024: (33, 0.205),
            2025: (41, -0.018),
        },
    },

    # ── BJ ────────────────────────────────────────────────────────────────────
    # Monthly-ish put spread (45 DTE). allocation=$3K, max_concurrent=2
    "BJ": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            2019: (10, 0.0292), 2020: (15, 0.0913), 2021: (19, 0.1220),
            2022: (31, 0.0645), 2023: (21, -0.0385), 2024: (27, 0.0874),
            2025: (31, 0.2178),
        },
    },

    # ── USO ───────────────────────────────────────────────────────────────────
    # Weekly put spread (post-restructuring, usable 2020+). Est. 43 trades/yr.
    # allocation=$3K, max_concurrent=2
    "USO": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            2020: (21, 0.0760), 2021: (47, 0.0875), 2022: (46, 0.0879),
            2023: (51, 0.0839), 2024: (45, 0.0822), 2025: (42, 0.1571),
        },
    },

    # ── INDA ──────────────────────────────────────────────────────────────────
    # Seasonal put spread. allocation=$2K, max_concurrent=1
    "INDA": {
        "allocation": 2_000,
        "max_concurrent": 1,
        "years": {
            2019: (5,  -0.0633), 2020: (22, 0.1057), 2021: (16, 0.3292),
            2022: (11, -0.0430), 2023: (1,  0.1212), 2024: (3,  0.1289),
            2025: (2,  0.1818),
        },
    },

    # ── ASHR Put Spread ───────────────────────────────────────────────────────
    # Weekly iron condor (put side). Est. 47 trades/year (IS: 247/5yr).
    # allocation=$3K, max_concurrent=2
    # Note: per-year data below is for old 0.05Δ wing; 0.10Δ wing improves OOS
    "ASHR_PUT": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            2019: (47, 0.0695), 2020: (47, 0.2044), 2021: (47, 0.0676),
            2022: (47, 0.0192), 2023: (47, 0.0719), 2024: (47, 0.2127),
            2025: (47, -0.0202),
        },
    },

    # ── ASHR Call Spread ──────────────────────────────────────────────────────
    # Weekly iron condor (call side). Est. 47 trades/year.
    # allocation=$3K, max_concurrent=2
    "ASHR_CALL": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            2019: (47, 0.1115), 2020: (47, -0.0399), 2021: (47, 0.0751),
            2022: (47, 0.0092), 2023: (47, 0.1563), 2024: (47, 0.1655),
            2025: (47, 0.0656),
        },
    },

    # ── TMF ───────────────────────────────────────────────────────────────────
    # Weekly bear call spread. Only 2024+ reliable. allocation=$2K, max_concurrent=2
    "TMF": {
        "allocation": 2_000,
        "max_concurrent": 2,
        "years": {
            2024: (47, 0.1093), 2025: (47, 0.2134),
        },
    },

    # ── GEV ───────────────────────────────────────────────────────────────────
    # Weekly put spread (provisional 2024+). allocation=$2K, max_concurrent=2
    "GEV": {
        "allocation": 2_000,
        "max_concurrent": 2,
        "years": {
            2024: (17, 0.2763), 2025: (48, 0.1441),
        },
    },

    # ── CLS ───────────────────────────────────────────────────────────────────
    # Weekly put spread (provisional 2024+). allocation=$2K, max_concurrent=2
    "CLS": {
        "allocation": 2_000,
        "max_concurrent": 2,
        "years": {
            2024: (21, 0.2615), 2025: (49, 0.1269),
        },
    },

    # ── SOXX ──────────────────────────────────────────────────────────────────
    # Weekly put spread (always-on). allocation=$5K, max_concurrent=2
    # max_loss ~$355/contract; at $5K/2 concurrent = $2,500/position → 7 contracts
    "SOXX": {
        "allocation": 5_000,
        "max_concurrent": 2,
        "years": {
            2019: (8,  0.2335), 2020: (8,  0.2669), 2021: (9,  -0.0121),
            2022: (12, 0.0988), 2023: (12, 0.0850), 2024: (8,  0.2507),
            2025: (15, 0.3190),
        },
    },

    # ── GLD put spread ────────────────────────────────────────────────────────
    # Weekly (VIX<25 filter). allocation=$3K, max_concurrent=2
    # 319 trades / 8 years = ~40/year. Overall avg ROC +7.98%.
    # "Losing years: 2018, 2021 only" → approximate distribution
    "GLD_PS": {
        "allocation": 3_000,
        "max_concurrent": 2,
        "years": {
            # Estimated per-year: overall +7.98% avg, 40 trades/yr
            # Worse years: 2021 (gold sold off H2), 2022 (rate hikes)
            2019: (40, 0.0798), 2020: (40, 0.0798), 2021: (35, -0.020),
            2022: (38, 0.050),  2023: (40, 0.0798), 2024: (40, 0.0798),
            2025: (40, 0.0798),
        },
    },

    # ── UUP ───────────────────────────────────────────────────────────────────
    # Short ATM straddle, fires ~24% of Fridays (~13 trades/yr).
    # allocation=$2K, max_concurrent=1
    # avg ROC +2.3% per trade (Reg T basis). Thin/supplementary.
    "UUP": {
        "allocation": 2_000,
        "max_concurrent": 1,
        "years": {
            # ~13 trades/yr, +2.3% avg. 2024-2025 sparse (fewer entries)
            2019: (13, 0.023), 2020: (13, 0.023), 2021: (13, 0.023),
            2022: (13, 0.023), 2023: (13, 0.023), 2024: (8,  0.023),
            2025: (5,  0.023),
        },
    },
}

# ── SPY regime-switching ──────────────────────────────────────────────────────
# Allocation: $3K spreads (2–3%), $1.5K straddle (1–2%). max_concurrent=2.
# risk_per_trade = allocation / max_concurrent
SPY_REGIMES = {
    # regime: (spread_alloc, roc_per_trade, is_straddle)
    "Bearish_HighIV":  (3_000, 0.0749, False),
    "Bearish_LowIV":   (1_500, 0.2260, True),   # long straddle
    "Bullish_HighIV":  (3_000, 0.0826, False),
    "Bullish_LowIV":   (0,     0.0,    False),   # skip
}
SPY_DIST = {
    # year: {regime: n_weeks}
    2019: {"Bearish_HighIV": 1,  "Bearish_LowIV": 8,  "Bullish_HighIV": 0,  "Bullish_LowIV": 42},
    2020: {"Bearish_HighIV": 10, "Bearish_LowIV": 0,  "Bullish_HighIV": 31, "Bullish_LowIV": 8},
    2021: {"Bearish_HighIV": 4,  "Bearish_LowIV": 1,  "Bullish_HighIV": 14, "Bullish_LowIV": 31},
    2022: {"Bearish_HighIV": 32, "Bearish_LowIV": 2,  "Bullish_HighIV": 14, "Bullish_LowIV": 3},
    2023: {"Bearish_HighIV": 7,  "Bearish_LowIV": 8,  "Bullish_HighIV": 2,  "Bullish_LowIV": 34},
    2024: {"Bearish_HighIV": 3,  "Bearish_LowIV": 4,  "Bullish_HighIV": 3,  "Bullish_LowIV": 41},
    2025: {"Bearish_HighIV": 7,  "Bearish_LowIV": 4,  "Bullish_HighIV": 8,  "Bullish_LowIV": 31},
}

# ── QQQ regime-switching ──────────────────────────────────────────────────────
# Allocation: $3K (2–3%), max_concurrent=2, risk_per_trade=$1,500
QQQ_REGIMES = {
    "Bearish_HighIV":  (3_000, 0.0738),
    "Bearish_LowIV":   (3_000, 0.0832),
    "Bullish_HighIV":  (3_000, 0.1411),
    "Bullish_LowIV":   (3_000, 0.0590),
}
QQQ_DIST = {
    2019: {"Bearish_HighIV": 1,  "Bearish_LowIV": 8,  "Bullish_HighIV": 0,  "Bullish_LowIV": 42},
    2020: {"Bearish_HighIV": 10, "Bearish_LowIV": 0,  "Bullish_HighIV": 31, "Bullish_LowIV": 8},
    2021: {"Bearish_HighIV": 4,  "Bearish_LowIV": 1,  "Bullish_HighIV": 14, "Bullish_LowIV": 31},
    2022: {"Bearish_HighIV": 32, "Bearish_LowIV": 2,  "Bullish_HighIV": 14, "Bullish_LowIV": 3},
    2023: {"Bearish_HighIV": 7,  "Bearish_LowIV": 8,  "Bullish_HighIV": 2,  "Bullish_LowIV": 34},
    2024: {"Bearish_HighIV": 3,  "Bearish_LowIV": 4,  "Bullish_HighIV": 3,  "Bullish_LowIV": 41},
    2025: {"Bearish_HighIV": 7,  "Bearish_LowIV": 4,  "Bullish_HighIV": 8,  "Bullish_LowIV": 31},
}

# ── XLE regime-gated (BearHI only) ───────────────────────────────────────────
# allocation=$3K, max_concurrent=2, risk_per_trade=$1,500. avg ROC +35.5%/trade
XLE_DIST = {
    # year: n_BearHI_weeks
    2019: 1, 2020: 26, 2021: 7, 2022: 14,
    2023: 7, 2024: 4,  2025: 10,
}
XLE_ROC_PER_TRADE = 0.355
XLE_ALLOCATION    = 3_000
XLE_MAX_CONC      = 2

# Strategies not in model (missing per-year data):
# SPY, QQQ — regime distribution only (no per-year $ P&L)
# XLE       — BearHI only (~9 wks/yr), regime count data only
# UUP       — ~2.3% avg/yr, no per-year breakdown
# GLD_PS    — overall 87.1% win / +7.98% ROC, no per-year breakdown
# SOXX      — missing playbook data

PORTFOLIO_CAPITAL = 100_000

# Typical margin per contract for each strategy (used for contract-capped model)
# Based on playbook economics sections
MARGIN_PER_CONTRACT = {
    "UVXY":      57,    # call spread: ~$57/contract avg ($38-76 range)
    "TLT":       87,    # avg across regimes ($/share × 100)
    "XLF":      116,    # avg Reg T across regimes ($/share × 100)
    "SQQQ":      60,    # bear call spread ~$0.60/share typical
    "XLU_CAL":   80,    # calendar debit ~$0.80/share
    "GLD_CAL":  150,    # calendar debit ~$1.50/share (GLD ~$180)
    "BJ":       100,    # put spread margin ~$1.00/share
    "USO":       50,    # put spread ~$0.50/share
    "INDA":      60,    # put spread ~$0.60/share
    "ASHR_PUT":  79,    # put spread max loss ~$79/contract
    "ASHR_CALL": 226,   # call spread max loss ~$226/contract avg
    "TMF":       30,    # call spread ~$0.30/share (leveraged ETF)
    "GEV":      150,    # put spread ~$1.50/share
    "CLS":      100,    # put spread ~$1.00/share
}

# Practical contract cap per trade (realistic for retail liquidity)
PRACTICAL_MAX_CONTRACTS = {
    "UVXY":      15,
    "TLT":       20,
    "XLF":       20,
    "SQQQ":      15,
    "XLU_CAL":   10,
    "GLD_CAL":   10,
    "BJ":        10,
    "USO":       15,
    "INDA":       5,
    "ASHR_PUT":   8,
    "ASHR_CALL":  8,
    "TMF":       15,
    "GEV":        5,
    "CLS":        5,
    # New strategies
    "SOXX":       7,    # put spread max loss ~$355, $2.5K/trade → 7 contracts
    "GLD_PS":    10,    # put spread max loss ~$250/contract
    "UUP":        3,    # ATM straddle Reg T ~$580/contract
    # Regime-switch (avg across regime structures)
    "SPY":        3,    # put spread on SPY ~$700/contract; ~2 in bear spread regimes
    "QQQ":        5,    # put spread on QQQ ~$500/contract
    "XLE":       10,    # put spread on XLE ~$200/contract
}

MARGIN_PER_CONTRACT.update({
    "SOXX":  355,   # playbook: max loss ~$355/contract
    "GLD_PS": 250,  # GLD ~$180, spread ~$2.50 wide, max loss ~$250
    "UUP":   580,   # Reg T: 0.20×$28×100 + credit ~$580/contract
    "SPY":   700,   # put spread on SPY, typical ~$7 width ($700/contract)
    "QQQ":   500,   # put spread on QQQ, typical ~$5 width ($500/contract)
    "XLE":   200,   # put spread on XLE, typical ~$2 width ($200/contract)
})


def compute_annual_pnl(strat_name, cfg, year):
    if year not in cfg["years"]:
        return None

    alloc = cfg["allocation"]
    method = cfg.get("method", "n_trades_roc")

    if method == "pnl_per_share":
        # TLT / XLF approach: use $/share annual P&L
        margin = cfg["avg_margin_per_share"]
        pnl_per_share = cfg["years"][year]
        n_contracts = alloc / (margin * 100)
        return n_contracts * pnl_per_share * 100

    else:
        # Default: n_trades × risk_per_trade × avg_ROC
        n_trades, avg_roc = cfg["years"][year]
        risk_per_trade = alloc / cfg["max_concurrent"]
        return n_trades * risk_per_trade * avg_roc


def compute_annual_pnl_capped(strat_name, cfg, year):
    """Same as above but caps contracts at PRACTICAL_MAX_CONTRACTS."""
    if year not in cfg["years"]:
        return None

    alloc = cfg["allocation"]
    method = cfg.get("method", "n_trades_roc")
    margin = MARGIN_PER_CONTRACT.get(strat_name, 100)
    max_cts = PRACTICAL_MAX_CONTRACTS.get(strat_name, 10)

    if method == "pnl_per_share":
        pnl_per_share = cfg["years"][year]
        # Natural contract count from allocation/margin, capped
        n_contracts = min(int(alloc / margin), max_cts)
        return n_contracts * pnl_per_share * 100
    else:
        n_trades, avg_roc = cfg["years"][year]
        # Cap: contracts per entry = min(allocation/max_concurrent/margin, max_cts)
        risk_per_trade = alloc / cfg["max_concurrent"]
        n_contracts = min(int(risk_per_trade / margin), max_cts)
        return n_trades * n_contracts * margin * avg_roc


def compute_spy_annual(year, practical=False):
    """SPY regime-switch: sum across regimes of n_weeks × risk_per_trade × roc."""
    if year not in SPY_DIST:
        return None
    total = 0.0
    for regime, (alloc, roc, _is_straddle) in SPY_REGIMES.items():
        if alloc == 0:
            continue
        n_weeks = SPY_DIST[year].get(regime, 0)
        if n_weeks == 0:
            continue
        max_conc = 2
        risk_per_trade = alloc / max_conc
        if practical:
            margin = MARGIN_PER_CONTRACT["SPY"]
            max_cts = PRACTICAL_MAX_CONTRACTS["SPY"]
            n_contracts = min(int(risk_per_trade / margin), max_cts)
            total += n_weeks * n_contracts * margin * roc
        else:
            total += n_weeks * risk_per_trade * roc
    return total


def compute_qqq_annual(year, practical=False):
    """QQQ regime-switch (all regimes active): sum across regimes."""
    if year not in QQQ_DIST:
        return None
    total = 0.0
    max_conc = 2
    for regime, (alloc, roc) in QQQ_REGIMES.items():
        n_weeks = QQQ_DIST[year].get(regime, 0)
        if n_weeks == 0:
            continue
        risk_per_trade = alloc / max_conc
        if practical:
            margin = MARGIN_PER_CONTRACT["QQQ"]
            max_cts = PRACTICAL_MAX_CONTRACTS["QQQ"]
            n_contracts = min(int(risk_per_trade / margin), max_cts)
            total += n_weeks * n_contracts * margin * roc
        else:
            total += n_weeks * risk_per_trade * roc
    return total


def compute_xle_annual(year, practical=False):
    """XLE BearHI-only: n_weeks × risk_per_trade × 35.5%."""
    if year not in XLE_DIST:
        return None
    n_weeks = XLE_DIST[year]
    risk_per_trade = XLE_ALLOCATION / XLE_MAX_CONC
    if practical:
        margin = MARGIN_PER_CONTRACT["XLE"]
        max_cts = PRACTICAL_MAX_CONTRACTS["XLE"]
        n_contracts = min(int(risk_per_trade / margin), max_cts)
        return n_weeks * n_contracts * margin * XLE_ROC_PER_TRADE
    else:
        return n_weeks * risk_per_trade * XLE_ROC_PER_TRADE


def main():
    years = list(range(2019, 2026))
    strat_alloc = sum(cfg["allocation"] for cfg in STRATEGIES.values())
    regime_alloc = (
        max(a for a, _, _ in SPY_REGIMES.values()) +  # SPY max allocation
        max(a for a, _ in QQQ_REGIMES.values()) +      # QQQ
        XLE_ALLOCATION
    )
    total_alloc = strat_alloc + regime_alloc

    for model, label in [
        ("theoretical", "THEORETICAL (full allocation / margin, uncapped)"),
        ("practical",   "PRACTICAL (~3–10 contracts/trade, retail sizing)"),
    ]:
        practical = (model == "practical")
        yearly_totals = {y: 0.0 for y in years}
        rows = []

        # Standard strategies
        for name, cfg in STRATEGIES.items():
            alloc = cfg["allocation"]
            row_pnls = []
            for y in years:
                pnl = (compute_annual_pnl_capped(name, cfg, y)
                       if practical else compute_annual_pnl(name, cfg, y))
                row_pnls.append(pnl)
                if pnl is not None:
                    yearly_totals[y] += pnl
            valid = [p for p in row_pnls if p is not None]
            rows.append((name, alloc, row_pnls, valid))

        # Regime-switching strategies
        for name, alloc_label, compute_fn in [
            ("SPY", 3_000, lambda y, p=practical: compute_spy_annual(y, p)),
            ("QQQ", 3_000, lambda y, p=practical: compute_qqq_annual(y, p)),
            ("XLE", XLE_ALLOCATION, lambda y, p=practical: compute_xle_annual(y, p)),
        ]:
            row_pnls = []
            for y in years:
                pnl = compute_fn(y)
                row_pnls.append(pnl)
                if pnl is not None:
                    yearly_totals[y] += pnl
            valid = [p for p in row_pnls if p is not None]
            rows.append((name, alloc_label, row_pnls, valid))

        print(f"\n{'═'*110}")
        print(f"  {label}")
        print(f"  $100K capital · ~${total_alloc:,} deployed (~{total_alloc/PORTFOLIO_CAPITAL*100:.0f}%)")
        print(f"{'═'*110}")
        print(f"  {'Strategy':<14}  {'Alloc':>5}  ", end="")
        for y in years:
            print(f"  {y:>8}", end="")
        print(f"  {'Avg/yr':>8}")
        print(f"  {'-'*105}")

        for name, alloc, row_pnls, valid in rows:
            print(f"  {name:<14}  ${alloc/1000:>3.0f}K  ", end="")
            for pnl in row_pnls:
                if pnl is None:
                    print(f"  {'—':>8}", end="")
                else:
                    print(f"  {pnl:>+8,.0f}", end="")
            avg = sum(valid) / len(valid) if valid else 0
            print(f"  {avg:>+8,.0f}")

        print(f"  {'─'*105}")
        print(f"\n  {'TOTAL':<14}  {'':>5}  ", end="")
        for y in years:
            print(f"  {yearly_totals[y]:>+8,.0f}", end="")
        grand = sum(yearly_totals.values()) / len(years)
        print(f"  {grand:>+8,.0f}")

        print(f"  {'% of $100K':<14}  {'':>5}  ", end="")
        for y in years:
            print(f"  {yearly_totals[y]/1000:>+7.1f}%", end="")
        print(f"  {grand/1000:>+7.1f}%")

    print(f"\n{'═'*110}")
    print("""
  KEY POINTS:
  • Theoretical model recycles capital fully (contracts = allocation ÷ margin, no cap).
    XLU_CAL dominates (48K avg) — 37 contracts × 49 trades on $3K = 3,800% theoretical ROC.
    These numbers are real compounding math but assume perfect liquidity and zero slippage.

  • Practical model caps at 3–10 contracts/trade (retail execution). Still shows $41K–$100K/yr
    range (41–100% annual return on $100K). XLU_CAL still large (~$13K avg) even at 10 contracts
    due to 49 trades/year recycling. Consider further capping XLU to 5–6 contracts in live trading.

  • Neither model includes: commissions (~$0.65/contract × N trades), bid-ask slippage (0.5–2%
    of credit on liquid ETFs, up to 25% on ASHR/UUP), or correlated drawdowns across positions.
    Real net would be roughly 10–25% lower than practical model.

  • Best years: 2024 (+91%), 2025 (+100%) — elevated VIX + many regime-switch signals.
    2019 weakest (+41%) — calm bull market, few regime triggers, SPY/XLE barely fire.
  • Top contributors (practical avg): XLU_CAL $12.8K, XLF $6.1K, QQQ $6.1K, TLT $2.9K.
  • Worst single year by strategy: XLF 2024 (-$5.3K), SQQQ 2022 (-$5.5K), XLF 2019 (-$1.4K).
  • SPY/QQQ both sell put spreads in high-VIX weeks — size each to 1.5% when both fire same week.
""")



if __name__ == "__main__":
    main()
