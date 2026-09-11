"""Daily in-play classification: which DIRECTION a name is eligible for today, from its daily chart
as of the prior close. The universe stays fixed; this decides whether its intraday alerts count.

  LONG   -1 <= ext21 <= +1 ADR, not a falling-EMA downtrend, not "above the 9 but still under the 21"
           (unconfirmed reclaim), and at least ROOM_MIN_ADR under the prior swing high: a pullback
           into rising EMAs or a base near the 21.
  SHORT  (0) parabolic: >= 3 up days and >= 4 ADR over the 21 (or >= 5 up days and >= 3 ADR);
         (a) trend-down: below the 9 and 21 EMA with the 21 falling, not already stretched down
           (ext21 >= -1.5 ADR);
         (b) exhaustion: >= +2 ADR over the 21 EMA and within EXH_BAND_ADR of a prior swing high.
  OUT    everything else: extended up (> +1 ADR) not at a prior high, stretched down (< -1.5 ADR in
         a downtrend), a breakdown (< -1 ADR under the 21), an unconfirmed reclaim, or no room.

ext21 = (close / EMA21 - 1) / ADR20, in ADR units. Prior swing high = the highest high from
RES_LOOKBACK .. RES_SKIP sessions back; the NEAREST one at or above (close - EXH_ABOVE_ADR) is the
resistance (not the window max: INTC's June 142 high would hide the 8/13 107.57 level).
INTC 9/10/2026: prior close +2.5 ADR over the 21, 0.3 ADR under the 8/13 high (107.57) -> SHORT.
INTC 9/4/2026 (prior close 9/3): over the 9, under the 21 -> OUT (unconfirmed reclaim; the move was a
daily-21-EMA reclaim, which no intraday detector trades yet).
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

LONG_MAX_EXT = 1.0        # ADR over the 21 EMA above which a long is a chase
LONG_MIN_EXT = -1.0       # ADR under the 21 EMA below which a long is fighting the trend
ROOM_MIN_ADR = 0.5        # a long needs at least this much room to the prior swing high
SHORT_MIN_EXT = -1.5      # a trend-down short below this is already stretched (short chase)
EXH_MIN_EXT = 2.0         # exhaustion short: at least this extended over the 21 EMA...
EXH_BELOW_ADR = 1.0       # ...and approaching a prior swing high from up to this far below it
EXH_ABOVE_ADR = 0.5       # ...or pushed up to this far over it (the failed-breakout zone)
RES_LOOKBACK = 60
RES_SKIP = 5
SWING_K = 3               # a swing high = the highest high within SWING_K sessions on each side
SLOPE_DAYS = 5
PARA_MIN_EXT = 4.0        # parabolic: >= this many ADR over the 21 EMA after >= PARA_MIN_UP up closes...
PARA_MIN_UP = 3
PARA_ALT_EXT, PARA_ALT_UP = 3.0, 5   # ...or >= 3 ADR after >= 5 up closes (a long streak is itself the extreme: CVI 9/10)
ALLOW_FLUSH_REVERSAL = False   # True = names >1 ADR under the 21 are LONG-eligible for day trades (see study)


@dataclass
class DayState:
    state: str = "OUT"            # LONG | SHORT | OUT
    reason: str = ""
    ext21_adr: float = 0.0
    ext9_pct: float = 0.0
    ema21_rising: bool = False
    res_level: float = 0.0        # prior swing high (0 = none)
    res_gap_adr: float = 99.0     # (res_level - close) in ADR units; negative = closed above it
    up_days: int = 0              # consecutive up closes into the prior close


def swing_highs(h: pd.Series) -> list[float]:
    """Swing highs between RES_LOOKBACK and RES_SKIP sessions back."""
    n = len(h)
    lo, hi = max(SWING_K, n - RES_LOOKBACK), n - RES_SKIP
    v = h.values
    return [float(v[i]) for i in range(lo, hi) if v[i] == max(v[max(0, i - SWING_K): i + SWING_K + 1])]


def nearest_swing_high(h: pd.Series, close: float, adr: float) -> float:
    """The nearest swing high at or above close - EXH_ABOVE_ADR (0 if none)."""
    floor = close * (1 - EXH_ABOVE_ADR * adr / 100)
    cands = [x for x in swing_highs(h) if x >= floor]
    return min(cands) if cands else 0.0


def classify(hist: pd.DataFrame) -> DayState:
    """hist: daily bars (open/high/low/close) up to and including the PRIOR session, oldest first."""
    c, h, l = hist["close"].astype(float), hist["high"].astype(float), hist["low"].astype(float)
    if len(c) < 30:
        return DayState(reason="short history")
    e9, e21 = c.ewm(span=9, adjust=False).mean(), c.ewm(span=21, adjust=False).mean()
    adr = float((h / l - 1).tail(20).mean() * 100) or 1.0
    close, ema9, ema21 = float(c.iloc[-1]), float(e9.iloc[-1]), float(e21.iloc[-1])
    ext21 = (close / ema21 - 1) * 100 / adr
    rising = bool(e21.iloc[-1] > e21.iloc[-1 - SLOPE_DAYS])
    up = 0
    for x in (c.diff() > 0).iloc[::-1]:
        if not x: break
        up += 1
    res = nearest_swing_high(h, close, adr)
    gap = (res / close - 1) * 100 / adr if res else 99.0
    s = DayState(ext21_adr=round(ext21, 2), ext9_pct=round((close / ema9 - 1) * 100, 2), ema21_rising=rising,
                 res_level=round(res, 2), res_gap_adr=round(gap, 2), up_days=up)
    below9, below21 = close < ema9, close < ema21
    # exhaustion first: an extended name at a prior high is a short candidate, never a long
    if ext21 >= EXH_MIN_EXT and res and -EXH_ABOVE_ADR <= gap <= EXH_BELOW_ADR:
        s.state, s.reason = "SHORT", f"exhaustion: +{ext21:.1f} ADR over the 21 EMA into the prior high {res:.2f}"
        return s
    # parabolic (Qullamaggie): a vertical multi-day run, no resistance needed -- short the crack, never the strength
    if up >= PARA_MIN_UP and (ext21 >= PARA_MIN_EXT or (ext21 >= PARA_ALT_EXT and up >= PARA_ALT_UP)):
        s.state, s.reason = "SHORT", f"parabolic: +{ext21:.1f} ADR over the 21 EMA after {up} up days"
        return s
    if below9 and below21 and not rising:
        if ext21 >= SHORT_MIN_EXT:
            s.state, s.reason = "SHORT", f"trend-down: under falling 9/21 EMAs ({ext21:+.1f} ADR)"
        else:
            s.state = "LONG" if ALLOW_FLUSH_REVERSAL else "OUT"
            s.reason = f"stretched down {ext21:+.1f} ADR under the 21 EMA (short chase / flush zone)"
        return s
    if ext21 > LONG_MAX_EXT:
        s.reason = f"extended +{ext21:.1f} ADR over the 21 EMA" + (f", prior high {res:.2f} {gap:+.1f} ADR away" if res else "")
        return s
    if ext21 < LONG_MIN_EXT:
        s.state = "LONG" if ALLOW_FLUSH_REVERSAL else "OUT"
        s.reason = f"{ext21:+.1f} ADR under the 21 EMA (not a pullback, a breakdown)"
        return s
    # 20-session study (2026-09-10): long alerts on "reclaiming the 9 under the 21" names averaged -0.48R
    # (n=22, both halves negative) and bases within ROOM_MIN_ADR of a prior high -0.11R (n=60, both halves)
    # -> both OUT. The kept LONG set scored +0.34R (n=176; first half +0.35, second +0.33).
    if below21 and not below9:
        s.reason = f"reclaiming the 9 but still under the 21 EMA ({ext21:+.1f} ADR): reclaim not confirmed"
        return s
    if res and 0 <= gap < ROOM_MIN_ADR:
        s.reason = f"no room: {gap:.1f} ADR under the prior high {res:.2f} ({ext21:+.1f} ADR from the 21)"
        return s
    s.state = "LONG"
    kind = ("pullback into the rising 9/21 EMAs" if (below9 and below21) else
            "near the rising 21 EMA" if rising else "near the 21 EMA")
    s.reason = f"{kind} ({ext21:+.1f} ADR)" + (f", {gap:.1f} ADR to the prior high {res:.2f}" if res and 0 < gap < 99 else "")
    return s
