#!/usr/bin/env python3
"""
12-1 MOMENTUM REFINEMENTS: a shorter skip, and waiting for a 20-EMA pullback (pre-registered 2026-10-02, before any run;
Gabe: "if they were leaders from the previous month, there's a good chance many of them will be extended").

WHY NEW. The certified sleeve (run_momentum_portfolio.py, PRIMARY top decile 12-1) has been tested for lookback (6-1),
bucket size, 20-name books, buffers, vol scaling, residual/frog and leverage vehicle. It has NEVER been tested for
(a) the length of the skip window or (b) entry timing inside the holding month. The EMA-pullback / band-entry nulls
(pullback_entry_study, band_runaway_entry) were on breakout names; the one supportive result (confirmation ladder P2:
dipping uptrend names beat non-dipping ones, t 2.5-5.5) was PARKED for survivorship. This runs on the
survivorship-free chain_spot panel, so it also answers that.

DATA     identical to the certified PRIMARY: silver.chain_spot_daily closes incl. delisted (run_dip_survivorship
         pull/adjust_and_clean), liquidity = 50-session mean option volume >= 1,000 and price >= $5 at formation,
         formations 2011-01 -> 2026-01, 10 bp per side. Closes only (no OHLC), so:
           EMA20  = 20-session EMA of the close, as of each close.
           ADRp   = 20-session mean |close-to-close % change| (a close-only ADR proxy), as of each close.
           dist   = (close / EMA20 - 1) / ADRp   (distance above the 20 EMA in ADR-proxy units).

CELLS (each compared, month by month, with the BASE = certified rule: top decile 12-1, buy all at the formation
       close, hold to the next month-end; same engine, same per-side costs)
  S15      IDEA 1 PRIMARY. Score = close(t-15) / close(t-252) - 1: skip 15 sessions instead of 21. Buy at formation.
  E0.5     IDEA 2 PRIMARY. Same top-decile names as BASE. A name NEW to the book waits: it is bought at the first close
           in the holding month (formation close included) with dist <= 0.5; if none, it stays in CASH (0 return) for
           that month. A name already held (bought earlier, still in the decile) carries over from the formation close
           with no wait. Equal capital per name; untriggered capital idles at 0.
  E0.0     as E0.5, trigger dist <= 0.0 (close at or below the 20 EMA).
  E1.0     as E0.5, trigger dist <= 1.0 (the house 1-ADR band).
  E0.5-T   [secondary] as E0.5 but capital is spread over the names actually held (triggered + carried); cash only if
           none. Tests "deploy into what pulled back" rather than equal-capital waiting.

STATISTIC  monthly difference (cell - BASE), percentage points; Newey-West t (lag 3); halves split 2018-01; years with a
           positive summed difference. Also reported: each arm's excess over the EW universe, trigger rate, invested
           fraction, mean sessions to trigger.
BAR        these are our own refinements (DISCOVERY track, not replication). M = 5 -> Sidak |t| >= 2.57; the house
           |t| >= 3 governs, both halves the same sign as the mean, and a majority of years. A cell must beat BASE,
           not just EW. Primaries named in advance: S15 (idea 1), E0.5 (idea 2). Everything else is exploratory.
KNOWN BIASES (declared now)
  - Cash earns 0 in E-cells; T-bills averaged ~1.6%/yr over 2011-26 -> idle capital is charged ~0.13pp/mo x idle
    share. Reported as an adjustment, not used for the verdict.
  - No stops in any arm (the certified rule has none); a name that pulls back and keeps falling is held to month-end.
  - The E-cells' entries are realised at the trigger CLOSE (decided on that close) - the same close-entry convention
    as the certified rule. No intraday fills.
READ  E0.5 PASS -> new entrants wait for the EMA; NULL -> buying at formation stays (timing is irrelevant, as for the
      breakout); INVERTED -> waiting misses the runners that carry the strategy. S15 PASS -> change the screener's skip.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_momentum_entry_refine.py
       (log -> data/studies/logs/momentum_entry_refine.log; table data/studies/momentum_entry_refine_2026-10-02.csv)
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = M.REPO
LOG = REPO / "data/studies/logs/momentum_entry_refine.log"
COST, SPLIT = M.COST, M.SPLIT


def book(C: pd.DataFrame, elig: pd.DataFrame, skip: int, trig: float | None, mode: str = "equal") -> pd.DataFrame:
    """Monthly returns of a top-decile 12-skip book.
    trig None -> buy every name at the formation close (BASE / S15).
    trig x    -> new names wait for the first close with dist <= x inside the month; held names carry over.
    mode 'equal' -> each decile name gets 1/N capital (untriggered = cash); 'trig' -> capital spread over held names."""
    idx = C.index; Cv = C.values; E = elig.values
    ema = C.ewm(span=20, adjust=False, min_periods=20).mean().values
    adr = C.pct_change().abs().rolling(20, min_periods=15).mean().values
    dist = (Cv / ema - 1) / adr
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    # formation sets first, so exits can see next month's membership (known at b, the exit close)
    forms = []
    for a in me[:-1]:
        if a - 252 < 0:
            forms.append(None); continue
        score = Cv[a - skip] / Cv[a - 252] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            forms.append(None); continue
        names = np.flatnonzero(ok)
        cut = np.nanquantile(score[names], 1 - 0.10)
        forms.append((names, set(names[score[names] >= cut])))
    rows, held_prev = [], set()
    for k, (a, b) in enumerate(zip(me[:-1], me[1:])):
        if forms[k] is None:
            continue
        names, dec = forms[k]
        nxt = forms[k + 1][1] if k + 1 < len(forms) and forms[k + 1] is not None else set()
        r_ew = pd.Series(Cv[np.minimum(b, last_valid[names]), names] / Cv[a, names] - 1).replace([np.inf, -np.inf], np.nan).mean()
        rets, held_now, n_trig, waits = [], set(), 0, []
        for j in dec:
            end = min(b, last_valid[j])
            if trig is None or j in held_prev:
                t0 = a
            else:
                cand = [t for t in range(a, end) if np.isfinite(dist[t, j]) and dist[t, j] <= trig]
                t0 = cand[0] if cand else None
                if t0 is not None:
                    n_trig += 1; waits.append(t0 - a)
            if t0 is None:
                rets.append(np.nan if mode == "trig" else 0.0)
                continue
            r = Cv[end, j] / Cv[t0, j] - 1
            if not np.isfinite(r):
                rets.append(np.nan if mode == "trig" else 0.0); continue
            cost = (0 if j in held_prev else COST) + (0 if (j in nxt and end == b) else COST)
            rets.append(r - cost)
            held_now.add(j)
        rr = pd.Series(rets)
        new = len(dec - held_prev) if trig is not None else 0
        rows.append(dict(month=idx[b].to_period("M"), mom=rr.mean() if rr.notna().any() else 0.0, ew=r_ew,
                         n=len(dec), held=len(held_now), new=new, trig=n_trig,
                         wait=np.mean(waits) if waits else np.nan))
        held_prev = held_now
    return pd.DataFrame(rows).set_index("month")


def compare(P: pd.DataFrame, B: pd.DataFrame, label: str, out: list[str]) -> dict:
    j = P.join(B, rsuffix="_b", how="inner")
    x = (j.mom - j.mom_b) * 100
    h = x.index < pd.Period(SPLIT, "M")
    yr = x.groupby(x.index.year).sum()
    t = M.nw_t(x)
    sgn = np.sign(x.mean())
    res = dict(cell=label, months=len(x), arm_mo=100 * j.mom.mean(), base_mo=100 * j.mom_b.mean(),
               arm_excess_ew=100 * (j.mom - j.ew).mean(), diff=x.mean(), t_nw=t, h1=x[h].mean(), h2=x[~h].mean(),
               yrs_pos=f"{(yr > 0).sum()}/{len(yr)}",
               invested=(j.held / j.n).mean(), trig_rate=(j.trig.sum() / j.new.sum()) if j.new.sum() else np.nan,
               wait_sessions=j.wait.mean())
    res["PASS"] = bool(abs(t) >= 3 and np.sign(res["h1"]) == sgn and np.sign(res["h2"]) == sgn
                       and ((yr > 0).sum() if sgn > 0 else (yr < 0).sum()) > len(yr) / 2)
    out.append(f"\n## {label}")
    out.append(f"  arm {res['arm_mo']:+.2f}%/mo vs BASE {res['base_mo']:+.2f}% | arm excess over EW {res['arm_excess_ew']:+.2f}pp")
    out.append(f"  arm - BASE {x.mean():+.2f}pp/mo t_NW {t:+.2f} | halves {res['h1']:+.2f} / {res['h2']:+.2f} | years + {res['yrs_pos']}"
               f" | invested {res['invested']:.0%}" + (f", new names triggered {res['trig_rate']:.0%} after ~{res['wait_sessions']:.1f} sessions"
                                                       if np.isfinite(res['trig_rate']) else ""))
    out.append("  diff by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()) + f"  -> {'PASS' if res['PASS'] else 'fail'}")
    return res


def main():
    import run_dip_survivorship as DS
    out = ["# 12-1 momentum refinements: skip 15 vs 21, wait for the 20 EMA (pre-registration in the docstring)"]
    d = DS.pull(); C, V = DS.adjust_and_clean(d)
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    B = book(C, liq, 21, None)
    out.append(f"\nBASE (certified rule, this engine): {100*B.mom.mean():+.2f}%/mo, excess over EW {100*(B.mom-B.ew).mean():+.2f}pp "
               f"(certified run: +1.65 / +0.67; small gaps = per-name cost accounting)")
    R = [compare(book(C, liq, 15, None), B, "S15  [IDEA 1 PRIMARY] skip 15 sessions", out),
         compare(book(C, liq, 21, 0.5), B, "E0.5 [IDEA 2 PRIMARY] new names wait for dist <= 0.5, else cash", out),
         compare(book(C, liq, 21, 0.0), B, "E0.0 wait for close <= 20 EMA, else cash", out),
         compare(book(C, liq, 21, 1.0), B, "E1.0 wait for dist <= 1.0 (house band), else cash", out),
         compare(book(C, liq, 21, 0.5, "trig"), B, "E0.5-T [secondary] dist <= 0.5, capital over held names", out)]
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    out.append("\nSidak(5) |t| >= 2.57; house |t| >= 3 governs. Cash at 0: T-bill credit ~0.13pp/mo x idle share (not in the verdict).")
    D.to_csv(REPO / "data/studies/momentum_entry_refine_2026-10-02.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
