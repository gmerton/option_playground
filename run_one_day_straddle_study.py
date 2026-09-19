#!/usr/bin/env python3
"""
1-DTE long ATM straddle study (the COHR 9/17 trade, generalized). Design agreed 2026-09-18, run 2026-09-19.

Trade: at the CLOSE the day before an expiry, buy the ATM straddle (call + put at the strike whose call delta is
nearest 0.50) at the ASK. Thesis: when the stock's recent realized moves are much larger than the one-day move the
straddle implies, the option market is underpricing a fresh vol regime, and the expiry-day MORNING is where the
straddle pays (it mean-reverts by the close).

Data: silver.options_daily_v3 (real bid/ask; rows with quotes end mid-July 2026), universe = the liquid daily
panel (data/cache/liquid_panel_2019.parquet, 1,743 names, split-adjusted). The panel is adjusted and v3 strikes are
not, so each trade's scale factor f = panel_close / raw_spot with raw_spot from put-call parity (K + C_mid - P_mid).

Exits (all settled from the UNDERLYING, so crash weeks are never truncated -- feedback_test_crash_weeks):
  open     intrinsic at the expiry-day open (the mechanical morning exit; the winning leg is sold, 1 leg traded)
  extreme  intrinsic at the day's best extreme (upper bound on any morning exit; 1 leg traded)
  close    intrinsic at the close (hold-to-settlement baseline; nothing traded, no exit cost)
Costs: lib.studies.costs.sim_cost (IBKR commission + 25% of the entry bid/ask on every traded side).
Return = P&L / premium paid (the straddle ask). Hurdle: the 0DTE long-strangle base rate, -26%/trade.

Gate: ratio of recent realized moves to the implied move: mean and max |close/close - 1| over the 5 sessions ending
at the entry close, divided by (straddle mid / spot). Reported by ratio bucket, by year (2020 + 2022 shown), both
halves, month-clustered t. Also the mean-reversion claim itself: is |open - K| > |close - K| on expiry day?

1-min calibration: the 2026 intraday cache (192 names, Feb-Sep) says what a 10:00 / 10:30 / 11:00 exit captures
between the open and the extreme, with K = the prior close (no chain needed for the shape of the day).

Usage: AWS_PROFILE=... PYTHONPATH=src .venv/bin/python3 run_one_day_straddle_study.py [--no-pull] [--years 2019-2026]
Writes data/studies/one_day_straddle/{quotes_<y>,trades}.parquet and data/studies/one_day_straddle_study.md.
"""
from __future__ import annotations
import argparse, sys, warnings
from datetime import date
from pathlib import Path
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
OUT = Path("data/studies/one_day_straddle"); OUT.mkdir(parents=True, exist_ok=True)
REPORT = Path("data/studies/one_day_straddle_study.md")
PANEL = "data/cache/liquid_panel_2019.parquet"
MIN1 = Path("data/cache/intraday_1min")
HURDLE = -0.26
OVERNIGHT_VAR_SHARE = 0.25


def bs_straddle(S, K, sig):
    """Call + put, r = 0, sig = sigma*sqrt(T) for the remaining horizon (vectorised, no scipy)."""
    from math import erf
    S = np.asarray(S, float); K = np.asarray(K, float); sig = np.maximum(np.asarray(sig, float), 1e-6)
    d1 = (np.log(S / K) + 0.5 * sig ** 2) / sig; d2 = d1 - sig
    N = np.vectorize(lambda x: 0.5 * (1.0 + erf(x / np.sqrt(2.0))))
    call = S * N(d1) - K * N(d2); put = K * N(-d2) - S * N(-d1)
    return call + put
BUCKETS = [(0, 1.0, "<1.0"), (1.0, 1.5, "1.0-1.5"), (1.5, 2.0, "1.5-2.0"), (2.0, 3.0, "2.0-3.0"), (3.0, 99, ">=3.0")]


# ---------------------------------------------------------------- pull
def pull(years: list[int]) -> pd.DataFrame:
    from lib.athena_lib import athena
    frames = []
    for y in years:
        f = OUT / f"quotes_{y}.parquet"
        if f.exists():
            frames.append(pd.read_parquet(f)); continue
        print(f"  pulling {y} ...", flush=True)
        d = athena(f"""SELECT ticker, trade_date, expiry, strike, cp, bid, ask, delta, open_interest, volume
                      FROM silver.options_daily_v3
                      WHERE bid > 0 AND ask >= bid AND abs(delta) BETWEEN 0.30 AND 0.70
                        AND date_diff('day', trade_date, expiry) = 1
                        AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'""")
        d.to_parquet(f, index=False); frames.append(d)
        print(f"    {len(d):,} rows", flush=True)
    q = pd.concat(frames, ignore_index=True)
    q["trade_date"] = pd.to_datetime(q["trade_date"]); q["expiry"] = pd.to_datetime(q["expiry"])
    return q


# ---------------------------------------------------------------- trades
def build_trades(q: pd.DataFrame) -> pd.DataFrame:
    from lib.studies.costs import sim_cost
    P = pd.read_parquet(PANEL, columns=["date", "ticker", "open", "high", "low", "close"])
    P["date"] = pd.to_datetime(P["date"]); P = P.sort_values(["ticker", "date"])
    q = q[q.ticker.isin(P.ticker.unique())].copy()
    # one ATM strike per (ticker, day): the call nearest 0.50 delta that also has a quoted put at that strike
    c = q[q.cp == "C"].copy(); p = q[q.cp == "P"].copy()
    c["dd"] = (c.delta - 0.5).abs()
    c = c.sort_values("dd").drop_duplicates(["ticker", "trade_date", "strike"])
    p = p.drop_duplicates(["ticker", "trade_date", "strike"])
    m = c.merge(p[["ticker", "trade_date", "strike", "bid", "ask", "delta", "open_interest"]], on=["ticker", "trade_date", "strike"], suffixes=("_c", "_p"))
    m = m.sort_values("dd").drop_duplicates(["ticker", "trade_date"])
    # underlying: entry close + prior closes (realized), expiry-day OHLC
    P["ret"] = P.groupby("ticker")["close"].pct_change().abs()
    P["rv5_mean"] = P.groupby("ticker")["ret"].transform(lambda s: s.rolling(5).mean())
    P["rv5_max"] = P.groupby("ticker")["ret"].transform(lambda s: s.rolling(5).max())
    P["rv20_mean"] = P.groupby("ticker")["ret"].transform(lambda s: s.rolling(20).mean())
    ent = P.rename(columns={"date": "trade_date", "close": "close_t"})[["ticker", "trade_date", "close_t", "rv5_mean", "rv5_max", "rv20_mean"]]
    ex = P.rename(columns={"date": "expiry", "open": "open_e", "high": "high_e", "low": "low_e", "close": "close_e"})[["ticker", "expiry", "open_e", "high_e", "low_e", "close_e"]]
    t = m.merge(ent, on=["ticker", "trade_date"]).merge(ex, on=["ticker", "expiry"])
    t["c_mid"] = (t.bid_c + t.ask_c) / 2; t["p_mid"] = (t.bid_p + t.ask_p) / 2
    t["spot_raw"] = t.strike + t.c_mid - t.p_mid                      # put-call parity, 1 day, r ~ 0
    t["f"] = t.close_t / t.spot_raw                                   # adjusted / raw scale (splits, dividends)
    t = t[(t.spot_raw > 0) & (t.f > 0)]
    # sanity on the ATM pick and the scale: strike within 4% of raw spot, f a clean split-ish factor or ~1
    t["moneyness"] = t.strike / t.spot_raw - 1
    t = t[t.moneyness.abs() <= 0.04]
    t["entry"] = t.ask_c + t.ask_p                                     # per share, raw units, at the ask
    t["entry_mid"] = t.c_mid + t.p_mid
    t["implied_move"] = t.entry_mid / t.spot_raw
    t["ratio_mean"] = t.rv5_mean / t.implied_move; t["ratio_max"] = t.rv5_max / t.implied_move
    t["ratio20"] = t.rv20_mean / t.implied_move
    # exits: panel prices converted to raw units, intrinsic vs the strike
    for col in ("open_e", "high_e", "low_e", "close_e"):
        t[col + "_raw"] = t[col] / t.f
    t["x_open"] = (t.open_e_raw - t.strike).abs()
    t["x_close"] = (t.close_e_raw - t.strike).abs()
    t["x_extreme"] = np.maximum(t.high_e_raw - t.strike, t.strike - t.low_e_raw).clip(lower=0)
    # fair-value open exit: the options still carry the session's time value at 09:30. Price the straddle at the open
    # with the intraday share of the day's variance left (OVERNIGHT_VAR_SHARE of the implied variance is spent by the
    # gap; panel 2019-26: mean |open-K| 0.95% vs |close-K| 1.98% -> ~23%). sigma_day from the entry straddle
    # (ATM straddle ~ 0.7979 * S * sigma * sqrt(T)); both legs are sold, so both pay exit costs.
    sig = t.implied_move / 0.7979 * np.sqrt(1.0 - OVERNIGHT_VAR_SHARE)
    t["x_open_fv"] = bs_straddle(t.open_e_raw, t.strike, sig)
    ba = list(zip(t.ask_c - t.bid_c, t.ask_p - t.bid_p))
    t["cost_traded"] = [sim_cost(b, 1, 2) for b in ba]                # open / extreme: sell the winning leg
    t["cost_settle"] = [sim_cost(b, 0, 2) for b in ba]                # close: settle at expiry
    t["cost_two"] = [sim_cost(b, 2, 2) for b in ba]                   # fair-value open exit: both legs sold
    t["ret_open_fv"] = (t.x_open_fv - t.entry - t.cost_two) / t.entry
    t["ret_open"] = (t.x_open - t.entry - t.cost_traded) / t.entry
    t["ret_extreme"] = (t.x_extreme - t.entry - t.cost_traded) / t.entry
    t["ret_close"] = (t.x_close - t.entry - t.cost_settle) / t.entry
    t["ret_open_gross"] = (t.x_open - t.entry) / t.entry
    t["ret_close_gross"] = (t.x_close - t.entry) / t.entry
    t["morning_beats_close"] = t.x_open > t.x_close
    t["gap_pct"] = (t.open_e / t.close_t - 1).abs(); t["move_pct"] = (t.close_e / t.close_t - 1).abs()
    t["year"] = t.trade_date.dt.year; t["ym"] = t.trade_date.dt.to_period("M").astype(str)
    t["dow"] = t.expiry.dt.day_name().str[:3]
    t["bucket"] = pd.cut(t.ratio_max, [b[0] for b in BUCKETS] + [99.0], labels=[b[2] for b in BUCKETS], right=False)
    t["bucket_mean"] = pd.cut(t.ratio_mean, [b[0] for b in BUCKETS] + [99.0], labels=[b[2] for b in BUCKETS], right=False)
    return t.reset_index(drop=True)


# ---------------------------------------------------------------- stats
def ct(x: pd.Series, cl: pd.Series) -> tuple[float, float, int]:
    """mean, cluster-robust t (clusters = year-month), n clusters."""
    x = x.dropna(); cl = cl.loc[x.index]
    if len(x) < 20: return x.mean() if len(x) else np.nan, np.nan, cl.nunique()
    e = x - x.mean(); s = e.groupby(cl).sum()
    se = np.sqrt((s ** 2).sum()) / len(x)
    return x.mean(), x.mean() / se if se > 0 else np.nan, cl.nunique()


def line(t: pd.DataFrame, label: str, arms=("ret_open", "ret_open_fv", "ret_extreme", "ret_close")) -> str:
    if len(t) == 0: return f"| {label} | 0 | | | | | | | |"
    cells = [label, f"{len(t):,}"]
    for a in arms:
        m, tt, _ = ct(t[a], t.ym); cells.append(f"{m*100:+.1f}% (t {tt:+.1f})" if np.isfinite(tt) else f"{m*100:+.1f}%")
    cells.append(f"{100*(t.ret_open > 0).mean():.0f}%")
    cells.append(f"{100*t.morning_beats_close.mean():.0f}%")
    cells.append(f"{t.implied_move.median()*100:.1f}%")
    return "| " + " | ".join(cells) + " |"


HDR = "| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |\n|---|---|---|---|---|---|---|---|---|"


# ---------------------------------------------------------------- 1-min calibration
def calibrate_1min(P: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    prev = P.sort_values(["ticker", "date"]).copy()
    prev["prev_close"] = prev.groupby("ticker")["close"].shift(1)
    prev["ret"] = prev.groupby("ticker")["close"].pct_change().abs()
    prev["rv5"] = prev.groupby("ticker")["ret"].transform(lambda s: s.rolling(5).mean().shift(1))
    key = prev.set_index(["ticker", "date"])[["prev_close", "close", "rv5"]]
    rows = []
    for f in sorted(MIN1.glob("*.parquet")):
        sym, day = f.stem.rsplit("_", 1)
        try: k = key.loc[(sym, pd.Timestamp(day))]
        except KeyError: continue
        if not np.isfinite(k.prev_close) or k.prev_close <= 0: continue
        b = pd.read_parquet(f)
        if len(b) < 300: continue
        if abs(b.close.iloc[-1] / k.close - 1) > 0.03: continue        # raw vs adjusted scale mismatch
        K = k.prev_close; tm = b.index.time
        def at(hh, mm):
            s = b[tm <= pd.Timestamp(f"{day} {hh:02d}:{mm:02d}").time()]
            return abs(s.close.iloc[-1] - K) / K if len(s) else np.nan
        ext = np.maximum(b.high - K, K - b.low).clip(lower=0) / K
        i_ext = int(ext.values.argmax())
        rows.append(dict(sym=sym, day=pd.Timestamp(day), dow=pd.Timestamp(day).day_name()[:3], rv5=k.rv5,
                         m_open=abs(b.open.iloc[0] - K) / K, m_0945=at(9, 45), m_1000=at(10, 0), m_1030=at(10, 30),
                         m_1100=at(11, 0), m_1200=at(12, 0), m_1400=at(14, 0), m_close=abs(b.close.iloc[-1] - K) / K,
                         m_ext=float(ext.max()), t_ext=b.index[i_ext].strftime("%H:%M"), ext_first_hour=b.index[i_ext].time() <= pd.Timestamp(f"{day} 10:30").time()))
    C = pd.DataFrame(rows)
    if C.empty: return C, "_no 1-min sessions matched the panel_\n"
    C["rv_tercile"] = pd.qcut(C.rv5.rank(method="first"), 3, labels=["low", "mid", "high"])
    arms = ["m_open", "m_0945", "m_1000", "m_1030", "m_1100", "m_1200", "m_1400", "m_close", "m_ext"]
    def blk(x, label):
        mm = x[arms].mean() * 100
        cap = (x[arms].div(x.m_ext, axis=0)).mean() * 100
        beats = {a: 100 * (x[a] > x.m_close).mean() for a in arms if a not in ("m_close", "m_ext")}
        return (f"| {label} | {len(x):,} | " + " | ".join(f"{mm[a]:.2f}" for a in arms) + " |\n"
                f"| &nbsp;&nbsp;share of extreme | | " + " | ".join(f"{cap[a]:.0f}%" for a in arms) + " |\n"
                f"| &nbsp;&nbsp;beats the close | | " + " | ".join(f"{beats.get(a, float('nan')):.0f}%" if a in beats else "" for a in arms) + " |\n")
    s = ("| sessions | n | open | 09:45 | 10:00 | 10:30 | 11:00 | 12:00 | 14:00 | close | extreme |\n|---|---|---|---|---|---|---|---|---|---|---|\n"
         + blk(C, "all cached sessions") + blk(C[C.dow == "Fri"], "Fridays (weekly expiries)")
         + blk(C[C.rv_tercile == "high"], "high prior-5d realized (top tercile)") + blk(C[(C.rv_tercile == "high") & (C.dow == "Fri")], "high realized x Friday"))
    s += f"\nMean |px - K| in % of K (K = prior close). Extreme falls in the first hour (by 10:30) on {100*C.ext_first_hour.mean():.0f}% of sessions; median extreme time {C.t_ext.median() if False else C.t_ext.mode().iloc[0]} (mode).\n"
    return C, s


# ---------------------------------------------------------------- report
def report(t: pd.DataFrame, C_txt: str, P: pd.DataFrame) -> str:
    L = []
    L.append("# 1-DTE long ATM straddle -- the COHR trade, generalized\n")
    L.append(f"_Run {date.today()}. {len(t):,} trades, {t.ticker.nunique():,} names, {t.trade_date.min().date()} to {t.trade_date.max().date()}; "
             f"real bid/ask from `silver.options_daily_v3`, exits settled from the underlying, costs = IBKR commission + 25% of the entry bid/ask per traded side. "
             f"Return = P&L / premium paid. Hurdle: 0DTE long strangle base rate {HURDLE*100:.0f}%/trade._\n")
    L.append("**Trade:** buy the ATM straddle at the ask at the close before expiry. **Exits:** `open` = sell the winning leg at intrinsic at the expiry-day open; "
             "`extreme` = same at the day's best extreme (upper bound); `close` = settle. **Gate:** `ratio_max` = largest |close/close| move in the prior 5 sessions / implied move (straddle mid / spot).\n")
    L.append(f"`open @intrinsic` sells the winning leg at intrinsic at 09:30 (ignores the session's remaining time value -- a floor). "
             f"`open @fair value` sells BOTH legs at a Black-Scholes price with {int((1-OVERNIGHT_VAR_SHARE)*100)}% of the day's implied variance still ahead (the realistic morning sale). "
             "`open win%` and `open>close` use the intrinsic arm.\n")
    L.append("## 1. Base rate and the realized/implied gate (ratio_max buckets)\n"); L.append(HDR)
    L.append(line(t, "ALL"))
    for b in BUCKETS: L.append(line(t[t.bucket == b[2]], f"ratio_max {b[2]}"))
    L.append(""); L.append("By `ratio_mean` (5-day MEAN move / implied):\n"); L.append(HDR)
    for b in BUCKETS: L.append(line(t[t.bucket_mean == b[2]], f"ratio_mean {b[2]}"))
    hi = t[t.ratio_max >= 2.0]; hi3 = t[t.ratio_max >= 3.0]
    L.append("\n## 2. The gated trade by year (ratio_max >= 2.0) -- 2020 and 2022 must appear\n"); L.append(HDR)
    for y, g in hi.groupby("year"): L.append(line(g, str(y)))
    L.append(line(hi[hi.trade_date < hi.trade_date.median()], "half 1")); L.append(line(hi[hi.trade_date >= hi.trade_date.median()], "half 2"))
    L.append("\nUngated, by year:\n"); L.append(HDR)
    for y, g in t.groupby("year"): L.append(line(g, str(y)))
    L.append("\n## 3. Expiry weekday (Fri = weeklies; Mon/Wed = index/ETF and mega-cap dailies)\n"); L.append(HDR)
    for d, g in t.groupby("dow"): L.append(line(g, d))
    L.append("\n## 4. Liquidity cut (both legs' bid/ask as % of the straddle mid)\n"); L.append(HDR)
    t = t.assign(ba_pct=((t.ask_c - t.bid_c) + (t.ask_p - t.bid_p)) / t.entry_mid)
    for lo, hi_, lab in [(0, .05, "<5%"), (.05, .10, "5-10%"), (.10, .20, "10-20%"), (.20, 9, ">20%")]:
        L.append(line(t[(t.ba_pct >= lo) & (t.ba_pct < hi_)], f"bid/ask {lab}"))
    L.append(line(t[(t.ba_pct < .10) & (t.ratio_max >= 2.0)], "bid/ask <10% AND ratio_max >= 2"))
    L.append(line(t[(t.ba_pct < .10) & (t.ratio_max >= 3.0)], "bid/ask <10% AND ratio_max >= 3"))
    L.append("\n## 5. Where the P&L lives (gated, ratio_max >= 2, open @fair value, net)\n")
    r = hi.ret_open_fv.sort_values(ascending=False)
    top = r.head(max(1, len(r) // 100)).sum() / max(1e-9, r.sum()) if r.sum() > 0 else np.nan
    L.append(f"- n {len(r):,}; mean {r.mean()*100:+.1f}%, median {r.median()*100:+.1f}%, p10 {r.quantile(.1)*100:+.1f}%, p90 {r.quantile(.9)*100:+.1f}%, max {r.max()*100:+.0f}%")
    L.append(f"- top 1% of trades = {top*100:.0f}% of the positive sum" if np.isfinite(top) else "- positive sum is zero or negative")
    L.append(f"- ex top 1%: mean {r.iloc[len(r)//100:].mean()*100:+.1f}%")
    L.append(f"- largest expiry-day moves included (no truncation): " + ", ".join(f"{a.ticker} {a.expiry.date()} {a.move_pct*100:+.0f}%" for a in hi.nlargest(5, "move_pct").itertuples()))
    L.append("\n## 6. The mean-reversion claim: is the morning move bigger than the close-to-close move?\n")
    L.append("Share of expiry days with |open - K| > |close - K|, and the mean of each, by gate bucket (trade set):\n")
    L.append("| bucket | n | open>close | mean |open-K| % | mean |close-K| % | mean extreme % | implied % |\n|---|---|---|---|---|---|---|")
    for b in ["ALL"] + [x[2] for x in BUCKETS]:
        g = t if b == "ALL" else t[t.bucket == b]
        if len(g) == 0: continue
        L.append(f"| {b} | {len(g):,} | {100*g.morning_beats_close.mean():.0f}% | {100*(g.x_open/g.spot_raw).mean():.2f} | {100*(g.x_close/g.spot_raw).mean():.2f} | {100*(g.x_extreme/g.spot_raw).mean():.2f} | {100*g.implied_move.mean():.2f} |")
    # the same question on EVERY panel day 2019-2026 (no options needed): does the open overshoot the close?
    D = P.sort_values(["ticker", "date"]).copy(); D["K"] = D.groupby("ticker")["close"].shift(1)
    D = D.dropna(subset=["K"]); D["mo"] = (D.open / D.K - 1).abs(); D["mc"] = (D.close / D.K - 1).abs()
    D["ret"] = (D.close / D.K - 1).abs(); D["rv5"] = D.groupby("ticker")["ret"].transform(lambda s: s.rolling(5).mean().shift(1))
    D = D.dropna(subset=["rv5"]); D["terc"] = pd.qcut(D.rv5.rank(method="first"), 3, labels=["low", "mid", "high"])
    L.append(f"\nAll panel days 2019-2026 ({len(D):,} name-days): open beats close on {100*(D.mo > D.mc).mean():.0f}%; "
             f"mean |open-K| {100*D.mo.mean():.2f}% vs |close-K| {100*D.mc.mean():.2f}%. By prior-5d realized tercile: "
             + "; ".join(f"{k}: {100*(g.mo > g.mc).mean():.0f}% ({100*g.mo.mean():.2f} vs {100*g.mc.mean():.2f})" for k, g in D.groupby("terc")) + ".")
    L.append("\n## 7. 1-min calibration of the morning exit (2026 cache, K = prior close, % of K)\n"); L.append(C_txt)
    L.append("\n## 8. Read\n")
    L.append("_filled in by the reader below the data; see the memory note for the verdict_\n")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--no-pull", action="store_true"); ap.add_argument("--years", default="2019-2026")
    a = ap.parse_args(); y0, y1 = (int(x) for x in a.years.split("-"))
    tf = OUT / "trades.parquet"
    if a.no_pull and tf.exists():
        t = pd.read_parquet(tf)
    else:
        q = pull(list(range(y0, y1 + 1))); print(f"quotes: {len(q):,} rows, {q.ticker.nunique():,} tickers")
        t = build_trades(q); t.to_parquet(tf, index=False)
    print(f"trades: {len(t):,}  names {t.ticker.nunique():,}  {t.trade_date.min().date()} -> {t.trade_date.max().date()}")
    print(f"scale factor f: median {t.f.median():.3f}, share within 1% of 1.0 {100*((t.f-1).abs()<.01).mean():.0f}%")
    P = pd.read_parquet(PANEL, columns=["date", "ticker", "open", "high", "low", "close"]); P["date"] = pd.to_datetime(P["date"])
    C, C_txt = calibrate_1min(P); C.to_parquet(OUT / "calibration_1min.parquet", index=False)
    print(f"1-min sessions: {len(C):,}")
    REPORT.write_text(report(t, C_txt, P)); print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
