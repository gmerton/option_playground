#!/usr/bin/env python3
"""
Test calculator.py's pre-earnings volatility gates against the 4,477-event set.

`~/Downloads/.../trade calculator/calculator.py` (Feb 2025) is a live GUI screener with no backtest
in it. It gates an earnings play on three things, thresholds hardcoded from a video with no stated
derivation:

    avg_volume     >= 1_500_000          liquidity floor, 30d mean
    iv30_rv30      >= 1.25               spline IV at 30d / Yang-Zhang RV30 -- is IV rich vs movement
    ts_slope_0_45  <= -0.00406           slope of the ATM IV term structure, front expiry -> 45d
                                         (negative = backwardation, the front is richest)

Both vol gates are refined versions of the richness idea that earnings_vol_premium_2026-09-20.md
already tested crudely: the premium sorts monotonically on implied-move size at MID, and INVERTS at
the bid because rich events carry wide spreads. These gates might sort better -- iv30/rv30 compares
IV to actual movement rather than to nothing, and the slope is a different axis entirely.

`yang_zhang` and `build_term_structure` are reimplemented exactly as the script has them, including
the spline's endpoint clamping.

Everything is scored the way the premium study was: short ATM straddle into the print, % of spot, at
MID and at the BID, since the bid is what decided the unconditional version.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_earnings_gates_test.py \
           > data/studies/earnings_gates_2026-09-20.log
"""
from __future__ import annotations
import os, uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
from scipy.interpolate import interp1d
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX

CACHE = "data/cache/earnings_term_structure.parquet"


def yang_zhang(px: pd.DataFrame, window=30, trading_periods=252):
    """Verbatim from calculator.py."""
    log_ho = np.log(px.High / px.Open); log_lo = np.log(px.Low / px.Open)
    log_co = np.log(px.Close / px.Open)
    log_oc_sq = np.log(px.Open / px.Close.shift(1)) ** 2
    log_cc_sq = np.log(px.Close / px.Close.shift(1)) ** 2
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    cv = log_cc_sq.rolling(window).sum() * (1.0 / (window - 1.0))
    ov = log_oc_sq.rolling(window).sum() * (1.0 / (window - 1.0))
    wrs = rs.rolling(window).sum() * (1.0 / (window - 1.0))
    k = 0.34 / (1.34 + ((window + 1) / (window - 1)))
    return np.sqrt(ov + k * cv + (1 - k) * wrs) * np.sqrt(trading_periods)


def term_spline(days, ivs):
    """Verbatim from calculator.py, including the endpoint clamping."""
    days, ivs = np.array(days, float), np.array(ivs, float)
    o = days.argsort(); days, ivs = days[o], ivs[o]
    sp = interp1d(days, ivs, kind="linear", fill_value="extrapolate")
    def f(dte):
        if dte < days[0]: return float(ivs[0])
        if dte > days[-1]: return float(ivs[-1])
        return float(sp(dte))
    return f, days


def pull(ev):
    if os.path.exists(CACHE):
        t = pd.read_parquet(CACHE); print(f"  term structure from cache: {len(t):,} rows"); return t
    k = ev[["row_id", "ticker", "pre_date"]].copy(); k["pre_date"] = k.pre_date.dt.date
    _ensure_glue_db(DB)
    name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy",
                     mode="overwrite", dtype={"row_id": "bigint", "ticker": "string", "pre_date": "date"})
    try:
        t = athena(f"""
          SELECT t.row_id, o.expiry, o.strike, o.cp, o.delta, o.bid_iv, o.ask_iv
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
          JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
            ON o.ticker = t.ticker AND o.trade_date = t.pre_date
          WHERE o.expiry > t.pre_date AND date_diff('day', t.pre_date, o.expiry) <= 90
            AND o.delta IS NOT NULL AND abs(o.delta) BETWEEN 0.40 AND 0.60
            AND o.bid_iv > 0 AND o.ask_iv > 0 AND o.ask_iv < 5""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    t.to_parquet(CACHE, index=False); print(f"  pulled {len(t):,} rows -> {CACHE}")
    return t


def main():
    d = pd.read_parquet("data/cache/earnings_vol_events.parquet")
    c = pd.read_parquet("data/cache/earnings_vol_chains.parquet"); c["expiry"] = pd.to_datetime(c.expiry)
    k = d[["row_id", "K", "front"]].merge(c, left_on=["row_id", "K", "front"],
                                          right_on=["row_id", "strike", "expiry"])
    w = k.pivot_table(index="row_id", columns="cp", values=["bid", "ask"], aggfunc="last")
    w.columns = [f"{a}_{b.lower()}" for a, b in w.columns]
    d = d.merge(w.reset_index(), on="row_id", how="left").dropna(subset=["bid_c", "ask_c", "bid_p", "ask_p"])
    d["s_bid"] = d.bid_c + d.bid_p; d["s_mid"] = (d.s_bid + d.ask_c + d.ask_p) / 2
    d["pnl_mid"] = 100 * (d.s_mid - d.payoff) / d.spot_raw
    d["pnl_bid"] = 100 * (d.s_bid - d.payoff) / d.spot_raw
    print(f"{len(d):,} events with straddle marks")

    T = pull(d)
    T["expiry"] = pd.to_datetime(T.expiry); T["iv"] = (T.bid_iv + T.ask_iv) / 2
    T["datm"] = (T.delta.abs() - 0.5).abs()
    # ATM IV per (event, expiry) = mean of the call and put nearest 0.50 delta
    leg = T.loc[T.groupby(["row_id", "expiry", "cp"]).datm.idxmin()]
    atm = leg.groupby(["row_id", "expiry"]).iv.mean().reset_index()
    atm = atm.merge(d[["row_id", "pre_date"]], on="row_id")
    atm["dte"] = (atm.expiry - atm.pre_date).dt.days
    atm = atm[atm.dte > 0]
    n_exp = atm.groupby("row_id").size()
    keep = n_exp[n_exp >= 3].index            # a spline needs a few points to mean anything
    atm = atm[atm.row_id.isin(keep)]
    print(f"  term structure on {atm.row_id.nunique():,} events (>=3 expiries)")

    rows = []
    for rid, g in atm.groupby("row_id"):
        f, days = term_spline(g.dte.values, g.iv.values)
        rows.append(dict(row_id=rid, iv30=f(30),
                         ts_slope=(f(45) - f(days[0])) / (45 - days[0]) if days[0] != 45 else np.nan,
                         front_dte=days[0], n_exp=len(g)))
    TS = pd.DataFrame(rows)
    d = d.merge(TS, on="row_id")

    # Yang-Zhang RV30 and 30d average volume as of the pre-print session, from the panel
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    raw["date"] = pd.to_datetime(raw.date)
    yz, av = {}, {}
    for tk, g in raw.groupby("ticker"):
        g = g.sort_values("date").set_index("date")
        px = g.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})
        yz[tk] = yang_zhang(px); av[tk] = g.volume.rolling(30).mean()
    d["rv30"] = [yz[r.ticker].get(r.pre_date, np.nan) for r in d.itertuples()]
    d["avg_volume"] = [av[r.ticker].get(r.pre_date, np.nan) for r in d.itertuples()]
    d["iv30_rv30"] = d.iv30 / d.rv30
    d = d.dropna(subset=["iv30_rv30", "ts_slope", "avg_volume"])
    print(f"  fully scored: {len(d):,} events, {d.ticker.nunique()} names\n")
    d.to_parquet("data/cache/earnings_gates.parquet", index=False)

    print("=" * 104)
    print("  calculator.py GATES vs the short-straddle premium (% of spot)")
    print("=" * 104)
    G = {"avg_volume >= 1.5M": d.avg_volume >= 1_500_000,
         "iv30_rv30 >= 1.25": d.iv30_rv30 >= 1.25,
         "ts_slope <= -0.00406": d.ts_slope <= -0.00406}
    G["ALL THREE (the recommendation)"] = G["avg_volume >= 1.5M"] & G["iv30_rv30 >= 1.25"] & G["ts_slope <= -0.00406"]
    base_m, base_b = d.pnl_mid.mean(), d.pnl_bid.mean()
    print(f"  {'gate':<34}{'n':>7}{'share':>8}{'MID':>9}{'vs base':>9}{'BID':>9}{'vs base':>9}{'win(bid)':>10}")
    print(f"  {'-- no gate (baseline) --':<34}{len(d):>7,}{'100%':>8}{base_m:>+9.3f}{'':>9}{base_b:>+9.3f}{'':>9}{100*(d.pnl_bid>0).mean():>9.1f}%")
    for lab, m in G.items():
        x = d[m]
        if len(x) < 60: print(f"  {lab:<34}{len(x):>7,}  too thin"); continue
        print(f"  {lab:<34}{len(x):>7,}{100*m.mean():>7.0f}%{x.pnl_mid.mean():>+9.3f}{x.pnl_mid.mean()-base_m:>+9.3f}"
              f"{x.pnl_bid.mean():>+9.3f}{x.pnl_bid.mean()-base_b:>+9.3f}{100*(x.pnl_bid>0).mean():>9.1f}%")

    print("\n  quintiles of each continuous variable (mean premium, % of spot):")
    for lab, col in (("iv30_rv30", "iv30_rv30"), ("ts_slope_0_45", "ts_slope"), ("avg_volume", "avg_volume")):
        q = pd.qcut(d[col], 5, duplicates="drop")
        t = d.groupby(q).agg(n=("pnl_mid", "size"), MID=("pnl_mid", "mean"), BID=("pnl_bid", "mean")).round(3)
        print(f"\n--- {lab} ---"); print(t.to_string())


if __name__ == "__main__":
    main()
