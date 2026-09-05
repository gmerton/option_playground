"""
Trailing-window market regime + setup scoreboard.

Built 2026-09-05 after the August 2026 retrospective
(data/studies/august_2026_retrospective.md). Everything here is computed on a
rolling basis from wide daily frames (date x ticker), so the same code answers
"what is working over the trailing N sessions as of today" and "what would the
read have been on any past date" using only data available on that date.

Three layers:
  1. breadth()        - daily breadth series (advancer %, 10-day advancer average,
                        % above 50/200-day, new highs/lows).
  2. style_spread()   - daily trailing-N return of the LAGGARD quintile (furthest
                        below its 52-week high N sessions ago) minus the LEADER
                        quintile. Positive = laggard-turn tape, negative = momentum
                        tape. Cohorts are fixed N sessions back, so it is ex-ante.
  3. setup_events() / scoreboard() - the setup definitions from the August study,
                        with forward returns, so any trailing window can be scored.

regime(asof) folds 1+2 into a small dict the daily report can print. Thresholds
live in REGIME_DEFAULTS and are meant to be set by run_regime_validation.py, not
tuned to a single month.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

REGIME_DEFAULTS = dict(
    window=21,            # trailing sessions (~30 calendar days)
    breadth_on=0.50,      # 10-day advancer average above this = breadth ON
    style_band=0.03,      # |laggard - leader| trailing spread beyond this = a style call
    laggard_off_hi=-0.30, # "laggard" = at least this far below the prior 52-week high
    leader_off_hi=-0.10,  # "leader" = within this of the prior 52-week high
    addv_min=30e6,
    px_min=5.0,
)


@dataclass
class Panel:
    close: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    dolvol: pd.DataFrame

    @classmethod
    def from_long(cls, df: pd.DataFrame) -> "Panel":
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        piv = lambda v: df.pivot(index="date", columns="ticker", values=v).sort_index()
        return cls(piv("close"), piv("high"), piv("low"), piv("dolvol"))

    @classmethod
    def from_cache(cls, path: str) -> "Panel":
        from lib.minervini.scan import load_cache
        c, h, l, dv = load_cache(path)
        return cls(c, h, l, dv)

    def restrict(self, tickers) -> "Panel":
        t = [x for x in tickers if x in self.close.columns]
        return Panel(self.close[t], self.high[t], self.low[t], self.dolvol[t])

    def suspect(self, jump: float = 0.8, pad: int = 30) -> pd.DataFrame:
        """
        True on ticker-days within +/-pad sessions of a single-day |return| > jump.
        The Polygon day-cache is NOT split-adjusted, so reverse splits show up as
        +900% days; anything spanning them is excluded from returns/cohorts.
        """
        r = self.close.pct_change(fill_method=None).abs()
        bad = (r > jump).astype(float)
        return bad.rolling(2 * pad + 1, center=True, min_periods=1).max().fillna(0).astype(bool)

    def upto(self, asof) -> "Panel":
        asof = pd.Timestamp(asof)
        return Panel(*(f.loc[:asof] for f in (self.close, self.high, self.low, self.dolvol)))


def liquid_universe(p: Panel, asof, addv_min=REGIME_DEFAULTS["addv_min"], px_min=REGIME_DEFAULTS["px_min"]) -> pd.Index:
    """Names with 50-day average dollar volume >= addv_min and price >= px_min as of `asof`."""
    asof = pd.Timestamp(asof)
    c = p.close.loc[:asof]
    addv = p.dolvol.loc[:asof].tail(50).mean()
    px = c.iloc[-1]
    ok = (addv >= addv_min) & (px >= px_min)
    return ok[ok].index


def liquidity_mask(p: Panel, addv_min=REGIME_DEFAULTS["addv_min"], px_min=REGIME_DEFAULTS["px_min"]) -> pd.DataFrame:
    """Point-in-time eligibility (date x ticker): trailing-50 ADDV >= addv_min and close >= px_min."""
    addv = p.dolvol.rolling(50, min_periods=30).mean()
    return (addv >= addv_min) & (p.close >= px_min)


# --------------------------------------------------------------------------- breadth
def breadth(p: Panel) -> pd.DataFrame:
    C, H, L = p.close, p.high, p.low
    r = C.pct_change(fill_method=None)
    adv = (r > 0).sum(axis=1) / r.notna().sum(axis=1)
    sma50 = C.rolling(50, min_periods=50).mean()
    sma200 = C.rolling(200, min_periods=150).mean()
    hi252 = H.rolling(252, min_periods=120).max().shift(1)
    lo252 = L.rolling(252, min_periods=120).min().shift(1)
    out = pd.DataFrame({
        "adv_pct": adv,
        "adv10": adv.rolling(10).mean(),
        "pct_above_50": (C > sma50).sum(axis=1) / sma50.notna().sum(axis=1),
        "pct_above_200": (C > sma200).sum(axis=1) / sma200.notna().sum(axis=1),
        "new_hi": (C > hi252).sum(axis=1),
        "new_lo": (C < lo252).sum(axis=1),
    })
    out["nh_nl_10"] = (out.new_hi - out.new_lo).rolling(10).sum()
    out["thrust"] = (adv > 0.70) & (adv.shift(1) > 0.70)  # two straight 70%+ advancer days
    return out


# --------------------------------------------------------------------------- style spread
def from_high(p: Panel) -> pd.DataFrame:
    """close / prior-252-session high - 1 (ex-ante: today's high excluded)."""
    return p.close / p.high.rolling(252, min_periods=120).max().shift(1) - 1


def style_spread(p: Panel, window: int = REGIME_DEFAULTS["window"], eligible: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    For each date t: equal-weight return over (t-window, t] of the laggard quintile
    vs the leader quintile, where quintiles are ranked on distance-from-52wk-high as
    of t-window. Returns columns laggard, leader, spread, n.
    """
    C = p.close
    fh = from_high(p).shift(window)
    ret = (C / C.shift(window) - 1).mask(p.suspect())
    if eligible is not None:
        fh = fh.where(eligible.shift(window).fillna(False).astype(bool))
    rank = fh.rank(axis=1, pct=True)
    lag = ret.where(rank <= 0.20)
    lead = ret.where(rank >= 0.80)
    # medians: robust to the handful of split/garbage names the cache carries
    out = pd.DataFrame({"laggard": lag.median(axis=1), "leader": lead.median(axis=1), "n": rank.notna().sum(axis=1)})
    out["spread"] = out.laggard - out.leader
    return out


def regime(p: Panel, asof, cfg: Optional[dict] = None, universe: Optional[pd.Index] = None) -> Dict:
    """Ex-ante regime read as of `asof` on the liquid universe."""
    cfg = {**REGIME_DEFAULTS, **(cfg or {})}
    asof = pd.Timestamp(asof)
    if universe is None:
        universe = liquid_universe(p, asof, cfg["addv_min"], cfg["px_min"])
    q = p.restrict(universe).upto(asof)
    b = breadth(q).iloc[-1]
    s = style_spread(q, cfg["window"]).iloc[-1]
    if s.spread > cfg["style_band"]:
        style = "LAGGARD-TURN"
    elif s.spread < -cfg["style_band"]:
        style = "MOMENTUM"
    else:
        style = "NEUTRAL"
    return dict(
        asof=asof.date(), n_universe=len(universe),
        adv10=float(b.adv10), pct_above_50=float(b.pct_above_50), pct_above_200=float(b.pct_above_200),
        new_hi=int(b.new_hi), new_lo=int(b.new_lo), nh_nl_10=float(b.nh_nl_10),
        breadth_on=bool(b.adv10 >= cfg["breadth_on"]),
        laggard_ret=float(s.laggard), leader_ret=float(s.leader), spread=float(s.spread), style=style,
    )


# --------------------------------------------------------------------------- setups
def setup_events(p: Panel, cfg: Optional[dict] = None) -> Dict[str, pd.DataFrame]:
    """Boolean event frames (date x ticker). Long-side setups unless prefixed SHORT."""
    cfg = {**REGIME_DEFAULTS, **(cfg or {})}
    C, H, L, DV = p.close, p.high, p.low, p.dolvol
    r1 = C.pct_change(fill_method=None)
    sma50 = C.rolling(50, min_periods=50).mean()
    sma200 = C.rolling(200, min_periods=150).mean()
    ema10 = C.ewm(span=10, adjust=False).mean()
    ema20 = C.ewm(span=20, adjust=False).mean()
    rvol = DV / DV.rolling(50, min_periods=30).mean().shift(1)
    hi50 = H.rolling(50, min_periods=50).max().shift(1)
    lo50 = L.rolling(50, min_periods=50).min().shift(1)
    lo20 = L.rolling(20, min_periods=20).min().shift(1)
    hi252 = H.rolling(252, min_periods=120).max().shift(1)
    fh = C / hi252 - 1
    up = (C > sma200) & (sma50 > sma200)
    bo = (C > hi50) & (C.shift(1) <= hi50.shift(1))
    ret6m = C / C.shift(126) - 1
    laggard = fh <= cfg["laggard_off_hi"]
    leader = fh >= cfg["leader_off_hi"]
    ev = {}
    ev["breakout_any"] = bo
    ev["breakout_leader_house"] = bo & (rvol >= 1.8) & (C > sma200) & (ret6m > -0.10)
    ev["breakout_leader_rvol1.5"] = bo & (rvol >= 1.5) & leader
    ev["breakout_laggard_rvol1.5"] = bo & (rvol >= 1.5) & laggard
    ev["breakout_52wk_rvol1.5"] = (C > hi252) & (C.shift(1) <= hi252.shift(1)) & (rvol >= 1.5)
    ext = (C / ema20 - 1).rolling(10).max().shift(1) >= 0.05
    ev["pullback_20ema"] = up & (L <= ema20 * 1.01) & (C > ema20) & ext & (C > sma50)
    below50 = C < sma50
    ev["ur_50sma"] = (C > sma50) & (C.shift(1) < sma50.shift(1)) & up & (below50.rolling(5).sum().shift(1) >= 1)
    ev["ur_20dlow"] = (L < lo20) & (C > lo20) & up
    ev["ur_20dlow_rvol1.5"] = ev["ur_20dlow"] & (rvol >= 1.5)
    ev["ep_gap10_rvol3"] = (r1 >= 0.10) & (rvol >= 3)
    ev["meanrev_3down_uptrend"] = (r1 < 0) & (r1.shift(1) < 0) & (r1.shift(2) < 0) & up & (C > sma50)
    sq = (C < sma200) & (C > sma50) & ((C / sma50 - 1) > 0.05) & (C.pct_change(5, fill_method=None) > 0.06)
    ev["laggard_squeeze"] = sq & ~sq.shift(1, fill_value=False)
    bd = (C < lo50) & (C.shift(1) >= lo50.shift(1))
    ev["SHORT_breakdown_any"] = bd
    ev["SHORT_breakdown_rvol1.3"] = bd & (rvol >= 1.3)
    ev["SHORT_gapdown10_rvol3"] = (r1 <= -0.10) & (rvol >= 3)
    return ev


def forward_returns(p: Panel, horizon: int, clip=(-0.6, 1.0)) -> pd.DataFrame:
    """Forward `horizon`-session return, NaN across split-suspect spans, clipped for robust means."""
    fr = (p.close.shift(-horizon) / p.close - 1).mask(p.suspect())
    return fr.clip(*clip) if clip else fr


def scoreboard(p: Panel, start, end, horizon: int = 10, events: Optional[Dict[str, pd.DataFrame]] = None,
               min_n: int = 5, eligible: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Score every setup on events dated in [start, end]. Returns n, names, mean/median
    forward return (means on returns clipped to [-60%, +100%]), win rate, and excess
    vs the every-stock-every-day baseline over the same dates (tape drift netted out).
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    events = events or setup_events(p)
    fr = forward_returns(p, horizon).loc[start:end]
    if eligible is not None:
        fr = fr.where(eligible.loc[start:end].reindex(columns=fr.columns).fillna(False).astype(bool))
    base = fr.stack().dropna()
    base_by_date = fr.mean(axis=1)
    rows = [dict(setup="BASELINE_all", n=len(base), names=fr.shape[1], mean=base.mean(), median=base.median(),
                 win=(base > 0).mean(), excess=0.0)]
    for name, m in events.items():
        mm = m.loc[start:end].reindex(columns=fr.columns).fillna(False).astype(bool)
        x = fr.where(mm).stack().dropna()
        if len(x) < min_n:
            rows.append(dict(setup=name, n=len(x), names=0, mean=np.nan, median=np.nan, win=np.nan, excess=np.nan))
            continue
        dates = x.index.get_level_values(0)
        rows.append(dict(setup=name, n=len(x), names=x.index.get_level_values(1).nunique(), mean=x.mean(),
                         median=x.median(), win=(x > 0).mean(), excess=(x.values - base_by_date.reindex(dates).values).mean()))
    return pd.DataFrame(rows).set_index("setup")


def cohort_paths(p: Panel, start, end, cfg: Optional[dict] = None) -> pd.DataFrame:
    """Median cumulative return from `start` of laggard / leader / all cohorts fixed at `start`."""
    cfg = {**REGIME_DEFAULTS, **(cfg or {})}
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    fh = from_high(p).loc[start]
    rel = (p.close.loc[start:end] / p.close.loc[start] - 1).mask(p.suspect().loc[start:end])
    return pd.DataFrame({
        "laggards(<=%.0f%% off hi)" % (100 * cfg["laggard_off_hi"]): rel[fh.index[fh <= cfg["laggard_off_hi"]]].median(axis=1),
        "leaders(>=%.0f%% off hi)" % (100 * cfg["leader_off_hi"]): rel[fh.index[fh >= cfg["leader_off_hi"]]].median(axis=1),
        "all": rel.median(axis=1),
    })
