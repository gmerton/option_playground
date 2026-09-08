#!/usr/bin/env python3
"""
Live scan for Tito Adhikary-style setups (data/studies/tito_selection_playbook.md, recipe v1).

Universe: names liquid on the panel (ADDV >= $50M), ADR%(20d) >= 3 (recipe #1), 52-week range
>= 17% of price. Today's bar = Tradier quote (open/high/low/last/volume) stamped onto daily history
(data/cache/liquid_panel_2019.parquet, yfinance adjusted); intraday RVOL is pro-rated by session
elapsed, so a mid-session run over-weights early volume -- re-run near the close for the real read.

Archetypes (recipe #5 pivot = highest high of the prior 15 sessions; #6 triggers):
  A  BREAKOUT   close clears the pivot, RVOL >= 1.1, close in the upper half of the bar,
                10>20>50 SMA stacked and held >= 5 sessions, no catalyst gap
  B  CATALYST   gap >= 5% or day >= +8%, RVOL >= 2, close clears the pivot, close in the top quarter
  C  EXHAUSTION new 20d high then reversal: close < open, close in the bottom 30%, RVOL >= 2.3,
                close >= 2 ADR above the 20 SMA (the short archetype; 0DTE put intraday)
  SETUP         pre-breakout watch: stacked, within 5% under the pivot, 10d range <= 0.6x the prior
                20d range, 5d volume <= 0.8x the 50d average (VCP contraction + dry-up)
Vehicle (recipe #7): <=11 DTE near-ATM 0.5-0.9 delta; >=15 DTE OTM 0.2-0.35 delta; premium $0.5-6.
Validation (data/studies/adhikary_detector_validation.md, 2019-2026): recipe-as-written A is ~flat (R +0.16, 29% win);
the PRECISION tier (ADR 4-7, within 15% of the 52wk high, stacked 5-40d) is the cohort that held up (R +0.67, positive
6 of 8 years); SETUP days raise P(break within 10s) 45%->57%; B has no edge; C on daily bars is INVERTED.
Exit: grind -> trail the 20 EMA daily close; spike (option 3x in days) -> sell into strength.

Usage: TRADIER_API_KEY=... PYTHONPATH=src python run_adhikary_scan.py [--asof YYYY-MM-DD] [--no-live]
  --no-live scores the last cached session instead of stamping today's quote.
"""
from __future__ import annotations
import argparse, asyncio, os, warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
REPO = Path(__file__).resolve().parent
PANEL = REPO / "data" / "cache" / "liquid_panel_2019.parquet"
INDMAP = REPO / "data" / "ticker_industry_map.csv"
OUT = REPO / "data" / "watchlist"
ADDV_MIN, ADR_MIN, RANGE52_MIN, PIVOT_N = 50e6, 3.0, 17.0, 15

async def quotes(symbols):
    out = {}
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as t:
        sem = asyncio.Semaphore(4)
        async def one(chunk):
            async with sem:
                q = (await t.get_json("/markets/quotes", params={"symbols": ",".join(chunk), "greeks": "false"}))["quotes"].get("quote", [])
                if isinstance(q, dict): q = [q]
                for x in q: out[x["symbol"]] = x
        await asyncio.gather(*[one(symbols[i:i+25]) for i in range(0, len(symbols), 25)])
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--asof", default=None); ap.add_argument("--no-live", action="store_true"); a = ap.parse_args()
    raw = pd.read_parquet(PANEL); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    raw["date"] = pd.to_datetime(raw.date)
    if a.asof: raw = raw[raw.date <= pd.Timestamp(a.asof)]
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index()
    O, H, L, C, V = piv("open"), piv("high"), piv("low"), piv("close"), piv("volume")
    addv = (C * V).tail(50).mean(); uni = addv[addv >= ADDV_MIN].index
    O, H, L, C, V = O[uni], H[uni], L[uni], C[uni], V[uni]
    elapsed = 1.0; label = str(C.index[-1].date()) + " (cached close)"
    if not a.no_live and not a.asof:
        Q = asyncio.run(quotes(list(uni)))
        now = datetime.now(ZoneInfo("America/New_York")); mins = (now.hour - 9) * 60 + now.minute - 30
        elapsed = float(np.clip(mins / 390, 0.1, 1.0))
        today = pd.Timestamp(now.date())
        row = {k: pd.Series({s: Q[s].get(k) for s in uni if s in Q and Q[s].get("last")}, dtype=float) for k in ("open", "high", "low", "last", "volume")}
        if today > C.index[-1] and len(row["last"]) > 0:
            O.loc[today], H.loc[today], L.loc[today], C.loc[today], V.loc[today] = row["open"], row["high"], row["low"], row["last"], row["volume"]
            label = f"{today.date()} LIVE at {now:%H:%M} ET (session {100*elapsed:.0f}% elapsed; RVOL pro-rated)"
    C, O, H, L, V = C.ffill(limit=1), O.ffill(limit=1), H.ffill(limit=1), L.ffill(limit=1), V.fillna(0)
    s10, s20, s50 = C.rolling(10).mean(), C.rolling(20).mean(), C.rolling(50).mean()
    e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52, lo52 = H.shift(1).rolling(252, min_periods=120).max(), L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    pivot = H.shift(1).rolling(PIVOT_N).max()
    avgv = V.shift(1).rolling(50).mean(); rvol = V / (avgv * elapsed)
    stacked = (s10 > s20) & (s20 > s50); stack_days_last = stacked.iloc[::-1].cumprod().sum()  # trailing run length, last row only
    rng = (H - L); pos = (C - L) / rng.replace(0, np.nan)
    gap = O / C.shift(1) - 1; chg = C / C.shift(1) - 1
    r10 = (H.rolling(10).max() - L.rolling(10).min()); r20p = (H.shift(10).rolling(20).max() - L.shift(10).rolling(20).min())
    contraction = r10 / r20p; dryup = V.shift(1).rolling(5).mean() / avgv
    ext20 = (C / s20 - 1) * 100 / adr
    d = C.index[-1]
    base = pd.DataFrame({"px": C.loc[d], "chg%": 100 * chg.loc[d], "gap%": 100 * gap.loc[d], "piv": pivot.loc[d], "vs_pivot%": 100 * (C.loc[d] / pivot.loc[d] - 1),
                         "rvol": rvol.loc[d], "pos": pos.loc[d], "adr": adr.loc[d], "range52": range52.loc[d], "stack_d": stack_days_last, "contr": contraction.loc[d],
                         "dryup": dryup.loc[d], "ext20_adr": ext20.loc[d], "off52%": 100 * (C.loc[d] / hi52.loc[d] - 1), "addv_M": addv[uni] / 1e6})
    if INDMAP.exists():
        im = pd.read_csv(INDMAP).set_index("ticker").industry; base["industry"] = im.reindex(base.index).fillna("?").str.slice(0, 22)
    gate = (base.adr >= ADR_MIN) & (base.range52 >= RANGE52_MIN) & base.piv.notna()
    b = base[gate].copy()
    # validated precision tier (data/studies/adhikary_detector_validation.md): ADR 4-7, within 15% of the 52wk high, stacked 5-40d
    b["precision"] = np.where(b.adr.between(4, 7) & (b["off52%"] > -15) & b.stack_d.between(5, 40), "YES", "")
    A = b[(b.px >= b.piv) & (b.rvol >= 1.1) & (b.pos >= 0.5) & (b.stack_d >= 5) & (b["gap%"] < 5) & (b["chg%"] < 8)]
    B = b[((b["gap%"] >= 5) | (b["chg%"] >= 8)) & (b.rvol >= 2) & (b.px >= b.piv) & (b.pos >= 0.75)]
    Cx = b[(H.loc[d] >= H.shift(1).rolling(20).max().loc[d]) & (C.loc[d] < O.loc[d]) & (b.pos <= 0.30) & (b.rvol >= 2.3) & (b.ext20_adr >= 2) & stacked.loc[d]]
    S = b[stacked.loc[d] & (b["vs_pivot%"].between(-5, 0)) & (b.contr <= 0.6) & (b.dryup <= 0.8)]
    lines = [f"=== ADHIKARY SCAN — {label} | universe {len(uni)} liquid, {int(gate.sum())} pass ADR>={ADR_MIN}% & 52wk range>={RANGE52_MIN}% ===",
             "vehicle: <=11 DTE near-ATM 0.5-0.9d | >=15 DTE OTM 0.2-0.35d | premium $0.5-6 || exit: grind -> 20 EMA daily close; spike (3x) -> sell into strength"]
    def block(title, df, cols, sort, asc=False, note=""):
        lines.append(f"\n--- {title}: {len(df)} ---" + (f"  {note}" if note else ""))
        if len(df): lines.append(df.sort_values(sort, ascending=asc)[cols].round(2).to_string())
    cA = ["px", "chg%", "piv", "vs_pivot%", "rvol", "pos", "adr", "stack_d", "contr", "dryup", "off52%", "addv_M", "precision", "industry"]
    block("A  BREAKOUT (close clears the 15d pivot, RVOL>=1.1, stacked >=5d)", A, cA, "rvol", note="precision=YES is the validated cohort (mean R +0.67 vs +0.16 for all A); the rest is context")
    block("B  CATALYST (gap/8%+ day on >=2x vol, clears pivot, closes near high)", B, ["px", "chg%", "gap%", "piv", "vs_pivot%", "rvol", "pos", "adr", "stack_d", "off52%", "addv_M", "industry"], "rvol", note="do not chase the AH pop; require the pivot to HOLD in the cash session")
    block("C  EXHAUSTION -- DAILY PROXY ONLY (validation 2019-26: this bar is a CONTINUATION signal on daily data, +1.8%/21s; do NOT short it from the daily bar)", Cx, ["px", "chg%", "rvol", "pos", "ext20_adr", "adr", "off52%", "addv_M", "industry"], "rvol", note="candidate-narrower for an intraday 0DTE fade only")
    block("SETUP (stacked, within 5% under the pivot, contraction <=0.6x, volume dry-up <=0.8x)", S, ["px", "piv", "vs_pivot%", "contr", "dryup", "adr", "stack_d", "off52%", "addv_M", "precision", "industry"], "vs_pivot%", note="set alerts at the pivot; this is the list to be early on")
    txt = "\n".join(lines); print(txt)
    OUT.mkdir(exist_ok=True); (OUT / f"adhikary_scan_{d.date()}.txt").write_text(txt + "\n")

if __name__ == "__main__":
    main()
