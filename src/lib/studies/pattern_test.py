"""
One harness for testing an entry pattern, so a new idea costs ~20 lines instead of a 200-line script.

A pattern is a function that returns signals. The harness owns everything else: fills with slippage, the
exit arms, the same-name random control, the split sample, day-clustered t-stats, and the ledger row.

    from lib.studies.pattern_test import daily_signals, run_daily, run_intraday, Signal

    def my_pattern(P):                      # P = DailyPanel (close/high/low/open/adr/elig, all DataFrames)
        hit = (P.close > P.high.shift(1)) & (P.adr >= 3)
        return daily_signals(hit, stop=P.low, side="long")

    run_daily("my pattern", my_pattern, note="the idea in one line")

Why the control matters: every pattern tested so far (UR/ORB9/LVL triggers, the bouncy ball at two
timeframes) was matched or beaten by a RANDOM entry in the same name over the same window. A pattern that
does not beat that control is finding days, not moments -- see data/studies/pattern_ledger.md.

Bar to pass: beats its control, positive in both halves, |t| >= 3 on day-clustered means.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

SLIP = 0.0010
MIN_RISK = 0.005      # a stop closer than 0.5% of price is noise, not a stop: those R's explode
R_CLIP = 10.0         # winsorise R so one tiny-denominator trade cannot carry a mean
RNG = np.random.default_rng(20260918)
REPO = Path(__file__).resolve().parents[3]
LEDGER = REPO / "data" / "studies" / "pattern_ledger.csv"
LEDGER_MD = REPO / "data" / "studies" / "pattern_ledger.md"
BARS = REPO / "data" / "cache" / "intraday_1min"
DAILY_ARMS = ["stop_hold", "t1R", "t2R", "trail_bar", "ema20"]
INTRA_ARMS = ["stop_close", "t1R", "t2R", "vwap_flip", "time30", "next_close"]


@dataclass
class DailyPanel:
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    adr: pd.DataFrame
    elig: pd.DataFrame
    ema20: pd.DataFrame


def load_panel(path: str = "data/cache/liquid_panel_2019.parquet") -> DailyPanel:
    from lib.regime.trailing import Panel, liquidity_mask
    raw = pd.read_parquet(REPO / path)
    p = Panel.from_long(raw)
    C, H, L = p.close, p.high, p.low
    return DailyPanel(open=raw.pivot(index="date", columns="ticker", values="open").sort_index(),
                      high=H, low=L, close=C,
                      adr=(H / L - 1).shift(1).rolling(20).mean() * 100,
                      elig=liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect(),
                      ema20=C.ewm(span=20, adjust=False).mean())


def daily_signals(hit: pd.DataFrame, stop: pd.DataFrame, side: str = "long",
                  since: str = "2019-10-01") -> pd.DataFrame:
    """Boolean mask + a stop frame -> the signal table the harness expects."""
    m = hit.fillna(False).astype(bool)
    m = m[m.index >= since]
    ii, jj = np.where(m.values)
    off = len(hit) - len(m)
    return pd.DataFrame(dict(i=ii + off, j=jj, date=hit.index[ii + off], sym=hit.columns[jj],
                             stop=stop.values[ii + off, jj], side=side))


def _daily_arms(P: DailyPanel, j: int, i: int, stop: float, side: str, hold: int) -> dict | None:
    """Enter at the next session's open; R = move in favour / risk. Long and short share one code path."""
    O, C, H, L, E = P.open.values, P.close.values, P.high.values, P.low.values, P.ema20.values
    if i + 1 >= len(C):
        return None
    sgn = 1.0 if side == "long" else -1.0
    entry = O[i + 1, j] * (1 + sgn * SLIP)
    risk = sgn * (entry - stop)
    if not np.isfinite(entry) or not np.isfinite(risk) or risk / entry < MIN_RISK or risk / entry > 0.25:
        return None
    out = {}
    for arm in DAILY_ARMS:
        r = np.nan
        for k in range(i + 1, min(i + 1 + hold, len(C))):
            c = C[k, j]
            if not np.isfinite(c):
                continue
            if sgn * (c - stop) < 0:                               # stopped on a close through the level
                r = sgn * (c * (1 - sgn * SLIP) - entry) / risk
                break
            if arm == "t1R" and sgn * (c - entry) >= risk:
                r = 1.0
                break
            if arm == "t2R" and sgn * (c - entry) >= 2 * risk:
                r = 2.0
                break
            if arm == "trail_bar" and k > i + 1 and sgn * (c - (L if side == "long" else H)[k - 1, j]) < 0:
                r = sgn * (c * (1 - sgn * SLIP) - entry) / risk
                break
            if arm == "ema20" and np.isfinite(E[k, j]) and sgn * (c - E[k, j]) < 0:
                r = sgn * (c * (1 - sgn * SLIP) - entry) / risk
                break
        if not np.isfinite(r):
            k = min(i + hold, len(C) - 1)
            r = sgn * (C[k, j] * (1 - sgn * SLIP) - entry) / risk
        out[arm] = float(np.clip(r, -R_CLIP, R_CLIP))
    return out


def _stats(x: pd.DataFrame, arm: str) -> dict:
    s = x[arm].dropna()
    if len(s) < 20:
        return dict(n=len(s))
    d = s.groupby(x.loc[s.index, "date"]).mean()
    return dict(n=len(s), meanR=s.mean(), medR=s.median(), win=100 * (s > 0).mean(),
                p90=s.quantile(0.9), t=d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan)


def _report(name: str, T: pd.DataFrame, K: pd.DataFrame, arms: list[str], split: str,
            note: str, timeframe: str, ledger: bool = True) -> pd.DataFrame:
    tab = pd.DataFrame({a: _stats(T, a) for a in arms}).T
    tab["ctrl"] = [K[a].dropna().mean() if len(K) and a in K else np.nan for a in arms]
    tab["edge"] = tab.meanR - tab.ctrl
    print(f"\n=== {name} ({timeframe}) — {len(T):,} signals, {T.sym.nunique()} names, "
          f"{pd.to_datetime(T.date).min().date()} -> {pd.to_datetime(T.date).max().date()} ===")
    print(tab.round(3).to_string())
    h1, h2 = T[T.date < split], T[T.date >= split]
    halves = pd.DataFrame({f"<{split}": {a: h1[a].mean() for a in arms},
                           f">={split}": {a: h2[a].mean() for a in arms}}).round(3)
    print(f"\nby half (n {len(h1)} / {len(h2)}):")
    print(halves.to_string())
    best = tab.edge.idxmax() if tab.edge.notna().any() else tab.meanR.idxmax()
    row = tab.loc[best]
    passed = (np.isfinite(row.get("edge", np.nan)) and row.edge > 0 and abs(row.t) >= 3
              and h1[best].mean() > 0 and h2[best].mean() > 0)
    if ledger:
        append_ledger(name=name, timeframe=timeframe, n=len(T), best_arm=best, meanR=row.meanR,
                      ctrl=row.get("ctrl", np.nan), edge=row.get("edge", np.nan), t=row.t,
                      half1=h1[best].mean(), half2=h2[best].mean(), passed=passed, note=note)
    print(f"\nbest arm by edge: {best} | passes the bar (beats control, both halves positive, |t|>=3): "
          f"{'YES' if passed else 'no'}")
    return tab


def append_ledger(**row) -> None:
    row = {"tested": datetime.now().strftime("%Y-%m-%d"), **row}
    df = pd.DataFrame([row])
    if LEDGER.exists():
        df = pd.concat([pd.read_csv(LEDGER), df], ignore_index=True)
    df.to_csv(LEDGER, index=False)
    cols = ["tested", "name", "timeframe", "n", "best_arm", "meanR", "ctrl", "edge", "t", "half1", "half2", "passed", "note"]
    d = df.reindex(columns=cols).round(3).astype(str)
    md = ("| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
          + "\n".join("| " + " | ".join(r) + " |" for r in d.values))
    hdr = (f"# Pattern ledger\n\n_Every entry pattern tested with `lib.studies.pattern_test`, newest last._\n\n"
           f"**Bar to pass:** beats the same-name random control, positive in both halves, |t| >= 3.\n"
           f"**Multiple testing:** {len(df)} patterns tested so far — at 5% significance, expect "
           f"~{0.05 * len(df):.1f} to clear by chance. Discount accordingly.\n\n")
    LEDGER_MD.write_text(hdr + md + "\n")


def run_daily(name: str, pattern, *, hold: int = 5, controls: int = 3, split: str = "2023-01-01",
              note: str = "", panel: DailyPanel | None = None, ledger: bool = True) -> pd.DataFrame:
    """pattern(P) -> signal table (from daily_signals). Control = same name, random session, same month.
    ledger=False for parameter sweeps: report only, no ledger row (keeps the multiple-testing count honest)."""
    P = panel or load_panel()
    S = pattern(P)
    idx = P.close.index
    recs, ctrl, keys = [], [], {(int(r.j), int(r.i)) for r in S.itertuples()}
    for r in S.itertuples(index=False):
        o = _daily_arms(P, int(r.j), int(r.i), float(r.stop), r.side, hold)
        if not o:
            continue
        recs.append({**o, "sym": r.sym, "date": str(pd.Timestamp(r.date).date()), "side": r.side})
        d = pd.Timestamp(r.date)
        same_month = np.flatnonzero((idx.year == d.year) & (idx.month == d.month))
        cand = [k for k in same_month if (int(r.j), int(k)) not in keys and k + hold + 2 < len(idx)
                and P.elig.values[k, int(r.j)]]
        if not cand:
            continue
        stop_pct = float(r.stop) / P.open.values[int(r.i) + 1, int(r.j)] - 1
        for k in RNG.choice(cand, size=min(controls, len(cand)), replace=False):
            k = int(k)
            co = _daily_arms(P, int(r.j), k, P.open.values[k + 1, int(r.j)] * (1 + stop_pct), r.side, hold)
            if co:
                ctrl.append({**co, "sym": r.sym, "date": str(idx[k].date()), "side": r.side})
    T, K = pd.DataFrame(recs), pd.DataFrame(ctrl)
    if T.empty:
        print(f"{name}: no signals"); return T
    T.to_parquet(REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet", index=False)
    return _report(name, T, K, DAILY_ARMS, split, note, "daily", ledger=ledger)


def run_intraday(name: str, pattern, *, controls: int = 3, split: str = "2026-06-01",
                 note: str = "", files: list[Path] | None = None) -> pd.DataFrame:
    """pattern(sym, day, bars, adr_pct) -> [{t, stop, side, ...}]. Control = same name-day, random minute."""
    daily = pd.read_parquet(REPO / "data/cache/stage_a_daily.parquet")
    daily["date"] = pd.to_datetime(daily.date)
    dcl = daily.pivot(index="date", columns="ticker", values="close").sort_index()
    adr = ((daily.pivot(index="date", columns="ticker", values="high")
            / daily.pivot(index="date", columns="ticker", values="low") - 1) * 100).rolling(20).mean()
    recs, ctrl = [], []
    for p in (files or sorted(BARS.glob("*.parquet"))):
        sym, day = p.name.rsplit("_", 1)[0], p.name.rsplit("_", 1)[1][:-8]
        ts = pd.Timestamp(day)
        if sym not in adr.columns or ts not in adr.index:
            continue
        a_pct = adr[sym].iloc[max(adr.index.searchsorted(ts) - 1, 0)]
        b = pd.read_parquet(p)
        b = b[~b.index.duplicated(keep="first")].sort_index()
        if len(b) < 60 or not np.isfinite(a_pct):
            continue
        cv = (b.vwap * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)
        for s in pattern(sym, day, b, a_pct):
            i0 = int(b.index.searchsorted(pd.Timestamp(s["t"]), side="right"))
            if i0 >= len(b) - 2:
                continue
            o = _intra_arms(b, cv, i0, float(s["stop"]), s.get("side", "long"), sym, day, dcl)
            if not o:
                continue
            recs.append({**o, "sym": sym, "date": day, "side": s.get("side", "long"),
                         **{k: v for k, v in s.items() if k not in ("t", "stop", "side")}})
            lo = int(b.index.searchsorted(pd.Timestamp(f"{day} 09:45")))
            hi = int(b.index.searchsorted(pd.Timestamp(f"{day} 15:30")))
            if hi - lo <= 10:
                continue
            sgn = 1.0 if s.get("side", "long") == "long" else -1.0
            stop_pct = float(s["stop"]) / (float(b.iloc[i0].open) * (1 + sgn * SLIP)) - 1
            for k in RNG.choice(np.arange(lo, hi), size=min(controls, hi - lo), replace=False):
                e = float(b.iloc[int(k)].open) * (1 + sgn * SLIP)
                co = _intra_arms(b, cv, int(k), e * (1 + stop_pct), s.get("side", "long"), sym, day, dcl)
                if co:
                    ctrl.append({**co, "sym": sym, "date": day})
    T, K = pd.DataFrame(recs), pd.DataFrame(ctrl)
    if T.empty:
        print(f"{name}: no signals"); return T
    T.to_parquet(REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_intraday.parquet", index=False)
    print(f"{len(T) / T.date.nunique():.2f} signals per session")
    return _report(name, T, K, INTRA_ARMS, split, note, "intraday")


def _intra_arms(b: pd.DataFrame, cv: pd.Series, i0: int, stop: float, side: str,
                sym: str, day: str, dcl: pd.DataFrame) -> dict | None:
    sgn = 1.0 if side == "long" else -1.0
    entry = float(b.iloc[i0].open) * (1 + sgn * SLIP)
    risk = sgn * (entry - stop)
    if not np.isfinite(risk) or risk / entry < MIN_RISK or risk / entry > 0.10:
        return None
    sub, out, stopped = b.iloc[i0:], {}, False
    hi, lo, cl = sub.high.values, sub.low.values, sub.close.values
    for arm in INTRA_ARMS:
        if arm == "next_close":
            continue
        r, lim = np.nan, (30 if arm == "time30" else len(sub))
        for k in range(min(lim, len(sub))):
            through = (lo[k] <= stop) if side == "long" else (hi[k] >= stop)
            if through:
                r, stopped = sgn * (stop * (1 - sgn * SLIP) - entry) / risk, True
                break
            fav = (hi[k] - entry) if side == "long" else (entry - lo[k])
            if arm == "t1R" and fav >= risk:
                r = 1.0
                break
            if arm == "t2R" and fav >= 2 * risk:
                r = 2.0
                break
            if arm == "vwap_flip" and k > 0 and sgn * (cl[k] - cv.iloc[i0 + k]) < 0:
                r = sgn * (cl[k] * (1 - sgn * SLIP) - entry) / risk
                break
        if not np.isfinite(r):
            r = sgn * (cl[min(lim, len(sub)) - 1] * (1 - sgn * SLIP) - entry) / risk
        out[arm] = float(np.clip(r, -R_CLIP, R_CLIP))
    if stopped or sym not in dcl.columns:
        out["next_close"] = out["stop_close"]
    else:
        pos = dcl.index.searchsorted(pd.Timestamp(day))
        nxt = dcl[sym].iloc[pos + 1] if pos + 1 < len(dcl) else np.nan
        out["next_close"] = (sgn * (float(nxt) * (1 - sgn * SLIP) - entry) / risk
                             if np.isfinite(nxt) else np.nan)
    return out
