"""Archetype C — intraday entry-trigger + invalidation analysis (1-min bars).

The daily detector (`scratch_fade_detector.py`) has NO next-day edge (coin flip). But
Tito exits 0DTE puts INTRADAY, so the real question is what an intraday trigger captures
to the SAME-SESSION low, and how often it gets faked out by a V-reversal.

Reads 1-min RTH bars saved by `ibkr_bot/fetch_intraday.py --end-date <day>` for every
2024 detector hit. Models the winning trigger (lose_vwap = first bar closing below running
VWAP, AFTER the morning high) for a 0DTE PUT, with the playbook invalidation:
**a reclaim of the high-of-day (HOD) is the stop.** Put P&L on the underlying moves
opposite to price: capture% = (entry - exit) / entry.

Policies measured per case:
  MFE    : best intraday exit = lowest low reached BEFORE HOD is reclaimed (upper bound;
           Tito's "sell into weakness" lands near here).
  stop   : if HOD is reclaimed after entry, exit at HOD (a loss); else exit at session close.
           The no-skill mechanical version (invalidation stop only, no profit-taking).

Caveat: capture% is the UNDERLYING move. A real 0DTE put is convex (delta accelerates as it
goes ITM) so true put P&L > underlying% on winners, but IV crush / theta cut into it. Use
capture% for trigger comparison, not as literal option return.
"""
import os, glob
import numpy as np
import pandas as pd
from scipy.stats import norm

CLOSE_T = pd.Timestamp("16:00").time()
TRADING_MIN_YEAR = 252 * 390   # annualized IV is quoted in trading time, not calendar


def _t_years(ts):
    """TRADING years from bar timestamp to 16:00 ET expiry (0DTE). Calendar time is
    wrong intraday -- it counts dead overnight hours and collapses the premium."""
    close_dt = pd.Timestamp.combine(ts.date(), CLOSE_T)
    if ts.tz is not None:
        close_dt = close_dt.tz_localize(ts.tz)
    mins = max((close_dt - ts).total_seconds() / 60.0, 0.0)
    return mins / TRADING_MIN_YEAR


def bs_put(S, K, T, sigma, r=0.0):
    """Black-Scholes put; T in years. T<=0 -> intrinsic."""
    if T <= 0 or sigma <= 0:
        return max(K - S, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot", "data")
SIGNALS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "studies", "Adhikary", "fade_signals_2024.csv")
KNOWN = {("SMCI", "2024-02-16"), ("NVDA", "2024-03-08")}  # the 2 in-sample Tito cases


def load(sym, day):
    hits = glob.glob(os.path.join(DATA, f"{sym}_{day}*_1min.csv"))
    if not hits:
        return None
    df = pd.read_csv(hits[0], parse_dates=["time"])
    d0 = df["time"].dt.date.iloc[-1]
    df = df[df["time"].dt.date == d0].reset_index(drop=True)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    return df


ARM_TIME = pd.Timestamp("09:44").time()   # ignore first-15-min noise
MAX_ENTRIES = 3                           # re-entries allowed per day


def _vwap_loss_after(df, start_i):
    """first bar at/after start_i (and after ARM_TIME) that closes below VWAP."""
    for j in range(start_i, len(df)):
        if df["time"].iloc[j].time() <= ARM_TIME:
            continue
        if df["close"].iloc[j] < df["vwap"].iloc[j]:
            return j
    return None


def analyze(sym, day, df):
    """Fade-the-failed-new-high with re-entry. Each entry is a 0DTE put:
    enter on a VWAP-loss; a NEW high above the high-at-entry is the stop (the failed
    high turned out not to be the top). After a stop, re-arm and fade the NEXT failed
    high, up to MAX_ENTRIES. The final un-stopped leg exits at close (mechanical) or at
    its intraday low (MFE / 'sell into weakness'). Day P&L sums the legs (equal unit each)."""
    close = df["close"].iloc[-1]
    close_t = df["time"].iloc[-1]
    trades = []          # each leg: entry/exit times + underlying prices
    cursor, n = 0, len(df)
    while len(trades) < MAX_ENTRIES:
        i = _vwap_loss_after(df, cursor)
        if i is None:
            break
        ent = df["close"].iloc[i]
        ent_t = df["time"].iloc[i]
        hi_at_entry = df["high"].iloc[:i + 1].max()
        post = df.iloc[i + 1:]
        reclaim = post.index[post["high"] > hi_at_entry]
        stop_idx = int(reclaim[0]) if len(reclaim) else None
        end_i = stop_idx if stop_idx is not None else n - 1
        low_rel = int(df["low"].iloc[i:end_i + 1].values.argmin())
        mfe_i = i + low_rel
        mfe_low, mfe_t = df["low"].iloc[mfe_i], df["time"].iloc[mfe_i]
        if stop_idx is not None:
            trades.append({"t": ent_t, "ent": ent, "kind": "stop",
                           "exit": hi_at_entry, "exit_t": df["time"].iloc[stop_idx],
                           "mfe": mfe_low, "mfe_t": mfe_t})
            cursor = stop_idx + 1          # re-arm after the new high
        else:
            trades.append({"t": ent_t, "ent": ent, "kind": "hold",
                           "exit": close, "exit_t": close_t,
                           "mfe": mfe_low, "mfe_t": mfe_t})
            break                          # held to close -> done for the day

    if not trades:
        return None

    legs_mech = [(t["ent"] - t["exit"]) / t["ent"] * 100 for t in trades]
    legs_mfe = [(t["ent"] - t["mfe"]) / t["ent"] * 100 if t["kind"] == "hold"
                else (t["ent"] - t["exit"]) / t["ent"] * 100 for t in trades]
    n_stops = sum(1 for t in trades if t["kind"] == "stop")
    path = " -> ".join(
        f"{t['t']:%H:%M}{'X' if t['kind']=='stop' else '✓'}" for t in trades)
    return {
        "sym": sym, "day": day, "k": "*" if (sym, day) in KNOWN else "",
        "n_leg": len(trades), "n_stop": n_stops,
        "net_mech_%": round(sum(legs_mech), 1),
        "net_mfe_%": round(sum(legs_mfe), 1),
        "last": trades[-1]["kind"], "path": path,
        "_trades": trades,
    }


def price_day(row, sigma, exit_mode, haircut=0.0):
    """Reprice each leg as an ATM 0DTE put (K = entry underlying). exit_mode:
    'mech' = stop legs exit at the new high, final leg at close (intrinsic);
    'mfe'  = stop legs same, final leg sold into its intraday low.
    haircut = round-trip bid/ask cost (pay ask = mid*(1+h), sell bid = mid*(1-h)).
    Returns (sum_leg_return_%, list_of_leg_returns_%). Each leg risks 1 unit of
    premium; day total is the sum (capital re-deployed after a stop)."""
    legs = []
    for t in row["_trades"]:
        K = t["ent"]                                   # ATM at entry
        pe = bs_put(t["ent"], K, _t_years(t["t"]), sigma) * (1 + haircut)
        if t["kind"] == "stop":
            Sx, tx = t["exit"], t["exit_t"]
        elif exit_mode == "mfe":
            Sx, tx = t["mfe"], t["mfe_t"]
        else:
            Sx, tx = t["exit"], t["exit_t"]
        px = bs_put(Sx, K, _t_years(tx), sigma) * (1 - haircut)
        legs.append((px / pe - 1.0) * 100 if pe > 0 else 0.0)
    return sum(legs), legs


IV_SCEN = [0.60, 0.90, 1.20]   # annualized 0DTE IV scenarios for high-flyers


def main():
    sig = pd.read_csv(SIGNALS, parse_dates=["date"])
    sig["date"] = sig["date"].dt.strftime("%Y-%m-%d")
    rows = []
    for _, r in sig.iterrows():
        df = load(r["ticker"], r["date"])
        if df is None:
            continue
        res = analyze(r["ticker"], r["date"], df)
        if res:
            rows.append(res)

    disp = pd.DataFrame([{k: v for k, v in r.items() if k != "_trades"} for r in rows])
    with pd.option_context("display.width", 240, "display.max_columns", None):
        print(disp.to_string(index=False))

    ok = disp
    print(f"\n=== UNDERLYING capture ({len(ok)} cases; re-entry up to {MAX_ENTRIES} legs) ===")
    print(f"  MECH: median {ok['net_mech_%'].median():.1f}%  mean {ok['net_mech_%'].mean():.1f}%  "
          f"win {(ok['net_mech_%']>0).sum()}/{len(ok)}")
    print(f"  MFE : median {ok['net_mfe_%'].median():.1f}%  mean {ok['net_mfe_%'].mean():.1f}%  "
          f"win {(ok['net_mfe_%']>0).sum()}/{len(ok)}")
    print(f"  avg legs/day {ok['n_leg'].mean():.1f}; re-entry days {(ok['n_stop']>0).sum()}/{len(ok)}")

    # --- option repricing: ATM 0DTE put, per IV scenario (mid, no costs) ---
    for mode in ("mech", "mfe"):
        print(f"\n=== 0DTE ATM PUT return, exit={mode}, MID (no costs) ===")
        for sigma in IV_SCEN:
            day_tot, worst_leg = [], []
            for r in rows:
                tot, legs = price_day(r, sigma, mode)
                day_tot.append(tot); worst_leg.append(min(legs))
            arr = np.array(day_tot)
            print(f"  IV {sigma*100:3.0f}%:  median {np.median(arr):+6.0f}%  mean {arr.mean():+6.0f}%  "
                  f"win {(arr>0).sum()}/{len(arr)}  worst-day {arr.min():+.0f}%  "
                  f"worst-leg {min(worst_leg):+.0f}%")

    # --- central realistic estimate: IV 90%, 10% round-trip haircut ---
    print(f"\n=== CENTRAL estimate: IV 90%, 10% round-trip bid/ask haircut ===")
    for mode in ("mech", "mfe"):
        day_tot, worst_leg = [], []
        for r in rows:
            tot, legs = price_day(r, 0.90, mode, haircut=0.10)
            day_tot.append(tot); worst_leg.append(min(legs))
        arr = np.array(day_tot)
        print(f"  exit={mode:4s}:  median {np.median(arr):+6.0f}%  mean {arr.mean():+6.0f}%  "
              f"win {(arr>0).sum()}/{len(arr)}  worst-day {arr.min():+.0f}%  "
              f"worst-leg {min(worst_leg):+.0f}%")


if __name__ == "__main__":
    main()
