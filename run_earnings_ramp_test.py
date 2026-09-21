#!/usr/bin/env python3
"""
The pre-earnings volatility RAMP -- src/lib/earnings/earnings.py (2025-10-12), modernised and scaled.

The old script bought an ATM strangle N business days before a print and sold it ON the pre-print
session, never holding through the event. It ran on one ticker (AXP), read options_daily_v2, and its
own ToDo flagged the BMO/AMC gap. This runs the same trade across the 4,477-event set on v3, with the
report hour known so the exit is the last clean session BEFORE the print (BMO -> prior session).

Why it is the last open earnings idea: every other expression tested today held through the print
and paid the spread on a quote the print had just blown out. The ramp harvests the IV run-up and is
out before the event -- but it crosses the spread TWICE (buy in, sell out) and pays theta the whole
way, so the question is whether the vega gain clears both.

Faithful to the old script: the strike is the ATM pair at ENTRY (call/put mids closest), the expiry
is the first after the print, and the SAME contracts are priced at exit. Three fills: mid, a patient
limit (mid +/- 25% of spread), and crossing (buy the ask, sell the bid). The IV ramp itself is
reported alongside as the mechanism, independent of P&L.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_earnings_ramp_test.py \
           > data/studies/earnings_ramp_2026-09-20.log
"""
from __future__ import annotations
import os, uuid, warnings
import numpy as np, pandas as pd, awswrangler as wr
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX

CACHE = "data/cache/earnings_ramp_chains.parquet"
LOOKBACKS = (3, 5, 10)          # business days before the pre-print session


def main():
    d = pd.read_parquet("data/cache/earnings_gates.parquet")[["row_id", "ticker", "pre_date", "front", "spot_raw", "avg_volume"]]
    d["pre_date"] = pd.to_datetime(d.pre_date); d["front"] = pd.to_datetime(d.front)
    idx = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet("data/cache/liquid_panel_2019.parquet").date.unique())).sort_values()
    pos = idx.searchsorted(d.pre_date.values)
    for n in LOOKBACKS:
        p = pos - n
        d[f"e{n}"] = np.where(p >= 0, idx[np.clip(p, 0, len(idx) - 1)], pd.NaT)
    d = d.dropna(subset=[f"e{n}" for n in LOOKBACKS])
    for n in LOOKBACKS: d[f"e{n}"] = pd.to_datetime(d[f"e{n}"])   # np.where left these as object
    print(f"{len(d):,} events | entry dates {', '.join(f'-{n}bd' for n in LOOKBACKS)} before the pre-print session")

    if os.path.exists(CACHE):
        c = pd.read_parquet(CACHE); print(f"  chains from cache: {len(c):,} rows")
    else:
        k = d[["row_id", "ticker", "front", "pre_date"] + [f"e{n}" for n in LOOKBACKS]].copy()
        for col in k.columns[2:]: k[col] = pd.to_datetime(k[col]).dt.date
        _ensure_glue_db(DB); name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
        wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy", mode="overwrite",
                         dtype={"row_id": "bigint", "ticker": "string", "front": "date", "pre_date": "date",
                                **{f"e{n}": "date" for n in LOOKBACKS}})
        dates = " OR ".join([f"o.trade_date = t.e{n}" for n in LOOKBACKS] + ["o.trade_date = t.pre_date"])
        try:
            c = athena(f"""SELECT t.row_id, o.trade_date, o.strike, o.cp, o.bid, o.ask, o.delta, o.bid_iv, o.ask_iv
              FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
                ON o.ticker = t.ticker AND o.expiry = t.front AND ({dates})
              WHERE o.delta IS NOT NULL AND abs(o.delta) BETWEEN 0.25 AND 0.75
                AND o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999 AND o.ask >= o.bid""")
        finally: _drop_temp_targets_table(DB, name, path)
        c.to_parquet(CACHE, index=False); print(f"  pulled {len(c):,} rows -> {CACHE}")
    c["trade_date"] = pd.to_datetime(c.trade_date); c["mid"] = (c.bid + c.ask) / 2; c["iv"] = (c.bid_iv + c.ask_iv) / 2
    W = c.pivot_table(index=["row_id", "trade_date", "strike"], columns="cp",
                      values=["bid", "ask", "mid", "iv"], aggfunc="last").reset_index()
    W.columns = [f"{a}_{b}" if b else a for a, b in W.columns]
    W = W.dropna(subset=["mid_C", "mid_P"])

    out = []
    for n in LOOKBACKS:
        e = d[["row_id", f"e{n}", "pre_date", "spot_raw", "avg_volume", "ticker"]].rename(columns={f"e{n}": "entry"})
        # ATM at ENTRY: the strike whose call and put mids are closest (the old script's nearest-to-spot pair)
        En = W.merge(e[["row_id", "entry"]], left_on=["row_id", "trade_date"], right_on=["row_id", "entry"])
        En["gap"] = (En.mid_C - En.mid_P).abs()
        En = En.loc[En.groupby("row_id").gap.idxmin()]
        # the SAME strike at EXIT (pre-print session)
        Ex = W.merge(e[["row_id", "pre_date"]], left_on=["row_id", "trade_date"], right_on=["row_id", "pre_date"])
        m = En.merge(Ex, on=["row_id", "strike"], suffixes=("_in", "_out")).merge(
            e[["row_id", "spot_raw", "avg_volume", "ticker"]], on="row_id")   # entry/pre_date already carried by En/Ex
        m = m[m.entry < m.pre_date]
        cost_mid = m.mid_C_in + m.mid_P_in; val_mid = m.mid_C_out + m.mid_P_out
        cost_ask = m.ask_C_in + m.ask_P_in; val_bid = m.bid_C_out + m.bid_P_out
        sp_in = cost_ask - (m.bid_C_in + m.bid_P_in); sp_out = (m.ask_C_out + m.ask_P_out) - val_bid
        cost_lim = cost_mid + 0.25 * sp_in; val_lim = val_mid - 0.25 * sp_out
        ok = cost_mid > 0.05
        r = pd.DataFrame({"row_id": m.row_id, "n": n, "yr": m.pre_date.dt.year, "date": m.pre_date,
                          "avg_volume": m.avg_volume, "spot": m.spot_raw, "cost": cost_mid,
                          "pct_mid": 100 * (val_mid / cost_mid - 1), "pct_lim": 100 * (val_lim / cost_lim - 1),
                          "pct_real": 100 * (val_bid / cost_ask - 1),
                          "spot_mid": 100 * (val_mid - cost_mid) / m.spot_raw, "spot_real": 100 * (val_bid - cost_ask) / m.spot_raw,
                          "iv_in": (m.iv_C_in + m.iv_P_in) / 2, "iv_out": (m.iv_C_out + m.iv_P_out) / 2,
                          "rt_spread_pct": 100 * (sp_in + sp_out) / cost_mid})[ok]
        out.append(r)
    R = pd.concat(out, ignore_index=True); R.to_parquet("data/cache/earnings_ramp.parquet", index=False)

    def t_day(s, dates):
        g = s.groupby(dates).mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))
    print("\n" + "=" * 112)
    print("  PRE-EARNINGS RAMP: buy the ATM straddle N business days out, sell it on the pre-print session (% of cost)")
    print("=" * 112)
    print(f"  {'entry':<8}{'n':>6}{'IV in->out':>14}{'ramp vp':>9}{'MID':>8}{'LIMIT':>8}{'CROSS':>8}{'t(lim)':>8}{'win(lim)':>9}{'rt spread':>11}  neg yrs (lim)")
    for n in LOOKBACKS:
        x = R[R.n == n]; yr = x.groupby("yr").pct_lim.mean()
        print(f"  -{n}bd{'':<4}{len(x):>6,}{x.iv_in.mean():>7.3f}->{x.iv_out.mean():<5.3f}{100*(x.iv_out-x.iv_in).mean():>+8.1f}"
              f"{x.pct_mid.mean():>+8.2f}{x.pct_lim.mean():>+8.2f}{x.pct_real.mean():>+8.2f}{t_day(x.pct_lim, x.date):>+8.2f}"
              f"{100*(x.pct_lim>0).mean():>8.1f}%{x.rt_spread_pct.median():>10.1f}%  {int((yr<0).sum())}/{len(yr)}")
    print("\n  IV ramp = ATM implied vol on the pre-print session minus at entry, in vol points (the mechanism).")
    print("  rt spread = round-trip bid/ask as % of the mid straddle cost (median). Theta is inside the MID number.")

    print("\n" + "=" * 112); print("  LIQUIDITY SPLIT (the review's check), -5bd entry, % of cost"); print("=" * 112)
    x = R[R.n == 5]; q = pd.qcut(x.avg_volume, 5, labels=["q1", "q2", "q3", "q4", "q5"])
    print(f"  {'cell':<26}{'n':>6}{'MID':>8}{'LIMIT':>8}{'CROSS':>8}{'t(lim)':>8}{'rt spread':>11}  neg yrs")
    for lab, msk in (("ALL", np.ones(len(x), bool)), ("volume q5", (q == "q5").values), ("volume top 40%", q.isin(["q4", "q5"]).values),
                     ("avg_volume >= 5M", (x.avg_volume >= 5e6).values)):
        y = x[msk]; yr = y.groupby("yr").pct_lim.mean()
        print(f"  {lab:<26}{len(y):>6,}{y.pct_mid.mean():>+8.2f}{y.pct_lim.mean():>+8.2f}{y.pct_real.mean():>+8.2f}"
              f"{t_day(y.pct_lim, y.date):>+8.2f}{y.rt_spread_pct.median():>10.1f}%  {int((yr<0).sum())}/{len(yr)}")
    print("\n  by year, -5bd, LIMIT fill:", x.groupby("yr").pct_lim.mean().round(1).to_dict())


if __name__ == "__main__":
    main()
