"""Archetype C — intraday entry-trigger analysis (the one lever daily data can't settle).

Reads 1-min RTH bars saved by `ibkr_bot/fetch_intraday.py --end-date <day>` and, for
each candidate entry trigger, measures what a 0DTE PUT would have captured:

  triggers (all fire only AFTER the morning high is in -- we fade a FAILED new high):
    - lose_open : first bar that trades back below the session OPEN
    - lose_vwap : first bar that CLOSES below running VWAP
    - lose_or5  : first bar that breaks below the first-5-min opening-range LOW

For each: entry time/price, then capture to (a) session LOW (MFE, best 0DTE exit) and
(b) session CLOSE (lazy hold-to-bell). Benchmarks: 'short_at_open' (naive) and the
'perfect' open->low. Put P&L moves opposite to price, so capture% = (entry-target)/entry.
"""
import os, sys, glob
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot", "data")
CASES = [("SMCI", "2024-02-16"), ("NVDA", "2024-03-08")]


def load(sym, day):
    # tolerate the exact date or any file for that symbol+date
    hits = glob.glob(os.path.join(DATA, f"{sym}_{day}*_1min.csv"))
    if not hits:
        return None
    df = pd.read_csv(hits[0], parse_dates=["time"])
    d0 = df["time"].dt.date.iloc[-1]
    df = df[df["time"].dt.date == d0].reset_index(drop=True)
    # running VWAP from typical price
    tp = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    return df


def first_after(df, hi_idx, mask):
    """first index strictly after the high where mask is True"""
    cand = df.index[(df.index > hi_idx) & mask]
    return int(cand[0]) if len(cand) else None


def analyze(sym, day, df):
    o = df["open"].iloc[0]
    hi_idx = int(df["high"].idxmax())
    low = df["low"].min()
    close = df["close"].iloc[-1]
    or5_low = df["low"].iloc[:5].min()
    hi_px = df["high"].iloc[hi_idx]
    print(f"\n=== {sym} {day} ===  {len(df)} bars | open {o:.2f}  high {hi_px:.2f}@{df['time'].iloc[hi_idx]:%H:%M}  "
          f"low {low:.2f}  close {close:.2f}")
    print(f"  benchmarks (put capture): short_at_open {(o-low)/o*100:+.1f}% to low / {(o-close)/o*100:+.1f}% to close"
          f" | perfect open->low {(o-low)/o*100:.1f}%")
    triggers = {
        "lose_open": df["close"] < o,
        "lose_vwap": df["close"] < df["vwap"],
        "lose_or5":  df["close"] < or5_low,
    }
    rows = []
    for name, mask in triggers.items():
        i = first_after(df, hi_idx, mask)
        if i is None:
            rows.append({"trigger": name, "fired": "no"}); continue
        ent = df["close"].iloc[i]
        t = df["time"].iloc[i]
        cap_low = (ent - low) / ent * 100
        cap_close = (ent - close) / ent * 100
        rows.append({
            "trigger": name, "fired": f"{t:%H:%M}", "entry_px": round(ent, 2),
            "delay_min": int(i - hi_idx),
            "cap_to_low_%": round(cap_low, 1),
            "cap_to_close_%": round(cap_close, 1),
            "give_up_vs_perfect_pp": round((o-low)/o*100 - cap_low, 1),
        })
    return pd.DataFrame(rows)


def main():
    missing = [f"{s} {d}" for s, d in CASES if load(s, d) is None]
    if missing:
        print(f"Missing 1-min CSVs for: {missing}")
        print(f"Pull them first (Gateway up):")
        for s, d in CASES:
            if f"{s} {d}" in missing:
                print(f"  IB_PORT=4001 IB_ALLOW_LIVE=1 IB_CLIENT_ID=41 "
                      f".venv/bin/python3 ibkr_bot/fetch_intraday.py {s} --end-date {d}")
        if len(missing) == len(CASES):
            sys.exit(1)
    for sym, day in CASES:
        df = load(sym, day)
        if df is None:
            continue
        res = analyze(sym, day, df)
        with pd.option_context("display.width", 200, "display.max_columns", None):
            print(res.to_string(index=False))


if __name__ == "__main__":
    main()
