"""Intraday condition detectors, parameterized in ADR units.

Every detector = gate (context worth acting on) -> trigger (the bar that times the
entry) -> one-shot per session. Both were specified from the 2026-09-08 tape:

  UR   undercut & reclaim   SPCX: open +0.7%, flushed -2.6% (0.5 ADR) in 12 min,
                            undercut the prior-day low, 1-min close back above VWAP
                            at 09:46, closed +3.7%.
                            TXG: gapped -2.1% BELOW the daily 9 EMA (open = session
                            low), dipped 0.6% under VWAP at 09:45, reclaimed at
                            09:55, closed +4.7%. So the flush is measured from
                            max(open, prev close) and the arming band is fixed.
  ORB9 opening-range break  LITE: gap +1.9%, first-minute low held the daily 9 EMA
       above the 9 EMA      (0.4% above) and VWAP, 09:45 5-min close above the
                            15-min opening-range high, closed +11%.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from .bars import Bar, SymbolBook
from .context import DailyCtx
from .volprofile import vol_frac

try:  # only replay needs pandas here
    import pandas as pd  # noqa: F401
except ImportError:  # pragma: no cover
    pd = None

# --- UR parameters -----------------------------------------------------------------
UR_LOW_BY = time(11, 0)        # the session low must be printed before this
UR_MIN_FLUSH_ADR = 0.25        # open -> low, in ADR units, always required
UR_BIG_FLUSH_ADR = 0.50        # ...or a flush this deep qualifies on its own
UR_EMA_TAG_PCT = 0.30          # low within this % of the daily 9/21 EMA counts as a tag
UR_MAX_FIRES = 2               # second fire only after a NEW session low...
UR_REFIRE_ADR = 0.25           # ...that is at least this many ADR below the first fire's low
UR_NOT_BEFORE = time(9, 40)    # VWAP has no shape before this; every gap-down ticked "above VWAP" at 9:33 on 9/10
UR_FLUSH_WINDOW_MIN = 45       # the session low must print inside this many minutes of the open (a flush)...
UR_FLUSH_FAST_ADR = 0.40       # ...OR the drop into the low was >= this many ADR within UR_FLUSH_FAST_MIN (HPE 9/10 failed both)
UR_FLUSH_FAST_MIN = 20
UR_REQUIRE_HL = True           # a HIGHER LOW must print before the reclaim: bounce >= UR_HL_BOUNCE_ADR off the low, then a pullback
UR_HL_BOUNCE_ADR = 0.20        #   retracing >= UR_HL_RETRACE of that bounce that HOLDS above the low (CRCL 9/9, HPE 9/10 had none; INTC 10:35 did)
UR_HL_RETRACE = 0.40
UR_HL_MIN_BARS = 2             #   each leg of the swing (low->peak, peak->higher low) must span >= this many 1-min bars
RS_SHORT_GATE_PCT = 1.5        # shorts on a name this far stronger than its group (day change) are gated, like the index gate
UR_ARM_BAND = 0.0010           # a 1-min close this far under VWAP arms the reclaim
UR_TRIG_BAND = 0.0010          # reclaim trigger: close must clear VWAP by this fraction
                               # (dance protection = UR_MAX_FIRES + new-low requirement, not a wide band)
# --- ORB9 parameters ---------------------------------------------------------------
ORB_MINUTES = 15
ORB_BY = time(12, 0)
ORB_MIN_PACE = 1.0             # cumulative volume vs. profile-projected, x avg20 (below 1.2 is tagged "light vol")
GAP_WARN_ADR = 1.0             # tag alerts whose open gapped >= this many ADR (lens rule: no gap-up buys in hour one)
ORB_HOLD_ADR = 0.15            # session low may undercut the 9 EMA by this many ADR (floor 0.3%)


INDEX_SYMBOLS = ("SPY", "QQQ")


class IndexState:
    """SPY (and QQQ) position vs their own session VWAP, queried at an alert's bar time.
    Live: fed by the index SymbolBooks. Replay: a per-minute frame of close/vwap."""

    def __init__(self) -> None:
        self.books: dict[str, SymbolBook] = {}
        self.series: dict[str, "pd.DataFrame"] = {}
        self.prev_close: dict[str, float] = {}          # SPY/QQQ prior closes
        self.groups: dict[str, str] = {}                # ticker -> group
        self.universe_books: dict[str, SymbolBook] = {}
        self.universe_ctx: dict[str, DailyCtx] = {}

    def day_change(self, sym: str, t: datetime | None = None) -> float | None:
        pc = self.prev_close.get(sym)
        if not pc:
            return None
        if sym in self.series:
            s = self.series[sym]
            s = s.loc[:t] if t is not None else s
            return (s["close"].iloc[-1] / pc - 1) * 100 if len(s) else None
        b = self.books.get(sym)
        if b is None:
            return None
        bar = b.cur or (b.bars[-1] if b.bars else None)
        return None if bar is None else (bar.close / pc - 1) * 100

    def group_change(self, sym: str) -> tuple[float, str] | None:
        g = self.groups.get(sym)
        if not g:
            return None
        vals = []
        for s2, g2 in self.groups.items():
            if g2 != g or s2 == sym:
                continue
            bk = self.universe_books.get(s2); k = self.universe_ctx.get(s2)
            if bk is None or k is None or not bk.last_close():
                continue
            vals.append((bk.last_close() / k.prev_close - 1) * 100)
        return (sum(vals) / len(vals), g) if vals else None

    def pct(self, sym: str, t: datetime) -> float | None:
        if sym in self.series:
            s = self.series[sym]
            s = s.loc[:t]
            if s.empty:
                return None
            r = s.iloc[-1]
            return (r["close"] / r["vwap"] - 1) * 100
        b = self.books.get(sym)
        if b is None:
            return None
        bar = b.cur or (b.bars[-1] if b.bars else None)
        return None if bar is None or not bar.vwap else (bar.close / bar.vwap - 1) * 100

    def above(self, t: datetime, sym: str = "SPY") -> bool | None:
        p = self.pct(sym, t)
        return None if p is None else bool(p > 0)

    def stamp(self, fields: dict, t: datetime) -> str:
        """Add spy_vs_vwap / qqq_vs_vwap / index_above to fields; return the message tag."""
        sp, qq = self.pct("SPY", t), self.pct("QQQ", t)
        fields["spy_vs_vwap"] = None if sp is None else round(float(sp), 2)
        fields["qqq_vs_vwap"] = None if qq is None else round(float(qq), 2)
        fields["index_above"] = None if sp is None else bool(sp > 0)      # plain bool: `is False` checks + JSON
        if sp is None:
            return ""
        return f" | SPY {'>' if sp > 0 else '<'} VWAP ({sp:+.2f}%)"


@dataclass
class Alert:
    symbol: str
    kind: str
    t: datetime
    price: float
    stop: float
    msg: str
    fields: dict = field(default_factory=dict)   # structured copy of the tags for the website/JSON


def vwap_band(adr_pct: float) -> float:
    """Schmitt-trigger deadband around VWAP, as a fraction (same rule as fade_watch)."""
    return max(0.0010, 0.20 * adr_pct / 100.0)


def vol_pace(book: SymbolBook, ctx: DailyCtx, t: datetime) -> float:
    elapsed = (t.hour - 9) * 60 + t.minute - 30 + 1
    proj = ctx.avg_vol20 * vol_frac(elapsed)
    return book.cum_volume / proj if proj > 0 else 0.0


def adr_from_21(price: float, ctx: DailyCtx) -> float:
    return (price / ctx.ema21 - 1) * 100 / ctx.adr_pct if ctx.adr_pct else 0.0


def gap_tag(book: SymbolBook, ctx: DailyCtx) -> str:
    gap_adr = (book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct if ctx.adr_pct else 0.0
    return f" | GAP {gap_adr:+.1f} ADR (no hour-one gap buys)" if gap_adr >= GAP_WARN_ADR else ""


LEVEL_RANK = {"200 SMA": 3, "50 SMA": 3, "50 EMA": 3, "21 EMA": 2, "9 EMA": 2, "VWAP": 2, "PDH": 1, "OR": 1}


def swing_lower_high(bars: list, hi_bar, hi: float, adr_pct: float) -> bool:
    """A real lower high since the session high: a pullback, then a rebound of >= 0.1 ADR that stayed under the high."""
    since = [x for x in bars if x.t > hi_bar.t]
    if len(since) < 2:
        return False
    trough = min(since, key=lambda x: x.low)
    need = trough.low * (1 + 0.10 * adr_pct / 100)
    return any(x.t > trough.t and need <= x.high < hi for x in since)


def level_type(name: str) -> str:
    return "MA" if LEVEL_RANK.get(name, 1) >= 2 and name != "VWAP" else ("VWAP" if name == "VWAP" else "PRICE")


def rs_tags(book: SymbolBook, ctx: DailyCtx, idx: "IndexState | None", t: datetime) -> tuple[dict, str]:
    """Relative strength vs SPY and vs the name's group (mean day change of the group's other
    names in the universe), both in % of the day. Positive = stronger than the reference."""
    chg = (book.last_close() / ctx.prev_close - 1) * 100 if book.last_close() else 0.0
    out = {"chg_pct": round(chg, 2)}
    msg = ""
    if idx is not None:
        spy = idx.day_change("SPY", t)
        if spy is not None:
            out["rs_spy"] = round(chg - spy, 2); msg += f" | RS vs SPY {chg - spy:+.1f}%"
        g = idx.group_change(book.symbol)
        if g is not None:
            out["rs_group"] = round(chg - g[0], 2); out["group"] = g[1]
            msg += f" | vs {g[1]} {chg - g[0]:+.1f}%"
            if chg - g[0] >= RS_SHORT_GATE_PCT:
                out["rs_leader"] = True
                msg += " (STRONGEST IN GROUP -- don't short it)"
    return out, msg


class ShortState:
    def __init__(self) -> None:
        self.bir_fires: list[float] = []     # bounce highs already used
        self.fbo_fired: set[str] = set()     # levels already used ("PDH", "OR")


class SymbolState:
    def __init__(self) -> None:
        self.below_vwap_seen = False
        self.ur_fires: list[float] = []      # session lows at each UR fire
        self.orb_fired = False
        self.orb_disqualified = False
        self.short = ShortState()


def higher_low(book: SymbolBook, lo: float, ctx: DailyCtx, before: datetime) -> tuple[float, datetime] | None:
    """First swing higher-low after the session low: a bounce of >= UR_HL_BOUNCE_ADR off the low, then a
    pullback that retraces >= UR_HL_RETRACE of that bounce without breaking the low. Returns (low, time)."""
    need = lo * (1 + UR_HL_BOUNCE_ADR * ctx.adr_pct / 100)
    after = [x for x in book.bars if x.t > book.low_time and x.t < before]
    peak = None
    for x in after:
        if (peak is None or x.high > peak.high) and x.high >= need and (x.t - book.low_time) >= timedelta(minutes=UR_HL_MIN_BARS):
            peak = x
        if peak is None:
            continue
        floor = peak.high - UR_HL_RETRACE * (peak.high - lo)
        if (x.t - peak.t) >= timedelta(minutes=UR_HL_MIN_BARS) and x.low <= floor and x.low > lo:
            return x.low, x.t
    return None


def detect_ur(book: SymbolBook, ctx: DailyCtx, st: SymbolState, b: Bar, idx: IndexState | None = None) -> Alert | None:
    """Runs on every CLOSED 1-min bar."""
    if b.close < b.vwap * (1 - UR_ARM_BAND):
        st.below_vwap_seen = True
        return None
    if not st.below_vwap_seen or book.low_time is None or book.session_open is None:
        return None
    if len(st.ur_fires) >= UR_MAX_FIRES:
        return None
    if st.ur_fires and book.session_low > st.ur_fires[-1] * (1 - UR_REFIRE_ADR * ctx.adr_pct / 100):
        return None
    if book.low_time.time() > UR_LOW_BY or b.t <= book.low_time or b.t.time() < UR_NOT_BEFORE:
        return None
    lo = book.session_low
    # the low has to be a FLUSH, not the end of a stair-step: inside the opening window, or a fast drop into it
    mins_in = (book.low_time.hour - 9) * 60 + book.low_time.minute - 30
    if mins_in > UR_FLUSH_WINDOW_MIN:
        before = [x for x in book.bars if book.low_time - timedelta(minutes=UR_FLUSH_FAST_MIN) <= x.t < book.low_time]
        if not before or (max(x.high for x in before) / lo - 1) * 100 / ctx.adr_pct < UR_FLUSH_FAST_ADR:
            return None
    # a HIGHER LOW has to have printed: bounce off the low, pullback that retraces part of it and holds above the low
    hl = higher_low(book, lo, ctx, b.t)
    if UR_REQUIRE_HL and hl is None:
        return None
    ref = max(book.session_open, ctx.prev_close)          # gap-down opens count as the flush
    flush_adr = (ref - lo) / ref * 100 / ctx.adr_pct
    if flush_adr < UR_MIN_FLUSH_ADR:
        return None
    tag = None
    if lo <= ctx.prev_low:
        tag = f"undercut PDL {ctx.prev_low:.2f}"
    elif abs(lo / ctx.ema9 - 1) * 100 <= UR_EMA_TAG_PCT or lo < ctx.ema9 <= ref:
        tag = ("opened below" if book.session_open < ctx.ema9 else "tagged") + f" 9 EMA {ctx.ema9:.2f}"
    elif abs(lo / ctx.ema21 - 1) * 100 <= UR_EMA_TAG_PCT or lo < ctx.ema21 <= ref:
        tag = ("opened below" if book.session_open < ctx.ema21 else "tagged") + f" 21 EMA {ctx.ema21:.2f}"
    elif flush_adr >= UR_BIG_FLUSH_ADR:
        tag = "deep flush"
    if tag is None:
        return None
    # trigger: this bar closed back above VWAP (small fixed band; the wide ADR band only arms)
    if b.close <= b.vwap * (1 + UR_TRIG_BAND):
        return None
    st.ur_fires.append(lo)
    st.below_vwap_seen = False
    pace = vol_pace(book, ctx, b.t)
    ema_note = "" if b.close >= ctx.ema9 else f" | still below 9 EMA {ctx.ema9:.2f}"
    rsf, rsm = rs_tags(book, ctx, idx, b.t)
    rsm = rsm.replace(" (STRONGEST IN GROUP -- don't short it)", " (strongest in group)")
    hl_note = f" | higher low {hl[0]:.2f}@{hl[1]:%H:%M}" if hl else " | NO HIGHER LOW YET"
    msg = (f"UR reclaim {b.close:.2f} > VWAP {b.vwap:.2f} | low {lo:.2f}@{book.low_time:%H:%M} "
           f"({-flush_adr:.2f} ADR, {tag}){hl_note} | stop {lo:.2f} ({(b.close / lo - 1) * 100:.1f}%){ema_note} | "
           f"{adr_from_21(b.close, ctx):+.1f} ADR vs 21 EMA | vol pace {pace:.1f}x{gap_tag(book, ctx)}{rsm}")
    return Alert(book.symbol, "UR", b.t, b.close, lo, msg, {
        "side": "long", **rsf, "low": round(lo, 2), "low_time": book.low_time.strftime("%H:%M"), "flush_adr": round(-flush_adr, 2),
        "tag": tag, "stop_pct": round((b.close / lo - 1) * 100, 2), "below_ema9": b.close < ctx.ema9,
        "adr_vs_21": round(adr_from_21(b.close, ctx), 1), "vol_pace": round(pace, 1),
        "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})


def detect_orb9(book: SymbolBook, ctx: DailyCtx, st: SymbolState, b: Bar, idx: IndexState | None = None) -> Alert | None:
    """Runs on every CLOSED 1-min bar; acts only when a 5-min bar has just completed.
    HARD index gate: a continuation pattern never fires while SPY is under its VWAP
    (all four ORB9 alerts on 2026-09-09 fired into a falling index and stopped)."""
    if st.orb_fired or st.orb_disqualified or book.session_open is None:
        return None
    if idx is not None and idx.above(b.t) is False:
        return None
    hold = ctx.ema9 * (1 - max(0.003, ORB_HOLD_ADR * ctx.adr_pct / 100))
    if book.session_open < hold or book.session_low < hold:
        st.orb_disqualified = True
        return None
    if b.t.time() > ORB_BY:
        st.orb_disqualified = True
        return None
    orng = book.opening_range(ORB_MINUTES)
    if orng is None or (b.t.minute + 1) % 5 != 0:      # need a completed 5-min bar
        return None
    or_high, or_low = orng
    f5 = book.five_min_bars()
    if not f5 or f5[-1].t.time() < time(9, 30 + ORB_MINUTES):
        return None
    last5 = f5[-1]
    if last5.close <= or_high or last5.close <= last5.vwap:
        return None
    pace = vol_pace(book, ctx, b.t)
    if pace < ORB_MIN_PACE:
        return None
    st.orb_fired = True
    stop = max(or_low, last5.low)
    msg = (f"ORB9 5-min close {last5.close:.2f} > OR high {or_high:.2f} | open {book.session_open:.2f} "
           f"({(book.session_open / ctx.prev_close - 1) * 100:+.1f}%) held 9 EMA {ctx.ema9:.2f} | "
           f"stop {stop:.2f} ({(last5.close / stop - 1) * 100:.1f}%) | {adr_from_21(last5.close, ctx):+.1f} ADR vs 21 EMA | "
           f"vol pace {pace:.1f}x{' (light vol)' if pace < 1.2 else ''} | 15d high {ctx.high15:.2f}{gap_tag(book, ctx)}")
    return Alert(book.symbol, "ORB9", b.t, last5.close, stop, msg, {
        "side": "long", "or_high": round(or_high, 2), "open_pct": round((book.session_open / ctx.prev_close - 1) * 100, 2),
        "ema9": round(ctx.ema9, 2), "stop_pct": round((last5.close / stop - 1) * 100, 2), "below_ema9": False,
        "adr_vs_21": round(adr_from_21(last5.close, ctx), 1), "vol_pace": round(pace, 1), "light_vol": pace < 1.2,
        "high15": round(ctx.high15, 2),
        "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})


# --- short-side parameters ------------------------------------------------------------
BIR_MIN_BOUNCE_ADR = 0.40      # rally from the session low into the level, in ADR
BIR_TAG_PCT = 0.30             # high within this % of the level (floor; 0.1 ADR if larger) counts as a tag
BIR_MAX_AGE_MIN = 60           # the bounce high must be within this many minutes of the trigger
BIR_MAX_FIRES = 2
BIR_NOT_BEFORE = time(9, 50)   # first-20-minute rejections are gap-and-fade, not a bounce into resistance
BIR_FAIL_MARGIN_ADR = 0.10     # the trigger close must be >= this far under the tagged level, OR a lower high must have printed after the tag
BIR_VWAP_LEVEL_MIN = 45        # after this many minutes below a falling VWAP, a touch of VWAP counts as the level (HPE 9/10)
STOP_BUFFER_ADR = 0.10         # stop = high * (1 + this * ADR)
STOP_NOISE_ADR = 0.40          # stops closer than this are tagged "stop in noise" (SPCX/IONQ lesson)
FBO_BY = time(15, 0)
FBO_OR_BY = time(11, 30)       # the opening-range variant only counts in the first two hours
FBO_MIN_PUSH_ADR = 0.15        # the breakout must have carried this far above the level (not a wick)
FBO_NOT_BEFORE = time(9, 50)   # let the opening range form; a first-15-min failure is a gap-and-fade, not this pattern
FBO_MAX_AGE_MIN = 90           # the failure must come within this long of the session high (else the stop is a day-range away)
FBO_FAIL_MARGIN_ADR = 0.10     # the failure close must be >= this far under the level, or a lower high must have printed after the high (AAPL 9/10: 5 cents)


def _five(book: SymbolBook) -> list[Bar]:
    return book.five_min_bars()


def _stop_fields(entry: float, high: float, ctx: DailyCtx) -> tuple[float, dict]:
    stop = high * (1 + STOP_BUFFER_ADR * ctx.adr_pct / 100)
    dist_pct = (stop / entry - 1) * 100
    dist_adr = dist_pct / ctx.adr_pct if ctx.adr_pct else 0.0
    return stop, {"stop_pct": round(dist_pct, 2), "stop_adr": round(dist_adr, 2), "stop_in_noise": dist_adr < STOP_NOISE_ADR}


def detect_bir(book: SymbolBook, ctx: DailyCtx, st: "SymbolState", b: Bar, idx: IndexState | None = None) -> Alert | None:
    """Bounce Into Resistance (short). Daily gate: below the 9 and 21 EMA at the prior close.
    Intraday: a rally of >= BIR_MIN_BOUNCE_ADR from the session low that tags a level above
    (9/21/50 EMA, 50/200 SMA, prior-day high), then the first completed 5-min bar that closes
    below the previous 5-min bar's low -- the first violation of the bounce's higher lows.
    Stop above the bounce high. IONQ 9/8 (200 SMA), AXTI 9/8 (50 EMA), AAPL 9/9 (50 SMA)."""
    ss = st.short
    if not ctx.bearish or (b.t.minute + 1) % 5 != 0 or len(ss.bir_fires) >= BIR_MAX_FIRES or b.t.time() < BIR_NOT_BEFORE:
        return None
    f5 = _five(book)
    if len(f5) < 3:
        return None
    cur, prev = f5[-1], f5[-2]
    if cur.close >= prev.low:                                   # need the violation of the prior 5-min low
        return None
    hist = f5[:-1]
    hi_bar = max(hist, key=lambda x: x.high); hi = hi_bar.high
    if (b.t - hi_bar.t).total_seconds() / 60 > BIR_MAX_AGE_MIN:
        return None
    if ss.bir_fires and hi <= ss.bir_fires[-1]:
        return None
    lo_before = min(x.low for x in hist if x.t <= hi_bar.t)
    if (hi / lo_before - 1) * 100 / ctx.adr_pct < BIR_MIN_BOUNCE_ADR:
        return None
    band = max(BIR_TAG_PCT, 0.10 * ctx.adr_pct) / 100
    levels = list(ctx.levels_above())
    # intraday VWAP counts as resistance once the name has spent a long stretch under a falling VWAP
    below = [x for x in f5 if x.close < x.vwap]
    if len(below) >= BIR_VWAP_LEVEL_MIN // 5 and f5[-1].vwap < f5[max(0, len(f5) - 6)].vwap:
        levels.append(("VWAP", hi_bar.vwap))
    tagged = [(n, v) for n, v in levels if v >= lo_before and (abs(hi / v - 1) <= band or (lo_before < v <= hi and cur.close < v))]
    if not tagged:
        return None
    # prefer a moving average over a price level when both were tagged
    name, level = max(tagged, key=lambda nv: (LEVEL_RANK.get(nv[0], 1), -abs(hi - nv[1])))
    if cur.close >= level:
        return None
    # the failure has to have developed: a close with margin under the level, or a lower high since the tag
    lower_high = swing_lower_high(book.bars, hi_bar, hi, ctx.adr_pct)
    if (level / cur.close - 1) * 100 / ctx.adr_pct < BIR_FAIL_MARGIN_ADR and not lower_high:
        return None
    ss.bir_fires.append(hi)
    stop, sf = _stop_fields(cur.close, hi, ctx)
    pace = vol_pace(book, ctx, b.t)
    rsf, rsm = rs_tags(book, ctx, idx, b.t)
    msg = (f"BIR short {cur.close:.2f} < prior 5m low {prev.low:.2f} | bounce {lo_before:.2f}->{hi:.2f}@{hi_bar.t:%H:%M} "
           f"({(hi / lo_before - 1) * 100 / ctx.adr_pct:.2f} ADR) into {name} {level:.2f} [{level_type(name)}] | stop {stop:.2f} ({sf['stop_pct']:.1f}%, {sf['stop_adr']:.2f} ADR"
           f"{', STOP IN NOISE -- size to it' if sf['stop_in_noise'] else ''}) | {adr_from_21(cur.close, ctx):+.1f} ADR vs 21 EMA | vol pace {pace:.1f}x{rsm}")
    return Alert(book.symbol, "BIR", b.t, cur.close, stop, msg, {"side": "short", "level": name, "level_type": level_type(name), "level_px": round(level, 2), **rsf,
                 "bounce_high": round(hi, 2), "bounce_adr": round((hi / lo_before - 1) * 100 / ctx.adr_pct, 2), **sf,
                 "adr_vs_21": round(adr_from_21(cur.close, ctx), 1), "vol_pace": round(pace, 1), "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})


def detect_fbo(book: SymbolBook, ctx: DailyCtx, st: "SymbolState", b: Bar, idx: IndexState | None = None) -> Alert | None:
    """Failed Breakout (short). The session traded above the prior-day high (or, after 09:45, the
    15-min opening-range high), then a completed 5-min bar closes back below that level AND
    below VWAP. Stop above the failed-breakout high. The mirror of ORB9; 'the better it looks
    long, the better the failed-breakout short'. MU 9/1, SNDK/WDC climax cases."""
    ss = st.short
    if (b.t.minute + 1) % 5 != 0 or not (FBO_NOT_BEFORE <= b.t.time() <= FBO_BY) or book.session_open is None:
        return None
    f5 = _five(book)
    if len(f5) < 2:
        return None
    cur = f5[-1]
    hi_bar = max(f5[:-1], key=lambda x: x.high)
    if (b.t - hi_bar.t).total_seconds() / 60 > FBO_MAX_AGE_MIN:
        return None
    levels = [("PDH", ctx.prev_high)]
    orng = book.opening_range(15)
    if orng is not None:
        levels.append(("OR", orng[0]))
    for name, level in levels:
        if name in ss.fbo_fired or level <= 0:
            continue
        if name == "OR" and b.t.time() > FBO_OR_BY:
            continue
        if book.session_high <= level or cur.close >= level or cur.close >= cur.vwap:
            continue
        # it has to have LOOKED like a breakout: a completed 5-min bar closed above the level
        # before this one, and the push carried at least FBO_MIN_PUSH_ADR above it
        if not any(x.close > level for x in f5[:-1]):
            continue
        if (book.session_high / level - 1) * 100 / ctx.adr_pct < FBO_MIN_PUSH_ADR:
            continue
        hi = book.session_high
        lower_high = swing_lower_high(book.bars, hi_bar, hi, ctx.adr_pct)
        if (level / cur.close - 1) * 100 / ctx.adr_pct < FBO_FAIL_MARGIN_ADR and not lower_high:
            continue
        ss.fbo_fired.add(name)
        stop, sf = _stop_fields(cur.close, hi, ctx)
        pace = vol_pace(book, ctx, b.t)
        was_orb = " | was an ORB9 long" if st.orb_fired else ""
        rsf, rsm = rs_tags(book, ctx, idx, b.t)
        msg = (f"FBO short {cur.close:.2f} < {name} {level:.2f} [{level_type(name)}] and VWAP {cur.vwap:.2f} after high {hi:.2f}{' (lower high since)' if lower_high else ''} | stop {stop:.2f} "
               f"({sf['stop_pct']:.1f}%, {sf['stop_adr']:.2f} ADR{', STOP IN NOISE -- size to it' if sf['stop_in_noise'] else ''}) | "
               f"{adr_from_21(cur.close, ctx):+.1f} ADR vs 21 EMA | vol pace {pace:.1f}x{was_orb}{rsm}")
        return Alert(book.symbol, "FBO", b.t, cur.close, stop, msg, {"side": "short", "level": name, "level_type": level_type(name), "level_px": round(level, 2), **rsf,
                     "failed_high": round(hi, 2), **sf, "adr_vs_21": round(adr_from_21(cur.close, ctx), 1), "vol_pace": round(pace, 1),
                     "was_orb9": bool(st.orb_fired), "gap_adr": round((book.session_open / ctx.prev_close - 1) * 100 / ctx.adr_pct, 2) if ctx.adr_pct else 0.0})
    return None


DETECTORS = {"ur": detect_ur, "orb9": detect_orb9, "bir": detect_bir, "fbo": detect_fbo}
SHORT_KINDS = {"BIR", "FBO"}
