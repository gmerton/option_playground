#!/usr/bin/env python3
"""
BEAR-LEG PAIR: sector-momentum 12-1 spread + multi-asset TSMOM, equal-vol, as one hedge sleeve (pre-registered
2026-09-26, before any code or run; Gabe: "I don't think we have any strategies that will help us in a sustained
bear market"). Run 2026-09-26 on Gabe's go; the design below is unchanged from the pre-registration.

WHY NEW. Each sleeve was tested alone, never together:
  sector_overlay_test_2026-09-24  sector 12-1 K3 spread = the ONLY sleeve whose drawdown cut survives de-meaning
                                  (a real hedge); pays 2008 +25.4 / 2020 +16.0 / 2022 +30.8, but LOST -10.3% in
                                  2000-02; costs ~0.14 Sharpe on the book.
  tsmom_bear_leg_2026-09-25       multi-asset TSMOM (family B) = positive in all 4 episodes (2000-02 +29.5, 2008
                                  +16.1, 2020 +0.7, 2022 +13.0) but a priced hedge (~-1.6%/yr vs the assets held
                                  long) whose overlay cut did NOT survive de-meaning.
  The two fail in different places: sector misses the slow 2000-02 bear, TSMOM misses the fast 2020 crash. The
  question is whether the PAIR covers every bear at a lower cost per point of drawdown than either sleeve alone.
  The 2000-02 episode is outside the house book's window (2018-04 ->), so the complementarity can only show on a
  long-history proxy book -- that is the PRIMARY here, and the house-book overlay is the confirmation.

SLEEVES (built by the existing, already-audited functions; nothing re-fit)
  S   run_sector_momentum_spread.spread_series(12, 3): net of 20 bp + borrow (the sector test's PRIMARY).
  T   run_tsmom_bear_leg.family_b(): 12-month sign, inverse-vol, 7 assets, 5 bp/side + 0.25%/yr borrow (its PRIMARY).
  T_A run_tsmom_bear_leg.family_a(SPY, "sma10"): index short-or-flat. EXPLORATORY partner only.
  PAIR = S / sd(S) + T / sd(T), rescaled to the target vol. FIXED 50/50 risk weights declared now -- no weight
  search (a search over weights on ~5 bear episodes would fit the episodes). Vol scaling on the full-sample sd, as
  in both parent overlays (a mild look-ahead in SIZE, not in sign; EXPLORATORY: trailing 36-month sd instead).

PRIMARY (long history)  proxy long book = VFINX total return (S&P 500), monthly, 2000-01 -> 2026-08 (~320 months;
  first month the sector sleeve has a 12-1 signal). Overlay each of {S, T, PAIR} at 50% of the proxy book's vol.
  Episodes (as tsmom_bear_leg): 2000-03->2002-09, 2007-11->2009-02, 2020-02->2020-03, 2022-01->2022-10.
SECONDARY (house book)  exactly as the parent overlays: run_put_overlay_study.book_series() (straddle + bull put +
  breakout) and the no-straddle book, 2018-04 -> 2026-02, sizes 25 / 50 / 100%, PRIMARY 50%.

CONTROLS (declared now)
  (1) each sleeve ALONE at the same vol -- the pair must beat BOTH, or it adds nothing over the better one;
  (2) the DE-MEANED pair (mean set to 0) -- the drawdown cut must be hedging, not the sleeve's own drift (the
      defect that sank the RV sleeve and TSMOM alone);
  (3) a same-vol SPY (VFINX) SHORT -- is the pair better than simply shorting the index?

BAR  (a hedge screen, not a return test; the pair has no return edge to certify -- neither parent does)
  The PAIR is a CANDIDATE only if ALL hold:
  (i)   positive in all 4 episodes standalone, and beats the beta-equivalent index short on aggregate across them;
  (ii)  PRIMARY proxy book at 50%: the DE-MEANED pair cuts maxDD by more than the de-meaned S alone and the
        de-meaned T alone (hedging efficiency: the only reason to hold two sleeves);
  (iii) PRIMARY proxy book at 50%: maxDD falls more than with the same-vol SPY short, and the pair's mean in the proxy
        book's 20 worst months > 0;
  (iv)  SECONDARY house book at 50%, BOTH books: maxDD falls and the de-meaned pair still cuts maxDD (Sharpe may
        fall -- it is insurance -- but report dSharpe per point of maxDD cut vs S alone; the pair must not be the
        more expensive of the two).
  Also reported, not gated: the carry (standalone mean, %/yr) of S, T, PAIR over 2000-2026 -- that IS the premium.
  Multiple testing: one primary pairing (S+T), one primary size (50%). S+T_A and the other sizes are exploratory.
  POWER: ~4 bear episodes in 26 years. A pass is a screen for a paper-tracked sleeve, never an adoption; a fail at
  (ii) means "hold the better single sleeve", not "no hedge exists".

READ  pass -> the pair is the bear leg to paper-track alongside the momentum sleeve, sized by the carry Gabe is
      willing to pay. Fail at (ii) -> the sector sleeve alone remains the only de-meaning-robust hedge.
      Prior: the S-T correlation is low (they fail in different episodes), so (i) is likely to pass; (ii) is the
      real question.

Local vs cloud: local (yfinance monthly closes + two existing sleeve builders; minutes of CPU, no Athena).

Usage (when approved): PYTHONPATH=src:. .venv/bin/python3 run_bear_leg_pair.py > data/studies/logs/bear_leg_pair.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

import run_put_overlay_study as po
import run_sector_momentum_spread as sm
import run_tsmom_bear_leg as ts
from run_sector_overlay_test import score

SIZES, PRIMARY = [0.25, 0.50, 1.00], 0.50
START, END = "2000-01", "2026-08"
EPISODES = ts.EPISODES
OUT = "data/studies/bear_leg_pair_2026-09-26.csv"


def pm(s: pd.Series) -> pd.Series:
    s = s.copy(); s.index = s.index.to_period("M"); return s


def dd(x: pd.Series) -> float:
    c = x.cumsum(); return (c.cummax() - c).max()


def pair(a: pd.Series, b: pd.Series, trailing: bool = False) -> pd.Series:
    idx = a.dropna().index.intersection(b.dropna().index); a, b = a.loc[idx], b.loc[idx]
    if trailing:  # EXPLORATORY: size on the trailing 36-month sd (no look-ahead in size), 24-month minimum
        za = a / a.rolling(36, min_periods=24).std().shift(1); zb = b / b.rolling(36, min_periods=24).std().shift(1)
    else:
        za, zb = a / a.std(), b / b.std()
    p = (za + zb).dropna()
    return p / p.std() * (a.std() + b.std()) / 2  # pair at the parents' average vol, for comparable episode payoffs


def overlay(book: pd.Series, sl: pd.Series, s: float) -> pd.Series:
    idx = book.index.intersection(sl.dropna().index)
    return book.loc[idx] + s * book.loc[idx].std() / sl.loc[idx].std() * sl.loc[idx]


def main() -> None:
    px, mo = ts.load()
    spx = pm(mo["VFINX"].pct_change()).loc[START:END]
    net, _ = sm.spread_series(12, 3)
    S = pm(net).loc[START:END]
    T = pm(ts.family_b(px, mo)).loc[START:END]
    TA = pm(ts.family_a(mo, "SPY", "sma10")).loc[START:END]
    sleeves = {"S sector 12-1": S, "T TSMOM multi": T, "PAIR S+T *P*": pair(S, T),
               "PAIR S+T trailing-vol (expl)": pair(S, T, trailing=True), "PAIR S+T_A (expl)": pair(S, TA),
               "T_A SPY sma10 (expl)": TA}
    idx = spx.index  # window = the PRIMARY sleeves only; exploratory sleeves are scored on their own overlap
    for k in ("S sector 12-1", "T TSMOM multi", "PAIR S+T *P*"): idx = idx.intersection(sleeves[k].dropna().index)
    print(f"common window {idx.min()} -> {idx.max()} ({len(idx)} months); corr(S, T) {S.corr(T):+.2f}, "
          f"corr(S, T_A) {S.corr(TA):+.2f}\n")

    D = pd.DataFrame([ts.describe(k, v.reindex(idx).dropna(), spx) for k, v in sleeves.items()])
    D["carry %/yr"] = D["mean"] * 12
    print("STANDALONE (% per month; carry = mean x 12 -- the premium)")
    print(D[["cell", "n", "mean", "carry %/yr", "t", "h1", "h2", "beta", "alpha", "t_alpha", "yrs_pos"]].round(2).to_string(index=False))
    ecols = ["cell"] + [c for k in EPISODES for c in (k, k + " betaSh")]
    print("\nCRISIS EPISODES (cumulative %, sleeve vs the beta-equivalent S&P short)")
    print(D[ecols].round(1).to_string(index=False))

    # ---- PRIMARY: proxy long book = VFINX, overlay at 25/50/100% of its vol ----
    book = 100 * spx.loc[idx]
    rows = []
    def add(name, sl):
        for s in [0.0] + SIZES:
            b = book if s == 0 else overlay(book, sl, s)
            w20 = book.nsmallest(20).index
            rows.append(dict(sleeve=name, size="none" if s == 0 else f"{int(s*100)}%" + (" *P*" if s == PRIMARY else ""),
                             mean=b.mean(), sharpe=b.mean() / b.std() * np.sqrt(12), maxDD=dd(b),
                             worst=b.min(), mean_w20=np.nan if s == 0 else sl.loc[w20].mean(),
                             **{k: b.loc[a:e].sum() for k, (a, e) in EPISODES.items()}))
            if s == 0: return
    add("VFINX book alone", book)
    for k in ["S sector 12-1", "T TSMOM multi", "PAIR S+T *P*", "PAIR S+T trailing-vol (expl)", "PAIR S+T_A (expl)"]:
        sl = 100 * sleeves[k].reindex(idx).dropna()
        for tag, x in ((k, sl), ("  de-meaned " + k.split()[0] + (" " + k.split()[1] if k.startswith("PAIR") else ""), sl - sl.mean())):
            for s in SIZES:
                b = overlay(book, x, s); w20 = book.nsmallest(20).index
                rows.append(dict(sleeve=tag, size=f"{int(s*100)}%" + (" *P*" if s == PRIMARY else ""), mean=b.mean(),
                                 sharpe=b.mean() / b.std() * np.sqrt(12), maxDD=dd(b), worst=b.min(),
                                 mean_w20=x.reindex(w20).mean(), **{e: b.loc[a:z].sum() for e, (a, z) in EPISODES.items()}))
    for s in SIZES:
        b = overlay(book, -book, s)
        rows.append(dict(sleeve="  SPY short (control)", size=f"{int(s*100)}%" + (" *P*" if s == PRIMARY else ""), mean=b.mean(),
                         sharpe=b.mean() / b.std() * np.sqrt(12), maxDD=dd(b), worst=b.min(), mean_w20=-book.nsmallest(20).mean(),
                         **{e: b.loc[a:z].sum() for e, (a, z) in EPISODES.items()}))
    R = pd.DataFrame(rows); b0 = R.iloc[0]
    R["dSharpe"], R["dDD"] = R.sharpe - b0.sharpe, R.maxDD - b0.maxDD
    print(f"\nPRIMARY -- VFINX proxy book {idx.min()} -> {idx.max()}, overlay sized to % of the book's vol "
          f"(maxDD = % of the cumulative sum; mean_w20 = sleeve %/mo in the book's 20 worst months)")
    print(R[["sleeve", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "mean_w20"] + list(EPISODES)].round(2).to_string(index=False))
    R.assign(part="proxy").to_csv(OUT, index=False)
    g = lambda name: R[(R.sleeve.str.strip() == name) & R["size"].str.contains(r"\*P\*")].iloc[0]

    # ---- SECONDARY: the house book, exactly as the parent overlays ----
    try:
        Bk = po.book_series()
    except FileNotFoundError as e:
        print(f"\nSECONDARY -- BLOCKED: house-book inputs missing ({e.filename}); criterion (iv) NOT EVALUATED")
        Bk = None
    if Bk is None:
        Pd = D.set_index("cell").loc["PAIR S+T *P*"]; eps = list(EPISODES)
        c1 = all(Pd[k] > 0 for k in eps) and sum(Pd[k] for k in eps) > sum(Pd[k + " betaSh"] for k in eps)
        dP, dS, dT = g("de-meaned PAIR S+T"), g("de-meaned S"), g("de-meaned T")
        pr, sh = g("PAIR S+T *P*"), g("SPY short (control)")
        crit = {"(i) + in all 4 episodes & beats beta-short": c1,
                f"(ii) de-meaned DD cut: PAIR {dP.dDD:+.1f} vs S {dS.dDD:+.1f}, T {dT.dDD:+.1f}": dP.dDD < dS.dDD and dP.dDD < dT.dDD,
                f"(iii) PAIR dDD {pr.dDD:+.1f} vs SPY short {sh.dDD:+.1f}; mean in worst-20 {pr.mean_w20:+.2f}": pr.dDD < sh.dDD and pr.mean_w20 > 0}
        print("\nBAR (i)-(iii); (iv) blocked:"); [print(f"  {'PASS' if v else 'FAIL'}  {k}") for k, v in crit.items()]
        print(f"\nVERDICT: {'NOT A CANDIDATE' if not all(crit.values()) else 'PASSES (i)-(iii); (iv) PENDING'}\n-> {OUT}")
        return
    P100 = 100 * sleeves["PAIR S+T *P*"]; S100 = 100 * S; T100 = 100 * T; sp = 100 * spx
    hidx = Bk.index.intersection(P100.dropna().index).intersection(S100.index).intersection(T100.dropna().index)
    Bk = Bk.loc[hidx]
    z = Bk[["bullput", "breakout"]] / Bk[["bullput", "breakout"]].std()
    nb = z.sum(axis=1); nb = nb / nb.std() * po.BOOK_VOL
    parts = []
    for lab, bk in (("full book", Bk.book), ("no-straddle", nb)):
        for nm, x in (("PAIR", P100), ("S alone", S100), ("T alone", T100)):
            x = x.loc[hidx]
            parts += [score(bk, x, lab, nm), score(bk, x - x.mean(), lab, "  de-meaned " + nm)]
        parts.append(score(bk, -sp.loc[hidx], lab, "  SPY short (control)"))
    H = pd.concat(parts, ignore_index=True); H = H[~((H["size"] == "none") & (H.sleeve != "PAIR"))]
    print(f"\nSECONDARY -- house book {hidx.min()} -> {hidx.max()} ({len(hidx)} months)")
    print(H[["book", "sleeve", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "y2020", "y2022"]].round(2).to_string(index=False))
    H.assign(part="house").to_csv(OUT, mode="a", index=False)
    hg = lambda lab, name: H[(H.book == lab) & (H.sleeve.str.strip() == name) & H["size"].str.contains(r"\*P\*")].iloc[0]
    cost = lambda r: (max(0.0, -r.dSharpe) / -r.dDD) if r.dDD < 0 else np.inf

    # ---- verdict per the pre-registered bar ----
    Pd = D.set_index("cell").loc["PAIR S+T *P*"]
    eps = list(EPISODES)
    c1 = all(Pd[k] > 0 for k in eps) and sum(Pd[k] for k in eps) > sum(Pd[k + " betaSh"] for k in eps)
    dP, dS, dT = g("de-meaned PAIR S+T"), g("de-meaned S"), g("de-meaned T")
    c2 = dP.dDD < dS.dDD and dP.dDD < dT.dDD
    pr, sh = g("PAIR S+T *P*"), g("SPY short (control)")
    c3 = pr.dDD < sh.dDD and pr.mean_w20 > 0
    c4 = {}
    for lab in ("full book", "no-straddle"):
        p_, d_, s_ = hg(lab, "PAIR"), hg(lab, "de-meaned PAIR"), hg(lab, "S alone")
        c4[lab] = bool(p_.dDD < 0 and d_.dDD < 0 and cost(p_) <= cost(s_))
        print(f"{lab}: Sharpe lost per maxDD point cut -- PAIR {cost(p_):.3f} vs S alone {cost(s_):.3f}")
    crit = {"(i) + in all 4 episodes & beats beta-short": c1,
            f"(ii) de-meaned DD cut: PAIR {dP.dDD:+.1f} vs S {dS.dDD:+.1f}, T {dT.dDD:+.1f}": c2,
            f"(iii) PAIR dDD {pr.dDD:+.1f} vs SPY short {sh.dDD:+.1f}; mean in worst-20 {pr.mean_w20:+.2f}": c3,
            "(iv) house full book": c4["full book"], "(iv) house no-straddle": c4["no-straddle"]}
    print("\nBAR:"); [print(f"  {'PASS' if v else 'FAIL'}  {k}") for k, v in crit.items()]
    print(f"\nVERDICT: {'CANDIDATE' if all(crit.values()) else 'NOT A CANDIDATE'}\n-> {OUT}")


if __name__ == "__main__":
    main()
