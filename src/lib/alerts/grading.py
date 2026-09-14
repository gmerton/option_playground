"""Setup grade -- ONE rubric shared by the alert engine (what gets shown / dimmed / hidden) and the
trade journal (how an entry is graded). If the two ever disagree, fix it HERE, not in either consumer.

Rubric v1 (2026-09-10), built on the 20-session alert study (8/13-9/10, 1,073 alerts, 1-min-bar R):

  LONG   F  daily chart not LONG (the in-play gate)                        R -0.05 (n=415)
         A  ORB9 at/after 10:00 ET on a day-LONG name                       R +2.41 (n=20; halves +2.60 / +2.18)
         B  ORB9 before 10:00, or UR / any other entry at/after 10:00       R +0.22 (n=101; halves +0.22 / +0.21)
            (LVL, the pivot break added 2026-09-13, grades as "other" until it has its own study; the engine
            treats a day-OUT "no room" name as LONG for an LVL alert -- the break IS the resolution of no room)
         C  UR / other entry before 10:00                                   R -0.18 (n=55)
  SHORT  F  daily chart not SHORT, or before 10:30 ET                       R -0.15 (n=385)
         C  day-SHORT name at/after 10:30 -- the best short cell found,     R +0.07 (n=97)
            still no demonstrated edge, so shorts cap at C until one is found

Deliberately NOT in the rubric (tested, no stable signal in the same data): SPY vs VWAP (the old
index gate -- for shorts it pointed the wrong way), relative strength vs SPY or vs group (inverted:
longs weaker than their group did better), STOP IN NOISE, still-below-9-EMA. They stay in the alert
text as context. Cut points were chosen on the full sample; the halves check stability, not
out-of-sample skill -- re-validate with `run_alert_study.py --report grades` as sessions accrue.
"""
from __future__ import annotations

from dataclasses import dataclass

RUBRIC_VERSION = "v1-2026-09-10"
SHORT_KINDS = ("BIR", "FBO", "PARA")
LONG_AFTER = 10 * 60          # 10:00 ET, minutes since midnight
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
    """side 'long'/'short'; kind = alert kind (UR/ORB9/BIR/FBO/PARA) or None for an entry no alert
    matched; minute = ET minutes since midnight of the alert (or of the fill when unmatched);
    day_state = LONG/SHORT/OUT from lib.alerts.daily_state."""
    side = side.lower()
    want = "LONG" if side == "long" else "SHORT"
    ds = day_state or "?"
    day_ok = ds == want
    comp = [("day", ds, want, "pass" if day_ok else "fail")]
    if side == "long":
        early = minute < LONG_AFTER
        comp.append(("time", _hhmm(minute), ">=10:00", "marginal" if early else "pass"))
        comp.append(("setup", kind or "no alert", "ORB9", "pass" if kind == "ORB9" else "marginal"))
        if not day_ok:
            return Grade("F", f"daily chart is {ds}, not LONG (out of play for longs)", tuple(comp))
        if kind == "ORB9":
            return (Grade("B", "ORB9 before 10:00", tuple(comp)) if early
                    else Grade("A", "ORB9 after 10:00 on a day-LONG name", tuple(comp)))
        what = kind or "entry without an alert"
        return (Grade("C", f"{what} before 10:00", tuple(comp)) if early
                else Grade("B", f"{what} after 10:00 on a day-LONG name", tuple(comp)))
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
