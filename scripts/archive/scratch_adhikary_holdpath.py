"""'When to hang tight' — path analysis of the HELD-to-expiry winners.

For each multi-day held-to-expiry trade, walk entry->expiry on DAILY bars and ask:
  - How much HEAT did hanging tight require? (worst close drawdown from entry = MAE_close,
    worst intraday dip = MAE_low)
  - Did any DAILY CLOSE break the trailing levels (breakout pivot / 10-EMA / 20-EMA)?
    The level the winners never lose on a close = the "hold while above it" rule; intraday
    pokes below it that recover by the close = the noise you can ignore.
Excludes the 2 exhaustion 0DTE puts (intraday-only, not a multi-day hold).
"""
import os, asyncio, statistics as st
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient

SYMAP = {"BTC": "IBIT"}
# held-to-expiry multi-day calls: (ticker, entry, expiry)
HELD = [
    ("NVDA","2024-01-08","2024-01-19"),("SMCI","2024-01-19","2024-01-26"),
    ("MSTR","2024-02-08","2024-02-16"),("COIN","2024-02-09","2024-03-15"),
    ("GLD","2024-03-01","2024-04-19"),("AAPL","2024-06-11","2024-06-21"),
    ("IWM","2024-07-11","2024-07-19"),("APP","2024-09-11","2024-09-20"),
    ("MSTR","2024-10-11","2024-10-18"),("PLTR","2024-11-05","2024-12-20"),
    ("TSLA","2024-11-05","2024-11-22"),("BTC","2024-11-06","2024-11-22"),
]


def ema(vals, n):
    k = 2 / (n + 1); out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


async def hist(c, sym, s, e):
    r = await c.get_json("/markets/history", {"symbol": sym, "interval": "daily", "start": s, "end": e})
    d = r["history"]["day"]; return d if isinstance(d, list) else [d]


async def analyze(c, ticker, entry, expiry):
    sym = SYMAP.get(ticker, ticker)
    days = await hist(c, sym, "2023-09-01", expiry)
    closes = [d["close"] for d in days]; highs = [d["high"] for d in days]
    lows = [d["low"] for d in days]; dates = [d["date"] for d in days]
    e10 = ema(closes, 10); e20 = ema(closes, 20)
    ei = dates.index(entry); xi = dates.index(expiry)
    entry_c = closes[ei]
    pivot = max(highs[max(0, ei-15):ei])           # local breakout pivot (N=15)
    hold = range(ei, xi + 1)
    # heat
    min_close = min(closes[i] for i in hold); min_low = min(lows[i] for i in hold)
    mae_close = (min_close - entry_c) / entry_c * 100
    mae_low = (min_low - entry_c) / entry_c * 100
    # daily-close breaks of each trailing level (after entry day)
    def first_break(level_fn):
        for i in range(ei + 1, xi + 1):
            if closes[i] < level_fn(i):
                return i
        return None
    br_piv = first_break(lambda i: pivot)
    br_10 = first_break(lambda i: e10[i])
    br_20 = first_break(lambda i: e20[i])
    # intraday pokes below 10EMA that CLOSED back above (the 'noise')
    intraday_pokes = sum(1 for i in range(ei + 1, xi + 1) if lows[i] < e10[i] <= closes[i])
    hold_days = xi - ei
    def pct(bi): return None if bi is None else round((bi - ei) / max(1, hold_days) * 100)
    return {
        "ticker": ticker, "entry": entry, "hold_days": hold_days,
        "mae_close_%": round(mae_close, 1), "mae_low_%": round(mae_low, 1),
        "close<pivot?": "—" if br_piv is None else f"d{br_piv-ei}",
        "close<10EMA?": "—" if br_10 is None else f"d{br_10-ei}",
        "close<20EMA?": "—" if br_20 is None else f"d{br_20-ei}",
        "intraday_pokes_<10EMA_that_held": intraday_pokes,
    }


async def main():
    key = os.environ["TRADIER_API_KEY"]
    async with TradierClient(api_key=key) as c:
        rows = []
        for t, e, x in HELD:
            rows.append(await analyze(c, t, e, x))
    df = pd.DataFrame(rows)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(df.to_string(index=False))
    print(f"\nHEAT you had to tolerate to hang tight (held winners, n={len(df)}):")
    print(f"  worst close drawdown from entry: median {df['mae_close_%'].median():.1f}%, "
          f"deepest {df['mae_close_%'].min():.1f}%")
    print(f"  worst INTRADAY dip from entry:   median {df['mae_low_%'].median():.1f}%, "
          f"deepest {df['mae_low_%'].min():.1f}%")
    print(f"\nDaily-CLOSE breaks during the winning holds (— = never broke):")
    for lvl in ["close<pivot?", "close<10EMA?", "close<20EMA?"]:
        never = (df[lvl] == "—").sum()
        print(f"  {lvl:14}: never broken in {never}/{len(df)} winners")
    print(f"  intraday pokes below 10EMA that CLOSED back above (noise): "
          f"{df['intraday_pokes_<10EMA_that_held'].sum()} total across the set")
    df.to_csv("data/studies/Adhikary/Adhikary_holdpath.csv", index=False)


if __name__ == "__main__":
    asyncio.run(main())
