#!/usr/bin/env python3
"""
LUK'S OWN ENTRIES, REPLAYED ON 1-MINUTE BARS WITH THE TRIGGER AND STOP HE NAMED (pre-registered 2026-10-03, before
any data pull or scoring). Creator method -> DISCOVERY track.

WHY. Gabe 2026-10-03: Luk's competition return is audited, so it is real; the question is where it comes from. Two
tests have already ruled out the codable versions: his picks bought at the close ~ our precision tier (look 2,
-0.22pp, t -0.07), and a generic Luk-style pullback entry with a 0.4-2% stop ~ beta (tight-stop survival, 13,410
entries, t +0.02). Neither used HIS trades at HIS trigger. This one does: every entry card where he named an intraday
trigger is replayed on the day he filled, and the trigger is scored against a random minute in the same name-day.
What it varies: only the ENTRY MINUTE (and the stop construction that comes with it). Name and day are held fixed, so
this measures his timing/trigger, not his selection (selection was the picks test).

EVENTS. data/martin_luk/trades/entry_cards.jsonl joined to the trade log on `key` with Gabe's worklist fixes applied
(run_luk_trade_pages.load: ticker_fixed / direction_fixed / fill_date_fixed / drops). Kept: state ok, a fill date,
an intraday-codable trigger, timeframe 1m / 5m / 15m / 60m (missing -> 5m, his most common; weekly / daily dropped).
Coverage count before scoring (2026-10-03): 71 such cards, 59 with 1-minute bars (44 long / 27 short before the bar
filter); 68 after requiring the trigger's side to match the logged side (41 long / 27 short). Bars: Polygon 1-min s3://gmerton-stock-data/backfill/intraday_1min/bars/<SYM>/ (2024-10 -> 2026-09),
falling back to data/cache/intraday_1min/<SYM>_<date>.parquet. Here the name-days are HIS, fixed in advance, so the
local cache's hindsight universe is not a selection problem.
⚠ He never states the fill MINUTE. The replay takes the FIRST time his named trigger fires on the fill day; if he
took a later instance, this scores a different trade. Stated as the main limitation.

TRIGGERS (k-minute bars built from 1-minute bars, regular session; a trigger can fire on a k-bar that completes
between 09:45 and 15:30 ET; prior-day high / low from the prior session's 1-minute bars):
  LONG
  intraday_range_or_candle_breakout  first k-bar closing above the highest high of the previous 3 completed k-bars;
                                     stop = that bar's low (his "5/15-minute breakout candle low")
  pullback_to_ema                    a k-bar low touches the k-bar 9 EMA (EMA run over the prior + current session),
                                     then the first later k-bar closing above the previous k-bar's high;
                                     stop = lowest low since the touch
  pullback_to_avwap_or_vwap          as pullback_to_ema with session VWAP (cumsum(typical x vol) / cumsum(vol))
  opening_range_breakout             first k-bar after the first k-minute range closing above that range's high;
                                     stop = low of day so far
  reclaim_or_failed_breakdown        the day trades below the prior-day low, then the first k-bar closing back
                                     above it; stop = low of day so far
  prior_day_high_break               first k-bar closing above the prior-day high; stop = low of day so far
  SHORT (mirror)
  bounce_into_resistance_short       a k-bar high touches the k-bar 9 EMA or session VWAP from below (open of the
                                     session below that level at the touch), then the first later k-bar closing
                                     below the previous k-bar's low; stop = highest high since the touch
  breakdown_short                    first k-bar closing below the prior-day low; stop = high of day so far
  Where he STATED a stop distance (8 cards) it replaces the constructed one. Stop distance d = |entry - stop| / entry
  must lie in [0.2%, 5%], else the event is dropped (counted). A trigger that never fires drops the event (counted).

EXECUTION. Entry at the trigger k-bar's close, 5 bp adverse. Stop rests on 1-minute bars: the first minute whose low
(long) / high (short) crosses it exits at the stop, or at that minute's open if it gapped through. 5 bp per side.
  PRIMARY horizon: exit at the fill day's close if not stopped (his stops are intraday; 59% of the generic version
  stopped the same day).
  SECONDARY horizon: hold to the close of session t+5 with the same resting stop (1-minute bars throughout).

CONTROL. Same name-day, 20 random entry minutes (seed 20261003) drawn uniformly from the k-bar closes in the same
09:45-15:30 window, same side, SAME percentage stop distance d as the event, same execution and horizon.

STATISTIC. Per event: paired = event return - mean of its 20 control returns (signed % for shorts). Mean over events,
t clustered by fill date. Halves split at the median fill date.
PRIMARY = paired, primary horizon, longs and shorts pooled.
BAR (discovery): t >= 3 and both halves > 0 -> PASS (his trigger timing beats a random minute in his own names).
  t <= -3 and both halves < 0 -> INVERTED. Otherwise NULL if |mean| is below the MDE (80% power, 2.8 x SE),
  else UNDERPOWERED.
Reported, not a pass: paired in R (return / d); longs vs shorts; the t+5 horizon; per trigger class; share stopped
same day vs controls; and the raw event mean (to see whether HIS name-days are good days at all, beside the timing).
POWER (stated in advance): ~45-60 events. A paired SD near 2% gives SE ~0.3pp and an MDE ~0.8pp per trade; only a
large timing edge is detectable. PRIOR ~20%: Stage A (11,227 intraday alerts ~ a random later minute) and the generic
tight-stop test both found nothing.

  PYTHONPATH=src:. .venv/bin/python3 run_luk_card_replay.py
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

BUCKET, PREFIX = "gmerton-stock-data", "backfill/intraday_1min/bars/"
LOCAL = Path("data/cache/intraday_1min")
CARDS = Path("data/martin_luk/trades/entry_cards.jsonl")
OUT = "data/studies/luk_card_replay_2026-10-03"
TRIG = {"intraday_range_or_candle_breakout": "long", "pullback_to_ema": "long", "pullback_to_avwap_or_vwap": "long",
        "opening_range_breakout": "long", "reclaim_or_failed_breakdown": "long", "prior_day_high_break": "long",
        "bounce_into_resistance_short": "short", "breakdown_short": "short"}
TF = {"1m": 1, "5m": 5, "15m": 15, "60m": 60}
W0, W1 = 9 * 60 + 45, 15 * 60 + 30
SLIP, NCTL, DMIN, DMAX, HOLD2 = 0.0005, 20, 0.002, 0.05, 5
RNG = np.random.default_rng(20261003)


def events() -> pd.DataFrame:
    from run_luk_trade_pages import load
    d = pd.read_json(CARDS, lines=True)
    L = load().drop_duplicates("key").set_index("key")
    d = d.join(L[["tk", "dirn", "fill", "state"]], on="key")
    d["k"] = d.trigger_timeframe.map(TF)
    d.loc[d.trigger_timeframe.isna(), "k"] = 5
    d = d[d.entry_trigger.isin(TRIG) & d.k.notna() & d.fill.notna() & (d.state == "ok")].copy()
    d["side"] = d.entry_trigger.map(TRIG)
    d = d[d.side == d.dirn]                        # a trigger class must match the logged side
    return d.reset_index(drop=True)


def minutes(s3, tk: str, cache: dict) -> pd.DataFrame | None:
    if tk in cache:
        return cache[tk]
    m = None
    try:
        keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{PREFIX}{tk}/").get("Contents", [])]
        if keys:
            m = pd.concat([pd.read_parquet(io.BytesIO(s3.get_object(Bucket=BUCKET, Key=k)["Body"].read())) for k in keys]).sort_index()
            m = m[~m.index.duplicated()][["open", "high", "low", "close", "volume"]]
    except Exception:
        m = None
    if m is None:
        fs = sorted(LOCAL.glob(f"{tk}_*.parquet"))
        if fs:
            fr = []
            for f in fs:
                b = pd.read_parquet(f)
                if "ts" in b.columns:
                    b = b.set_index(pd.to_datetime(b.ts))
                if "price" in b.columns and "close" not in b.columns:
                    b["close"] = b.price
                fr.append(b[["open", "high", "low", "close", "volume"]])
            m = pd.concat(fr).sort_index()
            m = m[~m.index.duplicated()]
    if m is not None:
        if m.index.tz is not None:
            m.index = m.index.tz_convert("America/New_York").tz_localize(None)
        m["d"] = m.index.normalize(); m["mn"] = m.index.hour * 60 + m.index.minute
        m = m[(m.mn >= 570) & (m.mn < 960)]
    cache[tk] = m
    return m


def kbars(day: pd.DataFrame, k: int) -> pd.DataFrame:
    g = ((day.mn - 570) // k)
    b = day.groupby(g).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
                           volume=("volume", "sum"), end=("mn", "max"))
    tp = (day.high + day.low + day.close) / 3
    vw = (tp * day.volume).groupby(g).sum().cumsum() / day.volume.groupby(g).sum().cumsum()
    b["vwap"] = vw.values
    return b.reset_index(drop=True)


def trigger(cls: str, b: pd.DataFrame, ema: np.ndarray, pdh: float, pdl: float, k: int):
    """(bar index, entry, stop) of the first firing, or None."""
    H, Lo, C, O, V, E = b.high.values, b.low.values, b.close.values, b.open.values, b.vwap.values, b.end.values
    n = len(b); ok = lambda i: W0 <= E[i] + 1 <= W1
    lod = np.minimum.accumulate(Lo); hod = np.maximum.accumulate(H)
    for i in range(1, n):
        if not ok(i):
            continue
        if cls == "intraday_range_or_candle_breakout" and i >= 3 and C[i] > H[i - 3:i].max():
            return i, C[i], Lo[i]
        if cls == "opening_range_breakout" and i >= 1 and C[i] > H[0]:
            return i, C[i], lod[i]
        if cls == "prior_day_high_break" and np.isfinite(pdh) and C[i] > pdh:
            return i, C[i], lod[i]
        if cls == "reclaim_or_failed_breakdown" and np.isfinite(pdl) and lod[i - 1] < pdl and C[i] > pdl:
            return i, C[i], lod[i]
        if cls == "breakdown_short" and np.isfinite(pdl) and C[i] < pdl:
            return i, C[i], hod[i]
    if cls in ("pullback_to_ema", "pullback_to_avwap_or_vwap", "bounce_into_resistance_short"):
        lvl = ema if cls == "pullback_to_ema" else V
        lvl2 = V if cls == "bounce_into_resistance_short" else None
        touch = None
        for i in range(1, n):
            if cls == "bounce_into_resistance_short":
                hit = (H[i] >= ema[i] and O[i] < ema[i]) or (H[i] >= lvl2[i] and O[i] < lvl2[i])
            else:
                hit = Lo[i] <= lvl[i]
            if touch is None and hit:
                touch = i
                continue
            if touch is not None and ok(i):
                if cls == "bounce_into_resistance_short" and C[i] < Lo[i - 1]:
                    return i, C[i], H[touch:i + 1].max()
                if cls != "bounce_into_resistance_short" and C[i] > H[i - 1]:
                    return i, C[i], Lo[touch:i + 1].min()
    return None


def walk(m: pd.DataFrame, t0: pd.Timestamp, side: str, entry: float, stop: float, horizon_end: pd.Timestamp) -> float:
    """Signed net return from entry (after minute t0) to the stop or the horizon's last close."""
    s = 1 if side == "long" else -1
    px0 = entry * (1 + s * SLIP)
    w = m[(m.index > t0) & (m.index <= horizon_end)]
    if w.empty:
        return np.nan
    cross = (w.low.values <= stop) if s == 1 else (w.high.values >= stop)
    j = np.flatnonzero(cross)
    if len(j):
        o = w.open.values[j[0]]
        px = min(stop, o) if s == 1 else max(stop, o)
    else:
        px = w.close.values[-1]
    px1 = px * (1 - s * SLIP)
    return s * (px1 / px0 - 1) * 100


def main() -> None:
    import boto3
    s3 = boto3.Session(profile_name="clarinut-gmerton").client("s3")
    E = events(); cache = {}; rows = []; drops = {"no_bars": 0, "no_trigger": 0, "stop_range": 0}
    for e in E.itertuples():
        m = minutes(s3, e.tk, cache)
        day0 = pd.Timestamp(e.fill).normalize()
        if m is None or (m.d == day0).sum() < 60:
            drops["no_bars"] += 1; continue
        days = sorted(m.d.unique()); i0 = days.index(day0)
        prev = m[m.d == days[i0 - 1]] if i0 > 0 else None
        pdh, pdl = (prev.high.max(), prev.low.min()) if prev is not None and len(prev) else (np.nan, np.nan)
        k = int(e.k); day = m[m.d == day0]
        b = kbars(day, k)
        hist = pd.concat([kbars(prev, k), b]) if prev is not None and len(prev) else b
        ema = hist.close.ewm(span=9, adjust=False).mean().values[-len(b):]
        tr = trigger(e.entry_trigger, b, ema, pdh, pdl, k)
        if tr is None:
            drops["no_trigger"] += 1; continue
        i, entry, stop = tr
        if isinstance(e.stop_distance_pct, (int, float)) and np.isfinite(e.stop_distance_pct):
            dd = e.stop_distance_pct / 100
            stop = entry * (1 - dd) if e.side == "long" else entry * (1 + dd)
        d = abs(entry - stop) / entry
        if not (DMIN <= d <= DMAX):
            drops["stop_range"] += 1; continue
        t0 = day0 + pd.Timedelta(minutes=int(b.end.values[i]))
        end1 = day0 + pd.Timedelta(hours=16)
        end5 = (days[min(i0 + HOLD2, len(days) - 1)] + pd.Timedelta(hours=16)) if i0 + HOLD2 < len(days) else None
        r1 = walk(m, t0, e.side, entry, stop, end1)
        r5 = walk(m, t0, e.side, entry, stop, end5) if end5 is not None else np.nan
        cand = [j for j in range(len(b)) if W0 <= b.end.values[j] + 1 <= W1]
        c1, c5, cst = [], [], []
        for j in RNG.choice(cand, size=min(NCTL, len(cand)), replace=len(cand) < NCTL):
            ce = b.close.values[j]; cs = ce * (1 - d) if e.side == "long" else ce * (1 + d)
            tj = day0 + pd.Timedelta(minutes=int(b.end.values[j]))
            c1.append(walk(m, tj, e.side, ce, cs, end1))
            if end5 is not None:
                c5.append(walk(m, tj, e.side, ce, cs, end5))
            w = m[(m.index > tj) & (m.index <= end1)]
            cst.append(bool(((w.low <= cs) if e.side == "long" else (w.high >= cs)).any()))
        w = m[(m.index > t0) & (m.index <= end1)]
        stopped = bool(((w.low <= stop) if e.side == "long" else (w.high >= stop)).any())
        rows.append(dict(tk=e.tk, side=e.side, fill=day0, trig=e.entry_trigger, k=k, d=d, entry_min=int(b.end.values[i]),
                         r1=r1, c1=np.nanmean(c1), r5=r5, c5=np.nanmean(c5) if c5 else np.nan,
                         stopped=stopped, c_stopped=np.mean(cst)))
    R = pd.DataFrame(rows)
    R.to_csv(f"{OUT}_events.csv", index=False)
    report(R, E, drops)


def clus(x: pd.Series, dates: pd.Series) -> tuple[float, float, int]:
    x = x.dropna(); dates = dates.loc[x.index]
    n = len(x)
    if n < 5:
        return np.nan, np.nan, n
    mu = x.mean(); g = (x - mu).groupby(dates).sum(); G = len(g)
    se = np.sqrt((g ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1))
    return mu, mu / se if se > 0 else np.nan, n


def report(R: pd.DataFrame, E: pd.DataFrame, drops: dict) -> None:
    R["p1"] = R.r1 - R.c1; R["p5"] = R.r5 - R.c5; R["p1R"] = R.p1 / (R.d * 100)
    mid = R.fill.median()
    mu, t, n = clus(R.p1, R.fill)
    h1 = R[R.fill < mid].p1.mean(); h2 = R[R.fill >= mid].p1.mean()
    se = abs(mu / t) if t and np.isfinite(t) and t != 0 else np.nan
    mde = 2.8 * se
    if t >= 3 and h1 > 0 and h2 > 0:
        v = "PASS"
    elif t <= -3 and h1 < 0 and h2 < 0:
        v = "INVERTED"
    elif abs(mu) < mde:
        v = "NULL"
    else:
        v = "UNDERPOWERED"
    L = [f"# Luk entry cards replayed on 1-minute bars ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"Cards eligible {len(E)}; scored {len(R)}; dropped {drops}.", "", f"**{v}**", "",
         f"PRIMARY paired (his trigger - random minute, same name-day, same stop %, exit at the day's close): "
         f"{mu:+.3f}pp, t {t:.2f}, n {n}; halves {h1:+.3f} / {h2:+.3f}; MDE {mde:.2f}pp", "", "## Reported, not a pass", ""]
    for lab, col in (("paired, R units", "p1R"), ("paired, t+5 horizon", "p5"), ("raw event return, day", "r1"), ("raw event return, t+5", "r5")):
        a, b_, c = clus(R[col], R.fill); L.append(f"- {lab}: {a:+.3f}, t {b_:.2f}, n {c}")
    for sd, g in R.groupby("side"):
        a, b_, c = clus(g.p1, g.fill); L.append(f"- {sd}: paired {a:+.3f}pp, t {b_:.2f}, n {c}")
    L.append(f"- stopped same day: events {R.stopped.mean():.0%} vs controls {R.c_stopped.mean():.0%}; median stop {R.d.median():.2%}")
    L += ["", "Per trigger class (paired, primary horizon):", ""]
    for tg, g in R.groupby("trig"):
        L.append(f"- {tg}: {g.p1.mean():+.3f}pp n {len(g)}")
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
