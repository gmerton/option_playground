#!/usr/bin/env python3
"""
Score a window of the book's own trades through the Martin Luk / Tito Adhikary
rulebooks (data/martin_luk/philosophy/principles.md, data/studies/tito_selection_playbook.md).

For every flat-to-flat trade cycle (reconstruct_trade_cycles() off journal_trades)
it computes, at the entry session and using only prior data:
  ADR20, 50d dollar volume, 9/21/50 EMA stack, distance from the 9/21 EMA in % and
  in ADR units, entry-day gap, prior-5-day run in ADR units, RVOL, whether price
  touched the EMAs, 50d breakout/breakdown, fill time after the open
and after entry: close-basis MAE, first close through the 9/20 EMA, days held.
Then classifies each directional single-leg trade (multi-leg structures opened at
the same timestamp are set aside as systematic) into Luk/Tito setup classes and
prints P&L by class, by rule flag, by theme, plus counterfactuals (skip extended,
skip gap-ups, cap losers at Luk's 2% stop, hold winners to the 9 EMA break).

Built 2026-09-05 for the August retrospective (data/studies/august_2026_luk_tito_lens.md).

Usage:
  MYSQL_PASSWORD=... PYTHONPATH=src python run_trade_lens.py --start 2026-08-01 --end 2026-08-31
Prices: yfinance (adjusted) for the traded underlyings + SPY, pulled fresh each run.
"""
from __future__ import annotations
import argparse, warnings
import numpy as np, pandas as pd
import yfinance as yf
from lib.mysql_lib import reconstruct_trade_cycles, get_trade_reviews, _get_conn

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 40)
ap = argparse.ArgumentParser(); ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
ap.add_argument("--out", default=None, help="optional CSV path for the per-trade scored table"); ap.add_argument("--top", type=int, default=30)
A = ap.parse_args()

cyc = reconstruct_trade_cycles(); cyc = cyc[(cyc.entry_date.astype(str)>=A.start)&(cyc.entry_date.astype(str)<=A.end)].copy()
cyc["entry_date"]=cyc.entry_date.astype(str); cyc["exit_date"]=cyc.exit_date.astype(str).replace({"None":np.nan,"NaT":np.nan,"nan":np.nan})
conn=_get_conn()
fills=pd.read_sql("select * from journal_trades where trade_date between %s and %s", conn, params=[(pd.Timestamp(A.start)-pd.Timedelta(days=10)).date(), (pd.Timestamp.today()).date()])
conn.close()
fills["trade_datetime"]=pd.to_datetime(fills.trade_datetime); fills["trade_date"]=pd.to_datetime(fills.trade_date)
rev = get_trade_reviews()
# ---- prices
und = sorted(set(cyc.underlying_symbol) | {"SPY"})
raw = yf.download([t.replace(".","-") for t in und], start=(pd.Timestamp(A.start)-pd.Timedelta(days=400)).date().isoformat(), auto_adjust=True, threads=True, progress=False, group_by="ticker")
frames=[]
for t in und:
    y=t.replace(".","-")
    if y not in raw.columns.get_level_values(0): continue
    g=raw[y].dropna(subset=["Close"]).rename(columns=str.lower)[["open","high","low","close","volume"]].copy(); g["ticker"]=t; g.index.name="date"; frames.append(g.reset_index())
px=pd.concat(frames); px["dolvol"]=px.close*px.volume; px["date"]=pd.to_datetime(px.date)
P = {t: g.set_index("date").sort_index() for t,g in px.groupby("ticker")}
spy = P["SPY"].close
# ---- entry/exit fills per cycle
fills = fills.sort_values(["trade_datetime","trade_id"])
def cycle_fills(r):
    f = fills[(fills.conid==r.conid)&(fills.trade_date>=pd.Timestamp(r.entry_date))]
    if pd.notna(r.exit_date): f = f[f.trade_date<=pd.Timestamp(r.exit_date)]
    return f
rows=[]
for r in cyc.itertuples():
    f = cycle_fills(r)
    if f.empty: continue
    o = f[f.open_close.isin(["O","C;O"])]
    e0 = o.iloc[0] if not o.empty else f.iloc[0]
    rows.append(dict(_ix=r.Index, entry_dt=e0.trade_datetime, entry_px=e0.trade_price, exit_dt=f.iloc[-1].trade_datetime, exit_px=f.iloc[-1].trade_price, n_open_fills=len(o)))
cyc = cyc.join(pd.DataFrame(rows).set_index("_ix"))
cyc = cyc.dropna(subset=["entry_dt"])
cyc["entry_dt"]=pd.to_datetime(cyc.entry_dt); cyc["exit_dt"]=pd.to_datetime(cyc.exit_dt)
# multi-leg detection: same underlying, same opening timestamp, >=2 conids
key = cyc.groupby(["underlying_symbol","entry_dt"]).conid.transform("nunique")
cyc["multileg"] = key>=2
# direction
def direction(r):
    if r.asset_category=="STK": return "BULL" if r.first_side=="LONG" else "BEAR"
    if r.put_call=="C": return "BULL" if r.first_side=="LONG" else "BEAR"
    if r.put_call=="P": return "BEAR" if r.first_side=="LONG" else "BULL"
    return "?"
cyc["dir"]=cyc.apply(direction, axis=1)
cyc["vehicle"]=np.where(cyc.asset_category=="STK", np.where(cyc.first_side=="LONG","long stock","short stock"),
                        cyc.first_side.str.lower()+" "+cyc.put_call.map({"C":"call","P":"put"}).fillna("opt"))
cyc["notional"]=np.where(cyc.asset_category=="STK", cyc.entry_px*cyc.max_abs_qty, cyc.entry_px*cyc.max_abs_qty*100)

# ---- features at entry (underlying)
def feats(r):
    t=r.underlying_symbol; d=pd.Timestamp(r.entry_date)
    if t not in P: return {}
    g=P[t]; 
    if d not in g.index: 
        prior=g.loc[:d]; 
        if prior.empty: return {}
        d=prior.index[-1]
    i=g.index.get_loc(d); hist=g.iloc[:i]  # strictly prior sessions
    if len(hist)<60: return {}
    c=hist.close; e9=c.ewm(span=9,adjust=False).mean(); e21=c.ewm(span=21,adjust=False).mean(); e50=c.ewm(span=50,adjust=False).mean(); s20=c.rolling(20).mean()
    adr=(hist.high/hist.low-1).tail(20).mean(); dv=hist.dolvol.tail(50).mean()
    day=g.iloc[i]; ref = day.close if r.asset_category=="OPT" else r.entry_px   # option cycles: use underlying close as proxy for level
    if r.asset_category=="STK" and not (0.5*day.low < r.entry_px < 2*day.high): ref=day.close
    hi50=hist.high.tail(50).max(); lo50=hist.low.tail(50).min()
    o=dict(adr=adr, dolvol_M=dv/1e6, e9=e9.iloc[-1], e21=e21.iloc[-1], e50=e50.iloc[-1],
           stack_up=bool(e9.iloc[-1]>e21.iloc[-1]>e50.iloc[-1]), stack_dn=bool(e9.iloc[-1]<e21.iloc[-1]<e50.iloc[-1]),
           rising21=bool(e21.iloc[-1]>e21.iloc[-6]), ext9=ref/e9.iloc[-1]-1, ext21=ref/e21.iloc[-1]-1, ext21_adr=(ref/e21.iloc[-1]-1)/adr,
           gap=day.open/c.iloc[-1]-1, run5_adr=(c.iloc[-1]/c.iloc[-6]-1)/adr, rvol=day.dolvol/dv,
           touch_ema=bool(min(day.low, hist.low.iloc[-1]) <= max(e9.iloc[-1],e21.iloc[-1])*1.01),
           brk50=bool(day.close>hi50), brkdn50=bool(day.close<lo50), off_hi=ref/hist.high.tail(252).max()-1,
           day_close_pos=(day.close-day.low)/max(day.high-day.low,1e-9), spy_vs21=bool(spy.loc[:d].iloc[-1] > spy.loc[:d].ewm(span=21,adjust=False).mean().iloc[-1]))
    # exit-side: path after entry
    fut=g.iloc[i:]; 
    xd=pd.Timestamp(r.exit_date) if pd.notna(r.exit_date) else fut.index[-1]
    hold=fut.loc[:xd]
    call=pd.concat([hist.close, fut.close]); e9f=call.ewm(span=9,adjust=False).mean(); e20f=call.ewm(span=20,adjust=False).mean()
    after=fut.iloc[1:]
    if r.dir=="BULL":
        brk9 = after.index[after.close < e9f.reindex(after.index)]; brk20 = after.index[after.close < e20f.reindex(after.index)]
        o.update(mae_close=hold.close.min()/ref-1, mae_intra=hold.low.min()/ref-1, mfe=hold.high.max()/ref-1)
    else:
        brk9 = after.index[after.close > e9f.reindex(after.index)]; brk20 = after.index[after.close > e20f.reindex(after.index)]
        o.update(mae_close=1-hold.close.max()/ref, mae_intra=1-hold.high.max()/ref, mfe=1-hold.low.min()/ref)
    o.update(first_brk9=brk9[0] if len(brk9) else pd.NaT, first_brk20=brk20[0] if len(brk20) else pd.NaT, days_held=len(hold)-1 if pd.notna(r.exit_date) else np.nan,
             ret_to_9ema_exit=(fut.close.loc[brk9[0]]/ref-1 if len(brk9) else fut.close.iloc[-1]/ref-1)*(1 if r.dir=="BULL" else -1))
    return o
F = pd.DataFrame([feats(r) for r in cyc.itertuples()], index=cyc.index)
df = pd.concat([cyc, F], axis=1)
for c in ["stack_up","stack_dn","rising21","touch_ema","brk50","brkdn50","spy_vs21"]: df[c]=df[c].fillna(False).astype(bool)
df["mins_after_open"] = (df.entry_dt.dt.hour*60+df.entry_dt.dt.minute) - 570
df["pnl_pct_notional"] = df.realized_pnl/df.notional
rev["entry_date"]=rev.entry_date.astype(str)
rv = rev.groupby(["underlying_symbol","entry_date"]).agg(entry_verdict=("entry_verdict","first"), tags=("tags","first")).reset_index()
df = df.merge(rv, on=["underlying_symbol","entry_date"], how="left")

# ---- classification (directional, single-leg, with features)
d = df[(~df.multileg) & df.adr.notna()].copy()
def classify(r):
    cat = "big-mover" if r.adr>=0.04 else "grinder"
    if r.dir=="BULL":
        if r.stack_dn or (r.ext21 < -0.02 and not r.rising21): return "FIGHT_TREND (long below falling EMAs)"
        if r.gap>=0.08 and r.rvol>=2 and r.brk50: return "TITO_B earnings/EP breakout"
        if r.brk50 and r.stack_up and r.gap<0.05: return "TITO_A base breakout"
        if r.stack_up and r.touch_ema and r.ext9<=0.03 and r.gap<0.02: return "LUK pullback into rising EMAs"
        if r.gap>=0.03 and r.mins_after_open<60: return "GAP CHASE (bought gap-up early)"
        if r.ext21_adr>2 or r.ext9>0.05: return "EXTENDED CHASE (>2 ADR over 21ema / >5% over 9ema)"
        if r.stack_up: return "OK-ish long in uptrend (no defined trigger)"
        return "NO SETUP (mixed EMAs)"
    else:
        if r.stack_up and r.ext21_adr>3 and r.rvol>=2 and r.day_close_pos<0.35: return "TITO_C exhaustion fade"
        if r.stack_up: return "FIGHT_TREND (short a stacked uptrend)"
        if r.stack_dn and abs(r.ext9)<=0.03: return "LUK short: bounce into declining EMAs"
        if r.brkdn50 or r.ext21_adr < -1.5: return "SHORT CHASE (breakdown already extended down)"
        return "NO SETUP (mixed EMAs)"
d["setup"] = d.apply(classify, axis=1)
d["extended"] = (d.ext21_adr>2)|(d.ext9>0.05)
d["opening30"] = d.mins_after_open<30
d["gapup3"] = d.gap>=0.03
d["loss_beyond_2pct"] = (d.mae_close < -0.02)
if A.out: d.to_csv(A.out, index=False)

def agg(g):
    return pd.Series(dict(n=len(g), pnl=g.realized_pnl.sum(), win=(g.realized_pnl>0).mean(), avg=g.realized_pnl.mean(),
                          med_ext21_adr=g.ext21_adr.median(), med_adr=g.adr.median()))
print(f"Cycles {A.start}..{A.end}: {len(df)} total; multi-leg/systematic {int(df.multileg.sum())} (P&L {df[df.multileg].realized_pnl.sum():+.0f}); "
      f"directional single-leg with data: {len(d)} (P&L {d.realized_pnl.sum():+.0f}); no data {int(((~df.multileg)&df.adr.isna()).sum())}")
print("\n=== BY SETUP CLASS (directional, single-leg) ===")
print(d.groupby("setup").apply(agg).sort_values("pnl").round(3).to_string())
print("\n=== BY DIRECTION x VEHICLE ===")
print(d.groupby(["dir","vehicle"]).apply(agg).round(3).to_string())
print("\n=== LUK RULE FLAGS (long side) ===")
L = d[d.dir=="BULL"]
for name, m in [("extended (>2 ADR over 21ema or >5% over 9ema)", L.extended), ("not extended", ~L.extended),
                ("entered in first 30 min", L.opening30), ("entered after 30 min", ~L.opening30),
                ("bought a >=3% gap-up", L.gapup3), ("no gap", ~L.gapup3),
                ("stack 9>21>50 up", L.stack_up), ("stack not up", ~L.stack_up),
                ("SPY above 21ema at entry", L.spy_vs21), ("SPY below 21ema", ~L.spy_vs21),
                ("Tito big-mover (ADR>=4%)", L.adr>=0.04), ("grinder (ADR<4%)", L.adr<0.04),
                ("Luk-liquid (>=$100M/day)", L.dolvol_M>=100), ("thin (<$100M/day)", L.dolvol_M<100),
                ("run-up >2 ADR in prior 5d", L.run5_adr>2), ("run-up <=2 ADR", L.run5_adr<=2)]:
    g=L[m]; print(f"  {name:48s} n={len(g):3d} pnl {g.realized_pnl.sum():+8.0f} win {100*(g.realized_pnl>0).mean():4.0f}% avg {g.realized_pnl.mean():+6.0f}")
print("\n=== EXTENSION BUCKETS (long side), ADR units above 21ema ===")
b = pd.cut(L.ext21_adr, [-99,0,1,2,3,5,99], labels=["<=0 (at/below 21)","0-1","1-2","2-3","3-5",">5"])
print(L.groupby(b).apply(agg).round(3).to_string())
print("\n=== EXIT DISCIPLINE (long side, closed) ===")
Lc = L[L.exit_date.notna()]
early = Lc[Lc.first_brk9.notna() & (pd.to_datetime(Lc.exit_date) < Lc.first_brk9)]
late = Lc[Lc.first_brk9.notna() & (pd.to_datetime(Lc.exit_date) > Lc.first_brk9)]
on = Lc[Lc.first_brk9.notna() & (pd.to_datetime(Lc.exit_date) == Lc.first_brk9)]
never = Lc[Lc.first_brk9.isna()]
for name,g in [("exited BEFORE first close < 9ema",early),("exited ON that day",on),("exited AFTER (held through the 9ema break)",late),("9ema never broke by 9/4",never)]:
    print(f"  {name:45s} n={len(g):3d} pnl {g.realized_pnl.sum():+8.0f} win {100*(g.realized_pnl>0).mean():4.0f}%  median days held {g.days_held.median():.0f}  "
          f"P&L if held to first 9ema close-break (stock %, median) {100*g.ret_to_9ema_exit.median():+.1f}%")
print(f"  same-day round trips: n={int((Lc.days_held==0).sum())} pnl {Lc[Lc.days_held==0].realized_pnl.sum():+.0f} | multi-day: n={int((Lc.days_held>0).sum())} pnl {Lc[Lc.days_held>0].realized_pnl.sum():+.0f}")
print(f"  losers whose close-basis MAE exceeded Luk's 2% max stop: {int((Lc.realized_pnl<0)&(Lc.loss_beyond_2pct)).sum() if False else int(((Lc.realized_pnl<0)&Lc.loss_beyond_2pct).sum())} of {int((Lc.realized_pnl<0).sum())} losers; "
      f"their pnl {Lc[(Lc.realized_pnl<0)&Lc.loss_beyond_2pct].realized_pnl.sum():+.0f}")
stk = Lc[Lc.asset_category=="STK"]
print(f"  stock longs: median loss as % of notional {100*stk[stk.realized_pnl<0].pnl_pct_notional.median():.2f}%, median win {100*stk[stk.realized_pnl>0].pnl_pct_notional.median():.2f}%, "
      f"payoff ratio {abs(stk[stk.realized_pnl>0].pnl_pct_notional.mean()/stk[stk.realized_pnl<0].pnl_pct_notional.mean()):.2f}")
print("\n=== SHORT SIDE ===")
Sh = d[d.dir=="BEAR"]
print(Sh.groupby("setup").apply(agg).round(3).to_string())
print("\n=== REPEAT-TRADED NAMES (>=5 cycles) ===")
rep = d.groupby("underlying_symbol").agg(n=("realized_pnl","size"), pnl=("realized_pnl","sum"), win=("realized_pnl", lambda x:(x>0).mean()), ext=("ext21_adr","median"), adr=("adr","median"), longs=("dir", lambda x:(x=="BULL").sum()))
print(rep[rep.n>=5].sort_values("pnl").round(2).to_string())
print("\n=== LARGEST |P&L| directional trades ===")
cols=["underlying_symbol","vehicle","entry_date","exit_date","entry_dt","realized_pnl","setup","adr","ext21_adr","ext9","gap","rvol","run5_adr","mins_after_open","mae_close","days_held","entry_verdict"]
top = d.reindex(d.realized_pnl.abs().sort_values(ascending=False).index).head(A.top)[cols].copy()
top["entry_dt"]=top.entry_dt.dt.strftime("%H:%M")
for c in ["adr","ext21_adr","ext9","gap","rvol","run5_adr","mae_close"]: top[c]=top[c].round(2)
print(top.to_string(index=False))

im = pd.read_csv("/Users/gmerton/v2/options_playground/data/ticker_industry_map.csv").set_index("ticker")
manual = {"SOXL":"Semiconductors","SMCI":"Computer Hardware","DRAM":"Semiconductors","MUU":"Semiconductors","WDCX":"Computer Hardware","SNDQ":"Computer Hardware","SKHY":"Semiconductors",
          "IBIT":"Crypto","ETHA":"Crypto","BMNR":"Crypto","CRCL":"Crypto","HUT":"Crypto","SBET":"Crypto","IREN":"Crypto","CIFR":"Crypto","APLD":"Crypto/AI infra","MSTR":"Crypto",
          "QQQ":"Index","TLT":"Bonds","UVXY":"Vol","GLD":"Gold","GDX":"Gold","XLE":"Energy","KRE":"Regional Banks","XBI":"Biotech","ARKG":"Biotech","TSLQ":"Tesla inverse","SPCX":"SPAC ETF","SOLT":"Crypto","NVO":"Pharma","SE":"Internet Retail","ACHR":"Aerospace & Defense","BBAI":"Software - Infrastructure"}
ind = im.industry.to_dict(); ind.update(manual)
def theme(t):
    i = ind.get(t, "?")
    if i in ("Semiconductors","Semiconductor Equipment & Materials"): return "Semis"
    if i in ("Computer Hardware","Communication Equipment","Electronic Components","Scientific & Technical Instruments"): return "AI hardware/optical"
    if i.startswith("Software") or i in ("Information Technology Services",): return "Software"
    if "Crypto" in i: return "Crypto"
    if i in ("Internet Content & Information","Internet Retail","Entertainment"): return "Internet"
    if i in ("Biotechnology","Diagnostics & Research","Pharma","Drug Manufacturers - General","Medical Devices","Health Information Services"): return "Biotech/Health"
    if i in ("Gold","Copper","Other Industrial Metals & Mining","Energy","Oil & Gas E&P"): return "Metals/Energy"
    if i in ("Auto Manufacturers","Tesla inverse"): return "Tesla/Autos"
    return "Other ("+i+")"
d["theme"]=d.underlying_symbol.map(theme)
_unused = {"Semis":"+3% (H1 +9%, H2 -5%)","AI hardware/optical":"+9% hw","Software":"+13-14%","Crypto":"+25% (all after 8/14)","Biotech/Health":"+5-24%","Metals/Energy":"+7-39%","Internet":"+8%"}
print("=== P&L BY THEME (directional single-leg) ===")
g = d.groupby("theme").agg(n=("realized_pnl","size"), pnl=("realized_pnl","sum"), win=("realized_pnl", lambda x:(x>0).mean()), longs=("dir", lambda x:(x=="BULL").sum()), ext_share=("extended","mean")).sort_values("pnl")
print(g.round(2).to_string())
L = d[(d.dir=="BULL")&d.exit_date.notna()].copy()
stk = L[L.asset_category=="STK"]
print(f"\n=== COUNTERFACTUALS on closed long-side trades (n={len(L)}, actual P&L {L.realized_pnl.sum():+.0f}; stock-only n={len(stk)}, {stk.realized_pnl.sum():+.0f}) ===")
def cf(name, mask, base=L):
    keep=base[mask]; print(f"  {name:70s} keep {len(keep):3d}/{len(base)}  P&L {keep.realized_pnl.sum():+8.0f}  win {100*(keep.realized_pnl>0).mean():.0f}%")
cf("LUK: skip extended (>2 ADR over 21ema or >5% over 9ema)", ~L.extended)
cf("LUK: skip extended AND skip >=3% gap-ups", ~L.extended & ~L.gapup3)
cf("LUK: only stack 9>21>50 up, not extended, no gap", L.stack_up & ~L.extended & ~L.gapup3)
cf("LUK: entry within 1 ADR of 21ema (ext21_adr<=1)", L.ext21_adr<=1)
cf("TITO: only big movers (ADR>=4%) with a defined trigger (A/B/pullback)", (L.adr>=0.04) & L.setup.str.contains("TITO|LUK pullback"))
cf("Drop same-day round trips", L.days_held>0)
cf("Drop same-day round trips AND skip extended", (L.days_held>0) & ~L.extended)
# stop cap: cap each stock long loser at -2% of notional (Luk's max stop), close basis
capped = stk.realized_pnl.copy(); m = (stk.realized_pnl<0) & (stk.pnl_pct_notional < -0.02); capped[m] = -0.02*stk.notional[m]
print(f"  LUK 2% stop cap on stock longs: actual {stk.realized_pnl.sum():+.0f} -> capped {capped.sum():+.0f}  ({int(m.sum())} losers capped, they lost {stk.realized_pnl[m].sum():+.0f}, would have lost {capped[m].sum():+.0f})")
# hold rule: for winners exited before first 9ema break, what if held to the break (stock % move applied to notional; stock only)
w = stk[(stk.realized_pnl>0) & stk.first_brk9.notna() & (pd.to_datetime(stk.exit_date) < stk.first_brk9)]
w2 = stk[(stk.realized_pnl>0) & stk.first_brk9.isna()]
print(f"  TITO/LUK hold winners to first close < 9ema: {len(w)} winners sold early (actual {w.realized_pnl.sum():+.0f}); at the 9ema-break close they'd be {(w.ret_to_9ema_exit*w.notional).sum():+.0f}. "
      f"{len(w2)} winners whose 9ema never broke by 9/4: actual {w2.realized_pnl.sum():+.0f}, mark-to-9/4 {(w2.ret_to_9ema_exit*w2.notional).sum():+.0f}")
print("\n=== WHERE THE 1-2 ADR BUCKET LOST (the biggest hole): top losers ===")
b = L[(L.ext21_adr>1)&(L.ext21_adr<=2)].nsmallest(10,"realized_pnl")[["underlying_symbol","vehicle","entry_date","realized_pnl","ext21_adr","ext9","gap","days_held","theme","entry_verdict"]]
print(b.round(2).to_string(index=False))
print("\n=== TIME OF DAY (long entries) ===")
tb = pd.cut(L.mins_after_open, [-1,30,60,120,240,390,2000], labels=["0-30m","30-60m","1-2h","2-4h","last 2.5h","after-hours"])
print(L.groupby(tb).agg(n=("realized_pnl","size"), pnl=("realized_pnl","sum"), win=("realized_pnl", lambda x:(x>0).mean()), ext=("extended","mean")).round(2).to_string())
