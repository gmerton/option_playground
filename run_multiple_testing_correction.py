#!/usr/bin/env python3
"""
Ledger-wide multiple-testing correction (2026-09-22; method-upgrades queue item 1, from the AI Pathways review).

Unit = one research question (a TEST_INDEX row). Every row counts toward M, including the ~90 nulls/fails, which
enter with p = 1 (they were tested; they just didn't find anything). Only rows we ACT on (in book, adopted, parked,
or used as a veto) need a p, and those are curated below with the row's headline t and k = the number of variants
the row itself tried to get that t (within-row search). Within-row search is charged with Sidak: p_k = 1-(1-p)^k.

Three lenses, all two-sided normal p from t:
  BH-FDR  q = 0.05 and 0.10 over M (Benjamini-Hochberg: expected share of false discoveries among the kept)
  Holm    familywise 0.05 over M (no false discovery at all, ~95% of the time)
  HLZ     Harvey-Liu-Zhu 2016 "new factor" hurdle: raw |t| >= 3.0
M is uncertain (what counts as a test?): row-level M = 125 (TEST_INDEX §1-9 rows that ran a test, excluding
headers, playbook status lines, queued and not-tested reviews), cell-level stress M = 400 (every recorded cell,
pattern-ledger rows included). Verdicts:
  CONFIRMED   survives BH q=0.05 at M=125 AND at M=400
  SUPPORTED   survives BH q=0.05 at M=125 only, or q=0.10 at both
  WEAK        survives only BH q=0.10 at M=125
  NOT CERTIFIED  none of the above
  NO t ON FILE   the claim has no recorded test statistic -> cannot be certified until one is computed

Usage: .venv/bin/python3 run_multiple_testing_correction.py   (prints the table; write-up in data/studies/multiple_testing_correction_2026-09-22.md)
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy.stats import norm

# (group, claim, headline t, k variants in-row, what we do with it, source row)
C = [
    # --- in book ---
    ("book", "Straddle + bull put PAIR (50/50 blend, monthly)", 2.5, 3, "in book", "§0 pair; capital_allocation_framework"),
    ("book", "7-DTE straddle, both gates, after costs (hold)", 3.7, 8, "in book", "straddle_recenter_study (arms x DTE)"),
    ("book", "Bull put spread leg alone (monthly)", 1.2, 1, "in book (pair leg)", "§0 pair"),
    ("book", "Precision-tier breakout, close entry, cap 20 (date-clustered)", 3.3, 10, "in book", "precision_tier_control; tier picked in adhikary validation"),
    ("book", "  same, MONTH-weighted (2026-09-22)", -0.04, 1, "caveat", "oneil pyramid run"),
    ("book", "Size lever = exclusion (A+B only, +0.29R OOS)", None, 3, "in book", "size_lever_2026-09-18 (no t)"),
    ("book", "SPX condors / QQQ-SPY bull puts by regime (Tier A/B)", None, 30, "in book", "playbook_review (no t)"),
    ("book", "SPY double calendar / IWM put calendar (Tier B)", None, 6, "in book", "calendar playbooks (no t)"),
    # --- index-option discoveries ---
    ("index", "SPY negative dealer gamma -> +8% realised vol beyond VIX", 7.7, 3, "vol input", "§7 GEX regime"),
    ("index", "SPY 1-day SHORT straddle on positive-gamma days", 5.6, 2, "-> fly paper trade", "§2 gex_spy_straddle"),
    ("index", "SPY 1-day 2x iron fly on positive-gamma days", 3.4, 2, "paper trading from 9/22", "§2 iron fly"),
    ("index", "SPY 1-day put credit spread on positive-gamma days", 3.5, 2, "logged, not traded", "§2 condor/put spread"),
    ("index", "Gamma edge holds on weekdays only (not a weekend artefact)", 3.9, 1, "robustness", "§2 weekend"),
    ("index", "10-day variance risk premium (IV > realised)", 8.9, 3, "mechanism", "§1 VRP panel"),
    ("index", "QQQ noise-band momentum, negative-gamma days", 2.92, 2, "UNDERPOWERED near miss", "§5"),
    # --- parked ---
    ("parked", "HYB-B universe (TT at $100M + ADR>=4)", 2.6, 4, "PARKED", "§4 universe test"),
    ("parked", "Earnings drift good+MUTED (ledger)", 2.65, 6, "PARKED", "pattern ledger"),
    ("parked", "PEAD tape signal on the straddle pool", 1.89, 2, "PARKED", "§9 PEAD"),
    ("parked", "Earnings vol premium, liquid names, at the bid", 1.1, 3, "PARKED", "§9 earnings vol premium"),
    ("parked", "Retrace entry vs breakout", 0.48, 6, "PARKED", "§9 retrace"),
    ("parked", "Gap-share selection sort (edge vs same-name control)", 1.71, 9, "PARKED", "§5 gap share"),
    ("parked", "Event-convexity 0.12d over 0.25d at real fills", 0.29, 2, "strike choice", "§2 event convexity"),
    ("parked", "Event convexity calls vs random dates", None, 4, "lottery sizing", "event_convexity (no t)"),
    ("parked", "Sleeping Giants cheap LEAPs", None, 3, "MARGINAL", "(no t)"),
    ("parked", "Paid-to-wait put spreads, IV >= 60th pct gate", None, 4, "MARGINAL", "paid_to_wait (no t)"),
    # --- adopted mechanics / vetoes (claims that CHANGE behaviour) ---
    ("veto/mech", "Buy the CLOSE, not an intraday entry (paired)", 3.4, 4, "house process", "§4 entry study"),
    ("veto/mech", "ORB9 stop floor 0.6 ADR", 3.4, 4, "adopted", "§5 ORB9 stop floor"),
    ("veto/mech", "Alert-price entry worse than the close entry", 3.2, 2, "alerts = info only", "§5 alert funnel"),
    ("veto/mech", "Tightening a stop when extended INVERTS (10-EMA)", 4.8, 8, "veto", "§4 profit lock"),
    ("veto/mech", "Leading-group filter INVERTS (bottom-3 > top-3)", 2.6, 3, "veto / context only", "§7 rotation"),
    ("veto/mech", "Closing a put spread on the break costs", 5.8, 1, "never close on the break", "paid_to_wait"),
    ("veto/mech", "Earnings calendar loses at every back leg (liquid, limit fill)", 3.3, 3, "veto", "§9 earnings calendar"),
    ("veto/mech", "Event call as a debit spread: 2nd leg friction", 5.51, 2, "veto", "§9 event spread"),
    ("veto/mech", "Intraday alert arms lose (Stage A stop-close)", 4.3, 5, "no day-trading book", "§5 Stage A"),
    ("veto/mech", "VWAP double-rejection short worse than random", 6.2, 2, "veto", "§5"),
    ("veto/mech", "Straddle -50% stop is a cost (0/20 variants beat hold)", None, 20, "stop removed", "stop_path/sweep (no single t)"),
]
D = pd.DataFrame(C, columns=["group", "claim", "t", "k", "use", "source"])
D["p"] = D.t.map(lambda t: 2 * norm.sf(abs(t)) if t is not None and np.isfinite(t) else np.nan)
D["p_k"] = 1 - (1 - D.p) ** D.k


def bh_keep(pk: pd.Series, M: int, q: float) -> pd.Series:
    """BH over M hypotheses; the M - len(known) unlisted rows enter with p = 1."""
    known = pk.dropna().sort_values()
    thr = [(i + 1) / M * q for i in range(len(known))]
    passed = [p <= t for p, t in zip(known.values, thr)]
    kmax = max([i for i, ok in enumerate(passed) if ok], default=-1)
    keep = pd.Series(False, index=pk.index); keep.loc[known.index[:kmax + 1]] = True
    return keep


def holm_keep(pk: pd.Series, M: int, a: float = 0.05) -> pd.Series:
    known = pk.dropna().sort_values(); keep = pd.Series(False, index=pk.index)
    for i, (ix, p) in enumerate(known.items()):
        if p <= a / (M - i): keep[ix] = True
        else: break
    return keep


for M in (125, 400):
    for q in (0.05, 0.10):
        D[f"BH{int(q*100)}_M{M}"] = bh_keep(D.p_k, M, q)
    D[f"Holm_M{M}"] = holm_keep(D.p_k, M)
D["HLZ_t3"] = D.t.map(lambda t: t is not None and np.isfinite(t) and abs(t) >= 3.0)


def verdict(r):
    if r.t is None or not np.isfinite(r.t): return "NO t ON FILE"
    if r.BH5_M125 and r.BH5_M400: return "CONFIRMED"
    if r.BH5_M125 or (r.BH10_M125 and r.BH10_M400): return "SUPPORTED"
    if r.BH10_M125: return "WEAK"
    return "NOT CERTIFIED"


D["verdict"] = D.apply(verdict, axis=1)
# t needed to survive, as a reference line
def t_needed(M, q, k, rank):
    p = rank / M * q; p1 = 1 - (1 - p) ** (1 / k); return norm.isf(p1 / 2)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
show = D[["group", "claim", "t", "k", "p_k", "BH5_M125", "BH10_M125", "BH5_M400", "Holm_M125", "HLZ_t3", "verdict"]]
print(show.to_string(index=False, float_format=lambda x: f"{x:.2g}"))
print("\nreference: Bonferroni-style t needed for ONE claim at k=1: M=125 ->", round(norm.isf(0.05 / 125 / 2), 2),
      "; M=400 ->", round(norm.isf(0.05 / 400 / 2), 2))
print(D.verdict.value_counts().to_string())

# markdown write-up table
lines = ["| group | claim | t | k | Šidák p | BH 5% M125 | BH 10% M125 | BH 5% M400 | Holm M125 | |t|≥3 | verdict | use |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
yn = lambda b: "✓" if b else "·"
for r in D.itertuples():
    tt = "—" if r.t is None or not np.isfinite(r.t) else f"{r.t:+.2f}"
    pk = "—" if not np.isfinite(r.p_k) else f"{r.p_k:.1e}"
    lines.append(f"| {r.group} | {r.claim.strip()} | {tt} | {r.k} | {pk} | {yn(r.BH5_M125)} | {yn(r.BH10_M125)} | {yn(r.BH5_M400)} | {yn(r.Holm_M125)} | {yn(r.HLZ_t3)} | **{r.verdict}** | {r.use} |")
print("\n".join(lines))
D.to_csv("data/studies/multiple_testing_correction_2026-09-22.csv", index=False)
