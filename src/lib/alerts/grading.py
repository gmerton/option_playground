"""Setup grade -- ONE rubric shared by the alert engine (what gets shown / dimmed / hidden) and the
trade journal (how an entry is graded). If the two ever disagree, fix it HERE, not in either consumer.

Rubric v2 (2026-09-13), from the 153-session replay (2/2-9/10/2026, 19,456 alerts, 1-min-bar R) split into the
curated universe and a 39-name no-hindsight control set (data/studies/alert_filter_study_2026-09.md):

  LONG   F  daily chart not LONG (the in-play gate)             kept as the display gate; it does NOT rank R on
                                                                 either set (curated hidden longs +0.17 vs allowed
                                                                 +0.07; control -0.03 vs -0.11) -- pending a
                                                                 point-in-time universe test
         C  09:30-09:40, or after 12:00                          -0.15R on BOTH sets and every half (first ten
                                                                 minutes); afternoon flat to negative on both
         B  09:41-12:00 on a day-LONG name, any kind             09:41-10:00 +0.07 on both sets; nothing later
                                                                 separates once the universe is controlled
  SHORT  F  daily chart not SHORT, or before 10:30 ET            unchanged from v1
         C  day-SHORT name at/after 10:30                        shorts ~0 / negative on both sets: still no edge

Dropped from v1: the A grade (ORB9 at/after 10:00) -- +0.70R on the curated names but -0.39R (83% stopped) on the
control set, so it graded the universe, not the setup. The "before 10:00 = C" cut -- only the first ten minutes
are bad; 09:41-10:00 is as good as anything later. Deliberately NOT in the rubric (tested, no stable signal): SPY
vs VWAP, relative strength vs SPY or group, STOP IN NOISE, still-below-9-EMA. Re-validate with
`run_alert_study.py --report grades`; the control set (universe_study_extra.txt) is part of every replay now.
v1 (2026-09-10, 20 sessions): A = ORB9 >= 10:00, B = ORB9 early / other >= 10:00, C = other < 10:00.
"""
from __future__ import annotations

from dataclasses import dataclass

RUBRIC_VERSION = "v2-2026-09-13"
SHORT_KINDS = ("BIR", "FBO", "PARA")
LONG_OPEN_UNTIL = 9 * 60 + 40  # 09:40 ET: alerts at/before this minute are the opening flood (C)
LONG_NOON = 12 * 60            # after 12:00 ET: afternoon entries are C
SHORT_AFTER = 10 * 60 + 30    # 10:30 ET
VERDICT = {"A": "good", "B": "good", "C": "gray_area", "F": "bad"}

# Leveraged / inverse ETFs are graded on the index they track, with the side flipped for inverse funds.
# Their own charts are useless for the day state: volatility decay pushes BOTH the long and the inverse fund
# under falling EMAs in a choppy tape (on 9/11 SOXL and SOXS were both day-SHORT, and SQQQ read LONG while QQQ
# did too). symbol -> (tracked index/stock, +1 same direction / -1 inverse). Volatility products (UVXY, UVIX,
# SVXY, VXX) have no equity underlying and stay on their own chart.
LEVERAGED: dict[str, tuple[str, int]] = {
    "SOXL": ("SMH", 1), "SOXS": ("SMH", -1),
    "TQQQ": ("QQQ", 1), "SQQQ": ("QQQ", -1), "QLD": ("QQQ", 1), "QID": ("QQQ", -1),
    "UPRO": ("SPY", 1), "SPXL": ("SPY", 1), "SSO": ("SPY", 1), "SPXU": ("SPY", -1), "SPXS": ("SPY", -1), "SDS": ("SPY", -1),
    "TNA": ("IWM", 1), "TZA": ("IWM", -1), "URTY": ("IWM", 1), "SRTY": ("IWM", -1),
    "NUGT": ("GDX", 1), "DUST": ("GDX", -1), "JNUG": ("GDXJ", 1), "JDST": ("GDXJ", -1),
    "LABU": ("XBI", 1), "LABD": ("XBI", -1), "FAS": ("XLF", 1), "FAZ": ("XLF", -1),
    "ERX": ("XLE", 1), "ERY": ("XLE", -1), "UCO": ("USO", 1), "SCO": ("USO", -1),
    "TMF": ("TLT", 1), "TMV": ("TLT", -1), "YINN": ("FXI", 1), "YANG": ("FXI", -1), "BOIL": ("UNG", 1), "KOLD": ("UNG", -1),
    "NVDL": ("NVDA", 1), "TSLL": ("TSLA", 1), "TSLQ": ("TSLA", -1), "MSFU": ("MSFT", 1), "AAPU": ("AAPL", 1),
    "AMZU": ("AMZN", 1), "CONL": ("COIN", 1),
}


def resolve(symbol: str, side: str) -> tuple[str, str]:
    """(symbol to read the day state from, side to grade) -- the tracked index and the flipped side for inverse funds."""
    u = LEVERAGED.get(symbol.upper())
    if not u:
        return symbol.upper(), side
    return u[0], side if u[1] > 0 else ("short" if side == "long" else "long")


@dataclass(frozen=True)
class Grade:
    grade: str                # A / B / C / F
    why: str                  # one line, for the alert text and the journal
    components: tuple         # (name, value, threshold, tier) -- scorecard style

    @property
    def verdict(self) -> str:
        return VERDICT[self.grade]


def _hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def setup_grade(side: str, kind: str | None, minute: int, day_state: str | None) -> Grade:
    """side 'long'/'short'; kind = alert kind (UR/ORB9/LVL/BIR/FBO/PARA) or None for an entry no alert
    matched; minute = ET minutes since midnight of the alert (or of the fill when unmatched);
    day_state = LONG/SHORT/OUT from lib.alerts.daily_state."""
    side = side.lower()
    want = "LONG" if side == "long" else "SHORT"
    ds = day_state or "?"
    day_ok = ds == want
    comp = [("day", ds, want, "pass" if day_ok else "fail")]
    if side == "long":
        opening, afternoon = minute <= LONG_OPEN_UNTIL, minute >= LONG_NOON
        comp.append(("time", _hhmm(minute), "09:41-12:00", "marginal" if (opening or afternoon) else "pass"))
        comp.append(("setup", kind or "no alert", "-", "no kind ranks once the universe is controlled (v2)"))
        if not day_ok:
            return Grade("F", f"daily chart is {ds}, not LONG (out of play for longs)", tuple(comp))
        what = kind or "entry without an alert"
        if opening:
            return Grade("C", f"{what} in the first ten minutes (09:30-09:40)", tuple(comp))
        if afternoon:
            return Grade("C", f"{what} after 12:00", tuple(comp))
        return Grade("B", f"{what} 09:41-12:00 on a day-LONG name", tuple(comp))
    early = minute < SHORT_AFTER
    comp.append(("time", _hhmm(minute), ">=10:30", "fail" if early else "pass"))
    comp.append(("setup", kind or "no alert", "-", "cap C (no short edge yet)"))
    if not day_ok:
        return Grade("F", f"daily chart is {ds}, not SHORT (out of play for shorts)", tuple(comp))
    if early:
        return Grade("F", "short before 10:30", tuple(comp))
    return Grade("C", "day-SHORT name after 10:30 (shorts cap at C)", tuple(comp))


def grade_alert(kind: str, minute: int, day_state: str | None) -> Grade:
    return setup_grade("short" if kind in SHORT_KINDS else "long", kind, minute, day_state)
