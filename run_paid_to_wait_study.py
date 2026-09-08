#!/usr/bin/env python3
"""
Paid-to-wait study (2026-09-08): on a stacked name sitting just under its 15-day pivot (the Adhikary
SETUP shape), sell a 30/15-delta put credit spread 25-45 DTE and either hold to expiry or close it
the day the pivot breaks (when you would buy the stock instead). Real quotes from options_daily_v3
(bid/ask through mid-July 2026), cost model from lib.studies.costs, split by regime state at entry
and by the ticker's own 30-day IV percentile (silver.fwd_vol_daily, through 2026-02).

Events: Fridays 2019-10 .. 2026-05 on the liquid panel (ADDV>=$50M, ADR>=3%), 10>20>50 SMA stacked,
close within 5% under the prior-15-session high, 10d range <= 0.6x the prior 20d range, 5d volume
<= 0.8x the 50d average. Settlement at expiry = panel close vs strikes (events whose short strike
is not 0-25% under the entry close are dropped as split-basis mismatches).

Usage: AWS_PROFILE=... PYTHONPATH=src python run_paid_to_wait_study.py [--max-events 6000] [--iv-hist path]
"""
from __future__ import annotations
import argparse, uuid, warnings
import numpy as np, pandas as pd
import awswrangler as wr
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies.costs import COMMISSION_PER_LEG, SLIPPAGE_FRAC

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

def tmp_table(df: pd.DataFrame, dtype: dict) -> tuple[str, str]:
    _ensure_glue_db(DB); name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=df, path=path, dataset=True, database=DB, table=name, compression="snappy", mode="overwrite", dtype=dtype)
    return name, path

def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", default="data/cache/liquid_panel_2019.parquet"); ap.add_argument("--iv-hist", default=None)
    ap.add_argument("--max-events", type=int, default=6000); ap.add_argument("--out", default="data/studies/paid_to_wait_events.csv"); a = ap.parse_args()
    raw = pd.read_parquet(a.panel); spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
    p = Panel.from_long(raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]); C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    s10, s20, s50 = C.rolling(10).mean(), C.rolling(20).mean(), C.rolling(50).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100; piv = H.shift(1).rolling(15).max()
    r10 = H.rolling(10).max() - L.rolling(10).min(); r20p = H.shift(10).rolling(20).max() - L.shift(10).rolling(20).min()
    dry = V.shift(1).rolling(5).mean() / V.shift(1).rolling(50).mean(); vp = C / piv - 1
    setup = (s10 > s20) & (s20 > s50) & (vp >= -0.05) & (vp <= 0) & ((r10 / r20p) <= 0.6) & (dry <= 0.8) & (adr >= 3) & elig
    fri = setup.index.weekday == 4
    setup = setup[fri & (setup.index >= "2019-10-01") & (setup.index <= "2026-05-29")]
    ii, jj = np.where(setup.fillna(False).values)
    ev = pd.DataFrame({"entry_date": setup.index[ii], "ticker": setup.columns[jj]})
    ev["close"] = C.values[np.searchsorted(C.index, ev.entry_date), jj]; ev["pivot"] = piv.values[np.searchsorted(C.index, ev.entry_date), jj]
    # regime state at entry
    s50s, s200s = spy.rolling(50).mean(), spy.rolling(200).mean()
    adv10 = (C.pct_change(fill_method=None) > 0).where(elig).mean(axis=1).rolling(10).mean()
    trend = pd.Series(np.where((spy > s50s) & (s50s > s200s), "up", np.where(spy < s200s, "bear", "chop")), index=spy.index)
    ev["state"] = trend.reindex(ev.entry_date).values + "/" + np.where(adv10.reindex(ev.entry_date).values >= 0.5, "B+", "B-")
    if a.iv_hist:
        iv = pd.read_parquet(a.iv_hist)[["ticker", "trade_date", "iv_pct"]].rename(columns={"trade_date": "entry_date"})
        ev = ev.merge(iv, on=["ticker", "entry_date"], how="left")
    else:
        ev["iv_pct"] = np.nan
    if len(ev) > a.max_events:
        ev = ev.sample(a.max_events, random_state=7).sort_values("entry_date")
    ev = ev.reset_index(drop=True); ev["row_id"] = ev.index.astype("int64")
    print(f"events: {len(ev)} setup-Fridays, {ev.ticker.nunique()} names, {ev.entry_date.min().date()}..{ev.entry_date.max().date()} | IV pct known {ev.iv_pct.notna().mean():.0%}")
    # ---- entry legs from v3
    tg = ev[["row_id", "ticker", "entry_date"]].copy(); tg["entry_date"] = tg.entry_date.dt.date
    name, path = tmp_table(tg, {"row_id": "bigint", "ticker": "string", "entry_date": "date"})
    try:
        legs = athena(f"""
        SELECT t.row_id, o.expiry, o.strike, o.bid, o.ask, o.delta, date_diff('day', o.trade_date, o.expiry) AS dte
        FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
          ON o.ticker = t.ticker AND o.trade_date = t.entry_date
        WHERE o.cp = 'P' AND o.bid > 0 AND o.ask > 0 AND o.ask < 9999 AND o.delta IS NOT NULL
          AND o.delta BETWEEN -0.45 AND -0.08 AND date_diff('day', o.trade_date, o.expiry) BETWEEN 25 AND 45""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    legs["expiry"] = pd.to_datetime(legs.expiry); legs["mid"] = (legs.bid + legs.ask) / 2; legs["ba"] = legs.ask - legs.bid
    print(f"entry legs: {len(legs)} rows for {legs.row_id.nunique()} events")
    rows = []
    for rid, g in legs.groupby("row_id"):
        g = g.assign(dd=(g.dte - 35).abs()); xp = g.loc[g.dd.idxmin(), "expiry"]; g = g[g.expiry == xp]
        s = g.iloc[(g.delta + 0.30).abs().argsort()[:1]]; l = g[g.strike < s.strike.iloc[0]]
        if s.empty or l.empty or abs(s.delta.iloc[0] + 0.30) > 0.08: continue
        l = l.iloc[(l.delta + 0.15).abs().argsort()[:1]]
        if abs(l.delta.iloc[0] + 0.15) > 0.06: continue
        rows.append(dict(row_id=rid, expiry=xp, dte=int(s.dte.iloc[0]), ks=float(s.strike.iloc[0]), kl=float(l.strike.iloc[0]), credit=float(s.mid.iloc[0] - l.mid.iloc[0]),
                         ba_s=float(s.ba.iloc[0]), ba_l=float(l.ba.iloc[0]), ba_pct_s=float(s.ba.iloc[0] / s.mid.iloc[0])))
    sp = ev.merge(pd.DataFrame(rows), on="row_id", how="inner")
    sp = sp[(sp.credit > 0) & (sp.ks / sp.close).between(0.75, 1.0)]  # split-basis sanity
    sp["width"] = sp.ks - sp.kl; sp["max_loss"] = sp.width - sp.credit; sp = sp[sp.max_loss > 0]
    print(f"spreads built: {len(sp)} (credit med {sp.credit.median():.2f}, width med {sp.width.median():.2f}, credit/width med {(sp.credit/sp.width).median():.2f}, short BA med {sp.ba_pct_s.median():.0%})")
    # ---- exits: pivot break date from the panel, settlement at expiry from panel close
    idx = C.index; Cv = C.values; col = {t: i for i, t in enumerate(C.columns)}
    brk, sexp, sbrk = [], [], []
    for r in sp.itertuples():
        j = col[r.ticker]; i0 = idx.searchsorted(r.entry_date); i1 = idx.searchsorted(r.expiry, side="right") - 1
        path_ = Cv[i0 + 1:i1 + 1, j]; hit = np.where(path_ > r.pivot)[0]
        brk.append(idx[i0 + 1 + hit[0]] if len(hit) else pd.NaT); sexp.append(Cv[min(i1, len(idx) - 1), j]); sbrk.append(Cv[i0 + 1 + hit[0], j] if len(hit) else np.nan)
    sp["break_date"] = brk; sp["spot_expiry"] = sexp; sp["spot_break"] = sbrk
    sp["broke"] = sp.break_date.notna()
    # marks on the break date (real quotes) for the convert-on-break rule
    bt = sp[sp.broke][["row_id", "ticker", "expiry", "break_date", "ks", "kl"]].copy(); bt["expiry"] = bt.expiry.dt.date; bt["break_date"] = bt.break_date.dt.date
    marks = pd.DataFrame(columns=["row_id", "strike", "bid", "ask"])
    if len(bt):
        name, path = tmp_table(bt, {"row_id": "bigint", "ticker": "string", "expiry": "date", "break_date": "date", "ks": "double", "kl": "double"})
        try:
            marks = athena(f"""
            SELECT t.row_id, o.strike, o.bid, o.ask FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
              ON o.ticker = t.ticker AND o.expiry = t.expiry AND o.trade_date = t.break_date AND o.cp = 'P' AND (o.strike = t.ks OR o.strike = t.kl)
            WHERE o.bid IS NOT NULL AND o.ask IS NOT NULL AND o.ask < 9999""")
        finally:
            _drop_temp_targets_table(DB, name, path)
    marks["mid"] = (marks.bid + marks.ask) / 2
    ms = marks.merge(sp[["row_id", "ks", "kl"]], on="row_id"); ms_s = ms[ms.strike == ms.ks].groupby("row_id").mid.max(); ms_l = ms[ms.strike == ms.kl].groupby("row_id").mid.max()
    sp["mark_s_break"] = sp.row_id.map(ms_s); sp["mark_l_break"] = sp.row_id.map(ms_l)
    # ---- P&L per share
    intr = lambda K, S: np.maximum(0.0, K - S)
    sp["val_expiry"] = intr(sp.ks, sp.spot_expiry) - intr(sp.kl, sp.spot_expiry)
    sp["pnl_hold"] = sp.credit - sp.val_expiry
    cost_entry = 2 * COMMISSION_PER_LEG + SLIPPAGE_FRAC * (sp.ba_s + sp.ba_l)
    sp["pnl_hold_net"] = sp.pnl_hold - cost_entry
    val_break = (sp.mark_s_break - sp.mark_l_break)
    sp["pnl_conv"] = np.where(sp.broke & val_break.notna(), sp.credit - val_break, sp.pnl_hold)
    sp["pnl_conv_net"] = np.where(sp.broke & val_break.notna(), sp.pnl_conv - 2 * cost_entry, sp.pnl_hold_net)
    sp["days_conv"] = np.where(sp.broke, (sp.break_date - sp.entry_date).dt.days, (sp.expiry - sp.entry_date).dt.days)
    for k in ("hold", "conv"):
        sp[f"roc_{k}"] = sp[f"pnl_{k}"] / sp.max_loss; sp[f"roc_{k}_net"] = sp[f"pnl_{k}_net"] / sp.max_loss
    sp["stock_to_exit"] = np.where(sp.broke, sp.spot_break / sp.close - 1, sp.spot_expiry / sp.close - 1)
    sp["year"] = sp.entry_date.dt.year; sp["iv_gate"] = np.where(sp.iv_pct.isna(), "unknown", np.where(sp.iv_pct >= 0.6, "IV>=60pct", "IV<60pct"))
    sp.to_csv(a.out, index=False)
    def block(title, g):
        de = g.groupby("entry_date").roc_conv_net.mean()
        print(f"  {title:34s} n={len(g):5d}  broke {100*g.broke.mean():4.0f}%  | HOLD: roc {100*g.roc_hold.mean():+5.1f} net {100*g.roc_hold_net.mean():+5.1f} win {100*(g.pnl_hold_net>0).mean():3.0f}%"
              f"  | CONVERT-ON-BREAK: roc {100*g.roc_conv.mean():+5.1f} net {100*g.roc_conv_net.mean():+5.1f} win {100*(g.pnl_conv_net>0).mean():3.0f}% days {g.days_conv.median():3.0f} t {tstat(de):+.2f}"
              f"  | stock to same exit {100*g.stock_to_exit.mean():+5.2f}%")
    print("\n=== PAID-TO-WAIT: 30/15-delta put credit spread, 25-45 DTE, on SETUP Fridays (ROC on max loss; net = after costs) ===")
    block("ALL", sp)
    for k, g in sp.groupby("iv_gate"): block(f"IV gate: {k}", g)
    print("  by regime state at entry:")
    for k, g in sp.groupby("state"): block(f"  {k}", g)
    print("  by regime state, IV>=60pct only:")
    for k, g in sp[sp.iv_gate == "IV>=60pct"].groupby("state"): block(f"  {k}", g)
    print("  by year:")
    for k, g in sp.groupby("year"): block(f"  {k}", g)
    print(f"\n  P(pivot break before expiry) = {100*sp.broke.mean():.1f}%; when it broke, median days {sp[sp.broke].days_conv.median():.0f}; stock from entry to break median {100*sp[sp.broke].stock_to_exit.median():+.1f}%")
    print(f"  events saved to {a.out}")

if __name__ == "__main__":
    main()
