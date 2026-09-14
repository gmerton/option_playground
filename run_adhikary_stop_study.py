#!/usr/bin/env python3
"""
Where does the initial stop go on an Adhikary (Tito) breakout? Same events as run_adhikary_validation.py
(A_breakout15 = close clears the 15-session pivot, RVOL >= 1.1, upper-half close, stacked >= 5d, no catalyst
gap; plus the validated PRECISION cohort: ADR 4-7, within 15% of the 52wk high, stack 5-40d), same exit
(first daily close under the 20 EMA, capped at 60 sessions). Only the INITIAL stop changes:

  entry_low     close under the entry bar's low                (the harness default)
  entry_low_ID  intraday: any low under the entry bar's low, filled at the stop (or the open if gapped through)
  pivot         close back under the breakout pivot            (failed breakout)
  piv-0.5adr    close under pivot - 0.5 ADR                    (what the LVL alert prints)
  piv-1adr      close under pivot - 1.0 ADR
  base_low10    close under the lowest low of the 10 sessions before entry (last contraction low)
  fixed5/8      close 5% / 8% under the entry
  sma10         close under the 10-day SMA (from day 1)
  trail_only    no initial stop: the 20 EMA close trail alone

Per rule: mean / median return, win rate, how often the initial stop (not the trail) took you out, average
win and loss, profit factor, return in ADR units (scale-free), R = return / initial risk, and the FALSE-STOP
rate: trades the rule stopped that trail_only would have closed as winners. Halves (2019-22 / 2023-26) for
stability. Plus the winners' heat: how far under the entry the eventual trail_only winners traded (close and
intraday low), in ADR units -- the stop has to live outside that.

Usage: PYTHONPATH=src python run_adhikary_stop_study.py [--panel path] [--out data/studies/adhikary_stop_study.md]
"""
from __future__ import annotations
import argparse, warnings
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
HORIZON = 60


def md(df: pd.DataFrame) -> str:
    """Markdown table without the tabulate dependency."""
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for ix, r in df.iterrows():
        out.append("| " + " | ".join([str(ix)] + [f"{v:.2f}" if isinstance(v, (float, np.floating)) else str(v) for v in r.values]) + " |")
    return "\n".join(out)


def simulate(Cv, Ov, Hv, Lv, E20v, S10v, i, j, rule, stop0):
    """Return (ret, days, stopped_by_initial). Exit at close under the active stop, else under the 20 EMA."""
    entry = Cv[i, j]
    stop = stop0
    for k in range(i + 1, min(i + HORIZON + 1, len(Cv))):
        c, o, l = Cv[k, j], Ov[k, j], Lv[k, j]
        if not np.isfinite(c):
            continue
        if rule == "sma10":
            stop = S10v[k, j]
        if rule == "entry_low_ID":
            if np.isfinite(l) and l < stop:
                fill = o if (np.isfinite(o) and o < stop) else stop
                return fill / entry - 1, k - i, 1
        elif np.isfinite(stop) and c < stop:
            return c / entry - 1, k - i, 1
        if c < E20v[k, j]:
            return c / entry - 1, k - i, 0
    k = min(i + HORIZON, len(Cv) - 1)
    return Cv[k, j] / entry - 1, k - i, 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", default="data/cache/liquid_panel_2019.parquet")
    ap.add_argument("--out", default="data/studies/adhikary_stop_study.md"); a = ap.parse_args()
    raw = pd.read_parquet(a.panel); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    O = O.reindex(index=C.index, columns=C.columns)
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    s10, s20, s50 = C.rolling(10).mean(), C.rolling(20).mean(), C.rolling(50).mean(); e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52, lo52 = H.shift(1).rolling(252, min_periods=120).max(), L.shift(1).rolling(252, min_periods=120).min(); range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max(); avgv = V.shift(1).rolling(50).mean(); rvol = V / avgv
    stacked = (s10 > s20) & (s20 > s50)
    arr = stacked.astype(int).values.copy()
    for i in range(1, len(arr)): arr[i] = np.where(arr[i] > 0, arr[i - 1] + 1, 0)
    stack_days = pd.DataFrame(arr, index=C.index, columns=C.columns)
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    base_low10 = L.shift(1).rolling(10).min()
    gate = (adr >= 3) & (range52 >= 17) & elig
    A = gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)
    off52 = (C / hi52 - 1) * 100
    P = A & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)
    Cv, Ov, Hv, Lv, E20v, S10v = C.values, O.values, H.values, L.values, e20.values, s10.values
    ADRv, PIVv, BLv = adr.values, piv15.values, base_low10.values
    idx = C.index
    rules = ["entry_low", "entry_low_ID", "pivot", "piv-0.5adr", "piv-1adr", "base_low10", "fixed5", "fixed8", "sma10", "trail_only"]

    def stop_for(rule, i, j):
        e, lo, pv, ad, bl = Cv[i, j], Lv[i, j], PIVv[i, j], ADRv[i, j], BLv[i, j]
        return {"entry_low": lo, "entry_low_ID": lo, "pivot": pv, "piv-0.5adr": pv * (1 - 0.5 * ad / 100), "piv-1adr": pv * (1 - ad / 100),
                "base_low10": bl, "fixed5": e * 0.95, "fixed8": e * 0.92, "sma10": S10v[i, j], "trail_only": np.nan}[rule]

    lines = [f"# Adhikary breakout: initial-stop study\n", f"*{pd.Timestamp.today().date()}. `run_adhikary_stop_study.py` on the liquid panel "
             f"({C.shape[1]} names, {idx[0].date()}..{idx[-1].date()}), events 2019-10 on. Entry = breakout close; exit = first close under the 20 EMA "
             f"(capped {HORIZON} sessions) unless the initial stop hits first. Survivorship as in the validation doc: read the comparisons, not the levels.*\n"]
    for cname, M in (("A_breakout15 (every recipe breakout)", A), ("PRECISION cohort (ADR 4-7, <15% off high, stack 5-40)", P)):
        mm = M.fillna(False).astype(bool); mm = mm[mm.index >= "2019-10-01"]
        ii, jj = np.where(mm.values); ii = ii + (len(C) - len(mm))
        d = idx[ii]; adr_e = ADRv[ii, jj]
        res = {}
        for rule in rules:
            out = np.array([simulate(Cv, Ov, Hv, Lv, E20v, S10v, i, j, rule, stop_for(rule, i, j)) for i, j in zip(ii, jj)])
            risk = np.array([(Cv[i, j] - stop_for(rule, i, j)) / Cv[i, j] * 100 if rule != "trail_only" else np.nan for i, j in zip(ii, jj)])
            res[rule] = (out, risk)
        base_ret = res["trail_only"][0][:, 0]
        rows = []
        for rule in rules:
            out, risk = res[rule]; ret = out[:, 0] * 100; stp = out[:, 2] == 1
            valid = np.isfinite(ret) & (np.isnan(risk) | (risk > 0))
            ret, stp, rk, ad, yr, br = ret[valid], stp[valid], risk[valid], adr_e[valid], d.year.values[valid], base_ret[valid] * 100
            wins, losses = ret[ret > 0], ret[ret <= 0]
            R = ret / rk if rule != "trail_only" else np.full_like(ret, np.nan)
            early = yr <= 2022
            rows.append(dict(rule=rule, n=len(ret), risk_med=np.nanmedian(rk), ret=ret.mean(), ret_med=np.median(ret), win=100 * (ret > 0).mean(),
                             stopped=100 * stp.mean(), avg_win=wins.mean() if len(wins) else 0, avg_loss=losses.mean() if len(losses) else 0,
                             PF=wins.sum() / -losses.sum() if losses.sum() < 0 else np.inf, ret_adr=(ret / ad).mean(),
                             R=np.nanmean(R), R_med=np.nanmedian(R), false_stop=100 * (stp & (br > 0)).mean(),
                             ret_adr_19_22=(ret[early] / ad[early]).mean(), ret_adr_23_26=(ret[~early] / ad[~early]).mean()))
        t = pd.DataFrame(rows).set_index("rule").round(2)
        lines.append(f"\n## {cname}: n = {len(ii)}\n"); lines.append(md(t)); lines.append("")
        lines.append("`risk_med` = median initial risk % from entry; `stopped` = % exited by the initial stop (not the trail); `ret_adr` = mean return "
                     "in ADR units; `R` = return / initial risk; `false_stop` = % of ALL trades the stop took out that the trail alone would have closed green.\n")
        print(f"\n=== {cname}: n={len(ii)} ==="); print(t.to_string())
        # winners' heat under trail_only
        out = res["trail_only"][0]; win = out[:, 0] > 0
        mae_c, mae_l = [], []
        for (i, j), w, days in zip(zip(ii, jj), win, out[:, 1]):
            if not w: continue
            e = Cv[i, j]; k1 = i + 1; k2 = min(i + int(days) + 1, len(Cv))
            cs, ls = Cv[k1:k2, j], Lv[k1:k2, j]
            cs, ls = cs[np.isfinite(cs)], ls[np.isfinite(ls)]
            if len(cs) == 0: continue
            mae_c.append((cs.min() / e - 1) * 100 / ADRv[i, j]); mae_l.append((ls.min() / e - 1) * 100 / ADRv[i, j])
        mae_c, mae_l = np.array(mae_c), np.array(mae_l)
        q = [50, 70, 80, 90, 95]
        ht = pd.DataFrame({"pctile": q, "worst close vs entry (ADR)": np.percentile(mae_c, [100 - x for x in q]), "worst low vs entry (ADR)": np.percentile(mae_l, [100 - x for x in q])}).set_index("pctile").round(2)
        lines.append(f"\n### Winners' heat ({cname.split(' (')[0]}): how far under the entry the eventual trail_only winners traded, n = {len(mae_c)}\n")
        lines.append("Row = share of winners whose worst point stayed ABOVE this level; a stop inside it ejects the rest.\n"); lines.append(md(ht)); lines.append("")
        lines.append(f"Winners that never closed under the entry: {100 * (mae_c >= 0).mean():.0f}%; never traded under it intraday: {100 * (mae_l >= 0).mean():.0f}%.\n")
        print(ht.to_string()); print(f"never closed under entry {100 * (mae_c >= 0).mean():.0f}% | never traded under {100 * (mae_l >= 0).mean():.0f}%")
    open(a.out, "w").write("\n".join(lines) + "\n"); print("wrote", a.out)


if __name__ == "__main__":
    main()
