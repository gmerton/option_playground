#!/usr/bin/env python3
"""
TIGHT-STOP SURVIVAL AT LUK-STYLE INTRADAY PULLBACK ENTRIES, WITH A MACRO GATE
Pre-registered 2026-09-30, before any scoring. QUEUED by Gabe 2026-09-30 until he had done further
disambiguation of the Luk trade log (data/martin_luk/trades/clarify_worklist.csv); where to run it is also his call
(see RUN). The S3b stance weeks are to be RE-COUNTED from the log after that pass and before any scoring.
Creator method -> DISCOVERY track (|t| >= 3).

WHY. The goal (Gabe, 2026-09-30) is triple-digit returns in the style of Luk / Tito / Qullamaggie / Ariel. Two results
from today frame this test:
  * picks test (luk_picks_vs_controls_2026-09-30.md): his long picks held 20 sessions from the close earn +6.5% vs
    +5.1% for our same-date breakouts, t 0.92. Selection at the close does not explain his return.
  * entry cards (luk_entry_cards_2026-09-30.md): where he states them, stops are 1.0-2.5% (median 1.6%), risk 0.3% of
    the account, positions 20-30%, the book about 200% long; 88% of stated triggers are 1- to 60-minute bars; 30 of 45
    same-stream outcomes are stop-outs.
So the candidate source is POSITION SIZE BOUGHT WITH A VERY TIGHT STOP at an intraday entry. That contradicts the house
rule (stops under ~0.5 ADR are widened; resting tight stops intraday lost: entry study 2026-09-17, DINO 2026-09-22) and
Stage A (11,227 intraday alerts ~ a random later minute). What is NEW here: (1) his entry LOCATION (a pullback into the
rising EMAs, not a breakout or an alert), (2) the stop judged as a survival / payoff question in PERCENT, (3) the
account arithmetic at fixed risk, and (4) Gabe's observation that he spends long stretches with no longs at all, so
the same entry is scored inside and outside a macro gate. The "intraday version" of the Luk/Ariel pullback entry is
listed as untested in TEST_INDEX sections 9 and 10.

DATA
  intraday  s3://gmerton-stock-data/backfill/intraday_1min/bars/<SYM>/ -- Polygon 1-min, 1,715 liquid names,
            2024-10-01 -> 2026-09-24 (complete: 37,245 objects, 11.3 GB). The local watchlist cache (148 names) is NOT
            used: its names were chosen with hindsight.
  daily     data/cache/liquid_panel_2019.parquet (same universe). QQQ 1-min: data/cache/intraday_hist/QQQ_1min.parquet.
  sample    entries 2024-10-01 -> 2026-08-26, so every trade has 20 sessions of follow-up (the daily panel starts in
            2019, so the EMAs and betas need no warm-up inside the sample).
  ⚠ the universe is today's liquid list (survivor-biased), which flatters every long arm's LEVEL. Differences between
    arms on the same entries are much less affected. One tape (2024-10 -> 2026-09).

THE ENTRY (mechanical reading of principles.md: "buy pullbacks into the rising EMAs ... skip if price is > ~3% above
the LOD"; "the intraday trigger is the previous-bar-high breakout after a fast flush"; "sit out the first 15-30
minutes"; "avoid gap-ups"; leading list = price > 50 EMA, 50 > 150)
  daily state, all known at the prior close (t-1):
    price >= $5, 20-day average dollar volume >= $100M, ADR(20) >= 4%
    close > EMA50, EMA50 > EMA150, EMA21 higher than 5 sessions earlier
  day t, 5-minute bars built from the 1-minute bars, regular session only:
    no gap-up chase   open_t <= close_(t-1) + 0.5 ADR$            (ADR$ = ADR% x close_(t-1))
    pullback zone     session low so far L satisfies  EMA21_(t-1) - 0.5 ADR$ <= L <= EMA9_(t-1) + 0.25 ADR$
    trigger           between 10:00 and 15:30 ET, price trades above the high of the previous completed 5-minute bar,
                      and that bar's high is below the high of the bar before it (a step down, then the turn)
    not extended      entry <= L x 1.03, and stop distance d = (entry - stop) / entry is between 0.4% and 3.0% (2.0% per the 2026-10-01 amendment)
    fill              max(trigger price, the open of the 1-minute bar that trades through it)
    one entry per name per day (the FIRST qualifying trigger). Re-entries after a stop-out (up to 2 more, same rules)
    are a secondary, descriptive arm: he re-enters, but the primary must not depend on it.
  STOP   L - $0.01, resting, regular session only. Entry day on 1-minute bars (a new low in the entry minute counts as
         stopped). Later days on daily bars: a gap below the stop fills at the open (as he does), else at the stop.
  EXIT   first daily close below that day's 9 EMA, on any day after the entry day; cap 20 sessions. No partial sales
         into strength and no trailing (both are discretionary in his telling; stated as a limitation).
  COSTS  10 bp per side.

ARMS (same entries throughout)
  TIGHT   the stop above.
  WIDE    stop = entry - 1.0 ADR$ (the house disaster width), same exit.
  RANDOM  same name-day, entry at a random LATER minute (after the trigger, before 15:30; 5 draws, seed 20260930) with
          the same percentage stop distance d. Later, not earlier: an earlier minute is hindsight (Stage A lesson).
  BETA    beta_i x QQQ return over the trade's exact window (entry minute to exit), beta_i = 120-session daily beta to
          QQQ at t-1. The exposure-matched control the ledger requires for anything long.

PRIMARY  TIGHT net % return per trade minus BETA, on entry-date cluster means; t.
         BAR: t >= 3, both halves (2024-10 -> 2025-09 / 2025-10 -> 2026-08) positive, a majority of quarters positive.
         Report the minimum detectable effect at 80% power first; below it the verdict is UNDERPOWERED, not NULL.
         This asks: per dollar deployed, does the tight-stopped entry beat holding its own market exposure? If it does
         not, a 200% book of these is leveraged beta, whatever the equity curve looks like.
SECONDARY (4 cells; 5 in all with the primary, Sidak 5% two-sided |t| >= 2.57; the discovery bar of 3 governs)
  S1  trigger: TIGHT minus RANDOM, % per trade (does the turn matter, or just the name-day?).
  S2  stop width at equal dollars: TIGHT minus WIDE, % per trade (what the tight stop costs or saves per dollar).
      Judged in PERCENT; R is reported but never used to rank the stops.
  S3a MACRO, mechanical: primary excess with QQQ close_(t-1) > its 21 EMA and 9 EMA > 21 EMA (ON) minus OFF.
  S3b MACRO, his actual stance: primary excess in his LONG weeks minus his SHORT/EMPTY weeks. Weeks are labelled from
      the direction and stream date of the entry / add / hold rows in his log (no prices, no outcomes; rows still open
      on the clarification worklist are used for direction and date only): LONG if long rows > short rows. Counted
      before any scoring: 37 stream weeks 2025-11-22 -> 2026-09-25, 22 LONG and 15 SHORT/EMPTY, with runs of 7 weeks
      (2026-01-24 -> 03-13) and 4 weeks (2026-08-22 -> 09-18) short. Weeks with no stream are excluded. ⚠ This label
      is his discretion in hindsight, not a rule we can trade; it asks whether standing aside is where the value is.
DESCRIPTIVE (no claim)
  survival: share stopped the same day, within 3 sessions, ever; distribution of R (share >= 5R, >= 10R); share of the
  total from the top 10% of trades; re-entry arm.
  ACCOUNT SIMULATION, labelled a simulation: risk 0.3% of equity per trade, position = min(0.3% / d, 30%), gross cap
  200%, signals taken in time order and skipped at the cap; total return and max drawdown 2024-10 -> 2026-09, for all
  days and for the mechanical gate ON only; the same book with the WIDE stop at the same risk. Ignores margin
  interest, partial sales and fast-market slippage. This is the "does the mechanical version reach triple digits"
  number; it is beta-laden and survivor-flattered, and it is not the test.

RUN  Not a small panel: 37,245 parquet chunks, 11.3 GB in S3 (0.8 s per chunk measured). Local, streamed per name with
     ~16 parallel readers and nothing persisted (32 GB of disk free), is an estimated 40-60 minutes; the alternative is
     an ECS task next to the data. Gabe decides (CLAUDE.md: decide local vs cloud before running).

⚙ AMENDED 2026-10-01, BEFORE ANY SCORING (Gabe: "Let's use ECS", after the worklist went 64 -> 6 open; look 2 of the
picks test, luk_picks_vs_controls_look2_2026-10-01.md, put his selection at the close level with ours, t -0.07):
  * RUN = ECS Fargate via services/study-runner/deploy_and_run.sh (Gabe's call). Processes = WORKERS env.
  * STOP-DISTANCE CAP 3.0% -> 2.0%. His stated rule (entry cards + principles.md): a setup that needs a stop wider than
    ~2% is skipped, not taken with a wider stop; stated stops are 1.0-2.5%, median 1.6%. Floor stays 0.4%.
  * S3b stance weeks RE-COUNTED from the log after the worklist pass, before scoring, as required above: unchanged at
    37 weeks, 22 LONG / 15 SHORT-EMPTY (data/martin_luk/trades/stance_weeks_2026-10-01.json; week = W-FRI of the
    stream date; entry/buy/short/reentry/add/hold rows; the 2026-01-31 retrospective interview excluded).
  * Implementation fixed now: ADR = 20-day mean of (high/low - 1), the house definition; ADDV = 20-day mean dollar
    volume; EMAs on daily closes (adjust=False). The daily panel is dividend-adjusted and the 1-min bars split-adjusted
    only, so day-t levels (EMA9/21, close, ADR$) are rescaled by f = 1-min close(t-1) / panel close(t-1); the exit test
    "close < EMA9" is scale-free and is read on the panel. Trigger price = previous 5-min high + $0.01. RANDOM fills
    at the open of the drawn minute. A name-day needs 1-min bars on t-1 and t. Later-day stops use 1-min bars (first
    minute through the stop; an opening gap below fills at the open).
  * BETA arm: QQQ 1-min cache ends 2026-09-17; QQQ prices after that use the panel's daily QQQ close (affects only
    exits 2026-09-18 -> 09-24). Beta = 120-session cov/var of daily close returns vs QQQ at t-1; the BETA return is not
    charged costs (it is the exposure benchmark; TIGHT is net).
  * Halves split at 2025-10-01; quarters are calendar quarters of the entry date. MDE = 2.8 x SE.
  * ACCOUNT SIMULATION marks positions at exit only (realised equity curve); drawdown is on that curve.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

BUCKET, PREFIX = "gmerton-stock-data", "backfill/intraday_1min/bars/"
PANEL = Path("data/cache/liquid_panel_2019.parquet")
QQQ1 = Path("data/cache/intraday_hist/QQQ_1min.parquet")
STANCE = Path("data/martin_luk/trades/stance_weeks_2026-10-01.json")
LOG = Path("data/studies/logs/luk_tight_stop_survival.log")
TRADES = Path("data/studies/logs/luk_tight_stop_survival_trades.csv")
START, END = pd.Timestamp("2024-10-02"), pd.Timestamp("2026-08-26")
SPLIT = pd.Timestamp("2025-10-01")
COST, SEED, NRAND = 0.002, 20260930, 5
DMIN, DMAX = 0.004, 0.020
T_FIRST, T_LAST = 600, 930          # 10:00 .. 15:30 ET, minutes since midnight


def daily_state(panel: pd.DataFrame) -> pd.DataFrame:
    """Per ticker-day, everything known at the prior close, shifted onto day t."""
    q = panel[panel.ticker == "QQQ"].set_index("date").close
    qr = q.pct_change()
    out = []
    for tk, g in panel.groupby("ticker", sort=False):
        g = g.sort_values("date").set_index("date")
        C = g.close
        e9, e21 = C.ewm(span=9, adjust=False).mean(), C.ewm(span=21, adjust=False).mean()
        e50, e150 = C.ewm(span=50, adjust=False).mean(), C.ewm(span=150, adjust=False).mean()
        adr = (g.high / g.low - 1).rolling(20).mean() * 100
        addv = g.dolvol.rolling(20).mean()
        r = C.pct_change()
        qa = qr.reindex(r.index)
        beta = r.rolling(120).cov(qa) / qa.rolling(120).var()
        ok = (C >= 5) & (addv >= 100e6) & (adr >= 4) & (C > e50) & (e50 > e150) & (e21 > e21.shift(5))
        st = pd.DataFrame({"pc": C, "e9": e9, "e21": e21, "adr": adr, "beta": beta, "ok": ok}).shift(1)
        st["c"], st["e9_today"] = C, e9                     # same-day values, used only for the exit test
        st["ticker"] = tk
        out.append(st.reset_index())
    return pd.concat(out, ignore_index=True)


def load_minutes(s3, tk: str) -> pd.DataFrame | None:
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{PREFIX}{tk}/").get("Contents", [])]
    if not keys:
        return None
    fr = [pd.read_parquet(io.BytesIO(s3.get_object(Bucket=BUCKET, Key=k)["Body"].read())) for k in keys]
    m = pd.concat(fr).sort_index()
    m = m[~m.index.duplicated()]
    m["d"] = m.index.normalize()
    m["mn"] = m.index.hour * 60 + m.index.minute
    return m[["d", "mn", "open", "high", "low", "close", "volume"]]


def first_trigger(o, h, l, mn, Lb, fh, b, lo_z, hi_z, start):
    """Index of the first qualifying trigger minute >= start, plus entry, stop, d; or None."""
    p1, p2 = b - 1, b - 2
    valid = (p2 >= 0) & (mn >= T_FIRST) & (mn <= T_LAST) & (np.arange(len(o)) >= start)
    if not valid.any():
        return None
    P1 = np.where(p1 >= 0, fh[np.clip(p1, 0, None)], np.nan)
    P2 = np.where(p2 >= 0, fh[np.clip(p2, 0, None)], np.nan)
    trig = P1 + 0.01
    entry = np.maximum(trig, o)
    stop = Lb - 0.01
    d = (entry - stop) / entry
    q = valid & (P1 < P2) & (h >= trig) & (Lb >= lo_z) & (Lb <= hi_z) & (entry <= Lb * 1.03) & (d >= DMIN) & (d <= DMAX)
    idx = np.flatnonzero(q)
    if not len(idx):
        return None
    i = idx[0]
    return i, float(entry[i]), float(stop[i]), float(d[i])


def run_trade(entry, stop, i0, day_bars, later, st_later, d0):
    """Walk a long from minute i0 of day 0. Returns (gross return, exit Timestamp, sessions held, stopped flag, same-day stop)."""
    o, l, mn = day_bars
    hit = np.flatnonzero(l[i0:] <= stop)
    if len(hit):
        j = i0 + hit[0]
        px = stop if j == i0 else min(stop, o[j])
        return px / entry - 1, d0 + pd.Timedelta(minutes=int(mn[j])), 0, True, True
    for k, (dk, bars) in enumerate(later, start=1):
        bo, bl, bc, bmn = bars
        if bo[0] <= stop:
            return bo[0] / entry - 1, dk + pd.Timedelta(minutes=int(bmn[0])), k, True, False
        hit = np.flatnonzero(bl <= stop)
        if len(hit):
            return stop / entry - 1, dk + pd.Timedelta(minutes=int(bmn[hit[0]])), k, True, False
        c_pan, e9 = st_later[k - 1]
        if c_pan < e9 or k == len(later):
            return bc[-1] / entry - 1, dk + pd.Timedelta(hours=16), k, False, False
    return None


def process(tk: str, st: pd.DataFrame, cal: list, features=None, extra=None) -> list[dict]:
    """features(extra, t, f, minutes_before_entry, L, adr_d) -> dict is an optional, additive hook (used by
    run_luk_avwap_confluence.py); it never changes the trade itself."""
    import boto3
    s3 = boto3.client("s3")
    m = load_minutes(s3, tk)
    if m is None:
        return []
    days = {d: g for d, g in m.groupby("d", sort=True)}
    stx = st.set_index("date")
    pos = {d: i for i, d in enumerate(cal)}
    rows = []
    for t in stx.index[(stx.index >= START) & (stx.index <= END) & stx.ok.fillna(False).astype(bool)]:
        i = pos.get(t)
        if i is None or i == 0 or t not in days or cal[i - 1] not in days:
            continue
        r = stx.loc[t]
        if not np.isfinite([r.pc, r.e9, r.e21, r.adr]).all():
            continue
        f = days[cal[i - 1]].close.iloc[-1] / r.pc
        pc, e9, e21 = r.pc * f, r.e9 * f, r.e21 * f
        adr_d = r.adr / 100 * pc
        g = days[t]
        o, h, l, mn = g.open.values, g.high.values, g.low.values, g.mn.values
        if o[0] > pc + 0.5 * adr_d:
            continue
        b = (mn - 570) // 5
        nb = int(b.max()) + 1
        fh = np.full(nb, np.nan)
        np.fmax.at(fh, b, h)
        Lb = np.concatenate([[np.inf], np.minimum.accumulate(l)[:-1]])
        lo_z, hi_z = e21 - 0.5 * adr_d, e9 + 0.25 * adr_d
        later, st_later = [], []
        for k in range(1, 21):
            if i + k >= len(cal):
                break
            dk = cal[i + k]
            if dk not in days:
                break
            gk = days[dk]
            later.append((dk, (gk.open.values, gk.low.values, gk.close.values, gk.mn.values)))
            sk = stx.loc[dk] if dk in stx.index else None
            st_later.append((sk.c, sk.e9_today) if sk is not None else (np.inf, -np.inf))
        if len(later) < 20:
            continue
        rng = np.random.default_rng(SEED + zlib.crc32(f"{tk}|{t.date()}".encode()))
        start, attempt = 0, 0
        while attempt < 3:
            hit = first_trigger(o, h, l, mn, Lb, fh, b, lo_z, hi_z, start)
            if hit is None:
                break
            i0, entry, stop, d = hit
            tight = run_trade(entry, stop, i0, (o, l, mn), later, st_later, t)
            if tight is None:
                break
            row = dict(ticker=tk, date=t, attempt=attempt, entry_time=t + pd.Timedelta(minutes=int(mn[i0])), entry=entry,
                       stop=stop, d=d, adr=r.adr, beta=r.beta, ret_tight=tight[0], exit_tight=tight[1], held=tight[2],
                       stopped=tight[3], stopped_same_day=tight[4])
            if attempt == 0 and features is not None:
                row.update(features(extra, t, f, g.iloc[:i0], stop + 0.01, adr_d))
            if attempt == 0:
                wide = run_trade(entry, entry - adr_d, i0, (o, l, mn), later, st_later, t)
                row.update(ret_wide=wide[0], exit_wide=wide[1], stop_wide_pct=adr_d / entry)
                cand = np.flatnonzero((np.arange(len(o)) > i0) & (mn <= T_LAST))
                if len(cand):
                    rr = []
                    for j in rng.choice(cand, size=min(NRAND, len(cand)), replace=False):
                        e = o[j]
                        x = run_trade(e, e * (1 - d), j, (o, l, mn), later, st_later, t)
                        if x is not None:
                            rr.append(x[0])
                    row["ret_random"] = float(np.mean(rr)) if rr else np.nan
            rows.append(row)
            if not tight[4]:
                break                                   # re-entries only after a same-day stop-out
            stop_min = (tight[1] - t).total_seconds() / 60
            start = int(np.searchsorted(mn, stop_min, side="right"))
            attempt += 1
    return rows


def tstat(x: pd.Series) -> tuple[float, float, float, int]:
    x = x.dropna()
    n = len(x)
    if n < 3:
        return np.nan, np.nan, np.nan, n
    se = x.std(ddof=1) / sqrt(n)
    return x.mean(), x.mean() / se, 2.8 * se, n


def welch(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    a, b = a.dropna(), b.dropna()
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    se = sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return a.mean() - b.mean(), (a.mean() - b.mean()) / se


def qqq_price(ts: pd.Timestamp, q1: pd.Series, qd: pd.Series) -> float:
    if ts <= q1.index[-1]:
        k = q1.index.searchsorted(ts, side="right") - 1
        return float(q1.iloc[max(k, 0)])
    return float(qd.loc[:ts.normalize()].iloc[-1])


def account(tr: pd.DataFrame, ret: str, ex: str, dcol: str) -> tuple[float, float, int]:
    eq, peak, mdd, opn, taken = 1.0, 1.0, 0.0, [], 0
    for _, r in tr.sort_values("entry_time").iterrows():
        still = []
        for (xt, size, e0, rt) in opn:
            if xt <= r.entry_time:
                eq += size * e0 * rt
                peak = max(peak, eq)
                mdd = min(mdd, eq / peak - 1)
            else:
                still.append((xt, size, e0, rt))
        opn = still
        size = min(0.003 / r[dcol], 0.30)
        if sum(p[1] for p in opn) + size > 2.0:
            continue
        opn.append((r[ex], size, eq, r[ret] - COST))
        taken += 1
    for (xt, size, e0, rt) in sorted(opn):
        eq += size * e0 * rt
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return eq - 1, mdd, taken


def main() -> None:
    t0 = time.time()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(PANEL, columns=["date", "ticker", "high", "low", "close", "dolvol"])
    panel = panel[panel.date >= "2019-01-01"]
    cal = sorted(panel[panel.ticker == "QQQ"].date.unique())
    cal = [pd.Timestamp(x) for x in cal]
    st = daily_state(panel)
    tks = sorted(set(st[st.ok.fillna(False).astype(bool) & (st.date >= START) & (st.date <= END)].ticker))
    if os.environ.get("TICKERS"):                       # smoke test only
        tks = [t for t in os.environ["TICKERS"].split(",") if t in tks]
    by_tk = {tk: g for tk, g in st[st.ticker.isin(tks)].groupby("ticker")}
    print(f"daily state built {time.time()-t0:.0f}s; {len(tks)} tickers ever eligible", flush=True)
    workers = int(os.environ.get("WORKERS", "8"))
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        fut = {ex.submit(process, tk, by_tk[tk], cal): tk for tk in tks}
        for n, fu in enumerate(as_completed(fut), 1):
            try:
                rows += fu.result()
            except Exception as e:                      # one bad name must not kill the run
                print(f"  {fut[fu]} failed: {e!r}", flush=True)
            if n % 100 == 0:
                print(f"  {n}/{len(tks)} names, {len(rows)} trades, {time.time()-t0:.0f}s", flush=True)
    tr = pd.DataFrame(rows)
    tr.to_csv(TRADES, index=False)
    report(tr, panel, time.time() - t0)


def report(tr: pd.DataFrame, panel: pd.DataFrame, secs: float) -> None:
    q1 = pd.read_parquet(QQQ1, columns=["ts", "open"]).set_index("ts").open
    q1 = q1[q1.index >= "2024-09-01"]
    qd = panel[panel.ticker == "QQQ"].set_index("date").close
    qe9, qe21 = qd.ewm(span=9, adjust=False).mean(), qd.ewm(span=21, adjust=False).mean()
    gate = ((qd > qe21) & (qe9 > qe21)).shift(1)
    stance = {pd.Timestamp(k): v for k, v in json.loads(STANCE.read_text()).items()}

    f = tr[tr.attempt == 0].copy()
    f["net_tight"], f["net_wide"], f["net_random"] = f.ret_tight - COST, f.ret_wide - COST, f.ret_random - COST
    f["q_ret"] = [qqq_price(x, q1, qd) / qqq_price(e, q1, qd) - 1 for e, x in zip(f.entry_time, f.exit_tight)]
    f["ret_beta"] = f.beta * f.q_ret
    f["x_primary"] = f.net_tight - f.ret_beta
    f["gate"] = f.date.map(gate)
    f["wk"] = f.date.dt.to_period("W-FRI").dt.end_time.dt.normalize()
    f["stance"] = f.wk.map(stance)
    by = lambda col, sub=None: (f if sub is None else f[sub]).groupby("date")[col].mean()

    L = [f"# Luk tight-stop survival (pre-registered 2026-09-30, amended 2026-10-01 before scoring); runtime {secs/60:.0f} min",
         f"entries {f.date.min().date()} -> {f.date.max().date()}: {len(f)} first entries on {f.date.nunique()} dates, "
         f"{f.ticker.nunique()} names; re-entries {int((tr.attempt > 0).sum())}",
         f"stop distance d: median {f.d.median()*100:.2f}% (IQR {f.d.quantile(.25)*100:.2f}-{f.d.quantile(.75)*100:.2f}); "
         f"d / ADR median {(f.d*100/f.adr).median():.2f}; WIDE stop median {f.stop_wide_pct.median()*100:.2f}%", ""]

    def cell(name, col, sub=None, pct=True):
        s = by(col, sub)
        m, t, mde, n = tstat(s)
        h1, h2 = s[s.index < SPLIT].mean(), s[s.index >= SPLIT].mean()
        qs = s.groupby(s.index.to_period("Q")).mean()
        L.append(f"  {name:<44} dates {n:4d} | mean {m*100:+.3f}pp | t {t:+.2f} | MDE {mde*100:.2f}pp | halves "
                 f"{h1*100:+.3f} / {h2*100:+.3f} | quarters + {int((qs > 0).sum())}/{len(qs)}")
        return t, h1, h2, (qs > 0).mean()

    L.append("## Raw per-trade (first entries, net of 10 bp/side)")
    for c in ["net_tight", "net_wide", "net_random", "ret_beta"]:
        L.append(f"  {c:<12} mean {f[c].mean()*100:+.3f}%  median {f[c].median()*100:+.3f}%  win {(f[c] > 0).mean()*100:.0f}%")
    L.append("\n## PRIMARY: TIGHT net minus BETA (beta x QQQ over the same window), entry-date cluster means")
    t, h1, h2, qpos = cell("TIGHT - BETA", "x_primary")
    passed = t >= 3 and h1 > 0 and h2 > 0 and qpos > 0.5
    L.append(f"  -> bar t >= 3, both halves > 0, majority of quarters > 0: {'PASS' if passed else 'NOT MET'}")
    L.append("\n## SECONDARY (Sidak |t| >= 2.57 over 5 cells; discovery bar 3 governs)")
    f["s1"], f["s2"] = f.net_tight - f.net_random, f.net_tight - f.net_wide
    cell("S1 TIGHT - RANDOM later minute (same d)", "s1")
    cell("S2 TIGHT - WIDE (1 ADR stop), % per trade", "s2")
    on, off = by("x_primary", f.gate == True), by("x_primary", f.gate == False)
    dm, dt = welch(on, off)
    L.append(f"  S3a gate ON - OFF (QQQ > 21 EMA & 9 > 21)          diff {dm*100:+.3f}pp, Welch t {dt:+.2f} (ON {len(on)} dates mean {on.mean()*100:+.3f}, OFF {len(off)} mean {off.mean()*100:+.3f})")
    lg, sh = by("x_primary", f.stance == "LONG"), by("x_primary", f.stance == "SHORT/EMPTY")
    dm, dt = welch(lg, sh)
    L.append(f"  S3b his LONG weeks - SHORT/EMPTY weeks           diff {dm*100:+.3f}pp, Welch t {dt:+.2f} (LONG {len(lg)} dates mean {lg.mean()*100:+.3f}, SHORT {len(sh)} mean {sh.mean()*100:+.3f})")

    L.append("\n## DESCRIPTIVE")
    R = f.ret_tight / f.d
    L.append(f"  stopped same day {f.stopped_same_day.mean()*100:.0f}% | within 3 sessions {((f.stopped) & (f.held <= 3)).mean()*100:.0f}% | "
             f"stopped ever {f.stopped.mean()*100:.0f}% | median hold {f.held.median():.0f} sessions")
    L.append(f"  R (gross / d): mean {R.mean():+.2f}, median {R.median():+.2f}, share >= 5R {(R >= 5).mean()*100:.1f}%, >= 10R {(R >= 10).mean()*100:.1f}%")
    srt = f.net_tight.sort_values(ascending=False)
    top = srt.iloc[: max(1, len(srt) // 10)].sum() / srt.sum() if srt.sum() != 0 else np.nan
    L.append(f"  top 10% of trades = {top*100:.0f}% of the summed net return (sum {srt.sum()*100:+.1f}% over {len(srt)} trades)")
    re = tr[tr.attempt > 0]
    if len(re):
        L.append(f"  re-entry arm: {len(re)} re-entries, net mean {(re.ret_tight - COST).mean()*100:+.3f}%, same-day stop {re.stopped_same_day.mean()*100:.0f}%")
    L.append("\n## ACCOUNT SIMULATION (a simulation, not the test: 0.3% risk, position min(0.3%/d, 30%), gross cap 200%, realised equity)")
    f["dw"] = f.stop_wide_pct
    for lab, sub in [("all days", f), ("gate ON only", f[f.gate == True])]:
        tot, mdd, k = account(sub, "ret_tight", "exit_tight", "d")
        L.append(f"  TIGHT {lab:<13} total {tot*100:+.1f}%  maxDD {mdd*100:.1f}%  trades taken {k}")
        tot, mdd, k = account(sub, "ret_wide", "exit_wide", "dw")
        L.append(f"  WIDE  {lab:<13} total {tot*100:+.1f}%  maxDD {mdd*100:.1f}%  trades taken {k}")
    LOG.write_text("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--report":     # re-render from the saved trades csv
        tr = pd.read_csv(TRADES, parse_dates=["date", "entry_time", "exit_tight", "exit_wide"])
        report(tr, pd.read_parquet(PANEL, columns=["date", "ticker", "close"]), 0)
    else:
        main()
