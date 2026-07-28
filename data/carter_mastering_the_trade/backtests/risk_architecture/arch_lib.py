#!/usr/bin/env python3
"""
Shared machinery for the risk-architecture / selection-lift tests.

Holds the indicator prep, the entry-tier definitions, the 60-cell trade simulator and the
capital-constrained portfolio simulator, so `run_arch_test.py` (dumb entry only) and
`run_selection_lift.py` (all entry tiers) cannot drift apart.

ENTRY TIERS are strictly nested where possible, so the lift of each added gate is readable:

    DUMB        20-day closing high in a loose Stage 2. No pattern, no volume, no RS.
                The deliberately weak control from the first test.
    GATES       The repo's own universe gates, exactly as `premarket_watchlist.score_ticker`
                defines them: SMA50>SMA150>SMA200 & close>SMA50 [required],
                5d avg dollar volume >= $10M [required], ADR(20) >= 3.5% [optional-but-on].
                Entry fires on a 20-day closing high, same trigger as DUMB.
    BREAKOUT    GATES + a real pivot exists and today's close cleared it.
    CONFIRMED   BREAKOUT + volume >= 1.5x its trailing 50-day average.
    POTENT      CONFIRMED + EMA lead (9>21>50) + prior bar green + within +/-8% of pivot.
    LEADER      CONFIRMED + EMA lead + 1-month return > 15% + 3-month return > 30%.
    BOTH        POTENT and LEADER simultaneously — the top of the scorecard.

PIVOT DETECTION — vectorized, and provably identical to the production walk.
    `_detect_pivot` walks backward from the last bar, expanding the window while
    depth = (max-min)/max stays <= 25%, and breaks at the first violation. As the window
    grows, max is non-decreasing and min is non-increasing, so depth = 1 - min/max is
    MONOTONICALLY NON-DECREASING in window length. The first violation is therefore the
    only violation boundary, and base_len is just the COUNT of window lengths that pass.
    That turns an O(60) sequential walk per bar into 60 rolling min/max ops per ticker.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# --- production constants, mirrored from lib.interface.premarket_watchlist -----------
ADR_MIN = 3.5
DOLVOL_MIN = 10_000_000
VOL_CONFIRM_MULT = 1.5
VOL_AVG_LOOKBACK = 50
MAX_BASE_LEN, MIN_BASE_LEN, MAX_DEPTH = 60, 10, 0.25

# --- test configuration ---------------------------------------------------------------
MAX_HOLD = 250
COOLDOWN = 10
COST_BP = 10.0
RISK_PCT = 0.003
MAX_POS = 0.30
STOP_BUFFER = 0.001
MAX_STOP_PCT = 0.25

STOPS = [("1.0%", "pct", 0.010), ("1.5%", "pct", 0.015), ("3.0%", "pct", 0.030),
         ("5.0%", "pct", 0.050), ("1.0ATR", "atr", 1.0), ("2.0ATR", "atr", 2.0),
         ("bar low", "level", "barlow"), ("10d low", "level", "low10"),
         ("20d low", "level", "low20"), ("20EMA", "level", "ema20")]
EXITS = ["close<10EMA", "close<20EMA", "close<50EMA", "hold 20d", "target 2R", "target 4R"]
STOP_ORDER = [s[0] for s in STOPS]
ENTRY_ORDER = ["DUMB", "REQ-only", "GATES", "BREAKOUT", "CONFIRMED", "POTENT", "LEADER", "BOTH"]


def first_true(mask: np.ndarray) -> int:
    idx = np.argmax(mask)
    return int(idx) if mask[idx] else -1


def _roll(s: pd.Series, n: int, how: str) -> np.ndarray:
    return getattr(s.rolling(n, min_periods=n), how)().to_numpy()


def prep(g: pd.DataFrame) -> dict:
    c, h, l, o, v = (g[x].to_numpy(float) for x in ("close", "high", "low", "open", "volume"))
    cs, hs, ls, vs = pd.Series(c), pd.Series(h), pd.Series(l), pd.Series(v)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    ema = {n: cs.ewm(span=n, adjust=False).mean().to_numpy() for n in (9, 10, 20, 21, 50)}
    sma = {n: _roll(cs, n, "mean") for n in (50, 150, 200)}
    dv = cs * vs

    # ---- vectorized pivot: base_len = count of window lengths whose depth stays <= 25%
    n = len(c)
    rmax = np.full((MAX_BASE_LEN, n), np.nan)
    rmin = np.full((MAX_BASE_LEN, n), np.nan)
    for b in range(1, MAX_BASE_LEN + 1):
        rmax[b - 1] = _roll(hs, b, "max")
        rmin[b - 1] = _roll(ls, b, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        depth = 1.0 - rmin / rmax
    ok = np.nan_to_num(depth, nan=1.0) <= MAX_DEPTH
    base_len = ok.sum(axis=0)                                   # monotone => count == first break
    piv = np.where(base_len >= MIN_BASE_LEN,
                   rmax[np.clip(base_len - 1, 0, MAX_BASE_LEN - 1), np.arange(n)], np.nan)
    pivot_prev = np.r_[np.nan, piv[:-1]]                        # base built BEFORE today

    rng_pct = (h - l) / c * 100.0
    return dict(
        c=c, h=h, l=l, o=o, dates=g["date"].to_numpy(),
        atr=_roll(pd.Series(tr), 14, "mean"),
        sma50=sma[50], sma150=sma[150], sma200=sma[200],
        sma200_up=sma[200] > np.r_[[np.nan] * 20, sma[200][:-20]],
        hi52=_roll(cs, 252, "max"), lo52=_roll(cs, 252, "min"),
        hi20=_roll(cs, 20, "max"),
        low10=_roll(ls, 10, "min"), low20=_roll(ls, 20, "min"),
        ema20=ema[20],
        adr20=_roll(pd.Series(rng_pct), 20, "mean"),
        dolvol5=_roll(dv, 5, "mean"),
        dolvol50=_roll(dv, 50, "mean"),
        vol_ratio=v / np.r_[np.nan, _roll(vs, VOL_AVG_LOOKBACK, "mean")[:-1]],
        pivot=pivot_prev,
        ema_lead=(ema[9] > ema[21]) & (ema[21] > ema[50]),
        prev_green=np.r_[False, c[:-1] > o[:-1]],
        pct_1m=np.r_[[np.nan] * 22, c[22:] / c[:-22] - 1.0],
        pct_3m=np.r_[[np.nan] * 64, c[64:] / c[:-64] - 1.0],
        below={n_: c < ema[n_] for n_ in (10, 20, 50)},
    )


def entry_tiers(a: dict) -> dict[str, np.ndarray]:
    """Boolean arrays, one per entry tier. Nested where the scorecard nests them."""
    c = a["c"]
    T = lambda x: np.nan_to_num(x, nan=False).astype(bool)  # noqa: E731

    dumb = T((c > a["sma50"]) & (a["sma50"] > a["sma150"]) & (a["sma150"] > a["sma200"])
             & a["sma200_up"] & (c >= 1.25 * a["lo52"]) & (c >= 0.75 * a["hi52"])
             & (c >= a["hi20"]) & (a["dolvol50"] >= 5e6) & (c >= 5.0))

    stage2 = T((a["sma50"] > a["sma150"]) & (a["sma150"] > a["sma200"]) & (c > a["sma50"]))
    # required gates only — used to isolate how much of GATES' value is the ADR gate alone
    gates_noadr = T(stage2 & (a["dolvol5"] >= DOLVOL_MIN))
    gates = T(gates_noadr & (a["adr20"] >= ADR_MIN))

    gates_hi = T(gates & (c >= a["hi20"]))
    brk = T(gates & (a["pivot"] > 0) & (c >= a["pivot"]))
    conf = T(brk & (a["vol_ratio"] >= VOL_CONFIRM_MULT))

    dist = (c - a["pivot"]) / a["pivot"] * 100.0
    potent = T(conf & a["ema_lead"] & a["prev_green"] & (dist >= -8) & (dist <= 8))
    leader = T(conf & a["ema_lead"] & (a["pct_1m"] > 0.15) & (a["pct_3m"] > 0.30))

    return {"DUMB": dumb, "REQ-only": T(gates_noadr & (c >= a["hi20"])), "GATES": gates_hi, "BREAKOUT": brk, "CONFIRMED": conf,
            "POTENT": potent, "LEADER": leader, "BOTH": T(potent & leader)}


def to_indices(mask: np.ndarray, n: int) -> np.ndarray:
    """Signal bar indices, cooled down and with a full forward window available."""
    idx = np.flatnonzero(mask)
    idx = idx[(idx + 1 + MAX_HOLD) < n]
    keep, last = [], -10 ** 9
    for i in idx:
        if i - last >= COOLDOWN:
            keep.append(i)
            last = i
    return np.array(keep, dtype=int)


def _soonest(*days: int) -> int:
    """Earliest non-negative event index, or -1 if none fired."""
    hits = [d for d in days if d >= 0]
    return min(hits) if hits else -1


def run(a: dict, sig: np.ndarray, tkr: str, entry_name: str,
        regime_off: np.ndarray | None = None) -> list[dict]:
    """Simulate every (stop, exit) architecture on the same signal list.

    regime_off: optional bool array aligned to a['dates']. When supplied, a position is
    also closed on the first CLOSE where the market regime has turned off — evaluated on
    the close like every other exit, so the stop still takes precedence within a day and
    no path-order ambiguity is introduced.
    """
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
        rday = first_true(regime_off[seg]) if regime_off is not None else -1

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
            sday = first_true(lo_s <= sp)

            for ex in EXITS:
                if ex.startswith("close<"):
                    eday = first_true(a["below"][int(ex.split("<")[1][:-3])][seg])
                elif ex == "hold 20d":
                    eday = min(19, m - 1)
                else:
                    eday = first_true(cl_s >= entry + float(ex.split()[1].rstrip("R")) * risk)
                eday = _soonest(eday, rday)

                # stop is intraday, exit is on the close -> within a day the stop wins
                if sday >= 0 and (eday < 0 or sday <= eday):
                    px = op_s[sday] if op_s[sday] <= sp else sp      # gap-through fills at open
                    k, why = sday, "stop"
                elif eday >= 0:
                    px, k, why = cl_s[eday], eday, "exit"
                else:
                    px, k, why = cl_s[m - 1], m - 1, "timeout"

                ret = px / entry - 1.0 - COST_BP / 1e4
                out.append(dict(entry=entry_name, ticker=tkr, stop=sname, exit=ex,
                                entry_date=a["dates"][e], exit_date=a["dates"][e + k],
                                ret=ret, hold=k + 1, why=why, stop_pct=stop_pct,
                                pos=min(MAX_POS, RISK_PCT / stop_pct)))
    return out


def simulate(g: pd.DataFrame, slots: int = 10, max_gross: float = 1.0) -> dict:
    """Capital-constrained portfolio sim over one (entry, stop, exit) cell."""
    g = g.sort_values("entry_date")
    ent, ext = g["entry_date"].to_numpy(), g["exit_date"].to_numpy()
    ret, pos, hold = g["ret"].to_numpy(), g["pos"].to_numpy(), g["hold"].to_numpy()

    equity, open_pos, curve, pos_days = 1.0, [], [], []
    taken = skipped = 0
    for i in range(len(g)):
        now = ent[i]
        still = []
        for xd, notional, r in open_pos:
            if xd <= now:
                equity += notional * r
                curve.append((xd, equity))
            else:
                still.append((xd, notional, r))
        open_pos = still

        gross = sum(x[1] for x in open_pos)
        want = pos[i] * equity
        if len(open_pos) >= slots or gross + want > max_gross * equity or equity <= 0:
            skipped += 1
            continue
        open_pos.append((ext[i], want, ret[i]))
        pos_days.append(pos[i] * hold[i])
        taken += 1

    for xd, notional, r in sorted(open_pos):
        equity += notional * r
        curve.append((xd, equity))
    if not curve or equity <= 0:
        return {}

    cv = pd.DataFrame(curve, columns=["date", "eq"]).groupby("date")["eq"].last()
    yrs = (cv.index[-1] - cv.index[0]) / np.timedelta64(365, "D")
    if yrs <= 1:
        return {}
    dd = (cv / cv.cummax() - 1.0).min()
    dr = cv.resample("D").ffill().dropna().pct_change().dropna()
    ndays = np.busday_count(ent[0].astype("datetime64[D]"), ext[-1].astype("datetime64[D]"))
    cagr = 100 * (equity ** (1 / yrs) - 1)
    return {"taken": taken, "skipped": skipped,
            "fill%": 100 * taken / max(1, taken + skipped),
            "avg_expo%": 100 * sum(pos_days) / max(1, ndays),
            "final_x": equity, "CAGR%": cagr, "maxDD%": 100 * dd,
            "Sharpe": (dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else np.nan,
            "MAR": cagr / abs(100 * dd) if dd < 0 else np.nan}
