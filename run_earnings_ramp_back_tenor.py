#!/usr/bin/env python3
"""Pre-earnings IV ramp on a 30-45 DTE ATM straddle, vs same-date no-earnings controls (2026-09-30).

PRE-REGISTERED: data/studies/earnings_ramp_back_tenor_2026-09-30.md (committed a24ea22 before this script existed).
The parent (run_earnings_ramp_test.py) used the FRONT expiry and lost to theta; this is its named follow-up.
Implements the spec; must not be tuned against its own output.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_earnings_ramp_back_tenor.py \
           > data/studies/logs/earnings_ramp_back_tenor.log
"""
from __future__ import annotations

import os
import uuid
import warnings

import awswrangler as wr
import numpy as np
import pandas as pd

from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
from lib.studies.costs import COMMISSION_PER_LEG, SLIPPAGE_FRAC

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
CACHE = "data/cache/earnings_ramp_back_tenor_chains.parquet"
LOOKBACKS = (3, 5, 10)
PRIMARY = 5
N_CTRL = 3
DOLVOL_MIN = 50e6
SPLIT = pd.Timestamp("2023-01-01")
RNG = np.random.default_rng(20260930)


def build_events():
    p = pd.read_parquet("data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "dolvol"])
    p["date"] = pd.to_datetime(p.date)
    dv = p.pivot_table(index="date", columns="ticker", values="dolvol").sort_index()
    dv20 = dv.rolling(20, min_periods=15).mean().shift(1)             # known before the entry close
    idx = dv.index
    e = pd.read_parquet("data/cache/earnings_yf.parquet")
    e = e[e.ticker.isin(dv.columns) & e.timing.isin(["BMO", "AMC"])].copy()
    e["session"] = pd.to_datetime(e.session)
    e = e[(e.session >= "2019-02-01") & (e.session <= "2026-02-27")].drop_duplicates(["ticker", "session"])
    pos = idx.searchsorted(e.session.values)                          # index of the report session (or next)
    on_day = (pos < len(idx)) & (idx[np.clip(pos, 0, len(idx) - 1)] == e.session.values)
    e = e[on_day]; pos = pos[on_day]
    ppos = np.where(e.timing == "AMC", pos, pos - 1)
    e["P"] = idx[ppos]
    for n in LOOKBACKS:
        e[f"E{n}"] = np.where(ppos - n >= 0, idx[np.clip(ppos - n, 0, None)], pd.NaT)
    e = e.dropna(subset=[f"E{n}" for n in LOOKBACKS])
    for n in LOOKBACKS:
        e[f"E{n}"] = pd.to_datetime(e[f"E{n}"])
    e["dv20"] = [dv20.at[d, t] for d, t in zip(e[f"E{PRIMARY}"], e.ticker)]
    e = e[e.dv20 >= DOLVOL_MIN].reset_index(drop=True)
    e["row_id"] = np.arange(len(e))

    # controls: same E5 and P, dv20 >= min, no report in [E5, E5 + 45 calendar days]
    rep = pd.read_parquet("data/cache/earnings_yf.parquet", columns=["ticker", "session"])
    rep["session"] = pd.to_datetime(rep.session)
    rep_by = rep.groupby("ticker").session.apply(lambda s: np.sort(s.values)).to_dict()
    ctrl = []
    for r in e.itertuples():
        E = getattr(r, f"E{PRIMARY}")
        row = dv20.loc[E]
        cands = row[row >= DOLVOL_MIN].index.difference([r.ticker]).values
        RNG.shuffle(cands)
        got = 0
        for t in cands:
            s = rep_by.get(t)
            if s is None:
                continue
            i = np.searchsorted(s, np.datetime64(E))
            if i < len(s) and s[i] <= np.datetime64(E + pd.Timedelta(days=45)):
                continue
            ctrl.append((r.row_id, t, E, r.P)); got += 1
            if got == N_CTRL:
                break
    C = pd.DataFrame(ctrl, columns=["row_id", "ticker", "E", "P"])
    return e, C


def pull(targets: pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(CACHE):
        c = pd.read_parquet(CACHE); print(f"  chains from cache: {len(c):,} rows"); return c
    k = targets.copy(); k["trade_date"] = pd.to_datetime(k.trade_date).dt.date
    _ensure_glue_db(DB); name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=k, path=path, dataset=True, database=DB, table=name, compression="snappy", mode="overwrite",
                     dtype={"ticker": "string", "trade_date": "date"})
    try:
        c = athena(f"""SELECT o.ticker, o.trade_date, o.expiry, o.strike, o.cp, o.bid, o.ask, o.bid_iv, o.ask_iv
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
            ON o.ticker = t.ticker AND o.trade_date = t.trade_date
          WHERE date_diff('day', o.trade_date, o.expiry) BETWEEN 15 AND 50
            AND o.delta IS NOT NULL AND abs(o.delta) BETWEEN 0.2 AND 0.8
            AND o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999 AND o.ask >= o.bid""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    c.to_parquet(CACHE, index=False); print(f"  pulled {len(c):,} rows -> {CACHE}")
    return c


def price(trades: pd.DataFrame, W: pd.DataFrame) -> pd.DataFrame:
    """trades: key, ticker, E, P. Pick the ~37 DTE ATM pair at E, price the same pair at P."""
    en = W.merge(trades, left_on=["ticker", "trade_date"], right_on=["ticker", "E"])
    en = en[(en.dte >= 30) & (en.dte <= 45) & (en.expiry > en.P)]
    en["dd"] = (en.dte - 37).abs()
    en = en[en.dd == en.groupby("key").dd.transform("min")]
    en = en[en.expiry == en.groupby("key").expiry.transform("max")]       # tie on |dte-37|: the later one
    en["gap"] = (en.mid_C - en.mid_P).abs()
    en = en.loc[en.groupby("key").gap.idxmin()]
    ex = W.rename(columns={"trade_date": "P"})
    m = en.merge(ex, on=["ticker", "P", "expiry", "strike"], suffixes=("_in", "_out"))
    m = m[(m.bid_C_in > 0) & (m.bid_P_in > 0) & (m.bid_C_out > 0) & (m.bid_P_out > 0)]
    cost_mid = m.mid_C_in + m.mid_P_in; val_mid = m.mid_C_out + m.mid_P_out
    sp_in = (m.ask_C_in - m.bid_C_in) + (m.ask_P_in - m.bid_P_in)
    sp_out = (m.ask_C_out - m.bid_C_out) + (m.ask_P_out - m.bid_P_out)
    comm = 2 * COMMISSION_PER_LEG                                           # per share, 2 legs, each side
    cost_h = cost_mid + SLIPPAGE_FRAC * sp_in + comm; val_h = val_mid - SLIPPAGE_FRAC * sp_out - comm
    cost_x = m.ask_C_in + m.ask_P_in; val_x = m.bid_C_out + m.bid_P_out
    return pd.DataFrame({"key": m.key, "ticker": m.ticker, "E": m.E, "P": m.P, "dte": m.dte_in,
                         "pct_mid": 100 * (val_mid / cost_mid - 1), "pct_house": 100 * (val_h / cost_h - 1),
                         "pct_cross": 100 * (val_x / cost_x - 1),
                         "iv_in": (m.iv_C_in + m.iv_P_in) / 2, "iv_out": (m.iv_C_out + m.iv_P_out) / 2,
                         "rt_spread_pct": 100 * (sp_in + sp_out) / cost_mid})[cost_mid > 0.05]


def t_day(s, dates):
    g = s.groupby(dates).mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g)


def main():
    e, C = build_events()
    print(f"events {len(e):,} ({e.ticker.nunique()} names, prints {e.session.min().date()} -> {e.session.max().date()}); "
          f"controls {len(C):,} for {C.row_id.nunique():,} events")
    tg = pd.concat([pd.DataFrame({"ticker": e.ticker, "trade_date": e[c]}) for c in ["P"] + [f"E{n}" for n in LOOKBACKS]]
                   + [pd.DataFrame({"ticker": C.ticker, "trade_date": C[c]}) for c in ("E", "P")]).drop_duplicates()
    print(f"  (ticker, date) targets {len(tg):,}")
    c = pull(tg)
    c["trade_date"] = pd.to_datetime(c.trade_date); c["expiry"] = pd.to_datetime(c.expiry)
    c["mid"] = (c.bid + c.ask) / 2; c["iv"] = (c.bid_iv + c.ask_iv) / 2
    c["cp"] = c.cp.astype(str).str[0].str.upper()
    W = c.pivot_table(index=["ticker", "trade_date", "expiry", "strike"], columns="cp",
                      values=["bid", "ask", "mid", "iv"], aggfunc="last").reset_index()
    W.columns = [f"{a}_{b}" if b else a for a, b in W.columns]
    W = W.dropna(subset=["mid_C", "mid_P"])
    W["dte"] = (W.expiry - W.trade_date).dt.days

    R = []
    for n in LOOKBACKS:
        t = e[["row_id", "ticker", f"E{n}", "P"]].rename(columns={f"E{n}": "E"}).assign(key=lambda x: x.row_id)
        r = price(t, W).assign(n=n); r["row_id"] = r.key; R.append(r)
    R = pd.concat(R, ignore_index=True)
    Ct = C.assign(key=np.arange(len(C)))
    CR = price(Ct, W).merge(Ct[["key", "row_id"]], on="key")
    R.to_parquet("data/studies/logs/earnings_ramp_back_tenor_events.parquet", index=False)
    CR.to_parquet("data/studies/logs/earnings_ramp_back_tenor_controls.parquet", index=False)

    print("\n" + "=" * 110 + "\nEVENT TRADE: buy the ~37 DTE ATM straddle N sessions out, sell on the pre-print session (% of cost)")
    print(f"{'entry':<7}{'n':>7}{'dte':>6}{'IV in->out':>15}{'ramp vp':>9}{'MID':>8}{'HOUSE':>8}{'CROSS':>8}{'t(house)':>9}{'rt spr':>8}  neg yrs")
    for n in LOOKBACKS:
        x = R[R.n == n]; yr = x.groupby(x.P.dt.year).pct_house.mean(); tt, _ = t_day(x.pct_house, x.P)
        print(f"-{n:<6}{len(x):>7,}{x.dte.median():>6.0f}{x.iv_in.mean():>8.3f}->{x.iv_out.mean():<6.3f}"
              f"{100 * (x.iv_out - x.iv_in).mean():>+8.1f}{x.pct_mid.mean():>+8.2f}{x.pct_house.mean():>+8.2f}"
              f"{x.pct_cross.mean():>+8.2f}{tt:>+9.2f}{x.rt_spread_pct.median():>7.1f}%  {int((yr < 0).sum())}/{len(yr)}")

    ev = R[R.n == PRIMARY].set_index("row_id")
    cm = CR.groupby("row_id").agg(c_mid=("pct_mid", "mean"), c_house=("pct_house", "mean"), c_cross=("pct_cross", "mean"),
                                  c_ivin=("iv_in", "mean"), c_ivout=("iv_out", "mean"), n_ctrl=("key", "size"))
    J = ev.join(cm, how="inner")
    for f in ("mid", "house", "cross"):
        J[f"edge_{f}"] = J[f"pct_{f}"] - J[f"c_{f}"]
    J["half"] = np.where(J.P < SPLIT, "2019-2022", "2023-2026")
    print(f"\n{'=' * 110}\nPRIMARY: -{PRIMARY} session entry, paired edge vs same-date no-earnings controls "
          f"({len(J):,} events with >=1 control, mean {J.n_ctrl.mean():.2f} controls)")
    rows = []
    for lab, g in [("full", J)] + list(J.groupby("half")):
        te, nd = t_day(g.edge_house, g.P); tv, _ = t_day(g.pct_house, g.P)
        rows.append(dict(sample=lab, n=len(g), dates=nd, event_house=g.pct_house.mean(), t_event=tv,
                         ctrl_house=g.c_house.mean(), edge_mid=g.edge_mid.mean(), edge_house=g.edge_house.mean(),
                         t_edge=te, edge_cross=g.edge_cross.mean(),
                         ramp_evt_vp=100 * (g.iv_out - g.iv_in).mean(), ramp_ctrl_vp=100 * (g.c_ivout - g.c_ivin).mean()))
    T = pd.DataFrame(rows); print(T.round(3).to_string(index=False))
    Y = J.groupby(J.P.dt.year).agg(n=("edge_house", "size"), event_house=("pct_house", "mean"),
                                   ctrl_house=("c_house", "mean"), edge_house=("edge_house", "mean"))
    print(Y.round(2).to_string())
    full = T.iloc[0]
    ok = full.edge_house > 0 and full.t_edge >= 3 and full.event_house > 0 and (T.iloc[1:].edge_house > 0).all()
    print(f"-> edge {full.edge_house:+.2f}pp t {full.t_edge:.2f}; event house mean {full.event_house:+.2f}% "
          f"(t {full.t_event:.2f}); halves {T.iloc[1].edge_house:+.2f} / {T.iloc[2].edge_house:+.2f}  => {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
