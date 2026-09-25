#!/usr/bin/env python3
"""
Capital allocation calculator for confirmed option strategies.

Given a total portfolio size and a list of active strategies (from the Friday screener),
computes how much capital (in dollars of risk) to allocate to each under two schemes:

  1. Equal risk       — same max-loss dollars to every active strategy
  2. Sharpe-weighted  — more capital to strategies with higher year-level Sharpe ratios

Usage:
    # Show Sharpe table for all strategies:
    python run_allocation.py

    # Allocate capital across specific active strategies:
    python run_allocation.py --capital 100000 --active "GLD puts" "GLD calendar"

    # Use a custom portfolio risk budget (default 20%):
    python run_allocation.py --capital 100000 --risk-pct 0.15 --active "GLD puts" "TLT calls"

Output: Sharpe table + dollar allocation + contract guidance (user supplies max-loss/contract
        from the screener output).

Note: Sharpe scores are computed at the year level (mean / std of per-year avg ROC),
which reflects year-over-year consistency — the metric most relevant for portfolio sizing.
Per-trade Sharpe (mean / std of individual trade ROC) is a different, higher number and
is shown separately in each strategy's playbook.
"""

from __future__ import annotations

import argparse
from typing import Optional

from lib.studies.strategy_registry import ALL_STRATEGIES, STRATEGY_MAP, Strategy


# ── Display helpers ───────────────────────────────────────────────────────────

def print_sharpe_table() -> None:
    """Print all strategies ranked by year-level Sharpe score."""
    ranked = sorted(ALL_STRATEGIES, key=lambda s: s.sharpe_annual, reverse=True)

    W = 108
    print("\n" + "═" * W)
    print(f"  STRATEGY SHARPE RANKING  (year-level: mean(per-year ROC) / std(per-year ROC))")
    print("═" * W)
    print(
        f"  {'Strategy':<22}  {'Yrs':>3}  {'Win%':>5}  "
        f"{'Avg ROC':>7}  {'MeanAnn':>7}  {'StdAnn':>6}  {'Sharpe':>6}  "
        f"{'LossYrs':>7}  {'Freq/yr':>7}  Note"
    )
    print("─" * W)
    for s in ranked:
        caveat_flag = " *" if s.caveats else "  "
        print(
            f"  {s.name:<22}  {s.years:>3}  {s.win_rate:>4.1f}%  "
            f"  {s.avg_trade_roc:>+6.2f}%  {s.mean_annual:>+6.2f}%  {s.std_annual:>6.2f}  {s.sharpe_annual:>6.3f}  "
            f"  {s.losing_years:>4}/{s.years:<2}  {s.freq_per_year:>5}/yr  "
            f"{s.note[:45]}{caveat_flag}"
        )
    print("─" * W)
    print("  Columns: Yrs=years of data  Avg ROC=per-trade  MeanAnn/StdAnn=year-level  Sharpe=MeanAnn/StdAnn")
    print("  * = caveats apply (run with --detail for notes)")
    print("═" * W + "\n")


def print_detail(names: Optional[list[str]] = None) -> None:
    """Print caveats for strategies."""
    targets = [STRATEGY_MAP[n] for n in names] if names else ALL_STRATEGIES
    for s in targets:
        if s.caveats:
            print(f"  {s.name}:")
            for c in s.caveats:
                print(f"    - {c}")


def print_allocation(
    active_names: list[str],
    total_capital: float,
    risk_pct: float,
) -> None:
    """
    Print equal-risk and Sharpe-weighted allocations for active strategies.

    Outputs dollar risk budgets. To convert to contracts:
        contracts = allocated_dollars / max_loss_per_contract
    where max_loss_per_contract comes from the screener output for each strategy.
    """
    active = []
    for name in active_names:
        if name not in STRATEGY_MAP:
            print(f"  WARNING: '{name}' not found. Known strategies: {list(STRATEGY_MAP.keys())}")
        else:
            active.append(STRATEGY_MAP[name])

    if not active:
        print("  No valid active strategies.")
        return

    total_risk = total_capital * risk_pct
    n = len(active)

    # ── Equal risk ─────────────────────────────────────────────────────────────
    equal_per = total_risk / n

    # ── Sharpe-weighted ────────────────────────────────────────────────────────
    sharpes = [max(s.sharpe_annual, 0.01) for s in active]   # floor at 0.01
    total_sharpe = sum(sharpes)
    sharpe_weights = [sh / total_sharpe for sh in sharpes]
    sharpe_alloc = [total_risk * w for w in sharpe_weights]

    W = 100
    print("\n" + "═" * W)
    print(
        f"  CAPITAL ALLOCATION  ·  ${total_capital:,.0f} portfolio  ·  "
        f"{risk_pct * 100:.0f}% risk budget = ${total_risk:,.0f}"
    )
    print("═" * W)
    print(f"  {'Strategy':<22}  {'Sharpe':>6}  {'= Risk Alloc':>12}  {'Sharpe-Wtd':>10}  "
          f"{'Δ vs Equal':>10}  {'Concurrent':>10}")
    print("─" * W)

    for s, sw, sa in zip(active, sharpe_weights, sharpe_alloc):
        delta = sa - equal_per
        concurrent_note = f"~{s.avg_concurrent} open" if s.avg_concurrent > 1 else "~1 open"
        print(
            f"  {s.name:<22}  {s.sharpe_annual:>6.3f}  "
            f"  ${equal_per:>9,.0f}  ${sa:>9,.0f}  "
            f"  {'+' if delta >= 0 else ''}{delta:>+8,.0f}  "
            f"  {concurrent_note}"
        )

    print("─" * W)
    print(f"  {'TOTAL':<22}  {'':>6}  ${total_risk:>10,.0f}  ${sum(sharpe_alloc):>9,.0f}")
    print("─" * W)

    # ── Contract guidance ──────────────────────────────────────────────────────
    print()
    print("  To convert to contracts:")
    print("    contracts = allocation / max_loss_per_contract")
    print()
    print("  max_loss_per_contract from today's screener output:")
    print("    credit spread:  (spread_width - net_credit) × 100  per contract")
    print("    put calendar:   net_debit × 100  per contract  (full debit is at risk)")
    print()

    # Concurrent position notes
    multi = [s for s in active if s.avg_concurrent > 1]
    if multi:
        print("  Peak capital at risk (with overlapping positions):")
        for s in multi:
            eq_contracts_note = f"× {s.avg_concurrent} = ${equal_per * s.avg_concurrent:,.0f}" \
                                f" equal  /  ${(total_risk * (max(s.sharpe_annual, 0.01)/total_sharpe)) * s.avg_concurrent:,.0f} Sharpe-wtd"
            print(f"    {s.name}: {s.avg_concurrent} concurrent → {eq_contracts_note}")

    print("═" * W + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strategy Sharpe table + capital allocation calculator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--capital", type=float, default=100_000,
        help="Total portfolio size in dollars",
    )
    parser.add_argument(
        "--risk-pct", type=float, default=0.20,
        help="Fraction of capital to risk across all active strategies (e.g. 0.20 = 20%%)",
    )
    parser.add_argument(
        "--active", nargs="+", metavar="STRATEGY",
        help=(
            "Active strategy names to allocate. Quote names with spaces. "
            "Example: --active 'GLD puts' 'TLT calls' 'UVXY combined'"
        ),
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="Print caveats for all strategies",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all strategy names and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("\nKnown strategy names:")
        for name in STRATEGY_MAP:
            print(f"  {name!r}")
        return

    print_sharpe_table()

    if args.detail:
        print("  Caveats:")
        print_detail()
        print()

    if args.active:
        print_allocation(args.active, args.capital, args.risk_pct)
    else:
        print(
            "  Tip: run with --active 'Strategy A' 'Strategy B' --capital N\n"
            "  to compute dollar allocation for a specific set of active strategies.\n"
        )


if __name__ == "__main__":
    main()
