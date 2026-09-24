"""
One harness for testing an entry pattern, so a new idea costs ~20 lines instead of a 200-line script.

A pattern is a function that returns signals. The harness owns everything else: fills with slippage, the
exit arms, the same-name random control, the split sample, day-clustered t-stats, and the ledger row.

    from lib.studies.pattern_test import daily_signals, run_daily, run_intraday, Signal

    def my_pattern(P):                      # P = DailyPanel (close/high/low/open/adr/elig, all DataFrames)
        hit = (P.close > P.high.shift(1)) & (P.adr >= 3)
        return daily_signals(hit, stop=P.low, side="long")

    run_daily("my pattern", my_pattern, note="the idea in one line")

Why the control matters: a pattern that does not beat a random entry is finding days, not moments -- see
data/studies/pattern_ledger.md.

⚠ 2026-09-19: the original control (control="month": random session in the same calendar month, same name)
has LOOK-AHEAD -- it draws sessions from before the signal in a name known to be about to fire, which
inflated it ~3x on the house breakout. Use control="post" (random later session, timing) and control="xname"
(random other name, same date, selection). Every pre-re-run row was re-scored against both on 2026-09-19
(data/studies/ledger_rerun/ledger_rerun_2026-09-19.md): the default is now "post"; run "xname" alongside.
Also: R_CLIP = 10 removes a quarter of a breakout book's gross; report a cap-20 / stop-floor variant for
right-tail strategies (see breitstein_tests/precision_tier_control_2026-09-19.md).

Bar to pass (daily, from 2026-09-23 [WL-2]): PAIRED edge t >= 3 on the best arm (each signal minus its own controls,
date-clustered), both halves' paired edge > 0, and p_search < 0.003 from a label-permutation null that charges the
best-of-arms pick. run_grid() prices a whole pre-registered grid as one test (p_opt) and reports plateau vs spike.
Intraday runs still use the legacy unpaired rule (|t| on raw R + point edge > 0).
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


def _daily_arms(P: DailyPanel, j: int, i: int, stop: float, side: str, hold: int,
                entry_at: str = "next_open") -> dict | None:
    """Enter at the next session's open (default) or at the signal bar's close; R = move in favour / risk.
    Long and short share one code path."""
    O, C, H, L, E = P.open.values, P.close.values, P.high.values, P.low.values, P.ema20.values
    if i + 1 >= len(C):
        return None
    sgn = 1.0 if side == "long" else -1.0
    entry = (C[i, j] if entry_at == "close" else O[i + 1, j]) * (1 + sgn * SLIP)
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


# ---------------------------------------------------------------------------------------------------------------
# 2026-09-23 upgrade ([WL-2], design: data/neurotrader/videos/2025-03-03_NLBXgSmRBgU/notes.md)
#   A  PAIRED EDGE t. Each signal is paired with the mean of ITS OWN controls; t is on per-date means of
#      (R_signal - R_ctrl). "Beats the control" is now a significance statement, not `edge > 0`.
#   B  LABEL-PERMUTATION NULL for the best-of-arms pick. Each signal's matched STRATUM (the signal plus its candidate
#      controls: same name next 20 sessions for "post", same date other names for "xname") has the "signal" label
#      re-assigned at random; the max-over-arms edge t is recomputed; p_search = share of permutations >= observed.
#      Exact conditional null: name, date, vol regime and cross-section are held fixed by construction.
#   D  run_grid(): the whole pre-registered grid is re-run under each permutation (shared keys, so correlated cells
#      stay correlated) -> p_opt, the optimisation-aware p; plus a plateau metric (spike vs plateau).
# Pass (daily): paired edge t >= 3 on the best arm, both halves' paired edge > 0, p_search < 0.003.
# Halves are a CONSISTENCY check, not out-of-sample (true OOS = the forward lockbox from 2026-09-22).
# ---------------------------------------------------------------------------------------------------------------
PERMS = 2000
P_BAR = 0.003
_M64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 finaliser -> uniform [0,1). Deterministic keys shared across grid cells."""
    with np.errstate(over="ignore"):
        z = x.astype(np.uint64) + np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return (z >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def _build_strata(P: DailyPanel, S: pd.DataFrame, hold: int, entry_at: str, control: str, size: int,
                  plant: float = 0.0) -> dict | None:
    """For every signal: arms of the signal (member 0) and of up to `size` candidate controls (members 1..).
    Returns R[s, m, arm] (NaN = no member), member coordinates (session k, name j) for the permutation keys,
    stratum dates, and the legacy T/K tables."""
    idx = P.close.index
    px = P.close.values if entry_at == "close" else P.open.values
    off = 0 if entry_at == "close" else 1
    keys = {(int(r.j), int(r.i)) for r in S.itertuples()}
    A = len(DAILY_ARMS)
    Rs, Ks, Js, dates, recs = [], [], [], [], []
    for r in S.itertuples(index=False):
        i0, j0 = int(r.i), int(r.j)
        o = _daily_arms(P, j0, i0, float(r.stop), r.side, hold, entry_at)
        if not o:
            continue
        stop_pct = float(r.stop) / px[i0 + off, j0] - 1
        mem = [(i0, j0, o)]
        if control == "xname":
            ok = np.flatnonzero(P.elig.values[i0] & np.isfinite(px[i0 + off]))
            cand = [jj for jj in ok if jj != j0 and (int(jj), i0) not in keys]
            if cand:
                rng = np.random.default_rng((i0 * 1_000_003 + j0) % (2 ** 32))
                for jj in rng.choice(cand, size=min(size, len(cand)), replace=False):
                    co = _daily_arms(P, int(jj), i0, px[i0 + off, int(jj)] * (1 + stop_pct), r.side, hold, entry_at)
                    if co:
                        mem.append((i0, int(jj), co))
        else:
            if control == "post":
                window = range(i0 + 1, min(i0 + 21, len(idx)))
            else:
                d = pd.Timestamp(r.date)
                window = np.flatnonzero((idx.year == d.year) & (idx.month == d.month))
            for k in window:
                k = int(k)
                if (j0, k) in keys or k + hold + 2 >= len(idx) or not P.elig.values[k, j0] \
                        or not np.isfinite(px[k + off, j0]):
                    continue
                co = _daily_arms(P, j0, k, px[k + off, j0] * (1 + stop_pct), r.side, hold, entry_at)
                if co:
                    mem.append((k, j0, co))
                if len(mem) > size:
                    break
        if len(mem) < 2:
            continue
        R = np.full((size + 1, A), np.nan)
        kk = np.full(size + 1, -1, dtype=np.int64)
        jj_ = np.full(size + 1, -1, dtype=np.int64)
        for m, (k, j, arms) in enumerate(mem[:size + 1]):
            R[m] = [arms[a] for a in DAILY_ARMS]
            kk[m], jj_[m] = k, j
        R[0] += plant                                              # test hook: plant an effect in the real signal
        Rs.append(R); Ks.append(kk); Js.append(jj_)
        dates.append(str(idx[i0].date()))
        recs.append({**{a: R[0, n] for n, a in enumerate(DAILY_ARMS)}, "sym": r.sym, "date": str(idx[i0].date()),
                     "side": r.side})
    if not Rs:
        return None
    return dict(R=np.stack(Rs), k=np.stack(Ks), j=np.stack(Js), dates=np.array(dates), T=pd.DataFrame(recs))


def _date_t(diff: np.ndarray, codes: np.ndarray, nd: int) -> float:
    ok = np.isfinite(diff)
    if ok.sum() < 20:
        return np.nan
    c = np.bincount(codes[ok], minlength=nd)
    s = np.bincount(codes[ok], weights=diff[ok], minlength=nd)
    m = s[c > 0] / c[c > 0]
    return float(m.mean() / m.std(ddof=1) * np.sqrt(len(m))) if len(m) > 2 and m.std(ddof=1) > 0 else np.nan


def _pick(st: dict, u: np.ndarray, controls: int) -> tuple[np.ndarray, np.ndarray]:
    """Given keys u[s, m] (inf = no member), the lowest key is the signal and the next `controls` are its controls.
    Returns (signal R [s, arm], control-mean R [s, arm])."""
    order = np.argsort(u, axis=1)
    R = st["R"]
    s_ix = np.arange(len(R))
    sig = R[s_ix, order[:, 0]]
    cix = order[:, 1:1 + controls]
    cval = R[s_ix[:, None], cix]                                    # [s, c, arm]
    valid = np.isfinite(np.take_along_axis(u, cix, axis=1))[:, :, None]
    cval = np.where(valid, cval, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return sig, np.nanmean(cval, axis=1)


def _obs_keys(st: dict) -> np.ndarray:
    """Observed labelling: member 0 is the signal; controls = a fixed random draw among the others."""
    valid = st["k"] >= 0
    u = np.where(valid, _mix64(st["k"] * 7919 + st["j"] * 104_729 + 1) + 1.0, np.inf)
    u[:, 0] = -1.0
    return u


def _perm_keys(st: dict, p: int) -> np.ndarray:
    valid = st["k"] >= 0
    return np.where(valid, _mix64((st["k"] * 2_654_435_761 + st["j"]) * 1_000_003 + (p + 1) * 0x5851F42D), np.inf)


def _paired(st: dict, u: np.ndarray, controls: int, codes: np.ndarray, nd: int) -> np.ndarray:
    sig, ctl = _pick(st, u, controls)
    return np.array([_date_t(sig[:, a] - ctl[:, a], codes, nd) for a in range(sig.shape[1])])


def _stratum_stats(st: dict, controls: int, split: str, perms: int) -> dict:
    """Observed paired edge (per arm), its t and halves, and the permutation null of the max-over-arms t."""
    codes_s = pd.Series(st["dates"])
    codes, uniq = pd.factorize(codes_s)
    nd = len(uniq)
    u0 = _obs_keys(st)
    sig, ctl = _pick(st, u0, controls)
    diff = sig - ctl
    first = codes_s.values < split
    out = {}
    for a, arm in enumerate(DAILY_ARMS):
        d = diff[:, a]
        out[arm] = dict(pctrl=np.nanmean(ctl[:, a]), pedge=np.nanmean(d), edge_t=_date_t(d, codes, nd),
                        eh1=np.nanmean(d[first]) if first.any() else np.nan,
                        eh2=np.nanmean(d[~first]) if (~first).any() else np.nan)
    for a, arm in enumerate(DAILY_ARMS):
        out[arm]["diff"] = diff[:, a]
    obs = max((v["edge_t"] for v in out.values() if np.isfinite(v["edge_t"])), default=np.nan)
    null = np.array([np.nanmax(_paired(st, _perm_keys(st, p), controls, codes, nd)) for p in range(perms)])
    p_search = (np.sum(null >= obs) + 1) / (perms + 1) if (perms and np.isfinite(obs)) else np.nan
    return dict(arms=out, obs_max_t=obs, p_search=p_search, null=null, codes=codes, nd=nd, dates=codes_s.values)


def _report(name: str, T: pd.DataFrame, K: pd.DataFrame, arms: list[str], split: str,
            note: str, timeframe: str, ledger: bool = True, paired: dict | None = None) -> pd.DataFrame:
    """paired=None keeps the pre-2026-09-23 behaviour (raw-R t + point `edge > 0`), still used by intraday runs and
    by run_level_trigger_test.py. With `paired` (from _stratum_stats) the pass rule is the paired one."""
    tab = pd.DataFrame({a: _stats(T, a) for a in arms}).T
    tab["ctrl"] = [K[a].dropna().mean() if len(K) and a in K else np.nan for a in arms]
    tab["edge"] = tab.meanR - tab.ctrl
    if paired:
        tab["p_edge"] = [paired["arms"][a]["pedge"] for a in arms]
        tab["edge_t"] = [paired["arms"][a]["edge_t"] for a in arms]
    print(f"\n=== {name} ({timeframe}) — {len(T):,} signals, {T.sym.nunique()} names, "
          f"{pd.to_datetime(T.date).min().date()} -> {pd.to_datetime(T.date).max().date()} ===")
    print(tab.round(3).to_string())
    h1, h2 = T[T.date < split], T[T.date >= split]
    halves = pd.DataFrame({f"<{split}": {a: h1[a].mean() for a in arms},
                           f">={split}": {a: h2[a].mean() for a in arms}}).round(3)
    print(f"\nby half (n {len(h1)} / {len(h2)}):")
    print(halves.to_string())
    if paired:
        best = tab.edge_t.idxmax() if tab.edge_t.notna().any() else tab.meanR.idxmax()
        pa = paired["arms"][best]
        n_perm = len(paired["null"])
        if n_perm and 1 / (n_perm + 1) >= P_BAR:
            print(f"⚠ {n_perm} permutations cannot reach p < {P_BAR} (floor {1 / (n_perm + 1):.4f}); no verdict")
        passed = bool(np.isfinite(pa["edge_t"]) and pa["edge_t"] >= 3 and pa["eh1"] > 0 and pa["eh2"] > 0
                      and paired["p_search"] < P_BAR)
        extra = dict(edge_t=pa["edge_t"], p_search=paired["p_search"], ehalf1=pa["eh1"], ehalf2=pa["eh2"])
        print(f"\npaired edge by half ({best}): {pa['eh1']:+.3f} / {pa['eh2']:+.3f} | best-arm paired edge t "
              f"{pa['edge_t']:+.2f} | p_search (best of {len(arms)} arms, {len(paired['null'])} label perms) "
              f"{paired['p_search']:.4f}")
        yr = pd.DataFrame({"y": pd.to_datetime(paired["dates"]).year, "d": pa["diff"]}).dropna()
        yt = yr.groupby("y").d.agg(["size", "mean"]).round(3).T
        print(f"paired edge by year ({best}; chronological halves miss a back-half regime):\n{yt.to_string()}")
        bar = f"paired edge t >= 3, both halves' paired edge > 0, p_search < {P_BAR}"
    else:
        best = tab.edge.idxmax() if tab.edge.notna().any() else tab.meanR.idxmax()
        passed = bool(np.isfinite(tab.loc[best].get("edge", np.nan)) and tab.loc[best].edge > 0
                      and abs(tab.loc[best].t) >= 3 and h1[best].mean() > 0 and h2[best].mean() > 0)
        extra = {}
        bar = "beats control, both halves positive, |t|>=3 (legacy, unpaired)"
    row = tab.loc[best]
    if ledger:
        append_ledger(name=name, timeframe=timeframe, n=len(T), best_arm=best, meanR=row.meanR,
                      ctrl=row.get("ctrl", np.nan), edge=row.get("edge", np.nan), t=row.t,
                      half1=h1[best].mean(), half2=h2[best].mean(), passed=passed, note=note, **extra)
    print(f"\nbest arm: {best} | passes the bar ({bar}): {'YES' if passed else 'no'}")
    return tab


def append_ledger(**row) -> None:
    row = {"tested": datetime.now().strftime("%Y-%m-%d"), **row}
    df = pd.DataFrame([row])
    if LEDGER.exists():
        df = pd.concat([pd.read_csv(LEDGER), df], ignore_index=True)
    df.to_csv(LEDGER, index=False)
    cols = ["tested", "name", "timeframe", "n", "best_arm", "meanR", "ctrl", "edge", "t", "edge_t", "p_search",
            "p_opt", "half1", "half2", "passed", "note"]
    d = df.reindex(columns=cols).round(4).astype(str).replace("nan", "")
    md = ("| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
          + "\n".join("| " + " | ".join(r) + " |" for r in d.values))
    hdr = (f"# Pattern ledger\n\n_Every entry pattern tested with `lib.studies.pattern_test`, newest last._\n\n"
           f"**Bar to pass (daily, from 2026-09-23):** paired edge t >= 3 on the best arm, both halves' paired edge "
           f"> 0, and p_search < {P_BAR} (label-permutation null over the best-of-arms pick). Grid rows also carry "
           f"p_opt (the whole grid re-run under each permutation). Rows before 2026-09-23 used the unpaired rule "
           f"(|t| on raw R + point edge > 0) and have no edge_t / p_search.\n"
           f"**Multiple testing:** {len(df)} patterns tested so far — at 5% significance, expect "
           f"~{0.05 * len(df):.1f} to clear by chance. Discount accordingly.\n\n")
    LEDGER_MD.write_text(hdr + md + "\n")


def run_daily(name: str, pattern, *, hold: int = 5, controls: int = 3, split: str = "2023-01-01",
              note: str = "", panel: DailyPanel | None = None, ledger: bool = True,
              entry_at: str = "next_open", control: str = "post", strata: int = 20, perms: int = PERMS,
              plant: float = 0.0) -> pd.DataFrame:
    """pattern(P) -> signal table (from daily_signals).
    ledger=False for parameter sweeps: report only, no ledger row (keeps the multiple-testing count honest).
    entry_at="close" enters at the signal bar's close (the house process); the control then enters at the
    random session's close with the same stop distance in %.
    control =
      "month"  same name, random session in the SAME MONTH (the original). ⚠ includes sessions BEFORE the signal,
               which are hindsight-selected (the name is about to fire) -- inflates the control for continuation
               patterns, deflates it for reversal patterns. NOT the default since the 2026-09-19 re-run
               (data/studies/ledger_rerun/); kept only to reproduce the pre-re-run rows.
      "post"   same name, random session in the 20 sessions AFTER the signal (no look-ahead): is the signal DAY a
               better entry than a random later day in a name known to have fired?
      "xname"  random eligible OTHER name, same date, same stop %: does the NAME selection matter?
    2026-09-23: every signal now carries a STRATUM of up to `strata` candidate controls; `controls` of them are its
    paired controls; `perms` label permutations price the best-of-arms pick (p_search). perms=0 skips the null.
    plant = test hook only (adds a constant R to the real signal)."""
    P = panel or load_panel()
    S = pattern(P)
    st = _build_strata(P, S, hold, entry_at, control, strata, plant)
    if st is None:
        print(f"{name}: no signals"); return pd.DataFrame()
    T = st["T"]
    sig, ctl = _pick(st, _obs_keys(st), controls)
    K = pd.DataFrame(ctl, columns=DAILY_ARMS)                       # per-signal control means (legacy columns)
    T.to_parquet(REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet", index=False)
    paired = _stratum_stats(st, controls, split, perms)
    print(f"control = {control} (strata: median {np.median((st['k'] >= 0).sum(axis=1) - 1):.0f} candidates, "
          f"{controls} paired per signal)")
    tab = _report(name, T, K, DAILY_ARMS, split, note + f"; ctrl={control}", "daily", ledger=ledger, paired=paired)
    tab.attrs.update(p_search=paired["p_search"], null=paired["null"])
    return tab


def run_grid(name: str, pattern_factory, grid: list[dict], *, hold: int = 5, controls: int = 3,
             split: str = "2023-01-01", note: str = "", panel: DailyPanel | None = None, ledger: bool = True,
             entry_at: str = "next_open", control: str = "post", strata: int = 20, perms: int = PERMS,
             plant_cell: int | None = None, plant: float = 0.0) -> pd.DataFrame:
    """Pre-registered parameter grid, priced as ONE test. pattern_factory(P, **cell) -> signal table.
    Reports the surface (best-arm paired edge t per cell, halves), a plateau metric, and p_opt: the share of label
    permutations in which the max over ALL cells x arms is >= the observed max. Permutation keys are shared across
    cells (keyed by session x name), so overlapping cells stay as correlated as they really are.
    Writes one ledger row per grid. plant_cell / plant = test hooks."""
    P = panel or load_panel()
    cells = []
    for c, prm in enumerate(grid):
        st = _build_strata(P, pattern_factory(P, **prm), hold, entry_at, control, strata,
                           plant if plant_cell in (c, -1) else 0.0)
        if st is None:
            continue
        stats = _stratum_stats(st, controls, split, 0)
        best = max(stats["arms"], key=lambda a: (stats["arms"][a]["edge_t"]
                                                  if np.isfinite(stats["arms"][a]["edge_t"]) else -np.inf))
        b = stats["arms"][best]
        cells.append(dict(cell=c, params=prm, st=st, codes=stats["codes"], nd=stats["nd"], n=len(st["R"]),
                          best_arm=best, edge_t=b["edge_t"], p_edge=b["pedge"], eh1=b["eh1"], eh2=b["eh2"]))
    if not cells:
        print(f"{name}: no signals in any cell"); return pd.DataFrame()
    surf = pd.DataFrame([{k: v for k, v in c.items() if k not in ("st", "codes", "nd")} for c in cells])
    obs = np.nanmax(surf.edge_t)
    null = np.empty(perms)
    for p in range(perms):
        null[p] = max(np.nanmax(_paired(c["st"], _perm_keys(c["st"], p), controls, c["codes"], c["nd"]))
                      for c in cells)
    p_opt = (np.sum(null >= obs) + 1) / (perms + 1) if perms else np.nan
    good = (surf.edge_t >= 2) & (surf.eh1 > 0) & (surf.eh2 > 0)
    plateau = good.mean()
    ratio = surf.edge_t.median() / obs if obs > 0 else np.nan
    bi = surf.edge_t.idxmax()
    b = surf.loc[bi]
    print(f"\n=== GRID {name}: {len(surf)} cells x {len(DAILY_ARMS)} arms, control={control} ===")
    print(surf.drop(columns=["cell"]).round(3).to_string())
    print(f"\nbest cell {b.params} arm {b.best_arm}: paired edge t {b.edge_t:+.2f}, halves {b.eh1:+.3f}/{b.eh2:+.3f}"
          f"\nplateau share (edge t >= 2 & both halves > 0): {plateau:.0%} | median/best t ratio {ratio:.2f}"
          f"\np_opt (whole grid re-run on {perms} label perms): {p_opt:.4f}  [null max-t p50 {np.median(null):.2f}, "
          f"p99 {np.quantile(null, 0.99):.2f}]")
    if perms and 1 / (perms + 1) >= P_BAR:
        print(f"⚠ {perms} permutations cannot reach p < {P_BAR} (floor {1 / (perms + 1):.4f}); no verdict")
    passed = bool(b.edge_t >= 3 and b.eh1 > 0 and b.eh2 > 0 and p_opt < P_BAR)
    print(f"passes (best cell paired t >= 3, halves > 0, p_opt < {P_BAR}): {'YES' if passed else 'no'}")
    if ledger:
        append_ledger(name=f"GRID {name}", timeframe="daily", n=int(b.n), best_arm=f"{b.best_arm} @ {b.params}",
                      meanR=np.nan, ctrl=np.nan, edge=b.p_edge, t=np.nan, edge_t=b.edge_t, p_search=np.nan,
                      p_opt=p_opt, half1=b.eh1, half2=b.eh2, passed=passed,
                      note=note + f"; {len(surf)} cells, plateau {plateau:.0%}, median/best {ratio:.2f}; ctrl={control}")
    surf.attrs.update(p_opt=p_opt, plateau=plateau, ratio=ratio, null=null)
    return surf


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
        # Running SESSION VWAP. ⚠ The cached `vwap` column is the vendor's PER-BAR VWAP (identical to
        # `price` on every row), NOT this. Reading it as session VWAP made a 2026-09-23 study's
        # "pullback to VWAP" fire on 100% of signals. Same expression as `lib.journal.exit_kind.
        # session_vwap()`, duplicated deliberately: importing that module here would pull TradierClient
        # and aiohttp into a harness 20+ study scripts import.
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
