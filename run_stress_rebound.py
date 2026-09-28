#!/usr/bin/env python3
"""
Does the S&P REBOUND after stress Fridays? The mechanism under the certified stress bucket (pre-registered 2026-09-28).

WHY. stress_vehicle_h2h_2026-09-28.md: the certified 20-DTE 0.25/0.15 vertical earns nothing beyond the SPY move its
delta carries -- its return IS the post-selloff rebound. The certification (t 6.07) used 2010+ only, a sample in
which every stress episode recovered. The rebound itself has never been tested, and 1990-2009 is a clean holdout.

PRE-REGISTRATION (frozen before the first run)
  Data      ^GSPC close (price index; dividends excluded from every arm, so they cancel in the contrast) and ^VIX
            close, yfinance, 1990-01 -> 2026-09.
  Stress    Friday close < 50-session SMA AND VIX >= 20 (the certified regime definition).
  Outcome   forward index return from the Friday close over 5 / 20 / 45 sessions. PRIMARY horizon 20 (the vertical is
            20 DTE with a 50% take).
  Control   all NON-stress Fridays in the same window (the unconditional alternative: holding the index any week).
            Secondary controls: below-50-SMA Fridays with VIX < 20 (trend damage without fear); VIX >= 20 Fridays
            above the 50 SMA (fear without trend damage).
  Episodes  stress Fridays more than 31 days apart start a new episode; SE of the stress mean clustered by episode;
            excess = stress mean - control mean (control SE treated as negligible vs the clustered stress SE; also
            reported: a block bootstrap over episodes).
  PRIMARY   HOLDOUT 1990-01 -> 2009-12: 20-session excess > 0 with t >= 2 (a single confirmatory hypothesis on data the
            certification never saw). CONFIRMED iff the holdout passes AND 2010-2026 has the same sign.
            If the holdout fails -> the bucket's certification rests on 2010+ only -> recommend PARKED.
  Also      per-decade table, the 2008 episode's contribution, share of episodes positive, 5/45-session horizons,
            and risk context (stdev and worst 20-session outcome, stress vs control).

Usage: PYTHONPATH=src .venv/bin/python3 run_stress_rebound.py > data/studies/logs/stress_rebound.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)
RNG = np.random.default_rng(20260928)


def yf_close(tk):
    import yfinance as yf
    s = yf.download(tk, start="1989-06-01", end="2026-10-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def main():
    S = yf_close("^GSPC"); V = yf_close("^VIX").reindex(S.index).ffill()
    sma = S.rolling(50).mean()
    F = pd.DataFrame(dict(S=S, V=V, below=S < sma))
    for h in (5, 20, 45):
        F[f"f{h}"] = (S.shift(-h) / S - 1) * 100
    F = F[(F.index.dayofweek == 4) & (F.index >= "1990-03-15") & sma.notna()]
    F["stress"] = F.below & (F.V >= 20)
    F["calm_below"] = F.below & (F.V < 20)
    F["fear_above"] = ~F.below & (F.V >= 20)
    st = F[F.stress]
    F["ep"] = np.nan
    ep = (st.index.to_series().diff().dt.days.fillna(0) > 31).cumsum()
    F.loc[st.index, "ep"] = ep.values
    print(f"Fridays {len(F):,} ({F.index.min().date()} -> {F.index.max().date()}); stress {F.stress.sum()} in {int(ep.max()) + 1} episodes")

    def excess(sub, ctrl, h):
        x = sub[f"f{h}"].dropna(); c = ctrl[f"f{h}"].dropna()
        g = sub.loc[x.index, "ep"]
        mu = x.mean(); s = x.groupby(g).sum(); n = x.groupby(g).size()
        se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
        d = mu - c.mean()
        # block bootstrap over episodes
        eps = g.unique(); bs = []
        grp = {e: x[g == e].values for e in eps}
        for _ in range(2000):
            pick = RNG.choice(eps, len(eps), replace=True)
            bs.append(np.concatenate([grp[e] for e in pick]).mean() - c.mean())
        epm = x.groupby(g).mean() - c.mean()
        return dict(n=len(x), episodes=len(eps), stress_mean=mu, ctrl_mean=c.mean(), excess=d, t=d / se if se > 0 else np.nan,
                    boot_p_le0=(np.array(bs) <= 0).mean(), ep_pos=(epm > 0).mean(), sd_stress=x.std(), sd_ctrl=c.std(),
                    worst=x.min())

    rows = []
    windows = {"HOLDOUT 1990-2009": ("1990-01-01", "2009-12-31"), "2010-2026 (certification era)": ("2010-01-01", "2026-12-31"),
               "ALL 1990-2026": ("1990-01-01", "2026-12-31")}
    for wl, (a, b) in windows.items():
        W = F[(F.index >= a) & (F.index <= b)]
        for h in (20, 5, 45):
            for cl, cm in (("non-stress", ~W.stress), ("below-50 & VIX<20", W.calm_below), ("VIX>=20 & above-50", W.fear_above)):
                if h != 20 and cl != "non-stress":
                    continue
                r = excess(W[W.stress], W[cm], h)
                rows.append(dict(window=wl, h=h, control=cl, **r))
    T = pd.DataFrame(rows)
    print("\n" + T.round(3).to_string(index=False))

    H = T[(T.window.str.startswith("HOLDOUT")) & (T.h == 20) & (T.control == "non-stress")].iloc[0]
    C = T[(T.window.str.startswith("2010")) & (T.h == 20) & (T.control == "non-stress")].iloc[0]
    ok = H.excess > 0 and H.t >= 2 and np.sign(C.excess) == np.sign(H.excess)
    print(f"\nPRIMARY holdout 1990-2009, 20 sessions: excess {H.excess:+.2f}pp, t {H.t:+.2f}, bootstrap P(<=0) {H.boot_p_le0:.3f}; "
          f"2010-26 {C.excess:+.2f}pp (t {C.t:+.2f}) -> {'CONFIRMED' if ok else 'NOT CONFIRMED'}")

    st = F[F.stress].copy()
    st["dec"] = (st.index.year // 10) * 10
    nonst = F[~F.stress]
    dec = st.groupby("dec").f20.agg(["mean", "size"]).join(nonst.assign(dec=(nonst.index.year // 10) * 10).groupby("dec").f20.mean().rename("ctrl"))
    dec["excess"] = dec["mean"] - dec["ctrl"]
    print("\nper decade, 20-session (stress mean, n, control mean, excess):"); print(dec.round(2).to_string())
    g8 = st[(st.index >= "2007-06-01") & (st.index <= "2009-06-30")]
    print(f"\n2008 episode(s) 2007-06 -> 2009-06: {len(g8)} stress Fridays, mean 20s {g8.f20.mean():+.2f}%, worst {g8.f20.min():+.2f}%, "
          f"share of all stress Fridays {len(g8) / len(st):.0%}")
    ex08 = F[~((F.index >= "2007-06-01") & (F.index <= "2009-06-30"))]
    ex08 = ex08[(ex08.index <= "2009-12-31")]
    r = excess(ex08[ex08.stress], ex08[~ex08.stress], 20)
    print(f"holdout WITHOUT 2007-06..2009-06: excess {r['excess']:+.2f}pp t {r['t']:+.2f} ({r['episodes']} episodes)")
    F.to_csv("data/studies/logs/stress_rebound_fridays.csv")


if __name__ == "__main__":
    main()
