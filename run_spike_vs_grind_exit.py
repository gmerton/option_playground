#!/usr/bin/env python3
"""
Does Tito's SPIKE branch beat the 20-EMA trail on a long call? (pre-registered 2026-09-23, before Stage 1 landed)

THE CLAIM. Adhikary's exit is CONDITIONAL, not one rule: **grind up -> trail the 20 EMA on a daily close;
spike -> sell into strength.** `tito_selection_playbook.md` L231 states the trail FAILS on spike trades,
with his own numbers (ARM: he took +1966% selling the spike; the 20-EMA trail returned +578%, "held to
expiry, gave back the 2/12 spike"). His stated mechanism: a short-dated option that spikes gives back the
spike PLUS theta long before a daily close confirms the trend break.

WHY THIS TEST AND NOT ANOTHER SELECTION TEST. Four independent angles now say mechanical selection cannot
improve the breakout book (within-date ranking t -0.11, the universe test, the Trend-Template ablation,
and the 2026-09-23 precision-tier freeze-forward). Meanwhile the pool's own shape says the money is in the
TAIL, not the pick: 30% win, median -1.05R, top 1% of trades carry 26% of gross, and the mean slides
+0.32 -> +0.68 -> +1.14 purely on how far the right tail is allowed to run. For a distribution like that,
tail management is first-order and selection is second-order. **Every exit test we have run used the trail
unconditionally; the branch has never been tested.** It is also the one part of his system the four
selection nulls never touched.

⚠ AND IT IS NOT A LOSER-CUTTING RULE. Our exit ledger is 0-for-many, but every rule we killed conditions
on P&L (breakeven stops, profit locks, trims, "extended -> tighten"). The 21-DTE rule certified on
2026-09-23 (t +4.26) precisely because it removes exposure at a fixed, P&L-independent event. A spike rule
conditions on a MOVE. That is closer to the 21-DTE object than to a stop, which is why it is worth the pull.

DESIGN
  Pool     archetype-A breakouts (the generic pool, NOT the precision tier -- the tier does not select,
           and the pool gives the n Tito's own rarity never will), top-200 names, 2019-10 -> 2026-03.
  Vehicle  on the signal CLOSE buy the call with delta nearest 0.275 within [0.20, 0.35] and DTE nearest
           35 within [15, 75] -- his documented vehicle.
  Fills    REAL: buy the ASK, sell the BID. Never mid.
  ARM A    20-EMA trail: exit at the first daily close of the UNDERLYING below its 20 EMA.
  ARM B    conditional (the claim): exit on the first session whose underlying move >= K_SPIKE x ADR,
           otherwise the ARM A trail -- whichever comes first.
  ARM C    spike only: exit on the first spike; if none ever comes, hold to option expiry.
  All arms share a backstop: option expiry, or 60 sessions, whichever is first.
  Paired   A, B and C are the SAME trades in the same market. The comparison is within-trade.

⚠ THE TRAP IN THIS DATA, and it points at the losers. Stage 1 pulled `delta BETWEEN 0.02 AND 0.98`. A long
call that is dying falls below 0.02 delta and VANISHES from the pull -- so missing marks are concentrated
in LOSING trades, the mirror of the short-strangle case. Dropping those trades would flatter every arm.
**A contract whose path goes dark and never returns is settled at ZERO, not dropped** -- the losing
outcome, which is the conservative direction. `lib.studies.path_coverage` is wired in and BOTH conventions
are reported; if the answer moves between them there is no answer here.

PRE-REGISTERED PASS: ARM B minus ARM A, on trades where both resolve, positive with month-clustered
t >= 3 and both halves the same sign (split 2023-01-01). K_SPIKE = 2.0 ADR is the PRIMARY; the sweep over
{1.5, 2.0, 2.5, 3.0} x {single-day, cumulative-from-entry} is exploratory and carries a Sidak charge
(8 cells -> |t| >= 2.73; the house 3.0 governs).

PRIOR, stated before the data lands: ~35% that B beats A on the MEAN. Selling a spike CAPS THE RIGHT TAIL,
and on this pool the right tail is the entire edge -- so the mechanically likely outcome is that B raises
win rate and median while LOWERING the mean, a risk claim rather than a return claim, exactly as the
21-DTE rule turned out. The case for the other side is real though: a spiking call carries inflated IV and
delta, so holding it pays theta on a rich premium. If B wins the mean, the mechanism is the give-back.

Usage — NOTE the `tee`, not a pipe into `tail`:
    PYTHONPATH=src .venv/bin/python3 -u run_spike_vs_grind_exit.py 2>&1 | tee data/studies/logs/spike_grind.log

⚠ Piping this into `tail` buffers the ENTIRE run and shows nothing until it exits — a 73-minute run was
killed on 2026-09-23 with no way to tell whether it was 30% or 90% done. `tee` with `-u` streams it.
The trade table is also written to CSV BEFORE any reporting, so a crash in the stats never costs the walk.
"""
from __future__ import annotations

import pathlib
import time
import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)

from lib.studies.path_coverage import report as coverage_report
from run_precision_tier_freeze_forward import build

CHAINS = pathlib.Path("/private/tmp/claude-501/-Users-gmerton-v2-options-playground/"
                      "0dc56bae-9a64-43e3-9215-162f5d8a0c59/scratchpad/chains")
DELTA_LO, DELTA_HI, DELTA_TGT = 0.20, 0.35, 0.275
DTE_LO, DTE_HI, DTE_TGT = 15, 75, 35
HOLD_CAP = 60
K_PRIMARY = 2.0
K_SWEEP = [1.5, 2.0, 2.5, 3.0]
SPLIT = pd.Timestamp("2023-01-01")
END = pd.Timestamp("2026-03-01")
COMM = 0.65 / 100.0          # $0.65/contract, expressed per share of a 100-share contract


def load_chains() -> pd.DataFrame:
    """44M call-days: ticker as `category` and prices as float32, or the concat costs ~5GB."""
    files = sorted(CHAINS.glob("calls_*.parquet"))
    if not files:
        raise SystemExit(f"no chain files in {CHAINS} — run pull_spike_exit_chains.py first")
    cols = ["trade_date", "ticker", "strike", "expiry", "bid", "ask", "delta"]
    parts = []
    for f in files:
        d = pd.read_parquet(f, columns=cols)
        d["trade_date"] = pd.to_datetime(d["trade_date"])
        d["expiry"] = pd.to_datetime(d["expiry"])
        for c in ("strike", "bid", "ask", "delta"):
            d[c] = pd.to_numeric(d[c], errors="coerce").astype("float32")
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    # v3 is RAW (options_cache is the deduped one): ~0.5% of contract-days appear twice, with identical
    # bid/ask/OI/volume and delta differing in the 4th decimal — two snapshot passes. Prices agree, so
    # the dedupe is P&L-neutral; without it the path index has duplicate dates and lookups return Series.
    n0 = len(d)
    d = d.drop_duplicates(subset=["ticker", "expiry", "strike", "trade_date"], keep="first")
    print(f"deduped {n0 - len(d):,} duplicate contract-days ({100*(n0-len(d))/n0:.2f}%) — bid/ask identical in every case")
    d["ticker"] = d["ticker"].astype("category")
    print(f"chains: {len(d):,} call-days, {d.ticker.nunique()} names, "
          f"{d.trade_date.min().date()} -> {d.trade_date.max().date()}, "
          f"{d.memory_usage(deep=True).sum()/1e9:.2f} GB in memory")
    return d


def mt(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / (x.std(ddof=1) / sqrt(len(x)))) if len(x) > 2 else np.nan


def cell_tag(cell: tuple[float, bool]) -> str:
    """Column suffix for one (threshold, mode) cell, e.g. (2.0, False) -> 'day2p0'."""
    k, cumul = cell
    return f"{'cum' if cumul else 'day'}{str(k).replace('.', 'p')}"


CELLS = [(k, cumul) for cumul in (False, True) for k in K_SWEEP]
PRIMARY_CELL = (K_PRIMARY, False)


def build_trades(D: dict, ch: pd.DataFrame, cells: list[tuple[float, bool]], progress: int = 25) -> pd.DataFrame:
    """Walk each contract's forward path ONCE and resolve every (k, mode) cell on that single walk.

    ⚠ The first version called this per cell — nine full passes over ~3,600 events and their paths, so
    8/9 of the runtime bought exploratory cells while the PRIMARY result stayed trapped behind them. The
    path walk is the expensive part and it is identical across cells: only the *trigger date* differs.
    ARM A (trail) is cell-independent and is computed once.

    Scalar `.get()` on a pandas Series inside the inner loop was the other cost; the underlying series are
    converted to numpy once per symbol and indexed positionally, and each contract's bids become a dict.
    """
    C, E20, ADR = D["C"], D["ema20"], D["adr"]
    brk = D["brk"]
    dates = C.index
    dates_np = dates.to_numpy()
    n_dates = len(dates)
    end64 = np.datetime64(END)
    chg_adr = (C.pct_change(fill_method=None) * 100) / ADR       # today's move in ADR units

    rows, done, t0 = [], 0, time.time()
    groups = list(ch.groupby("ticker", sort=False, observed=True))
    for sym, g in groups:
        done += 1
        if done % progress == 0:
            print(f"    {done}/{len(groups)} names, {len(rows):,} trades, {time.time()-t0:.0f}s", flush=True)
        if sym not in C.columns:
            continue
        brk_col = brk[sym].reindex(dates).fillna(False).to_numpy()
        sig_pos = np.nonzero(brk_col & (dates_np <= end64))[0]
        if len(sig_pos) == 0:
            continue
        by_day = {d: x for d, x in g.groupby("trade_date", sort=False)}
        # index each contract once: a per-event linear scan over ~200k rows is ~700M comparisons overall.
        # integer strike key — float32 groupby keys do not round-trip reliably.
        g = g.assign(_sk=(g.strike.astype("float64") * 1000).round().astype("int64"))
        by_contract = {k: x.sort_values("trade_date") for k, x in g.groupby(["expiry", "_sk"], sort=False)}
        # numpy once per symbol: scalar Series.get() in the inner loop was a large share of the runtime
        c_a = C[sym].to_numpy(dtype="float64")
        e_a = E20[sym].to_numpy(dtype="float64")
        k_a = chg_adr[sym].to_numpy(dtype="float64")
        adr_a = ADR[sym].to_numpy(dtype="float64")

        for i in sig_pos:
            d0 = dates[i]
            day = by_day.get(d0)
            if day is None or day.empty:
                continue
            dte = (day["expiry"] - d0).dt.days
            cand = day[(day.delta.between(DELTA_LO, DELTA_HI)) & (dte.between(DTE_LO, DTE_HI))
                       & (day.ask > 0) & (day.bid > 0)]
            if cand.empty:
                continue
            cd = (cand["expiry"] - d0).dt.days
            cand = cand.assign(_score=(cand.delta - DELTA_TGT).abs() + (cd - DTE_TGT).abs() / 200.0)
            pick = cand.nsmallest(1, "_score").iloc[0]
            entry_px = float(pick.ask) + COMM                      # buy the ASK
            if entry_px <= 0:
                continue
            exp, strike = pick.expiry, float(pick.strike)

            full = by_contract.get((exp, int(round(strike * 1000))))
            if full is None:
                continue
            bid_of = dict(zip(full.trade_date.to_numpy(), full.bid.to_numpy()))
            exp64 = np.datetime64(exp)
            fwd_pos = [p for p in range(i + 1, min(i + HOLD_CAP, n_dates - 1) + 1) if dates_np[p] <= exp64]
            if not fwd_pos:
                continue

            base_px, adr0 = c_a[i], adr_a[i]
            ex_A = None
            ex_B = {c: None for c in cells}
            ex_C = {c: None for c in cells}
            n_marked = 0
            for p in fwd_pos:
                td = dates_np[p]
                bd = bid_of.get(td, np.nan)
                if np.isfinite(bd):
                    n_marked += 1
                proceeds = (bd - COMM) if np.isfinite(bd) else np.nan
                cp_, ep_ = c_a[p], e_a[p]
                trail_now = bool(np.isfinite(cp_) and np.isfinite(ep_) and cp_ < ep_)
                day_k = k_a[p]
                cum_k = (100 * (cp_ / base_px - 1) / adr0) if (np.isfinite(base_px) and base_px > 0
                                                               and np.isfinite(adr0) and adr0 > 0
                                                               and np.isfinite(cp_)) else np.nan
                if ex_A is None and trail_now:
                    ex_A = (td, proceeds)
                for cell in cells:
                    k, cumul = cell
                    m = cum_k if cumul else day_k
                    spike_now = bool(np.isfinite(m) and m >= k)
                    if ex_C[cell] is None and spike_now:
                        ex_C[cell] = (td, proceeds)
                    if ex_B[cell] is None and (trail_now or spike_now):
                        ex_B[cell] = (td, proceeds)
                if ex_A is not None and all(ex_B.values()) and all(ex_C.values()):
                    break

            # backstop: anything unexited settles at the last quote, or ZERO if the path went dark
            bids_all = full.bid.to_numpy()
            last_bid = float(bids_all[-1]) if len(bids_all) else np.nan
            dark = not np.isfinite(last_bid)
            fallback = (dates_np[fwd_pos[-1]], 0.0 if dark else max(last_bid - COMM, 0.0))

            rec = dict(sym=sym, entry=d0, expiry=exp, strike=strike, entry_px=entry_px,
                       delta=float(pick.delta), dte=int((exp - d0).days),
                       mark_cov=n_marked / len(fwd_pos), dark=dark)
            _, pA = ex_A if ex_A is not None else fallback
            rec["ret_A"] = (0.0 if not np.isfinite(pA) else pA) / entry_px - 1.0
            for cell in cells:
                tag = cell_tag(cell)
                for arm, store in (("B", ex_B), ("C", ex_C)):
                    _, p_ = store[cell] if store[cell] is not None else fallback
                    p_ = 0.0 if not np.isfinite(p_) else p_        # a missing mark on the exit day = dead
                    rec[f"ret_{arm}_{tag}"] = p_ / entry_px - 1.0
            rows.append(rec)

    T = pd.DataFrame(rows)
    if len(T):
        T["month"] = T.entry.dt.to_period("M")
    return T


def report(T: pd.DataFrame, cell: tuple[float, bool], label: str, primary: bool) -> dict:
    tag = cell_tag(cell)
    b, c = T[f"ret_B_{tag}"], T[f"ret_C_{tag}"]
    d = b - T.ret_A
    md = d.groupby(T["month"]).mean()
    h1, h2 = md[md.index < SPLIT.to_period("M")], md[md.index >= SPLIT.to_period("M")]
    t = mt(md)
    print(f"  {label:32s} n {len(T):>5,} | A {100*T.ret_A.mean():+7.1f}% | B {100*b.mean():+7.1f}% "
          f"| C {100*c.mean():+7.1f}% | B-A {100*d.mean():+6.1f}pp t {t:+5.2f} "
          f"| halves {100*h1.mean():+6.1f}/{100*h2.mean():+6.1f}")
    if primary:
        passed = bool(d.mean() > 0 and abs(t) >= 3 and np.sign(h1.mean()) == np.sign(h2.mean()))
        return dict(passed=passed, t=t, edge=d.mean())
    return {}


def main() -> None:
    print("building the breakout panel...", flush=True)
    D = build()
    ch = load_chains()

    print(f"\nwalking paths once, resolving all {len(CELLS)} cells on the same walk ...", flush=True)
    T = build_trades(D, ch, CELLS)
    if T.empty:
        raise SystemExit("no trades built — check chain coverage against the event dates")
    T.to_csv("data/studies/spike_vs_grind_exit_2026-09-23.csv", index=False)   # save BEFORE reporting
    print(f"\n{len(T):,} call trades · {T.sym.nunique()} names · {T.entry.min().date()} -> {T.entry.max().date()}")
    print(f"median entry delta {T.delta.median():.3f}, median DTE {T.dte.median():.0f}, "
          f"paths that went dark (settled at ZERO): {T.dark.mean():.1%}")

    coverage_report(T, cov_col="mark_cov", pnl_col="ret_A", floor=0.60,
                    label="long-call spike vs grind exit")

    tag = cell_tag(PRIMARY_CELL)
    b = T[f"ret_B_{tag}"]
    print(f"\n{'='*132}\nPRIMARY — ARM B (spike override) minus ARM A (20-EMA trail), same trades, paired\n{'='*132}")
    v = report(T, PRIMARY_CELL, f"single-day >= {K_PRIMARY} ADR", primary=True)
    c = T[f"ret_C_{tag}"]
    print(f"\n  win%   A {100*(T.ret_A>0).mean():.1f}   B {100*(b>0).mean():.1f}   C {100*(c>0).mean():.1f}")
    print(f"  median A {100*T.ret_A.median():+.1f}%  B {100*b.median():+.1f}%  C {100*c.median():+.1f}%")
    print(f"  sd     A {100*T.ret_A.std():.0f}pp  B {100*b.std():.0f}pp  C {100*c.std():.0f}pp")
    print(f"  p99    A {100*T.ret_A.quantile(.99):+.0f}%  B {100*b.quantile(.99):+.0f}%  "
          f"C {100*c.quantile(.99):+.0f}%   <- does the spike rule cap the tail that IS the edge?")
    print(f"\n  PRE-REGISTERED PASS: {'YES' if v['passed'] else 'NO'}")

    print(f"\n  ⚠ convention sensitivity — dark paths settled at ZERO (used above) vs DROPPED:")
    lit = T[~T.dark]
    print(f"     settle dark at 0: B-A {100*(b-T.ret_A).mean():+.1f}pp   |   "
          f"drop dark (n {len(lit):,}): B-A {100*(lit[f'ret_B_{tag}']-lit.ret_A).mean():+.1f}pp")

    print(f"\n{'='*132}\nEXPLORATORY sweep (Sidak over {len(CELLS)} cells -> |t| >= 2.73; house bar 3.0 governs)\n{'='*132}")
    for cell in CELLS:
        k, cumul = cell
        report(T, cell, f"{'cumulative' if cumul else 'single-day'} >= {k} ADR", primary=False)

    print("\nwrote data/studies/spike_vs_grind_exit_2026-09-23.csv")


if __name__ == "__main__":
    main()
