#!/usr/bin/env python3
"""
[BB-2] CAN SLIM "C" (quarterly EPS growth) as a universe filter on the production INT universe
(pre-registered 2026-09-30, BEFORE running; spec from data/traderlion/videos/interviews/2026-09-23_afkUTFNVpso/notes.md
"Not tested, could be" #1, queued by Gabe 2026-09-23 from the Haber CAN SLIM review).

Question: do INT names whose last three reported quarters each grew EPS >= 25% YoY out-earn same-date INT names over
the next 20 sessions, once the volatility mix is held fixed? The ledger has only ever varied price/volume criteria
and the earnings SURPRISE (PEAD NULL); growth LEVEL is untouched.

Panel: data/cache/liquid_panel_2009.parquet, 2010-01 -> 2026-09 (via run_precision_tier_control.build, same elig).
EPS: data/cache/earnings_yf.parquet eps_act (yfinance, consensus-basis/adjusted). Per ticker, reports sorted by date;
  g_q = eps_act_q / eps_act_{q-4} - 1, defined only if eps_act_{q-4} > 0 AND the q-4 report is 300-430 days earlier
  (guards against missing quarters). Known at the CLOSE of the reaction session (BMO/midday -> report session,
  AMC -> next session); state held until the next report, expired 100 sessions after the last one.
  C_state = g_q, g_{q-1}, g_{q-2} all >= 0.25. Membership then shifted ONE session (as of the prior close), like
  every universe mask in the repo.
INT = run_universe_test.build_masks INT (TT c1-c9 at ADDV >= $200M, intersected with the AH momentum scan).

PRIMARY CELL (named in advance): INT & C vs INT, 20d, ADR-matched, paired per non-overlapping 20-session date:
    delta = (mean fr[INT&C] - ADRbench[INT&C]) - (mean fr[INT] - ADRbench[INT])
  ADRbench = the eligible panel reweighted to the arm's own ADR-decile mix that date (TT-ablation method).
  Dates need >= 3 INT&C members and >= 5 INT members; the date count is reported.
Secondaries (Sidak over the 5 secondaries -> |t| >= 2.57):
  (a) C alone vs the eligible panel, ADR-matched (universe-test Q1 frame)
  (b) INT & C & ACCEL (g_q > g_{q-1} > g_{q-2}) vs INT
  (c) INT & TRIPLE (g_q >= 1.00) vs INT
  (d) the primary at 63d (non-overlapping 63-session dates)
  (e) the primary with member-days within 10 sessions after any report removed from BOTH arms (separates growth
      from the PEAD window)
Bar: primary |t| >= 3 AND both halves (split 2018-01-01, the panel midpoint) same sign, per-year sign table.
Reported in pp of forward excess, not R.
Caveats (pre-declared): survivorship (today's liquid names -> compare arms, not levels); eps_act is adjusted, not
  GAAP; EPS coverage ~1,300 of 1,728 names (names without EPS can never be C members: INT is NOT restricted to covered
  names in the primary, and (a) is reported both ways); RS percentile is ranked inside the panel.
Prior: low-moderate. Every single TT criterion was <= 0.26pp and unresolvable; growth may already be in price (RS).
Control named: date and ADR mix held fixed, the NAME varies -> this is a selection test, not a timing test.

Run: PYTHONPATH=src .venv/bin/python3 run_canslim_c_filter.py   (log -> data/studies/logs/canslim_c_filter.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

import run_precision_tier_control as pc
import run_universe_test as ut
from run_trend_template_ablation import per_date_returns

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/canslim_c_filter.log"
START, SPLIT = "2010-01-01", "2018-01-01"
PANEL = "data/cache/liquid_panel_2009.parquet"
EXPIRE = 100


def eps_states(C: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Point-in-time EPS-growth state frames (as of each close, before the one-session shift)."""
    e = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet").dropna(subset=["eps_act"])
    e = e[e.ticker.isin(C.columns)].copy()
    e["session"] = pd.to_datetime(e.session)
    e = e.sort_values(["ticker", "session"])
    idx = C.index
    frames = {k: pd.DataFrame(np.nan, index=idx, columns=C.columns) for k in ("g0", "g1", "g2")}
    report = pd.DataFrame(False, index=idx, columns=C.columns)
    for t, g in e.groupby("ticker"):
        eps, ses = g.eps_act.values, g.session.values
        gr = np.full(len(g), np.nan)
        for q in range(4, len(g)):
            gap = (ses[q] - ses[q - 4]) / np.timedelta64(1, "D")
            if eps[q - 4] > 0 and 300 <= gap <= 430:
                gr[q] = eps[q] / eps[q - 4] - 1
        # reaction session: AMC -> next trading session
        pos = idx.searchsorted(ses)
        amc = g.timing.values == "AMC"
        pos = pos + amc * (idx[np.minimum(pos, len(idx) - 1)] == ses)   # only step if the report day is a session
        for q in range(len(g)):
            p = pos[q]
            if p >= len(idx) or ses[q] < idx[0] - np.timedelta64(400, "D"):
                continue
            end = min(p + EXPIRE, len(idx))
            if q + 1 < len(g):
                end = min(end, pos[q + 1]) if pos[q + 1] > p else end
            if p < len(idx):
                report.iat[p, report.columns.get_loc(t)] = True
            vals = (gr[q], gr[q - 1] if q >= 1 else np.nan, gr[q - 2] if q >= 2 else np.nan)
            j = C.columns.get_loc(t)
            for k, v in zip(("g0", "g1", "g2"), vals):
                frames[k].iloc[p:end, j] = v
    g0, g1, g2 = frames["g0"], frames["g1"], frames["g2"]
    c = (g0 >= 0.25) & (g1 >= 0.25) & (g2 >= 0.25)
    covered = pd.DataFrame(np.broadcast_to(C.columns.isin(e.ticker.unique()), C.shape), index=idx, columns=C.columns)
    post = report.rolling(10, min_periods=1).max().astype(bool)          # report reaction session + next 9
    return dict(C=c, ACCEL=c & (g0 > g1) & (g1 > g2), TRIPLE=g0 >= 1.0, covered=covered, post=post)


def shift(m: pd.DataFrame) -> pd.DataFrame:
    m = m.shift(1).fillna(False).astype(bool)
    m[m.index < START] = False
    return m


def tt_(x: pd.Series) -> float:
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan


def paired(P, arm, ref, h, adr, base, min_arm=3, min_ref=5):
    C = P.close
    fr = C.shift(-h) / C - 1
    dates = C.index[C.index >= START][::h]
    dates = dates[dates <= C.index[-1 - h]]
    a_raw, a_b, a_n = per_date_returns(P, arm, fr, dates, adr, base)
    if ref is None:                                            # vs the eligible panel, ADR-matched
        d = (a_raw - a_b)[a_n >= min_arm].dropna()
        r_n = pd.Series(np.nan, index=dates)
    else:
        r_raw, r_b, r_n = per_date_returns(P, ref, fr, dates, adr, base)
        ok = (a_n >= min_arm) & (r_n >= min_ref)
        d = ((a_raw - a_b) - (r_raw - r_b))[ok].dropna()
    h1, h2 = d[d.index < SPLIT], d[d.index >= SPLIT]
    return d, dict(dates=len(d), of=len(dates), arm_n=float(a_n.median()), ref_n=float(r_n.median()),
                   d_pp=d.mean() * 100, t=tt_(d), h1=h1.mean() * 100, h2=h2.mean() * 100,
                   agree=bool(np.sign(h1.mean()) == np.sign(h2.mean())))


def main():
    P, _b, _p = pc.build(PANEL)
    raw = pd.read_parquet(REPO / PANEL)
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    M = ut.build_masks(P, raw, start=START)
    INT, adr = M["INT"], M["_adr"]
    base = P.elig.shift(1).fillna(False).astype(bool)
    base[base.index < START] = False
    S = eps_states(P.close)
    c, accel, triple = shift(S["C"]), shift(S["ACCEL"]), shift(S["TRIPLE"])
    covered, post = shift(S["covered"]), shift(S["post"])
    elig_c = base & c

    L = ["# [BB-2] CAN SLIM C as a universe filter (pre-registration in the docstring)",
         f"panel {P.close.shape}, window {START} -> {P.close.index.max().date()}",
         f"median names/day: eligible {int(base.sum(1)[base.index >= START].median())}, covered "
         f"{int((base & covered).sum(1)[base.index >= START].median())}, C {int(elig_c.sum(1)[base.index >= START].median())}, "
         f"INT {int(INT.sum(1)[INT.index >= START].median())}, INT&C {int((INT & c).sum(1)[INT.index >= START].median())}"]
    cells = [
        ("PRIMARY  INT&C vs INT, 20d", INT & c, INT, 20),
        ("(a) C vs eligible panel, 20d", elig_c, None, 20),
        ("(a') C vs EPS-covered panel, 20d  [info]", elig_c, base & covered, 20),
        ("(b) INT&C&ACCEL vs INT, 20d", INT & accel, INT, 20),
        ("(c) INT&TRIPLE vs INT, 20d", INT & triple, INT, 20),
        ("(d) INT&C vs INT, 63d", INT & c, INT, 63),
        ("(e) INT&C vs INT, 20d, ex 10 sessions post-report", INT & c & ~post, INT & ~post, 20),
    ]
    rows, series = [], {}
    for name, a, r, h in cells:
        d, res = paired(P, a, r, h, adr, base)
        rows.append(dict(cell=name, **res))
        series[name] = d
    R = pd.DataFrame(rows)
    L.append("\ndelta = ADR-matched forward excess, arm minus reference, paired per non-overlapping date (pp)")
    L.append(R.round(3).to_string(index=False))
    for name in ("PRIMARY  INT&C vs INT, 20d", "(a) C vs eligible panel, 20d"):
        d = series[name]
        Y = pd.DataFrame(dict(mean_pp=d.groupby(d.index.year).mean() * 100, dates=d.groupby(d.index.year).size()))
        L.append(f"\nper year — {name}:\n" + Y.round(2).T.to_string())
    R.to_csv(REPO / "data/studies/logs/canslim_c_filter_cells.csv", index=False)
    print("\n".join(L))
    p = R.iloc[0]
    print(f"\nPRIMARY INT&C - INT (20d, ADR-matched): {p.d_pp:+.3f}pp t {p.t:+.2f} halves {p.h1:+.2f}/{p.h2:+.2f} "
          f"dates {p.dates}/{p['of']}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
