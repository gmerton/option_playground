#!/usr/bin/env python3
"""
RISK-ARCHITECTURE TEST — does the payoff structure carry the edge, or the entry?

HYPOTHESIS (from the Luk/Qullamaggie/Minervini lineage)
    A breakout setup's job is not to FORECAST. Its job is to locate a tight, logical
    invalidation level. Tight stop -> small risk per share -> large position at fixed
    fractional risk -> a mediocre entry becomes a convex payoff.

    If true: holding a deliberately DUMB entry fixed and varying only the risk
    architecture should produce positive expectancy at tight stops with a trailing exit,
    and flat-to-negative at wide stops with a fixed target.

DESIGN
    Entry is held constant and is intentionally weak: "close is the highest close of the
    trailing 20 days, while in Stage 2." No pattern quality, no theme, no relative-strength
    ranking, no discretion. Every cell in the grid trades the SAME trade list. Only the
    stop and the exit differ. The deliverable is therefore the DIFFERENCE BETWEEN CELLS,
    not any cell's absolute number.

    That framing is what neutralizes the universe bias: longhistory.parquet is the 299 most
    liquid names as of today, so it is survivorship- and selection-biased upward. The bias
    inflates every cell by roughly the same amount and largely cancels in the comparison.
    Absolute returns here are NOT a deliverable.

PATH-ORDER AMBIGUITY — deliberately engineered out
    The gap study could not order intraday touches. Here every exit rule is evaluated on the
    CLOSE and the stop is the only intraday event, so within any day the order is known:
    stop first (intraday), exit second (on the close). No brackets needed. The one modelled
    concession to reality is gap-through: if the day opens below the stop, the fill is the
    open, not the stop.

TWO SIZING CONVENTIONS, because they disagree and the disagreement is the finding
    mean %      — fixed NOTIONAL per position. What a "just buy $10k of it" trader gets.
    acct bp     — fixed FRACTIONAL RISK (Luk's 0.3%), position = risk% / stop%, capped at a
                  30% position because a 1% stop would otherwise imply 30% of the account in
                  one name. This is the metric the hypothesis is actually about.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/run_arch_test.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

SRC = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
HERE = "data/carter_mastering_the_trade/backtests/risk_architecture"

MAX_HOLD = 250          # trading days
COOLDOWN = 10           # no re-entry in the same name within N days of a prior signal
COST_BP = 10.0          # round-trip: spread + commission on a single-name equity
RISK_PCT = 0.003        # Luk's ~0.3% of account risked per trade
MAX_POS = 0.30          # position-size ceiling (Luk's stated 20-30% band, top of it)

# Two families, and the contrast between them is the point.
#   "pct"/"atr"  — an ARBITRARY distance from an arbitrary entry price. Tight, but the level
#                  means nothing; price has no reason to respect it.
#   "level"      — a STRUCTURAL invalidation point: the low of the breakout bar, a recent swing
#                  low, the rising 20-EMA. This is what Luk actually means by "a logical stop",
#                  and the width is whatever the structure says it is.
STOPS = [("1.0%", "pct", 0.010), ("1.5%", "pct", 0.015), ("3.0%", "pct", 0.030),
         ("5.0%", "pct", 0.050), ("1.0ATR", "atr", 1.0), ("2.0ATR", "atr", 2.0),
         ("bar low", "level", "barlow"), ("10d low", "level", "low10"),
         ("20d low", "level", "low20"), ("20EMA", "level", "ema20")]

STOP_BUFFER = 0.001     # place the stop 10 bp under the structural level, not exactly on it
MAX_STOP_PCT = 0.25     # discard signals whose structural stop is absurdly far away

EXITS = ["close<10EMA", "close<20EMA", "close<50EMA", "hold 20d", "target 2R", "target 4R"]


def first_true(mask: np.ndarray) -> int:
    """Index of first True, or -1."""
    idx = np.argmax(mask)
    return int(idx) if mask[idx] else -1


def prep(g: pd.DataFrame) -> dict:
    c, h, l, o = (g[x].to_numpy(float) for x in ("close", "high", "low", "open"))
    s = pd.Series(c)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    ma = {n: s.rolling(n, min_periods=n).mean().to_numpy() for n in (50, 150, 200)}
    ema = {n: s.ewm(span=n, adjust=False).mean().to_numpy() for n in (10, 20, 50)}
    return dict(
        c=c, h=h, l=l, o=o,
        atr=pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy(),
        ma50=ma[50], ma150=ma[150], ma200=ma[200],
        ma200_up=ma[200] > np.r_[[np.nan] * 20, ma[200][:-20]],
        hi52=s.rolling(252, min_periods=200).max().to_numpy(),
        lo52=s.rolling(252, min_periods=200).min().to_numpy(),
        hi20=s.rolling(20, min_periods=20).max().to_numpy(),
        low10=pd.Series(l).rolling(10, min_periods=10).min().to_numpy(),
        low20=pd.Series(l).rolling(20, min_periods=20).min().to_numpy(),
        ema20=ema[20],
        dv=(g["close"] * g["volume"]).rolling(50, min_periods=50).mean().to_numpy(),
        below={n: c < ema[n] for n in (10, 20, 50)},
        dates=g["date"].to_numpy(),
    )


def signals(a: dict) -> np.ndarray:
    """Deliberately dumb entry: 20-day closing high, inside a Stage-2 trend template."""
    stage2 = ((a["c"] > a["ma50"]) & (a["ma50"] > a["ma150"]) & (a["ma150"] > a["ma200"])
              & a["ma200_up"] & (a["c"] >= 1.25 * a["lo52"]) & (a["c"] >= 0.75 * a["hi52"]))
    raw = stage2 & (a["c"] >= a["hi20"]) & (a["dv"] >= 5e6) & (a["c"] >= 5.0)
    raw = np.nan_to_num(raw, nan=False).astype(bool)
    idx = np.flatnonzero(raw)
    idx = idx[(idx + 1 + MAX_HOLD) < len(a["c"])]     # need full forward window
    keep, last = [], -10**9
    for i in idx:                                      # cooldown
        if i - last >= COOLDOWN:
            keep.append(i)
            last = i
    return np.array(keep, dtype=int)


def run(a: dict, sig: np.ndarray, tkr: str) -> list[dict]:
    out = []
    c, h, l, o, atr = a["c"], a["h"], a["l"], a["o"], a["atr"]
    n = len(c)
    for t in sig:
        e = t + 1
        entry = o[e]
        if not np.isfinite(entry) or entry <= 0 or not np.isfinite(atr[t]):
            continue
        end = min(e + MAX_HOLD, n)
        seg = slice(e, end)
        lo_s, op_s, cl_s = l[seg], o[seg], c[seg]
        m = end - e
        if m < 5:
            continue

        for sname, skind, sval in STOPS:
            if skind == "pct":
                sp = entry - sval * entry
            elif skind == "atr":
                sp = entry - sval * atr[t]
            else:
                lvl = {"barlow": l[t], "low10": a["low10"][t],
                       "low20": a["low20"][t], "ema20": a["ema20"][t]}[sval]
                if not np.isfinite(lvl):
                    continue
                sp = lvl * (1.0 - STOP_BUFFER)
            risk = entry - sp
            if risk <= 0:
                continue
            stop_pct = risk / entry
            if stop_pct > MAX_STOP_PCT:
                continue
            hit = lo_s <= sp
            sday = first_true(hit)

            for ex in EXITS:
                if ex.startswith("close<"):
                    ema_n = int(ex.split("<")[1].replace("EMA", ""))
                    eday = first_true(a["below"][ema_n][seg])
                elif ex == "hold 20d":
                    eday = min(19, m - 1)
                else:
                    mult = float(ex.split()[1].rstrip("R"))
                    eday = first_true(cl_s >= entry + mult * risk)

                # stop is intraday, exit is on the close -> within a day, stop wins
                if sday >= 0 and (eday < 0 or sday <= eday):
                    px = op_s[sday] if op_s[sday] <= sp else sp   # gap-through fills at the open
                    k, why = sday, "stop"
                elif eday >= 0:
                    px, k, why = cl_s[eday], eday, "exit"
                else:
                    px, k, why = cl_s[m - 1], m - 1, "timeout"

                ret = px / entry - 1.0 - COST_BP / 1e4
                pos = min(MAX_POS, RISK_PCT / stop_pct)
                out.append(dict(ticker=tkr, date=a["dates"][t], stop=sname, exit=ex,
                                entry_date=a["dates"][e], exit_date=a["dates"][e + k],
                                ret=ret, R=ret / stop_pct, hold=k + 1, why=why,
                                stop_pct=stop_pct, pos=pos, acct=pos * ret))
    return out


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    def agg(g):
        r, a_ = g["ret"], g["acct"]
        return pd.Series({
            "n": len(g), "win%": 100 * (r > 0).mean(),
            "mean_%": 100 * r.mean(), "med_hold": g["hold"].median(),
            "mean_R": g["R"].mean(),
            "acct_bp": 1e4 * a_.mean(),
            "t": a_.mean() / (a_.std(ddof=1) / np.sqrt(len(g))) if a_.std(ddof=1) > 0 else np.nan,
            "stop_out%": 100 * (g["why"] == "stop").mean(),
            "pos%": 100 * g["pos"].mean(),
            "stop_wid%": 100 * g["stop_pct"].mean(),
            # capital efficiency: account bp earned per DAY the capital is tied up.
            # Without this, long holds win by construction — they are simply 30x the bet.
            "bp_per_day": 1e4 * a_.mean() / g["hold"].mean(),
        })
    return df.groupby(["stop", "exit"], observed=True).apply(agg)


def main() -> None:
    px = pd.read_parquet(SRC).dropna(subset=["open", "close"])
    px = px.sort_values(["ticker", "date"])
    print(f"universe: {px.ticker.nunique()} names  {px.date.min().date()} -> {px.date.max().date()}")

    trades, nsig = [], 0
    for tkr, g in px.groupby("ticker"):
        if len(g) < 400:
            continue
        a = prep(g.reset_index(drop=True))
        sig = signals(a)
        nsig += len(sig)
        trades += run(a, sig, tkr)

    df = pd.DataFrame(trades)
    df.to_parquet(f"{HERE}/arch_trades.parquet", index=False)
    ncells = len(STOPS) * len(EXITS)
    print(f"signals: {nsig:,} (same trade list in every cell)   "
          f"rows: {len(df):,} = signals x {ncells} architecture cells")
    print(f"date range of entries: {df.date.min().date()} -> {df.date.max().date()}")

    s = summarize(df).reset_index()

    print("\n" + "=" * 110)
    print("A.  ACCOUNT RETURN PER TRADE, bp  —  fixed 0.3% risk, position capped at 30%")
    print("    (this is the metric the hypothesis is about)")
    print("=" * 110)
    print(s.pivot(index="stop", columns="exit", values="acct_bp")
          .reindex([x[0] for x in STOPS])[EXITS].round(2).to_string())

    print("\n  t-stats:")
    print(s.pivot(index="stop", columns="exit", values="t")
          .reindex([x[0] for x in STOPS])[EXITS].round(2).to_string())

    print("\n" + "=" * 110)
    print("B.  MEAN RETURN PER TRADE, %  —  fixed NOTIONAL (ignores the sizing lever)")
    print("=" * 110)
    print(s.pivot(index="stop", columns="exit", values="mean_%")
          .reindex([x[0] for x in STOPS])[EXITS].round(3).to_string())

    print("\n" + "=" * 110)
    print("B2. ACCOUNT bp PER DAY OF CAPITAL TIED UP  —  the same numbers, time-normalized")
    print("    A 60-day hold is 30x the capital commitment of a 2-day hold. Table A does not")
    print("    know that; this one does. Still not a portfolio result — see run_portfolio.py.")
    print("=" * 110)
    print(s.pivot(index="stop", columns="exit", values="bp_per_day")
          .reindex([x[0] for x in STOPS])[EXITS].round(3).to_string())

    print("\n" + "=" * 110)
    print("C.  MECHANICS — win rate / stop-out rate / median hold / implied position size")
    print("=" * 110)
    for metric, label in [("win%", "win rate %"), ("stop_out%", "stopped out %"),
                          ("med_hold", "median hold, days"), ("mean_R", "mean R (uncapped)")]:
        print(f"\n  {label}:")
        print(s.pivot(index="stop", columns="exit", values=metric)
              .reindex([x[0] for x in STOPS])[EXITS].round(2).to_string())

    print("\n  mean stop width % and implied position size at 0.3% risk (%, capped at 30):")
    print(pd.DataFrame({
        "mean_stop_width%": s.groupby("stop")["stop_wid%"].mean(),
        "mean_position%": s.groupby("stop")["pos%"].mean(),
        "n_signals_usable": df.groupby("stop")["ret"].size() // len(EXITS),
    }).reindex([x[0] for x in STOPS]).round(2).to_string())

    print("\n" + "=" * 110)
    print("D.  BENCHMARKS — is any of this better than doing nothing clever?")
    print("=" * 110)
    base = df[(df["stop"] == "5.0%") & (df["exit"] == "hold 20d")]
    print(f"  same entries, 20-day hold, 5% stop : {100*base.ret.mean():+.3f}% per trade")
    # naive: same entries, no stop at all, fixed holds
    for hold in (5, 10, 20, 60):
        rows = []
        for tkr, g in px.groupby("ticker"):
            if len(g) < 400:
                continue
            a = prep(g.reset_index(drop=True))
            for t in signals(a):
                e = t + 1
                k = min(e + hold, len(a["c"]) - 1)
                rows.append(a["c"][k] / a["o"][e] - 1 - COST_BP / 1e4)
        r = pd.Series(rows)
        print(f"  same entries, NO STOP, {hold:2}-day hold  : {100*r.mean():+.3f}% per trade   "
              f"(win {100*(r>0).mean():.1f}%, t={r.mean()/(r.std()/np.sqrt(len(r))):+.1f})")

    print(f"\n\nwrote {HERE}/arch_trades.parquet")


if __name__ == "__main__":
    main()
