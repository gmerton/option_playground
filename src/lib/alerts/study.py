"""Alert study harness: parse monitor logs (shown + out-of-play), score every alert against the tape,
enrich with the fields the gate studies use, and print the standard reports.

Scoring (identical for every alert): entry = alert price, stop = alert stop, R = |entry - stop|.
Stop hit on a later 1-min bar before the close = -1R; otherwise the close in R. MFE = best favorable
excursion before the stop (or the close), in R. No management, no costs (~0.06R per 0.10% round trip).

Study discipline (2026-09 studies): split sessions in half by date; a filter is only believable if it
holds in both halves. Everything here is in-sample for whatever period the logs cover.
Used by run_alert_study.py. See data/studies/alert_filter_study_2026-09.md.
"""
from __future__ import annotations

import asyncio
import glob
import os
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

LOGS = Path(__file__).resolve().parents[3] / "data" / "watchlist" / "logs"
BARS = Path(__file__).resolve().parents[3] / "data" / "cache" / "intraday_1min"
SHORT_KINDS = ("BIR", "FBO", "PARA")
PAT = re.compile(r"\[(\d{4}-\d\d-\d\d) (\d\d:\d\d)\] (\S+)\s+(UR|ORB9|BIR|FBO|PARA)\s+(\(gated\) )?"
                 r"(?:UR reclaim|ORB9 5-min close|BIR short|FBO short|PARA short) ([\d.]+).*?\| stop ([\d.]+)")
TAGS = ("deep flush", "undercut PDL", "opened below", "tagged", "still below 9 EMA", "light vol", "STOP IN NOISE",
        "GAP", "was an ORB9 long", "STRONGEST IN GROUP", "strongest in group", "[MA]", "[PRICE]", "[VWAP]", "[SWING HIGH]")
KEY = ["date", "t", "sym", "kind"]


# ---------------------------------------------------------------- parse
def log_paths(start: str | None = None, end: str | None = None, replay: bool = True) -> list[Path]:
    """Shown + out-of-play logs for sessions in [start, end]."""
    suf = "_replay" if replay else ""
    out = []
    for p in sorted(LOGS.glob(f"universe_alerts_2026-*{suf}.log")) + sorted(LOGS.glob(f"universe_alerts_2026-*{suf}_oop.log")):
        m = re.match(r"universe_alerts_(\d{4}-\d\d-\d\d)(_replay)?(_oop)?\.log$", p.name)
        if not m or bool(m.group(2)) != replay:
            continue
        d = m.group(1)
        if (start and d < start) or (end and d > end):
            continue
        out.append(p)
    return out


def parse_logs(paths: list[Path]) -> pd.DataFrame:
    rows = []
    for p in paths:
        oop = p.name.endswith("_oop.log")
        for l in p.read_text().splitlines():
            m = PAT.search(l)
            if not m:
                continue
            d, t, s, k, g, px, st = m.groups()
            f = lambda rx: (lambda mm: float(mm.group(1)) if mm else np.nan)(re.search(rx, l))
            lt = re.search(r"\[(MA|PRICE|VWAP|SWING HIGH)\]", l)
            ds = re.search(r"\| day (LONG|SHORT|OUT)\b", l)
            rows.append(dict(date=d, t=t, sym=s, kind=k, gated=bool(g) or oop, out_of_play=oop, px=float(px), stop=float(st),
                             tags="|".join(x for x in TAGS if x in l), spy=f(r"SPY [<>] VWAP \(([+-][\d.]+)%\)"),
                             rs_spy=f(r"RS vs SPY ([+-][\d.]+)%"), rs_grp=f(r"\| vs \S+ ([+-][\d.]+)%"),
                             ext21=f(r"\| ([+-][\d.]+) ADR vs 21 EMA"), level_type=lt.group(1) if lt else None,
                             day_state_logged=ds.group(1) if ds else None))
    return pd.DataFrame(rows).drop_duplicates(KEY) if rows else pd.DataFrame(columns=KEY)


# ---------------------------------------------------------------- score
def _score_one(r, m: pd.DataFrame | None) -> dict:
    if m is None or m.empty:
        return dict(stopped=None)
    seg = m[m.index.strftime("%H:%M") > r.t]
    short, risk = r.kind in SHORT_KINDS, abs(r.px - r.stop)
    if seg.empty or risk <= 0:
        return dict(stopped=None)
    hit = seg[seg.high >= r.stop] if short else seg[seg.low <= r.stop]
    end = seg.loc[: hit.index[0]] if len(hit) else seg
    mfe = ((r.px - end.low.min()) if short else (end.high.max() - r.px)) / risk
    if len(hit):
        return dict(stopped=True, t_stop=hit.index[0].strftime("%H:%M"), R=-1.0, mfe_R=round(mfe, 2), risk_pct=round(100 * risk / r.px, 2))
    close = float(seg.close.iloc[-1])
    return dict(stopped=False, t_stop=None, R=round(((r.px - close) if short else (close - r.px)) / risk, 2),
                mfe_R=round(mfe, 2), risk_pct=round(100 * risk / r.px, 2))


async def score_alerts(df: pd.DataFrame) -> pd.DataFrame:
    from lib.journal.exit_kind import bars_1min
    from lib.tradier.tradier_client_wrapper import TradierClient
    out, cache = [], {}
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        for r in df.itertuples():
            k = (r.sym, r.date)
            if k not in cache:
                try:
                    cache[k] = await bars_1min(r.sym, date.fromisoformat(r.date), c)
                except Exception:  # noqa: BLE001
                    cache[k] = None
            out.append(_score_one(r, cache[k]))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(out)], axis=1)


def score_with_cache(df: pd.DataFrame, cache_csv: Path, rescore: bool = False) -> pd.DataFrame:
    """Score only alerts not already in cache_csv (unless rescore); write the union back."""
    have = pd.read_csv(cache_csv) if (cache_csv.exists() and not rescore) else pd.DataFrame(columns=KEY + ["out_of_play"])
    done = set(map(tuple, have[KEY + ["out_of_play"]].astype(str).values)) if len(have) else set()
    todo = df[[tuple(x) not in done for x in df[KEY + ["out_of_play"]].astype(str).values]]
    if len(todo):
        print(f"scoring {len(todo)} new alerts ({len(df) - len(todo)} cached)", flush=True)
        have = pd.concat([have, asyncio.run(score_alerts(todo))], ignore_index=True)
        have.to_csv(cache_csv, index=False)
    keys = set(map(tuple, df[KEY + ["out_of_play"]].astype(str).values))
    return have[[tuple(x) in keys for x in have[KEY + ["out_of_play"]].astype(str).values]].reset_index(drop=True)


# ---------------------------------------------------------------- enrich
def _orb_stale(r) -> float:
    f = BARS / f"{r.sym}_{r.date}.parquet"
    if not f.exists():
        return np.nan
    m = pd.read_parquet(f); m = m[m.index.strftime("%H:%M") >= "09:30"]
    orh = m[m.index.strftime("%H:%M") < "09:45"].high.max()
    f5 = m.close.resample("5min", label="left", closed="left").last(); f5 = f5[f5.index.strftime("%H:%M") >= "09:45"]
    b = f5[f5 > orh]
    return (pd.Timestamp(f"{r.date} {r.t}") - (b.index[0] + pd.Timedelta(minutes=4))).total_seconds() / 60 if len(b) else np.nan


def enrich(S: pd.DataFrame, day_state: bool = True) -> pd.DataFrame:
    S = S.dropna(subset=["stopped"]).copy()
    S["stopped"] = S.stopped.astype(str).isin(["True", "true", "1"])
    S["side"] = np.where(S.kind.isin(SHORT_KINDS), "short", "long")
    S["same_min"] = S.groupby(["date", "t", "kind"]).sym.transform("size")
    S["mins"] = S.t.str[:2].astype(int) * 60 + S.t.str[3:].astype(int)
    for tgt in (0.5, 1.0, 2.0):
        S[f"t{tgt}"] = np.where(S.mfe_R >= tgt, tgt, S.R)
    days = sorted(S.date.unique()); first = set(days[: len(days) // 2])
    S["half"] = np.where(S.date.isin(first), "A", "B")
    S.loc[S.kind == "ORB9", "orb_stale_min"] = S[S.kind == "ORB9"].apply(_orb_stale, axis=1)
    if day_state:
        from lib.alerts.context import load_context
        rows = []
        for d, g in S.groupby("date"):
            ctx = asyncio.run(load_context(sorted(g.sym.unique()), date.fromisoformat(d)))
            rows += [dict(date=d, sym=s, day_state=c.day_state, day_reason=c.day_reason, ext_close=c.ext21_close_adr,
                          res_gap=c.res_gap_adr) for s, c in ctx.items()]
        S = S.merge(pd.DataFrame(rows), on=["date", "sym"], how="left")
        S["allowed"] = ((S.side == "long") & (S.day_state == "LONG")) | ((S.side == "short") & (S.day_state == "SHORT"))
        S["sub"] = S.day_reason.fillna("").str.extract(
            r"^(exhaustion|trend-down|pullback into|near the rising|near the 21|reclaiming|no room|extended|stretched|[+-]\d|short history)")[0]
    return S


# ---------------------------------------------------------------- reports
def _t(x) -> float:
    x = pd.Series(x).dropna()
    sd = x.std(ddof=1) if len(x) > 2 else 0.0
    return x.mean() / (sd / np.sqrt(len(x))) if sd > 0 else np.nan   # nan, not a divide-by-zero, for tiny/identical groups


def summ(g: pd.DataFrame, col: str = "R") -> pd.Series:
    return pd.Series(dict(n=len(g), avgR=round(g[col].mean(), 2), t=round(_t(g[col]), 2), stop=f"{100 * g.stopped.mean():.0f}%",
                          win=f"{100 * (g[col] > 0).mean():.0f}%", A=round(g[g.half == "A"][col].mean(), 2),
                          B=round(g[g.half == "B"][col].mean(), 2), days_pos=f"{int((g.groupby('date')[col].mean() > 0).sum())}/{g.date.nunique()}"))


def _tab(S: pd.DataFrame, by) -> str:
    return S.groupby(by, observed=True)[S.columns.tolist()].apply(summ).to_string()


def report_filters(S: pd.DataFrame) -> None:
    b = S.groupby("kind")[S.columns.tolist()].apply(summ)
    for tgt in (0.5, 1.0, 2.0):
        b[f"tgt{tgt}"] = S.groupby("kind")[f"t{tgt}"].mean().round(2)
    print("\n== BASELINE by kind (hold to stop/close) + profit-target variants ==\n" + b.to_string())
    print("\n== by kind x gated ==\n" + _tab(S, ["kind", "gated"]))
    U = S[S.kind == "UR"].copy()
    U["same_b"] = pd.cut(U.same_min, [0, 1, 4, 9, 999], labels=["1", "2-4", "5-9", "10+"])
    U["rs_b"] = pd.cut(U.rs_spy, [-99, -1, 0, 1, 99], labels=["<-1", "-1..0", "0..1", ">1"])
    U["time_b"] = pd.cut(U.mins, [0, 580, 600, 630, 720, 999], labels=["09:40", "09:41-10:00", "10:01-10:30", "10:31-12:00", "after 12"])
    for col, lbl in (("time_b", "time of day"), ("same_b", "names reclaiming in the same minute"), ("rs_b", "RS vs SPY")):
        print(f"\n== UR by {lbl} ==\n" + _tab(U, col))
    O = S[S.kind == "ORB9"].assign(fresh=lambda x: x.orb_stale_min <= 5)
    print("\n== ORB9: break alerted within 5 min (fresh) vs late ==\n" + _tab(O, "fresh"))
    Sh = S[S.side == "short"]
    print("\n== shorts by level type ==\n" + _tab(Sh, "level_type"))
    print("\n== shorts: strongest in group (RS vs group >= +1.5%) ==\n" + _tab(Sh.assign(leader=Sh.rs_grp >= 1.5), "leader"))


def report_extension(S: pd.DataFrame) -> None:
    S = S.assign(ext_b=pd.cut(S.ext21, [-99, -1, 0, 1, 2, 99], labels=["< -1 ADR", "-1..0", "0..+1", "+1..+2", "> +2 ADR"]))
    for k in ("UR", "ORB9", "BIR", "FBO", "PARA"):
        print(f"\n== {k} by distance from the daily 21 EMA at the alert ==\n" + _tab(S[S.kind == k], "ext_b"))


def report_daystate(S: pd.DataFrame) -> None:
    if "day_state" not in S:
        print("(day state not computed)"); return
    print(f"\nday-state coverage {S.day_state.notna().mean():.0%} of {len(S)} alerts "
          f"({int(S.out_of_play.sum())} from out-of-play logs)")
    for k in ("UR", "ORB9", "BIR", "FBO", "PARA"):
        print(f"\n== {k} by day state ==\n" + _tab(S[S.kind == k], "day_state"))
    print("\n== allowed by the daily gate vs blocked, by side ==\n" + _tab(S, ["side", "allowed"]))
    print("\n== long alerts by day sub-state ==\n" + _tab(S[S.side == "long"], "sub"))
    print("\n== short alerts by day sub-state ==\n" + _tab(S[S.side == "short"], "sub"))
    U = S[(S.kind == "UR") & (S.mins > 600)]
    print("\n== UR after 10:00, allowed vs blocked ==\n" + _tab(U, "allowed"))


def report_grades(S: pd.DataFrame) -> None:
    """The shared setup rubric (lib/alerts/grading.py) must rank R, in both halves -- if it stops doing
    that, the rubric is wrong and both the alert display and the journal grades inherit the error."""
    from lib.alerts.grading import RUBRIC_VERSION, setup_grade
    S = S.copy()
    S["grade"] = [setup_grade(sd, k, int(m), ds if isinstance(ds, str) else None).grade
                  for sd, k, m, ds in zip(S.side, S.kind, S.mins, S.day_state)]
    print(f"\n== SETUP GRADE {RUBRIC_VERSION} (lib/alerts/grading.py): must rank R in both halves ==")
    print(_tab(S, "grade"))
    print(_tab(S, ["side", "grade"]))
