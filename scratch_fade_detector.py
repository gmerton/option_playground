"""Archetype C (climactic-exhaustion fade) — daily-bar detector / gate calibration.

We CANNOT backtest the intraday entry trigger (no 2024 intraday available: Tradier
keeps ~20-40d, Polygon plan blocks it). What daily bars CAN settle: the SETUP gates
(extension above the 10-SMA, prior run-up) and the REVERSAL-BAR shape (new high that
fails, close near the low, wide range, climactic volume), plus the daily-capturable
confirmation (next-day follow-through down).

Run over the 2024 big-mover universe to (a) confirm it re-surfaces SMCI 2/16 + NVDA 3/8,
(b) see what else fires, (c) measure next-day follow-through. Gates are LOOSE knobs at
top — we dial them in together, not hard-code an opinion yet.
"""
import os, asyncio, statistics as st
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient

# ---- tunable gates (deliberately loose; calibrate with the user) ----
EXT10_MIN   = 0.10   # prior close must be >= +10% above the 10-SMA (extension/parabola)
NEWHIGH_LB  = 10     # day's high must exceed the highest high of the prior N days
CLOSE_PCTL  = 0.20   # close must sit in the bottom 20% of the day's range (rejection)
RANGE_MIN   = 0.05   # day range >= 5% of the open (wide-range bar)
VOL_MULT    = 2.0    # volume >= 2.0x the 50-day average (climactic)
RED_BAR     = True   # require close < open (reversed through the open)
# ---------------------------------------------------------------------

UNIVERSE = ["NVDA","SMCI","MSTR","ARM","COIN","GLD","AAPL","BRK/B","IWM","GEV","APP",
            "BABA","DJT","PLTR","TSLA","COST",            # Adhikary names
            "META","AMD","AVGO","DELL","CVNA","AFRM","ANF","MARA","CELH","NVO"]  # extra 2024 movers

START, END = "2023-09-01", "2024-12-31"   # ~4mo lead for SMA warmup, scan all of 2024
SCAN_FROM = "2024-01-01"


async def hist(client, sem, sym):
    async with sem:
        try:
            r = await client.get_json("/markets/history", {
                "symbol": sym, "interval": "daily", "start": START, "end": END})
        except Exception as e:
            return sym, None, f"err:{type(e).__name__}"
    h = (r or {}).get("history")
    if not h or h == "null":
        return sym, None, "no_hist"
    d = h.get("day")
    return sym, (d if isinstance(d, list) else [d]), "ok"


def sma(vals, n, i):
    return sum(vals[i-n+1:i+1]) / n if i+1 >= n else None


def scan(sym, days):
    closes = [d["close"] for d in days]
    highs  = [d["high"] for d in days]
    lows   = [d["low"] for d in days]
    opens  = [d["open"] for d in days]
    vols   = [d["volume"] for d in days]
    dates  = [d["date"] for d in days]
    hits = []
    for i in range(1, len(days)):
        if dates[i] < SCAN_FROM:
            continue
        s10 = sma(closes, 10, i-1)          # extension known at prior close (pre-market setup)
        if s10 is None:
            continue
        ext10 = (closes[i-1] - s10) / s10
        o, h, l, c, v = opens[i], highs[i], lows[i], closes[i], vols[i]
        rng = h - l
        if rng <= 0:
            continue
        avg50 = st.mean(vols[max(0, i-50):i])
        prior_high = max(highs[max(0, i-NEWHIGH_LB):i])
        close_pctl = (c - l) / rng
        # gate checks
        g = {
            "ext":     ext10 >= EXT10_MIN,
            "newhigh": h > prior_high,
            "reject":  close_pctl <= CLOSE_PCTL,
            "wide":    rng / o >= RANGE_MIN,
            "vol":     v / avg50 >= VOL_MULT,
            "red":     (c < o) if RED_BAR else True,
        }
        if all(g.values()):
            ft = (closes[i+1] - c) / c * 100 if i+1 < len(days) else None  # next-day follow-through
            hits.append({
                "ticker": sym, "date": dates[i],
                "ext10_%": round(ext10*100, 0),
                "gap_%": round((o-closes[i-1])/closes[i-1]*100, 1),
                "newhigh_over_open_%": round((h-o)/o*100, 1),
                "open_to_close_%": round((c-o)/o*100, 1),
                "close_pctl": round(close_pctl, 2),
                "range_%": round(rng/o*100, 1),
                "vol_x": round(v/avg50, 2),
                "nextday_ft_%": round(ft, 1) if ft is not None else None,
            })
    return hits


async def main():
    key = os.environ["TRADIER_API_KEY"]
    sem = asyncio.Semaphore(5)
    async with TradierClient(api_key=key) as client:
        res = await asyncio.gather(*[hist(client, sem, s) for s in UNIVERSE])
    all_hits, missing = [], []
    for sym, days, status in res:
        if status != "ok" or not days:
            missing.append((sym, status)); continue
        all_hits += scan(sym, days)
    df = pd.DataFrame(all_hits)
    print(f"Gates: ext10>={EXT10_MIN:.0%}, newhigh(>{NEWHIGH_LB}d), close<=bottom {CLOSE_PCTL:.0%} of range, "
          f"range>={RANGE_MIN:.0%}, vol>={VOL_MULT}x, red={RED_BAR}")
    print(f"Universe {len(UNIVERSE)} tickers, scan {SCAN_FROM}..{END}.  Missing: {missing}\n")
    if df.empty:
        print("No hits. Loosen a gate."); return
    df = df.sort_values(["date", "ticker"]).reset_index(drop=True)
    with pd.option_context("display.width", 200, "display.max_columns", None, "display.max_rows", None):
        print(df.to_string(index=False))
    ok_ft = df["nextday_ft_%"].dropna()
    print(f"\n{len(df)} fade-signal days across {df['ticker'].nunique()} tickers.")
    print(f"Next-day follow-through DOWN: {(ok_ft<0).sum()}/{len(ok_ft)} "
          f"({(ok_ft<0).mean()*100:.0f}%); median {ok_ft.median():+.1f}%")
    print(f"Re-surfaced the two known cases: "
          f"SMCI 2024-02-16 {'YES' if ((df.ticker=='SMCI')&(df.date=='2024-02-16')).any() else 'NO'}, "
          f"NVDA 2024-03-08 {'YES' if ((df.ticker=='NVDA')&(df.date=='2024-03-08')).any() else 'NO'}")
    df.to_csv("data/studies/Adhikary/fade_signals_2024.csv", index=False)


if __name__ == "__main__":
    asyncio.run(main())
