#!/usr/bin/env python3
"""
ANCHORED-VWAP CONFLUENCE AT LUK-STYLE TIGHT-STOP ENTRIES (pre-registered 2026-10-01, before any scoring; Gabe: "yes,
pre-register the AVWAP test"). Creator method -> DISCOVERY track.

WHY. The tight-stop survival test (luk_tight_stop_survival_2026-10-01.md) found his mechanical entry earns exactly its
exposure: TIGHT - BETA +0.003pp, t +0.02, 13,410 entries. Gabe: "Luk mentions anchored VWAP quite frequently." 27 of
his 113 entry cards cite it, and principles.md has him layering supports at the entry: "9/21/150 EMA, anchored VWAP
(anchored to base height, recent swing high, recent swing low, or big gap/volume bars -- an art ... what matters is
price reacting)". The one AVWAP the ledger tested (level_trigger_test_2026-09-21.md) was a single anchor (20-day low)
used as a break / hold TRIGGER, NULL. Untested: AVWAP as CONFLUENCE at his pullback low, across the anchors he names.

QUESTION. Among the same entries, do the ones whose pullback low sits AT an anchored VWAP beat their market exposure?

SAMPLE. Exactly the tight-stop test's first entries: same engine (run_luk_tight_stop_survival.process, imported, with
an additive feature hook that cannot change any trade), same universe, dates, trigger, stop, exit, costs and BETA
arm. ⚠ That population has been scored in AGGREGATE (null). The confluence subsets have not been looked at; this is a
subgroup test of a null population, so the prior is low and the bar is the discovery bar.

ANCHORS (all chosen from daily bars known at t-1; the window is the 60 sessions t-60 .. t-1 unless stated)
  A1 SWING HIGH   the day of the highest high in the window
  A2 SWING LOW    the day of the lowest low in the last 20 sessions (t-20 .. t-1)
  A3 GAP DAY      the most recent day whose open >= prior close + 1.0 ADR$ (prior day's ADR); none -> no A3
  A4 VOLUME DAY   the day of the highest volume in the window
AVWAP at the entry = (sum over anchor day .. t-1 of typical price x volume, rescaled to the 1-min price scale by the
engine's f, + the day-t 1-minute running sum of typical price x volume up to the minute before entry) / (the same
volume sums). Typical price = (high + low + close) / 3 (daily and 1-minute).
CONFLUENCE with anchor A: |L - AVWAP_A| <= 0.25 ADR$, where L = the session low at entry (the stop + $0.01) and ADR$ is
the engine's. (A quarter of a day's range: "price reacting" at the level, not a cross of it.)

PRIMARY  ANY: entries confluent with at least one of A1-A4. Statistic = TIGHT net - BETA on the ANY subset,
         entry-date cluster means, t. BAR: t >= 3, both halves (split 2025-10-01) positive, a majority of calendar
         quarters positive. MDE at 80% power reported first; below it the verdict is UNDERPOWERED, not NULL.
SECONDARY (4; 5 cells in all, Sidak 5% two-sided |t| >= 2.57; the discovery bar of 3 governs any adoption)
         A1, A2, A3, A4 subsets, same statistic.
REPORTED, NOT CELLS: ANY minus NOT-ANY (Welch t on date means); share of entries in each subset; TIGHT - BETA by the
         number of confluent anchors (0 / 1 / 2+); the same subsets on the WIDE arm.
RUN  ECS Fargate via services/study-runner (same as the tight-stop test; ~2 min). Local is too slow (11 GB of 1-min bars).
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

import run_luk_tight_stop_survival as base

LOG = Path("data/studies/logs/luk_avwap_confluence.log")
TRADES = Path("data/studies/logs/luk_avwap_confluence_trades.csv")
ANCH = ["A1", "A2", "A3", "A4"]
BAND = 0.25


def avwap_features(daily: pd.DataFrame, t, f, pre: pd.DataFrame, L: float, adr_d: float) -> dict:
    """daily: this ticker's panel rows indexed by date (open, high, low, close, volume, adr). Known at t-1 only."""
    i = daily.index.searchsorted(t)
    if i < 61:
        return {}
    w60, w20 = daily.iloc[i - 60:i], daily.iloc[i - 20:i]
    anchors = {"A1": w60.high.values.argmax() + i - 60, "A2": w20.low.values.argmin() + i - 20,
               "A4": w60.volume.values.argmax() + i - 60}
    prev_c, prev_adr = daily.close.shift(1).values, daily.adr.shift(1).values
    gaps = [k for k in range(i - 60, i) if daily.open.values[k] >= prev_c[k] + prev_adr[k] / 100 * prev_c[k]]
    if gaps:
        anchors["A3"] = gaps[-1]
    tp = ((daily.high + daily.low + daily.close) / 3).values * f
    vol = daily.volume.values
    if len(pre):
        ipv = float((((pre.high + pre.low + pre.close) / 3) * pre.volume).sum())
        iv = float(pre.volume.sum())
    else:
        ipv = iv = 0.0
    out = {}
    for a, k in anchors.items():
        v = vol[k:i].sum() + iv
        if v <= 0:
            continue
        av = ((tp[k:i] * vol[k:i]).sum() + ipv) / v
        out[f"dist_{a}"] = (L - av) / adr_d                      # in ADR units, signed
        out[f"conf_{a}"] = bool(abs(L - av) <= BAND * adr_d)
    return out


def work(tk, st, cal, daily):
    return base.process(tk, st, cal, features=avwap_features, extra=daily)


def main() -> None:
    t0 = time.time()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(base.PANEL, columns=["date", "ticker", "open", "high", "low", "close", "volume", "dolvol"])
    panel = panel[panel.date >= "2019-01-01"]
    cal = [pd.Timestamp(x) for x in sorted(panel[panel.ticker == "QQQ"].date.unique())]
    st = base.daily_state(panel)
    tks = sorted(set(st[st.ok.fillna(False).astype(bool) & (st.date >= base.START) & (st.date <= base.END)].ticker))
    if os.environ.get("TICKERS"):
        tks = [t for t in os.environ["TICKERS"].split(",") if t in tks]
    by_tk = {tk: g for tk, g in st[st.ticker.isin(tks)].groupby("ticker")}
    daily = {}
    for tk, g in panel[panel.ticker.isin(tks)].groupby("ticker"):
        g = g.sort_values("date").set_index("date")
        g["adr"] = (g.high / g.low - 1).rolling(20).mean() * 100
        daily[tk] = g[["open", "high", "low", "close", "volume", "adr"]]
    print(f"state built {time.time()-t0:.0f}s; {len(tks)} tickers", flush=True)
    rows = []
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "8"))) as ex:
        fut = {ex.submit(work, tk, by_tk[tk], cal, daily[tk]): tk for tk in tks}
        for n, fu in enumerate(as_completed(fut), 1):
            try:
                rows += fu.result()
            except Exception as e:
                print(f"  {fut[fu]} failed: {e!r}", flush=True)
            if n % 100 == 0:
                print(f"  {n}/{len(tks)} names, {len(rows)} trades, {time.time()-t0:.0f}s", flush=True)
    tr = pd.DataFrame(rows)
    tr.to_csv(TRADES, index=False)
    report(tr, panel, time.time() - t0)


def report(tr: pd.DataFrame, panel: pd.DataFrame, secs: float) -> None:
    q1 = pd.read_parquet(base.QQQ1, columns=["ts", "open"]).set_index("ts").open
    q1 = q1[q1.index >= "2024-09-01"]
    qd = panel[panel.ticker == "QQQ"].set_index("date").close
    f = tr[tr.attempt == 0].copy()
    f["q_ret"] = [base.qqq_price(x, q1, qd) / base.qqq_price(e, q1, qd) - 1 for e, x in zip(f.entry_time, f.exit_tight)]
    f["x"] = (f.ret_tight - base.COST) - f.beta * f.q_ret
    f["xw"] = (f.ret_wide - base.COST) - f.beta * f.q_ret       # descriptive only
    for a in ANCH:
        f[f"conf_{a}"] = f.get(f"conf_{a}", pd.Series(False, index=f.index)).fillna(False).astype(bool)
    f["n_conf"] = f[[f"conf_{a}" for a in ANCH]].sum(axis=1)
    f["ANY"] = f.n_conf > 0
    L = [f"# AVWAP confluence at Luk-style tight-stop entries (pre-registered 2026-10-01); runtime {secs/60:.0f} min",
         f"first entries {len(f)} on {f.date.nunique()} dates (tight-stop test: 13,410 / 473); band +/-{BAND} ADR",
         "share confluent: " + ", ".join(f"{a} {f[a if a == 'ANY' else f'conf_{a}'].mean()*100:.0f}%" for a in ["ANY"] + ANCH),
         "", "## cells: TIGHT net - BETA on the subset, entry-date cluster means (bar t >= 3 primary; Sidak |t| >= 2.57)"]

    def cell(name, mask, col="x"):
        s = f[mask].groupby("date")[col].mean()
        m, t, mde, n = base.tstat(s)
        h1, h2 = s[s.index < base.SPLIT].mean(), s[s.index >= base.SPLIT].mean()
        qs = s.groupby(s.index.to_period("Q")).mean()
        L.append(f"  {name:<22} trades {int(mask.sum()):5d} dates {n:4d} | mean {m*100:+.3f}pp | t {t:+.2f} | MDE {mde*100:.2f}pp"
                 f" | halves {h1*100:+.3f} / {h2*100:+.3f} | quarters + {int((qs > 0).sum())}/{len(qs)}")
        return t, h1, h2, (qs > 0).mean()

    t, h1, h2, qp = cell("PRIMARY ANY", f.ANY)
    L.append(f"  -> PRIMARY bar: {'PASS' if (t >= 3 and h1 > 0 and h2 > 0 and qp > 0.5) else 'NOT MET'}")
    for a in ANCH:
        cell(f"S {a}", f[f"conf_{a}"])
    L.append("\n## reported, not cells")
    cell("NOT-ANY", ~f.ANY)
    on, off = f[f.ANY].groupby("date").x.mean(), f[~f.ANY].groupby("date").x.mean()
    dm, dt = base.welch(on, off)
    L.append(f"  ANY - NOT-ANY: {dm*100:+.3f}pp, Welch t {dt:+.2f}")
    for k, msk in [("0 anchors", f.n_conf == 0), ("1 anchor", f.n_conf == 1), ("2+ anchors", f.n_conf >= 2)]:
        cell(k, msk)
    cell("WIDE arm, ANY", f.ANY, "xw")
    LOG.write_text("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
