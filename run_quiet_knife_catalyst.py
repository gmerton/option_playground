#!/usr/bin/env python3
"""
QUIET KNIFE x CROWDED SHORT x SCHEDULED CATALYST: is a beaten-down, quiet stock a buy when a KNOWN catalyst is coming
and the short side is crowded? (pre-registered 2026-09-27, before any code or data work; Gabe: "yes". Run 2026-09-27 on Gabe's
"go"; one method change declared below before the run.)

WHY. Gabe's Aug-2026 IBIT buys rode a rebound whose drivers were partly knowable before entry: a White House crypto
summit announced in advance (8/19), and a crowded short (~$2.7B liquidated in 24 h). Alone, "quiet and low in its
range" is a loser (quiet_knife_leaps_2026-09-27: stock lagged same-date control -7.7pp over 180 d; LEAPs INVERTED,
t -4.09). Scheduled catalysts alone don't pay here either (buying into earnings, earnings proximity RETRACTED,
post-catalyst entry NULL, FOMC noise) and neither does high short interest on breakouts (BB-1 NULL, leans negative).
The CONJUNCTION -- quiet knife + crowded short + a catalyst dated before entry -- has never been tested. Stock returns
only (Gabe: "I wouldn't focus on the vehicle").

UNIVERSE   liquid_panel_2009 (1,728 names, yfinance-adjusted; ⚠ survivor-biased, which FLATTERS buying low -- the
           same-date control shares the bias), eligible = ADDV >= $50M and price >= $5 on the prior day.
WINDOW     weekly evaluation dates (last session of each week) 2018-01 -> 2026-06, set by short-interest coverage
           (FINRA via Polygon, data/cache/short_interest.parquet, 2017-12 ->) and a 60-session exit.
STATE      QUIET KNIFE, a vectorised equivalent of lib.sleeping_giants.detector with the coiling gate flipped (as in
           run_quiet_knife_leaps.py): ATR(14)% in the bottom 25% of its trailing 756 sessions AND ATR(14) < ATR(50);
           trailing-1,500-session high-low range >= 50% of price; price <= 40% of that range; the window high set
           >= 1.5 years ago. VALIDATION (declared): on 200 random name-dates the vectorised flag must agree with
           analyze() >= 95% of the time, else fall back to analyze() on the episodes' dates.
           ⚙ CHANGED BEFORE THE RUN (2026-09-27): instead of validating a vectorised copy, a LOOSE vectorised pre-filter
           (ATR% <= rolling 30th pct of 756, ATR14 < ATR50, range >= 45%, price <= 45% of range) shortlists
           candidates and the EXACT analyze() (1,500-bar slice, as run_quiet_knife_leaps.py) decides the flag, so the
           knife state equals the detector by construction. Controls must FAIL the loose pre-filter (surely not knives).
           Episodes: first qualifying week, a new episode after a > 60-day gap (as before).
SHORT      days-to-cover from the latest FINRA settlement that was PUBLIC at entry: settlement date + 10 trading
           days (FINRA's publication lag) <= entry date. HIGH = top tercile of DTC within that week's eligible names;
           LOW = bottom tercile. (BB-1 used the same field.)
CATALYST   a scheduled earnings report (data/cache/earnings_yf.parquet) inside the first 30 calendar days after
           entry. ⚠ yfinance stores actual report dates; companies announce them ~2-5 weeks ahead, so the 30-day window
           is the stated point-in-time proxy.
TRADE      buy the close of the episode date, hold 60 sessions (exit at the close); no stop (the question is the
           direction of the drift, not a stop rule); 10 bp per side.
CONTROL    SAME-DATE: every other eligible name that week with the SAME short tercile and the SAME catalyst flag but
           NOT in the quiet-knife state -- holds the market, the short crowding and the catalyst fixed, varies only
           the quiet-knife state. excess = episode return - control mean.
PRIMARY    the HIGH-SHORT x CATALYST cell: mean excess 60-session return, t on entry-week cluster means.
           BAR: t >= 3, both halves (split 2022-01) positive, positive in a majority of years with episodes.
SECONDARY  (declared) the full 2x2 (short HIGH/LOW x catalyst YES/NO) and the interaction
           [HIGH & CAT] - [LOW & NO CAT]; 4 cells -> Sidak |t| ~ 2.5 for the secondaries.
POWER      report n per cell first; if the primary cell has < 40 episodes, the verdict is UNDERPOWERED whatever the t.
PRIOR      low: each ingredient alone is null or negative; the conjunction is the whole hypothesis.
Local vs cloud: local (cached panel, SI and earnings; the vectorised gates are minutes; the validation sample calls
analyze() 200 times).

Run (when approved): PYTHONPATH=src:. .venv/bin/python3 run_quiet_knife_catalyst.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.sleeping_giants.detector import analyze

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/quiet_knife_catalyst.log"
START, END, SPLIT, HOLD, COST, GAP_DAYS = "2018-01-01", "2026-06-30", "2022-01-01", 60, 0.0010, 60


def log(m):
    print(m, file=sys.stderr, flush=True)


def rma(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def tclu(x: pd.Series, d: pd.Series):
    g = x.groupby(d).mean()
    return g.mean(), (g.mean() / g.std(ddof=1) * np.sqrt(len(g)) if len(g) > 2 else np.nan), len(g)


def main():
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    C, H, L = P.close, P.high, P.low
    E = P.elig.fillna(False).shift(1).fillna(False).astype(bool)
    tr = pd.concat([H - L, (H - C.shift(1)).abs(), (L - C.shift(1)).abs()]).groupby(level=0).max().reindex(C.index)
    a14, a50 = rma(tr, 14), rma(tr, 50)
    ap = a14 / C
    q30 = ap.rolling(756, min_periods=378).quantile(0.30)
    hi, lo = H.rolling(1500, min_periods=378).max(), L.rolling(1500, min_periods=378).min()
    rng, pos = (hi - lo) / C * 100, (C - lo) / (hi - lo) * 100
    loose = (ap <= q30) & (a14 < a50) & (rng >= 45) & (pos <= 45)
    idx = C.index
    wk = pd.Series(idx, index=idx).groupby(idx.to_period("W")).max()
    wk = [d for d in wk if pd.Timestamp(START) <= d <= pd.Timestamp(END)]
    # exact detector on the shortlist
    Hv, Lv, Cv = H.values, L.values, C.values
    knife = []
    for d in wk:
        i = idx.get_loc(d)
        cand = np.where(loose.iloc[i].values & E.iloc[i].values)[0]
        for j in cand:
            s0 = max(0, i - 1499)
            h, l, c = Hv[s0:i + 1, j], Lv[s0:i + 1, j], Cv[s0:i + 1, j]
            ok = np.isfinite(h) & np.isfinite(l) & np.isfinite(c)
            if ok.sum() < 378:
                continue
            r = analyze(list(h[ok]), list(l[ok]), list(c[ok]))
            if r and r["sleeping"] and r["can_wake"] and r["base_len_ok"] and r["pos_in_base"] <= 40:
                knife.append((d, C.columns[j]))
    K = pd.DataFrame(knife, columns=["date", "ticker"]).sort_values(["ticker", "date"])
    eps = []
    for tk, g in K.groupby("ticker"):
        last = None
        for d in g.date:
            if last is None or (d - last).days > GAP_DAYS:
                eps.append((d, tk))
            last = d
    EP = pd.DataFrame(eps, columns=["date", "ticker"])
    log(f"knife weeks {len(K):,}, episodes {len(EP):,} on {EP.ticker.nunique()} names")
    # short interest public at entry: settlement + 10 trading days
    si = pd.read_parquet(REPO / "data/cache/short_interest.parquet")[["settlement_date", "ticker", "days_to_cover"]]
    si["settlement_date"] = pd.to_datetime(si.settlement_date)
    pub = pd.Series(idx[np.minimum(idx.searchsorted(si.settlement_date) + 10, len(idx) - 1)], index=si.index)
    si["public"] = pub.values
    si = si[si.ticker.isin(C.columns)].sort_values("public")
    # earnings dates
    er = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet")[["ticker", "session"]]
    er["session"] = pd.to_datetime(er.session); er = er[er.ticker.isin(C.columns)]
    erd = er.groupby("ticker").session.apply(lambda s: np.sort(s.values)).to_dict()
    fwd = C.shift(-HOLD) / C - 1 - 2 * COST
    rows = []
    for d in sorted(EP.date.unique()):
        i = idx.get_loc(d)
        el = C.columns[E.iloc[i].values & np.isfinite(fwd.iloc[i].values)]
        s = si[si.public <= d].drop_duplicates("ticker", keep="last").set_index("ticker").days_to_cover.reindex(el).dropna()
        if len(s) < 50:
            continue
        terc = pd.qcut(s.rank(method="first"), 3, labels=["LOW", "MID", "HIGH"])
        lim = np.datetime64(d + pd.Timedelta(days=30)); d64 = np.datetime64(d)
        cat = {t: bool(((erd.get(t, np.array([], dtype="datetime64[ns]")) > d64) &
                        (erd.get(t, np.array([], dtype="datetime64[ns]")) <= lim)).any()) for t in terc.index}
        notk = ~loose.iloc[i].reindex(terc.index).fillna(False).astype(bool)
        f = fwd.iloc[i]
        for t in EP[EP.date == d].ticker:
            if t not in terc.index:
                continue
            same = [u for u in terc.index if u != t and notk[u] and terc[u] == terc[t] and cat[u] == cat[t]]
            if len(same) < 5:
                continue
            rows.append(dict(date=d, ticker=t, si=str(terc[t]), cat=cat[t], dtc=s[t], ret=100 * f[t],
                             ctrl=100 * f[same].mean(), n_ctrl=len(same)))
    R = pd.DataFrame(rows); R["ex"] = R.ret - R.ctrl
    out = [f"# Quiet knife x crowded short x scheduled catalyst (pre-registration in the docstring)",
           f"knife weeks {len(K):,}; episodes {len(EP):,} ({EP.ticker.nunique()} names); with SI + control {len(R):,}; "
           f"60-session hold, 10 bp/side, excess vs same-date non-knife names in the same SI tercile and catalyst state"]
    out.append(f"  ALL episodes: raw {R.ret.mean():+.2f}% | excess {R.ex.mean():+.2f}pp t {tclu(R.ex, R.date)[1]:+.2f} "
               f"median {R.ex.median():+.2f} win {100 * (R.ex > 0).mean():.0f}%")
    res = {}
    for si_, cat_ in (("HIGH", True), ("HIGH", False), ("LOW", True), ("LOW", False), ("MID", True), ("MID", False)):
        x = R[(R.si == si_) & (R.cat == cat_)]
        if len(x) < 3:
            out.append(f"  {si_:4s} short x catalyst={cat_!s:5s}: n {len(x)} (too few)"); continue
        m, t, nd = tclu(x.ex, x.date)
        h = x.date < SPLIT
        yr = x.groupby(x.date.dt.year).ex.mean()
        tag = "  *PRIMARY*" if (si_ == "HIGH" and cat_) else ""
        out.append(f"  {si_:4s} short x catalyst={cat_!s:5s}: n {len(x):4d} weeks {nd:3d}  raw {x.ret.mean():+.2f}%  "
                   f"excess {m:+.2f}pp t {t:+.2f}  median {x.ex.median():+.2f}  halves "
                   f"{x[h].ex.mean() if h.any() else np.nan:+.2f} / {x[~h].ex.mean() if (~h).any() else np.nan:+.2f}  "
                   f"yrs+ {(yr > 0).sum()}/{len(yr)}{tag}")
        res[(si_, cat_)] = (len(x), m, t, x[h].ex.mean() if h.any() else np.nan, x[~h].ex.mean() if (~h).any() else np.nan,
                            (yr > 0).sum(), len(yr))
    a, b = R[(R.si == "HIGH") & R.cat], R[(R.si == "LOW") & ~R.cat]
    if len(a) > 2 and len(b) > 2:
        ga, gb = a.groupby("date").ex.mean(), b.groupby("date").ex.mean()
        tw = (ga.mean() - gb.mean()) / np.sqrt(ga.var(ddof=1) / len(ga) + gb.var(ddof=1) / len(gb))
        out.append(f"  interaction [HIGH & CAT] - [LOW & NO CAT]: {a.ex.mean() - b.ex.mean():+.2f}pp Welch t {tw:+.2f}")
    p = res.get(("HIGH", True))
    if p is None or p[0] < 40:
        verdict = f"UNDERPOWERED (primary n {0 if p is None else p[0]} < 40)"
    else:
        n, m, t, h1, h2, yp, ny = p
        verdict = "PASS" if (t >= 3 and h1 > 0 and h2 > 0 and yp > ny / 2) else "NOT MET"
    out.append(f"\nBAR (PRIMARY HIGH short x catalyst): {verdict}")
    R.to_csv(REPO / "data/studies/quiet_knife_catalyst_2026-09-27.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
