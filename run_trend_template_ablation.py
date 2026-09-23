#!/usr/bin/env python3
"""
Does every Minervini Trend Template criterion earn its place? (pre-registered 2026-09-22)

THE GAP. The Trend Template has only ever been tested WHOLE. `universe_test_2026-09-21.md` found it is the
weakest of five universes ADR-matched, and that HYB-B (the TT core at a $100M ADDV floor plus ADR >= 4)
beat it -- which already says at least one PARAMETER (the $200M liquidity floor) is miscalibrated. But the
nine core conjuncts have never been scored individually. Gabe's question, 2026-09-22: does each criterion
add value, or are some inert or negative?

METHOD: leave-one-out ablation. Rebuild the universe nine times, each time dropping ONE conjunct, and
measure how much the universe's selection changes. This is an ESTIMATION task (what is each criterion's
marginal contribution), not a search for a winner.

  Full TT = c1..c9 AND addv >= $200M, membership shifted one session (as of the prior close).
    c1 close > 150 SMA          c4 200 SMA rising (vs 20 sessions ago)    c7 close >= 1.30 x 252d low
    c2 close > 200 SMA          c5 50 SMA > 150 SMA                       c8 close >= 0.75 x 252d high
    c3 150 SMA > 200 SMA        c6 close > 50 SMA                         c9 RS percentile >= 70
                                                                          c10 ADDV >= $200M (the floor HYB-B relaxed)

  PRIMARY STATISTIC -- paired, date-held-fixed: for each non-overlapping 20-session date,
      delta(k) = [mean forward 20d return of members WITHOUT criterion k]
               - [mean forward 20d return of members of the FULL TT]
  t across dates. Holding the date fixed removes the tape entirely, so a criterion cannot look good
  merely by being in the universe on good days.

  READING: delta < 0 => dropping it HURTS => the criterion ADDS value.
           delta ~ 0 => INERT (and still costs universe size = foregone opportunity).
           delta > 0 => dropping it HELPS => the criterion SUBTRACTS.

  ⚠ ADR CONFOUND, handled explicitly. Dropping a criterion changes the volatility mix, and higher-ADR names
  have higher raw forward returns. Every cell is therefore reported twice: RAW excess, and ADR-MATCHED --
  the benchmark is reweighted to the members' own ADR-decile distribution on that date, so an arm cannot win
  by simply admitting more volatile names. The ADR-matched column governs.

  Secondary: universe size (names/day). A criterion that is inert but cuts the universe in half is not free.

BAR: 10 cells x 2 horizons = 20; Sidak at alpha 0.05 -> |t| >= 3.09. A criterion is called SUBTRACTS or ADDS
only if the ADR-matched paired t clears that AND both halves agree in sign (split 2023-01-01). Anything else
is INERT/UNRESOLVED -- with the note that "inert" is itself an actionable finding when the criterion is
expensive in universe size.

⚠ Survivorship: the panel is today's liquid names, so arms are comparable with each other but the absolute
level is optimistic. Same caveat as the parent universe test.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_trend_template_ablation.py \
         > data/studies/trend_template_ablation_2026-09-22.log 2>&1
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import DailyPanel

START, SPLIT = "2020-01-01", "2023-01-01"
N_CELLS = 20
SIDAK_T = float(stats.norm.ppf(1 - (1 - (1 - 0.05) ** (1 / N_CELLS)) / 2))

CRITERIA = {
    "c1 close>150sma":   "close above the 150 SMA",
    "c2 close>200sma":   "close above the 200 SMA",
    "c3 150>200":        "150 SMA above the 200 SMA",
    "c4 200 rising":     "200 SMA rising vs 20 sessions ago",
    "c5 50>150":         "50 SMA above the 150 SMA",
    "c6 close>50sma":    "close above the 50 SMA",
    "c7 >=30% off low":  "at least 30% above the 252d low",
    "c8 within 25% hi":  "within 25% of the 252d high",
    "c9 RS>=70":         "relative-strength percentile >= 70",
    "c10 ADDV>=$200M":   "50d average dollar volume >= $200M",
}


def build(P: DailyPanel, raw: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """The nine conjuncts + the liquidity floor, each as its own boolean frame."""
    C, H, L = P.close, P.high, P.low
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex(
        index=C.index, columns=C.columns)
    dolvol = piv("dolvol")
    sma50, sma150, sma200 = (C.rolling(n, min_periods=n).mean() for n in (50, 150, 200))
    hi252 = H.rolling(252, min_periods=200).max()
    lo252 = L.rolling(252, min_periods=200).min()
    addv = dolvol.rolling(50, min_periods=50).mean()
    rs = 2 * C / C.shift(63) + C / C.shift(126) + C / C.shift(189) + C / C.shift(252)
    rs_pct = rs.where(P.elig).rank(axis=1, pct=True) * 100
    adr = (H / L - 1).rolling(20).mean() * 100

    conj = {
        "c1 close>150sma":  C > sma150,
        "c2 close>200sma":  C > sma200,
        "c3 150>200":       sma150 > sma200,
        "c4 200 rising":    sma200 > sma200.shift(20),
        "c5 50>150":        sma50 > sma150,
        "c6 close>50sma":   C > sma50,
        "c7 >=30% off low": C >= 1.30 * lo252,
        "c8 within 25% hi": C >= 0.75 * hi252,
        "c9 RS>=70":        rs_pct >= 70,
        "c10 ADDV>=$200M":  addv >= 200e6,
    }
    return conj, adr.shift(1)


def mask_from(conj: dict, P: DailyPanel, drop: str | None) -> pd.DataFrame:
    m = None
    for k, v in conj.items():
        if k == drop:
            continue
        m = v if m is None else (m & v)
    m = (m & P.elig).shift(1).fillna(False).astype(bool)
    m[m.index < START] = False
    return m


def per_date_returns(P: DailyPanel, m: pd.DataFrame, fr: pd.DataFrame, dates, adr: pd.DataFrame,
                     base: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Members' mean forward return, the ADR-matched panel benchmark, and member count, per date."""
    mm = fr.where(m).loc[dates]
    raw_mean = mm.mean(axis=1)
    n = mm.count(axis=1)

    # ADR-matched benchmark: reweight the eligible panel to the members' ADR-decile mix on each date.
    dec = adr.loc[dates].rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int)
    panel_fr = fr.where(base).loc[dates]
    bench = {}
    for d in dates:
        md, pd_ = dec.loc[d].where(m.loc[d]), dec.loc[d].where(base.loc[d])
        w = md.value_counts(normalize=True)
        if w.empty:
            bench[d] = np.nan
            continue
        g = panel_fr.loc[d].groupby(pd_).mean()
        common = w.index.intersection(g.index)
        bench[d] = float((w[common] / w[common].sum() * g[common]).sum()) if len(common) else np.nan
    return raw_mean, pd.Series(bench), n


def main() -> None:
    import run_precision_tier_control as pc
    P, _brk, _p = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    conj, adr = build(P, raw)
    C, base = P.close, P.elig.shift(1).fillna(False).astype(bool)

    full = mask_from(conj, P, None)
    print(f"panel {C.shape}, window {START} -> {C.index.max().date()}")
    print(f"full Trend Template: median {int(full.sum(axis=1)[full.index >= START].median())} names/day")
    print(f"multiple testing: {N_CELLS} cells, Sidak -> |t| >= {SIDAK_T:.2f}\n")

    rows = []
    for h in (20, 5):
        fr = C.shift(-h) / C - 1
        dates = C.index[C.index >= START][::h]
        dates = dates[dates <= C.index[-1 - h]]
        f_raw, f_bench, f_n = per_date_returns(P, full, fr, dates, adr, base)
        ok = f_n >= 5

        for k in [None] + list(CRITERIA):
            m = full if k is None else mask_from(conj, P, k)
            a_raw, a_bench, a_n = per_date_returns(P, m, fr, dates, adr, base)
            good = ok & (a_n >= 5)

            d_raw = (a_raw - f_raw)[good].dropna()
            d_adj = ((a_raw - a_bench) - (f_raw - f_bench))[good].dropna()
            tt_ = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
            h1, h2 = d_adj[d_adj.index < SPLIT], d_adj[d_adj.index >= SPLIT]
            rows.append(dict(
                horizon=f"{h}d", dropped=("— full TT —" if k is None else k),
                names=int(m.sum(axis=1)[m.index >= START].median()),
                adr_med=float(adr.where(m).stack().median()),
                excess_raw=(a_raw - f_bench)[good].mean() * 100,
                d_raw=d_raw.mean() * 100,
                d_adj=d_adj.mean() * 100, t_adj=tt_(d_adj),
                h1=h1.mean() * 100, h2=h2.mean() * 100,
                agree=bool(np.sign(h1.mean()) == np.sign(h2.mean())),
                dates=len(d_adj)))

    R = pd.DataFrame(rows)
    R.to_csv(pt.REPO / "data/studies/trend_template_ablation_2026-09-22.csv", index=False)

    for h in ("20d", "5d"):
        sub = R[R.horizon == h].copy()
        sub["verdict"] = np.where(
            (sub.t_adj.abs() >= SIDAK_T) & sub.agree,
            np.where(sub.d_adj > 0, "SUBTRACTS", "ADDS"), "inert/unresolved")
        sub.loc[sub.dropped == "— full TT —", "verdict"] = ""
        print(f"\n{'=' * 118}\n{h} horizon — dropping each criterion (delta > 0 means the criterion SUBTRACTS)\n{'=' * 118}")
        print(sub[["dropped", "names", "adr_med", "excess_raw", "d_raw", "d_adj", "t_adj",
                   "h1", "h2", "agree", "verdict"]].round(3).to_string(index=False))

    print("\nnames = median universe size/day · d_adj = ADR-matched paired change vs full TT (pp) · "
          f"bar |t| >= {SIDAK_T:.2f} + halves agree")


if __name__ == "__main__":
    main()
