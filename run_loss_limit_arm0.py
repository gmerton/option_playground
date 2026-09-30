#!/usr/bin/env python3
"""
Breitstein test 1, ARM 0: is there a tilt signature in Gabe's own log after losses? (pre-registered 2026-09-30,
BEFORE pulling results; spec = TEST_INDEX §10 "Cameron's 80% chance of doubling the loss", restructured 2026-09-22.)

Why arm 0 first: under i.i.d. outcomes a daily loss limit is negative for a profitable book and positive for a losing
one purely because it changes n, so a dollar replay is predetermined by the sign of expectancy. The rule has content
only if outcomes AFTER the trigger are conditionally worse. If (a) is flat, three queue rows settle NULL together:
Cameron's max-loss limit, IQCapital's "stop after 2 consecutive losses", and the ~90-min shutoff.

ADMISSIBILITY: conformance / execution use of the journal only (feedback_gabes_trades_are_not_evidence). Nothing here
selects a setup.

DATA: stocks.journal_trades (Flex fills, ET timestamps), 2026-08-03 -> latest. ⚠ POWER CEILING, declared before
pulling: ~41 sessions. This test CANNOT certify a positive rule; the house bar |t| >= 3 applies and a t of 1.5 is not
encouragement. Only a large, same-direction signature across (a)-(c) is informative.

UNIT = an underlying-level EPISODE: starts at the first opening fill when the underlying is flat (all legs, stock and
options, counted via open_close), ends when every leg is flat again. P&L = sum of IBKR realized_pnl over its fills.
Rolls inside a live position stay in one episode. Closing fills of positions carried in from before 2026-08-03 form
"carried" episodes: they count in the loss sequence but are never scored as a candidate. BookTrade rows (expiry /
assignment) are kept for P&L.

(a) PRIMARY. For each opened episode E, k = the number of consecutive LOSING episodes closed earlier the SAME
    session before E's first fill (most recent first). Outcome: E's $ P&L and win. Paired control: E minus the mean of
    the OTHER episodes opened the same session with k = 0. Cells k >= 1, k >= 2 (= the IQCapital rule), k >= 3.
    t clustered by session. PRIMARY CELL: k >= 2, $ P&L.
(b) Size (the revenge fingerprint): entry notional (opening fills, options x100) / Gabe's median entry notional for
    that asset class, same k cells, same-session paired.
(c) Execution: for stock episodes, the entry-to-exit move in units of the name's ADR (20d mean high/low - 1, from the
    liquid panel, prior day; names off-panel dropped). Losing episodes whose loss exceeds 1 ADR = past the disaster stop.
    Share past 1 ADR after k >= 1 vs k = 0.
(d) Daily limits: L in {$500, $1,000, 1% NAV}. Cum realized P&L by fill time (realized only; no intraday marks). For
    sessions that breach -L: rest-of-day realized P&L after the breach and the share closing <= -2L (Cameron's "80%"),
    vs sessions that touch -0.5L but never -L (rest-of-day after the -0.5L touch).
(e) Shutoff: episodes opened after 11:00 ET minus episodes opened 09:30-11:00, same-session paired.
Prior (2026-09-22): ~70% that (a) is flat, ~45% that a size or stop signature (b)/(c) is present.

Run: PYTHONPATH=src .venv/bin/python3 run_loss_limit_arm0.py   (log -> data/studies/logs/loss_limit_arm0.log)
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from lib.mysql_lib import _get_conn

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/loss_limit_arm0.log"


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    con = _get_conn()
    f = pd.read_sql("select trade_id, conid, trade_date, underlying_symbol u, asset_category ac, buy_sell, open_close oc, "
                    "quantity q, trade_price px, realized_pnl pnl, transaction_type tt, trade_datetime dt "
                    "from journal_trades order by trade_datetime, trade_id", con)
    nav = pd.read_sql("select report_date, nav from journal_nav order by report_date", con)
    con.close()
    for c in ("q", "px", "pnl"):
        f[c] = f[c].astype(float)
    f["pnl"] = f.pnl.fillna(0.0)
    f["dt"] = pd.to_datetime(f.dt)
    f["trade_date"] = pd.to_datetime(f.trade_date)
    return f, nav


def episodes(f: pd.DataFrame) -> pd.DataFrame:
    pos = defaultdict(float)                       # conid -> |open quantity|
    live: dict[str, dict] = {}
    out = []
    for r in f.itertuples():
        mult = 100 if r.ac == "OPT" else 1
        ep = live.get(r.u)
        opening = "O" in str(r.oc)
        if ep is None:
            ep = dict(u=r.u, start=r.dt, day=r.trade_date, carried=not opening, pnl=0.0, notional=0.0,
                      ac=r.ac, legs=set(), entry_px=None, exit_px=None, stk_side=None)
            live[r.u] = ep
        ep["pnl"] += r.pnl
        ep["end"] = r.dt
        if opening:
            ep["notional"] += abs(r.q * r.px * mult)
            pos[r.conid] += abs(r.q)
            ep["legs"].add(r.conid)
            if r.ac == "STK" and ep["entry_px"] is None:
                ep["entry_px"], ep["stk_side"] = r.px, (1 if r.buy_sell == "BUY" else -1)
        else:
            pos[r.conid] = max(0.0, pos[r.conid] - abs(r.q))
            if r.ac == "STK":
                ep["exit_px"] = r.px
        if ep["ac"] != r.ac:
            ep["ac"] = "MIX"
        if all(pos[c] <= 1e-9 for c in ep["legs"]):
            out.append(ep)
            del live[r.u]
    E = pd.DataFrame(out)
    E["win"] = E.pnl > 0
    E["loss"] = E.pnl < 0
    return E, len(live)


def tstat(x: pd.Series, g: pd.Series) -> float:
    m = x.groupby(g).mean()
    return float(m.mean() / m.std(ddof=1) * np.sqrt(len(m))) if len(m) > 2 and m.std(ddof=1) > 0 else np.nan


def add_streak(E: pd.DataFrame) -> pd.DataFrame:
    E = E.sort_values("start").reset_index(drop=True)
    ks = []
    for r in E.itertuples():
        prior = E[(E.day == r.day) & (E.end < r.start)].sort_values("end", ascending=False)
        k = 0
        for w in prior.loss.values:
            if not w:
                break
            k += 1
        ks.append(k)
    E["k"] = ks
    return E


def paired(E: pd.DataFrame, cond: pd.Series, ref: pd.Series, col: str) -> dict:
    rows = []
    for d, g in E.groupby("day"):
        a, b = g[cond.loc[g.index]], g[ref.loc[g.index]]
        if len(a) and len(b):
            rows.append(dict(day=d, diff=a[col].mean() - b[col].mean(), n=len(a)))
    R = pd.DataFrame(rows)
    if R.empty:
        return dict(sessions=0, n=0, diff=np.nan, t=np.nan)
    t = R["diff"].mean() / R["diff"].std(ddof=1) * np.sqrt(len(R)) if len(R) > 2 else np.nan
    return dict(sessions=len(R), n=int(R.n.sum()), diff=R["diff"].mean(), t=t)


def adr_lookup(E: pd.DataFrame) -> pd.Series:
    p = pd.read_parquet(REPO / "data/cache/liquid_panel_2019.parquet", columns=["date", "ticker", "high", "low"])
    p = p[p.ticker.isin(E.u.unique()) & (p.date >= "2026-06-01")].copy()
    p["r"] = p.high / p.low - 1
    p = p.sort_values("date")
    p["adr"] = p.groupby("ticker").r.transform(lambda s: s.rolling(20).mean().shift(1))
    key = p.set_index(["ticker", "date"]).adr
    return pd.Series([key.get((u, d), np.nan) for u, d in zip(E.u, E.day)], index=E.index)


def main():
    f, nav = load()
    E, open_left = episodes(f)
    L = [f"# Loss-limit ARM 0 (pre-registration in the docstring)",
         f"fills {len(f):,}, sessions {f.trade_date.nunique()} ({f.trade_date.min().date()} -> {f.trade_date.max().date()}); "
         f"episodes {len(E):,} (carried-in {int(E.carried.sum())}), still open {open_left}"]
    E = add_streak(E)
    S = E[~E.carried].copy()
    L.append(f"scored episodes {len(S):,}; win {100 * S.win.mean():.1f}%, mean ${S.pnl.mean():+.1f}, total ${S.pnl.sum():+,.0f}")
    L.append("k distribution (same-session consecutive prior losses): " + S.k.value_counts().sort_index().to_string().replace("\n", "; "))
    med = S.groupby("ac").notional.median()
    S["size_rel"] = S.notional / S.ac.map(med)

    L.append("\n## (a) outcome after k same-session consecutive losses vs k = 0 same session (paired, t by session)")
    rows = []
    for k in (1, 2, 3):
        cond, ref = S.k >= k, S.k == 0
        for col in ("pnl", "win"):
            r = paired(S.assign(win=S.win.astype(float)), cond, ref, col)
            rows.append(dict(cell=f"k>={k}", metric=col, **r,
                             uncond_cond=S.loc[cond, col].astype(float).mean(), uncond_k0=S.loc[ref, col].astype(float).mean()))
    A = pd.DataFrame(rows)
    L.append(A.round(3).to_string(index=False))

    L.append("\n## (b) size relative to his own median notional (per asset class)")
    rows = [dict(cell=f"k>={k}", **paired(S, S.k >= k, S.k == 0, "size_rel"),
                 med_cond=S.loc[S.k >= k, "size_rel"].median(), med_k0=S.loc[S.k == 0, "size_rel"].median())
            for k in (1, 2, 3)]
    L.append(pd.DataFrame(rows).round(3).to_string(index=False))

    L.append("\n## (c) stock episodes: move to exit in ADR units")
    st = S[(S.ac == "STK") & S.entry_px.notna() & S.exit_px.notna()].copy()
    st["adr"] = adr_lookup(st)
    st = st[st.adr.notna()]
    st["move_adr"] = st.stk_side * (st.exit_px / st.entry_px - 1) / st.adr
    lo = st[st.loss]
    for lab, m in (("k>=1", lo.k >= 1), ("k=0", lo.k == 0)):
        x = lo[m]
        L.append(f"{lab}: losing stock episodes {len(x)}, median loss {x.move_adr.median():+.2f} ADR, "
                 f"past the 1-ADR disaster stop {100 * (x.move_adr < -1).mean():.1f}%")
    L.append(f"(stock episodes with ADR {len(st)} of {int((S.ac == 'STK').sum())})")

    L.append("\n## (d) daily loss limits on cumulative realized P&L (realized only)")
    f = f.sort_values("dt")
    navd = nav.set_index(pd.to_datetime(nav.report_date)).nav.astype(float)
    rows = []
    for lab in ("$500", "$1000", "1% NAV"):
        br, half = [], []
        for d, g in f.groupby("trade_date"):
            lim = 500 if lab == "$500" else 1000 if lab == "$1000" else 0.01 * float(navd[navd.index < d].iloc[-1] if (navd.index < d).any() else navd.iloc[0])
            cum = g.pnl.cumsum().values
            day = cum[-1]
            hit = np.where(cum <= -lim)[0]
            hh = np.where(cum <= -0.5 * lim)[0]
            if len(hit):
                i = hit[0]
                br.append(dict(rest=day - cum[i], closes_2x=day <= -2 * lim, day=day, lim=lim))
            elif len(hh):
                i = hh[0]
                half.append(dict(rest=day - cum[i], day=day))
        B, H = pd.DataFrame(br), pd.DataFrame(half)
        rows.append(dict(limit=lab, breach_sessions=len(B), rest_of_day_mean=B.rest.mean() if len(B) else np.nan,
                         rest_neg_share=100 * (B.rest < 0).mean() if len(B) else np.nan,
                         close_le_2x_share=100 * B.closes_2x.mean() if len(B) else np.nan,
                         half_touch_sessions=len(H), half_rest_mean=H.rest.mean() if len(H) else np.nan,
                         half_rest_neg_share=100 * (H.rest < 0).mean() if len(H) else np.nan))
    L.append(pd.DataFrame(rows).round(1).to_string(index=False))

    L.append("\n## (e) opened after 11:00 ET vs 09:30-11:00, same session paired")
    late = S.start.dt.time >= pd.Timestamp("11:00").time()
    for col in ("pnl", "win"):
        r = paired(S.assign(win=S.win.astype(float)), late, ~late, col)
        L.append(f"{col}: {r}  | late n {int(late.sum())} mean {S.loc[late, col].astype(float).mean():.3f}, "
                 f"early n {int((~late).sum())} mean {S.loc[~late, col].astype(float).mean():.3f}")

    S.drop(columns=["legs"]).to_csv(REPO / "data/studies/logs/loss_limit_arm0_episodes.csv", index=False)
    print("\n".join(L))
    p = A[(A.cell == "k>=2") & (A.metric == "pnl")].iloc[0]
    print(f"\nPRIMARY k>=2 minus k=0 same session ($ P&L): {p['diff']:+.1f} t {p.t:+.2f} ({p.n} episodes, {p.sessions} sessions)")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
