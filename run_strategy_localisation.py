#!/usr/bin/env python3
"""
[WL-2b] Strategy localisation: do strategies have PREDICTABLE good stretches? (pre-registered 2026-09-23)

Gabe: "it's possible that Strategy A is good for one 6-month stretch and Strategy B for another. If that's true, it
might be incorrect to treat all occurrences of a strategy over a 10-year stretch as equal."
Pooling is the right number only if the good stretches can't be identified in advance. This asks whether they can.

STRATEGIES (one representative per family; per-trade logs already on disk, no re-simulation):
  equity (harness trade tables, arm = ema20, the house exit; R units): precision-tier breakout (close, hold 60), all
  breakouts (close, hold 60), counter-trend long (>=3 ADR + prior-bar-high break), earnings drift good+MUTED, in-play up
  mover, in-play down mover (short), bouncy ball (short), boring stock violent move (4x), VCP damped sine N3, Kell wedge
  pop, DR-EP catalyst+retrace, reclaim (pb >= 1 ADR, wait <= 10).
  options (% return on risk/credit, net where the log has it): Tier A/B cells (SPY bull put Bearish_HighIV, QQQ bull put
  x4 cells, SPX condor x2), the 13 Tier C screener spreads, SPY 1-day iron fly (2x wings, all days), ETF 7-DTE long
  straddle, UVXY combined, ETF 45-DTE put-spread roster.
MONTHLY SERIES: mean return of trades ENTERED that month; months with < 3 trades are missing. A strategy needs >= 24
valid months.
NO LOOK-AHEAD: holds run up to ~60 sessions, so at month t the "trailing 6 months" = entry months t-8 .. t-3.

TESTS
 1 PRIMARY (localisation persistence): pooled Spearman over (strategy, month) of the strategy-DEMEANED trailing score
   vs the strategy-demeaned month-t return (both scaled by the strategy's own std). Null: shuffle each strategy's
   months (destroys time structure, keeps its distribution), recompute. 2,000 perms. p < 0.003 -> localisation is
   predictable from its own recent history.
 2 Rotation: each month from 2021-01, hold the top 3 strategies by trailing score (in each strategy's expanding-std
   units, known at t) vs equal weight over all strategies with a score. Metric = mean monthly difference (std units),
   t over months. In-sample 2021-2023, held-out 2024+ (PRIMARY for this test). Null: random 3 each month.
 3 Regime sweep (false-negative sweep of the nulls): each strategy's month-t return by observable state at the prior
   month end: VIX tercile (expanding) x SPY above/below its 200-day SMA = 6 cells. Statistic = max |t| over strategy x
   cell of (cell mean - strategy mean). Null: shuffle the state labels across months (same for all strategies,
   keeps the cross-section). Any cell with p_max < 0.003 is reported as a regime-specific candidate.
Priors: low for 1-2 (21-day persistence was nil: trailing_regime_validation.md; breakout paying months unforecastable),
moderate for 3 (the GEX fly and the certified put sale are regime results).

Run: PYTHONPATH=src .venv/bin/python3 run_strategy_localisation.py  (log -> data/studies/logs/strategy_localisation.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent
C = REPO / "data/cache"
ST = REPO / "data/studies"
LOG = ST / "logs/strategy_localisation.log"
PERMS, P_BAR, MIN_MONTHS, LAG, WIN = 2000, 0.003, 24, 3, 6
RNG = np.random.default_rng(20260923)

HARNESS = {
    "EQ precision-tier breakout": "precision-tier_breakout_(house),_close_entry,_hold_60",
    "EQ all breakouts": "all_breakouts_(generic_pool),_close_entry,_hold_60",
    "EQ counter-trend long": "counter-trend_long:_>=3_adr_below_20_ema_+_prior-bar-high_break",
    "EQ earnings drift good+muted": "earnings_drift,_good+muted",
    "EQ in-play up mover": "in-play_up_mover_(+4%_on_2x_vol)",
    "EQ in-play down mover (short)": "in-play_down_mover_(-4%_on_2x_vol)",
    "EQ bouncy ball (short)": "bouncy_ball_(breitstein_short)",
    "EQ boring stock violent move": "boring_stock,_violent_move_(drop_>=_4x_own_adr,_adr_bottom_tercile)",
    "EQ VCP damped sine": "vcp_damped_sine_n3",
    "EQ Kell wedge pop": "kell_wedge_pop",
    "EQ DR-EP catalyst+retrace": "dr-ep_2026-09-22:_b_dr-ep_catalyst+retrace_[post]",
    "EQ reclaim": "b_reclaim_|_pb>=1.0adr_wait<=10d",
}


def trades() -> dict[str, pd.DataFrame]:
    out = {}
    for k, f in HARNESS.items():
        d = pd.read_parquet(C / f"pattern_{f}_daily.parquet")
        out[k] = pd.DataFrame({"date": pd.to_datetime(d.date), "ret": d.ema20})
    ab = pd.read_csv(ST / "tierab_trades_2026-09-22.csv")
    for cell, g in ab.groupby("cell"):
        out[f"OPT {cell}"] = pd.DataFrame({"date": pd.to_datetime(g.entry), "ret": g.roc_net})
    tc = pd.read_csv(ST / "tierc_trades_2026-09-22.csv")
    for s, g in tc.groupby("strategy"):
        out[f"OPT {s}"] = pd.DataFrame({"date": pd.to_datetime(g.entry), "ret": g.roc_net})
    fly = pd.read_csv(ST / "gex_spy_ironfly_2026-09-21.csv")
    fly = fly[fly.w == 2.0]
    out["OPT SPY 1-day iron fly (all days)"] = pd.DataFrame({"date": pd.to_datetime(fly.day), "ret": fly.ret_risk})
    sd = pd.read_csv(ST / "straddle_trades.csv")
    out["OPT ETF 7-DTE long straddle"] = pd.DataFrame({"date": pd.to_datetime(sd.edate), "ret": sd.roc})
    ux = pd.read_csv(ST / "uvxy_significance_trades_2026-09-22.csv")
    out["OPT UVXY combined"] = pd.DataFrame({"date": pd.to_datetime(ux.entry_date), "ret": ux.comb_net})
    ep = pd.read_csv(ST / "etf_put_spread_trades.csv")
    out["OPT ETF 45-DTE put-spread roster"] = pd.DataFrame({"date": pd.to_datetime(ep.entry), "ret": ep.roc_hold})
    return out


def monthly(tr: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = {}
    for k, d in tr.items():
        d = d.dropna()
        g = d.groupby(d.date.dt.to_period("M")).ret
        m = g.mean().where(g.size() >= 3)
        if m.notna().sum() >= MIN_MONTHS:
            cols[k] = m
    M = pd.DataFrame(cols).sort_index()
    M.index = M.index.to_timestamp()
    return M.asfreq("MS")


def trailing(M: pd.DataFrame) -> pd.DataFrame:
    """Score at month t = mean of months t-8 .. t-3 (needs >= 3 valid)."""
    s = M.shift(LAG).rolling(WIN, min_periods=3).mean()
    return s


def z_by_strategy(M: pd.DataFrame) -> pd.DataFrame:
    return (M - M.mean()) / M.std()


def persistence(M: pd.DataFrame) -> tuple[float, float, np.ndarray]:
    def stat(MM):
        Z = z_by_strategy(MM)
        S = trailing(Z)
        x, y = S.values.ravel(), Z.values.ravel()
        ok = np.isfinite(x) & np.isfinite(y)
        return stats.spearmanr(x[ok], y[ok]).statistic
    obs = stat(M)
    null = np.empty(PERMS)
    for p in range(PERMS):
        MM = M.copy()
        for c in MM.columns:
            v = MM[c].values
            idx = np.flatnonzero(np.isfinite(v))
            v2 = v.copy()
            v2[idx] = v[RNG.permutation(idx)]
            MM[c] = v2
        null[p] = stat(MM)
    p_two = (np.sum(np.abs(null) >= abs(obs)) + 1) / (PERMS + 1)
    return obs, p_two, null


def per_strategy_persistence(M: pd.DataFrame) -> pd.DataFrame:
    Z = z_by_strategy(M)
    S = trailing(Z)
    rows = []
    for c in M.columns:
        ok = S[c].notna() & Z[c].notna()
        if ok.sum() >= 12:
            r = stats.spearmanr(S[c][ok], Z[c][ok]).statistic
            rows.append(dict(strategy=c, months=int(M[c].notna().sum()), paired=int(ok.sum()), rho=r))
    return pd.DataFrame(rows).sort_values("rho")


def rotation(M: pd.DataFrame, k: int = 3) -> dict:
    sd = M.expanding(min_periods=12).std().shift(1)            # scale known at t
    Zt = M / sd
    S = trailing(M) / sd
    start = pd.Timestamp("2021-01-01")
    diffs, rand = {}, []
    months = [t for t in M.index if t >= start]
    for t in months:
        s, z = S.loc[t], Zt.loc[t]
        ok = s.notna() & z.notna()
        if ok.sum() < k + 3:
            continue
        top = s[ok].nlargest(k).index
        diffs[t] = z[top].mean() - z[ok].mean()
    D = pd.Series(diffs)
    out = {}
    for lab, sub in (("in-sample 2021-2023", D[D.index < "2024-01-01"]), ("HELD-OUT 2024+", D[D.index >= "2024-01-01"])):
        t = sub.mean() / sub.std(ddof=1) * np.sqrt(len(sub)) if len(sub) > 2 else np.nan
        out[lab] = dict(months=len(sub), mean_diff=sub.mean(), t=t, hit=(sub > 0).mean())
    # null for the held-out window: random k each month
    null = []
    ho = [t for t in D.index if t >= pd.Timestamp("2024-01-01")]
    for _ in range(PERMS):
        v = []
        for t in ho:
            s, z = S.loc[t], Zt.loc[t]
            ok = (s.notna() & z.notna()).values
            names = M.columns[ok]
            pick = RNG.choice(names, k, replace=False)
            v.append(z[pick].mean() - z[names].mean())
        null.append(np.mean(v))
    null = np.array(null)
    obs = out["HELD-OUT 2024+"]["mean_diff"]
    out["p_heldout"] = (np.sum(null >= obs) + 1) / (PERMS + 1)
    out["_D"] = D
    return out


def state_labels(index: pd.DatetimeIndex) -> pd.Series:
    import yfinance as yf
    px = yf.download(["SPY", "^VIX"], start="2009-01-01", progress=False, auto_adjust=True)["Close"]
    spy, vix = px["SPY"].dropna(), px["^VIX"].dropna()
    trend = (spy > spy.rolling(200).mean()).resample("ME").last()
    v = vix.resample("ME").last()
    terc = v.expanding(min_periods=24).apply(lambda s: int(s.iloc[-1] > s.quantile(1 / 3)) + int(s.iloc[-1] > s.quantile(2 / 3)), raw=False)
    lab = (terc.map({0: "VIXlo", 1: "VIXmid", 2: "VIXhi"}) + "|" + trend.map({True: "SPY>200", False: "SPY<200"}))
    lab.index = (lab.index + pd.offsets.MonthBegin(1))           # state at prior month end -> label for month t
    return lab.reindex(index)


def regime_sweep(M: pd.DataFrame, lab: pd.Series) -> tuple[pd.DataFrame, float, float, np.ndarray]:
    Z = z_by_strategy(M)

    def table(L):
        rows = []
        for c in Z.columns:
            z = Z[c]
            for cell in sorted(L.dropna().unique()):
                x = z[(L == cell) & z.notna()]
                if len(x) >= 6:
                    rest = z[(L != cell) & L.notna() & z.notna()]
                    t = (x.mean() - rest.mean()) / np.sqrt(x.var(ddof=1) / len(x) + rest.var(ddof=1) / len(rest))
                    rows.append(dict(strategy=c, cell=cell, n=len(x), cell_z=x.mean(), rest_z=rest.mean(), t=t))
        return pd.DataFrame(rows)
    T = table(lab)
    obs = T.t.abs().max()
    null = np.empty(PERMS)
    ok = lab.notna().values
    for p in range(PERMS):
        L = lab.copy()
        vals = L.values.copy()
        vals[ok] = vals[ok][RNG.permutation(ok.sum())]
        null[p] = table(pd.Series(vals, index=lab.index)).t.abs().max()
    p_max = (np.sum(null >= obs) + 1) / (PERMS + 1)
    return T.sort_values("t", key=np.abs, ascending=False), obs, p_max, null


def main():
    tr = trades()
    M = monthly(tr)
    print(f"# Strategy localisation [WL-2b] -- {M.shape[1]} strategies with >= {MIN_MONTHS} months "
          f"({M.index.min().date()} -> {M.index.max().date()})")
    print(M.notna().sum().sort_values().to_string())
    print("\n## 1. PRIMARY: localisation persistence (trailing t-8..t-3 vs month t, strategy-demeaned, pooled Spearman)")
    obs, p, null = persistence(M)
    print(f"rho {obs:+.4f} | two-sided permutation p {p:.4f} | null rho p2.5/p97.5 {np.quantile(null, .025):+.4f} / "
          f"{np.quantile(null, .975):+.4f}")
    print("\nper strategy (descriptive, no verdict of its own):")
    print(per_strategy_persistence(M).round(3).to_string(index=False))
    print("\n## 2. Rotation: top 3 by trailing score vs equal weight (strategy-std units)")
    R = rotation(M)
    for k in ("in-sample 2021-2023", "HELD-OUT 2024+"):
        r = R[k]
        print(f"{k:22s} months {r['months']:3d} | mean diff {r['mean_diff']:+.3f} sd-units | t {r['t']:+.2f} | "
              f"top-3 beat EW in {r['hit']:.0%} of months")
    print(f"held-out p vs random-3 null: {R['p_heldout']:.4f}")
    print("\n## 3. Regime sweep: VIX tercile x SPY vs 200d SMA (state at prior month end)")
    lab = state_labels(M.index)
    print(lab.value_counts().to_string())
    T, tmax, pmax, nullt = regime_sweep(M, lab)
    print(f"\nmax |t| over {len(T)} strategy x cell tests: {tmax:.2f} | permutation p_max {pmax:.4f} "
          f"(null max|t| p50 {np.median(nullt):.2f}, p99 {np.quantile(nullt, .99):.2f})")
    print("\ntop 20 cells by |t|:")
    print(T.head(20).round(3).to_string(index=False))
    thr = np.quantile(nullt, 1 - P_BAR)
    print(f"\ncells clearing the family-wise |t| threshold {thr:.2f} (p < {P_BAR}): "
          f"{int((T.t.abs() >= thr).sum())}")
    print(T[T.t.abs() >= thr].round(3).to_string(index=False))
    M.to_csv(ST / "strategy_localisation_monthly_2026-09-23.csv")
    T.to_csv(ST / "strategy_localisation_regime_cells_2026-09-23.csv", index=False)
    return obs, p, R, tmax, pmax, T, thr


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
