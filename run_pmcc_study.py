#!/usr/bin/env python3
"""
Does a poor man's covered call beat just holding the long call? (pre-registered 2026-09-23)

THE CLAIM. Nick Galarnyk (2026-06-16, reviewed 3/5): a $10K account cannot buy 100 shares of a mega-cap,
so buy a long-dated ITM call instead and sell shorter-dated calls against it, grinding the cost basis down
each cycle. His worked example: NVDA ~210 spot, buy the Sep 180 call (94 DTE) for $36 -> breakeven 216;
sell the Jul 220 call for $4.50 -> "12.5% return on risk", and if it pushes through, ~31% in 31 days.
He presents it as a solid small-account grinder. **He shows one favourable NVDA path and no backtest.**

⚠ WHY THE PRIOR IS NEGATIVE. A PMCC is a DIAGONAL. Our own path study (`calendar_path_study`, after the
truncation erratum was corrected) found on a clean re-run: **no edge in single/double calendars, diagonals
or condors on ETFs, and stocks lose 8-18%.** So the structure he recommends is one we have already
measured as negative on single names. This test asks the narrower, fairer question he actually poses:
does adding the rolled short call beat simply holding the long call you were going to buy anyway?

⚠⚠ PRE-REGISTER THE TAIL — this is the trap. The PMCC **caps the right tail by construction** while the
naked long keeps it. Twice today a management rule looked good on the mean-ish stats and turned out to be
a RISK rule, not a RETURN rule: the 21-DTE strangle exit (PASS, t +4.26, but both arms negative) and
Tito's spike branch (win rate 14.6 -> 19.3%, sd 201 -> 158pp, and p99 capped +834% -> +671%). So the
headline here is NOT the mean alone. **Tail percentiles are reported at the same size as the mean**, and a
PMCC that wins the median while losing p90/p99 is a risk result and must be called one.

DESIGN
  Universe  18 mega-caps (his recommendation ~ our measured tradeable set)
  Entry     first eligible session of each month, 2019 -> 2026
  LONG      DTE nearest 90 within [75,100], delta nearest 0.80 within [0.70,0.90]. Buy the ASK.
  Breakeven long strike + long cost -- his stated rule for where the short goes.
  SHORT     at each ~30-day cycle: DTE nearest 30 within [21,45], the LOWEST strike strictly ABOVE the
            breakeven. Sell the BID. Settled at its own expiry at intrinsic; then the next one is sold.
  ARM A     naked long call, held to its expiry, settled at intrinsic.
  ARM B     the same long call + the rolled shorts. PAIRED -- identical long leg, same entry, same name.
  Fills     REAL: buy the ask, sell the bid, plus $0.65/contract/leg/side. Never mid.
  Settle    spot recovered from the CHAIN (`lib.studies.chain_spot`), never from a price panel: v3 strikes
            are RAW and every panel we keep is split-adjusted (3.1% median mismatch; a whole split factor
            for a name that split in-sample -- this has produced two wrong results already).

PRE-REGISTERED PASS: ARM B minus ARM A, paired, positive with month-clustered t >= 3 and both halves the
same sign (split 2023-01-01). Anything else = the rolled short call does not pay for itself.

PRIOR: B loses to A on the mean (~75%), because the short call is a drag once costs are charged and the
path study already found diagonals on stocks negative. Most likely shape: B wins the median and the win
rate, loses the mean, and truncates p90/p99 -- i.e. a third instance of today's pattern, a real risk lever
sold as a return lever.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u run_pmcc_study.py 2>&1 | tee data/studies/logs/pmcc.log
"""
from __future__ import annotations

import pathlib
import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

from lib.studies.chain_spot import spot_from_chain

CH = pathlib.Path("/private/tmp/claude-501/-Users-gmerton-v2-options-playground/"
                  "0dc56bae-9a64-43e3-9215-162f5d8a0c59/scratchpad/pmcc")
COMM = 0.65 / 100.0                      # per share of a 100-share contract
LONG_DTE, LONG_LO, LONG_HI = 90, 75, 100
LONG_D, LONG_DLO, LONG_DHI = 0.80, 0.70, 0.90
SHORT_DTE, SHORT_LO, SHORT_HI = 30, 21, 45
N_CYCLES = 3
SPLIT = pd.Timestamp("2023-01-01")


def load() -> tuple[pd.DataFrame, pd.Series]:
    files = sorted(CH.glob("calls_*.parquet"))
    if not files:
        raise SystemExit(f"no chain files in {CH} — run pull_pmcc_chains.py first")
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d["trade_date"] = pd.to_datetime(d["trade_date"]); d["expiry"] = pd.to_datetime(d["expiry"])
    n0 = len(d)
    d = d.drop_duplicates(subset=["ticker", "expiry", "strike", "trade_date"], keep="first")
    d["dte"] = (d["expiry"] - d["trade_date"]).dt.days
    d["iv"] = d[["bid_iv", "ask_iv"]].mean(axis=1)
    d["cp"] = "C"
    print(f"chains: {len(d):,} call-days ({n0-len(d):,} dupes dropped), {d.ticker.nunique()} names, "
          f"{d.trade_date.min().date()} -> {d.trade_date.max().date()}")
    spot = spot_from_chain(d)            # RAW spot per (ticker, trade_date), median across legs
    print(f"spot recovered for {len(spot):,} ticker-days")
    return d, spot


def mt(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / (x.std(ddof=1) / sqrt(len(x)))) if len(x) > 2 else np.nan


def main() -> None:
    d, spot = load()
    rows = []
    for sym, g in d.groupby("ticker", sort=False):
        by_day = {t: x for t, x in g.groupby("trade_date", sort=False)}
        days = sorted(by_day)
        sp = spot.xs(sym, level=0) if sym in spot.index.get_level_values(0) else None
        if sp is None or not days:
            continue
        # one entry per calendar month
        firsts = pd.Series(days).groupby(pd.Series(days).dt.to_period("M")).min().tolist()
        for d0 in firsts:
            day = by_day[d0]
            cand = day[(day.dte.between(LONG_LO, LONG_HI)) & (day.delta.between(LONG_DLO, LONG_DHI))
                       & (day.ask > 0)]
            if cand.empty:
                continue
            pick = cand.iloc[((cand.delta - LONG_D).abs() + (cand.dte - LONG_DTE).abs() / 500).argsort()[:1]].iloc[0]
            lk, lx = float(pick.strike), pick.expiry
            lcost = float(pick.ask) + COMM
            if lcost <= 0:
                continue
            be = lk + lcost                                   # his rule: short goes above breakeven
            s_at = sp.get(lx, np.nan)
            if not np.isfinite(s_at):
                continue
            long_settle = max(s_at - lk, 0.0)

            credits, buybacks, ok = 0.0, 0.0, True
            cyc = d0
            for _ in range(N_CYCLES):
                cd = [t for t in days if t >= cyc]
                if not cd:
                    ok = False; break
                cday = by_day[cd[0]]
                sc = cday[(cday.dte.between(SHORT_LO, SHORT_HI)) & (cday.strike > be) & (cday.bid > 0)
                          & (cday.expiry <= lx)]
                if sc.empty:
                    ok = False; break
                s = sc.sort_values(["strike", "dte"]).iloc[0]   # LOWEST strike above breakeven
                credits += float(s.bid) - COMM
                ss = sp.get(s.expiry, np.nan)
                if not np.isfinite(ss):
                    ok = False; break
                buybacks += max(ss - float(s.strike), 0.0) + COMM
                cyc = s.expiry
            if not ok:
                continue
            a = (long_settle - lcost) / lcost
            b = (long_settle - lcost + credits - buybacks) / lcost
            rows.append(dict(sym=sym, entry=d0, lstrike=lk, lexp=lx, lcost=lcost,
                             delta=float(pick.delta), dte=int(pick.dte),
                             credits=credits, buybacks=buybacks, ret_A=a, ret_B=b))
    T = pd.DataFrame(rows)
    if T.empty:
        raise SystemExit("no trades built — check the chain pull")
    T["month"] = T.entry.dt.to_period("M")
    T.to_csv("data/studies/pmcc_study_2026-09-23.csv", index=False)
    print(f"\n{len(T):,} PMCC cycles · {T.sym.nunique()} names · {T.entry.min().date()} -> {T.entry.max().date()}")
    print(f"median long: delta {T.delta.median():.2f}, {T.dte.median():.0f} DTE, cost ${100*T.lcost.median():,.0f}")
    print(f"credits collected ${100*T.credits.mean():,.0f} vs bought back ${100*T.buybacks.mean():,.0f} "
          f"-> net ${100*(T.credits-T.buybacks).mean():+,.0f} per cycle-set")

    dd = T.ret_B - T.ret_A
    md = dd.groupby(T["month"]).mean()
    h1, h2 = md[md.index < SPLIT.to_period("M")], md[md.index >= SPLIT.to_period("M")]
    print(f"\n{'='*104}\nPRIMARY — ARM B (PMCC) minus ARM A (hold the long call), paired\n{'='*104}")
    print(f"  n {len(T):,}   mean diff {100*dd.mean():+.2f}pp   month-clustered t {mt(md):+.2f}   "
          f"halves {100*h1.mean():+.2f} / {100*h2.mean():+.2f}")
    passed = bool(dd.mean() > 0 and abs(mt(md)) >= 3 and np.sign(h1.mean()) == np.sign(h2.mean()))
    print(f"  PRE-REGISTERED PASS: {'YES' if passed else 'NO'}")

    print(f"\n{'='*104}\n⚠ THE TAIL — reported at the same size as the mean (pre-registered)\n{'='*104}")
    stat = pd.DataFrame({
        "A hold the long": [T.ret_A.mean(), T.ret_A.median(), (T.ret_A > 0).mean(), T.ret_A.std(),
                            T.ret_A.quantile(.10), T.ret_A.quantile(.90), T.ret_A.quantile(.99)],
        "B PMCC": [T.ret_B.mean(), T.ret_B.median(), (T.ret_B > 0).mean(), T.ret_B.std(),
                   T.ret_B.quantile(.10), T.ret_B.quantile(.90), T.ret_B.quantile(.99)],
    }, index=["mean", "median", "win%", "sd", "p10", "p90", "p99"]) * 100
    print(stat.round(1).to_string())
    print("\n  ⭐ read p90/p99 before the mean: a PMCC that wins the median while truncating the right tail")
    print("     is a RISK result, not a return result — the 21-DTE and spike-branch shape from today.")
    print("\nwrote data/studies/pmcc_study_2026-09-23.csv")


if __name__ == "__main__":
    main()
