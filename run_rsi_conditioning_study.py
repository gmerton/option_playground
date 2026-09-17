# RSI(14) as a conditioning variable on the two surviving strategies + Ryan's RSI swing on SPY/QQQ.
# Pre-registered before looking at results:
#   RSI = Wilder 14 on adjusted daily close, read at the ENTRY-DATE close (same timestamp as the option marks).
#   Buckets <30, 30-40, 40-50, 50-60, 60-70, >=70.  Primary contrast: RSI<40 vs the rest.
#   Ryan signal = RSI<=35 AND close < lower Bollinger(20,2); "Ryan full" adds close>SMA200 and QQQ>SMA200.
#   Hurdle for a new variable: |t| >= 3 on the week-clustered contrast (several cuts are being looked at).
import pandas as pd, numpy as np, statsmodels.formula.api as smf
pd.set_option("display.width", 250)
SP = "data/cache/"

C = pd.read_parquet(SP + "rsi_closes.parquet").sort_index()

def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)

feat = {}
for t in C:
    s = C[t].dropna()
    if len(s) < 60: continue
    f = pd.DataFrame({"close": s, "rsi": rsi(s)})
    f.loc[f.index[:50], "rsi"] = np.nan                       # warm-up
    mid = s.rolling(20).mean(); sd = s.rolling(20).std()
    f["below_bb"] = s < mid - 2 * sd
    f["above_200"] = s > s.rolling(200).mean()
    f.loc[s.rolling(200).mean().isna(), "above_200"] = np.nan
    feat[t] = f
F = pd.concat(feat, names=["ticker", "entry_date"]).reset_index()
qqq = feat["QQQ"][["above_200"]].rename(columns={"above_200": "qqq_above_200"})
F = F.merge(qqq, left_on="entry_date", right_index=True, how="left")

BINS = [-1, 30, 40, 50, 60, 70, 101]; LABS = ["<30", "30-40", "40-50", "50-60", "60-70", ">=70"]

def attach(df):
    d = df.merge(F, on=["ticker", "entry_date"], how="left")
    d["bucket"] = pd.cut(d.rsi, BINS, labels=LABS, right=False)
    d["low40"] = (d.rsi < 40).astype(int)
    d["ryan"] = ((d.rsi <= 35) & d.below_bb.astype(bool)).astype(int)
    d["ryan_full"] = (d.ryan.astype(bool) & (d.above_200 == 1) & (d.qqq_above_200 == 1)).astype(int)
    d["week"] = d.entry_date.dt.to_period("W-FRI").astype(str)
    return d

def stats(x):
    if len(x) < 30: return dict(n=len(x))
    roc = pd.Series(x.roc.values); d = pd.Series(pd.to_datetime(x.entry_date).values)
    w = roc.groupby(d.dt.to_period("W-FRI")).mean(); mo = roc.groupby(d.dt.to_period("M")).mean()
    cut = roc.quantile(0.99)
    return dict(n=len(x), mean=roc.mean(), median=roc.median(), win=100 * (roc > 0).mean(),
                t_week=w.mean() / w.std() * np.sqrt(len(w)) if len(w) > 2 else np.nan,
                t_month=mo.mean() / mo.std() * np.sqrt(len(mo)) if len(mo) > 2 else np.nan,
                ex_top1=roc[roc < cut].mean())

def table(d, col):
    rows = {"ALL": stats(d)}
    for k, g in d.groupby(col, observed=True): rows[str(k)] = stats(g)
    return pd.DataFrame(rows).T.apply(pd.to_numeric, errors="coerce").round(2)

def contrast(d, var):
    """roc ~ var, SE clustered by entry week. Pooled = timing + selection; week-demeaned = selection only."""
    d = d.dropna(subset=["rsi"]).copy()
    out = {}
    m = smf.ols(f"roc ~ {var}", d).fit(cov_type="cluster", cov_kwds={"groups": d.week})
    out["pooled"] = (m.params[var], m.tvalues[var])
    d["roc_dm"] = d.roc - d.groupby("week").roc.transform("mean")
    d[var + "_dm"] = d[var] - d.groupby("week")[var].transform("mean")
    m2 = smf.ols(f"roc_dm ~ {var}_dm - 1", d).fit(cov_type="cluster", cov_kwds={"groups": d.week})
    out["within_week"] = (m2.params[var + "_dm"], m2.tvalues[var + "_dm"])
    return {k: f"coef {v[0]:+.2f}  t {v[1]:+.2f}" for k, v in out.items()}

def by_year(d, var):
    y = d.groupby([d.entry_date.dt.year, var]).roc.mean().unstack()
    y["delta"] = y.get(1) - y.get(0)
    y["n_flag"] = d.groupby(d.entry_date.dt.year)[var].sum()
    return y.round(1)

# ================= A. ETF bull put spreads (45 DTE 0.35/0.25, take 50%, no stop) =================
R = pd.read_parquet("data/cache/etf_condor_recon.parquet")
R = R[R.side == "put"].copy()
R["entry_date"] = pd.to_datetime(R.entry_date)
R["cw"] = R.net_credit_mid / (R.short_strike - R.long_strike).abs()
R = R[(R.cw <= 0.50) & (R.margin >= 0.10) & (R.exit_type != "missing")]
R = R[pd.to_datetime(R.expiry) <= pd.Timestamp("2026-03-31")]
R = R[R.roc <= 100 * R.net_credit_mid / R.margin + 1e-6]           # ROC-ceiling filter (condor study §0)
A = attach(R)
print(f"\n##### A. ETF BULL PUT SPREADS  rows {len(A):,}, RSI coverage {A.rsi.notna().mean():.1%}")
print(table(A, "bucket").to_string())
print("\nRyan signal (RSI<=35 & below lower BB):"); print(table(A, "ryan").to_string())
print("\nRyan full (+ name>200d & QQQ>200d):"); print(table(A, "ryan_full").to_string())
for v in ["low40", "rsi", "ryan", "ryan_full"]: print(f"contrast {v:10s}", contrast(A, v))
print("\nby year, RSI<40 (1) vs rest (0):"); print(by_year(A, "low40").to_string())

# ================= B. 7-DTE long straddle (both gates) =================
L = pd.read_parquet("data/cache/straddle_recenter/leg_decomp.parquet")
L = L[L.pass_both].drop(columns=["close"]).rename(columns={"straddle": "roc"})
B = attach(L)
print(f"\n##### B. 7-DTE LONG STRADDLE  rows {len(B):,}, RSI coverage {B.rsi.notna().mean():.1%}")
print(table(B, "bucket").to_string())
B["extreme"] = ((B.rsi < 30) | (B.rsi >= 70)).astype(int)
print("\nextreme RSI (<30 or >=70) vs middle:"); print(table(B, "extreme").to_string())
for v in ["low40", "rsi", "extreme"]: print(f"contrast {v:10s}", contrast(B, v))
top = B.roc >= B.roc.quantile(0.99)
print("\nwhere the top-1% trades sit vs all trades (share %):")
print(pd.DataFrame({"all": B.bucket.value_counts(normalize=True), "top1pct": B[top].bucket.value_counts(normalize=True)}).mul(100).round(1).reindex(LABS).to_string())
print("\nby year, extreme (1) vs middle (0):"); print(by_year(B, "extreme").to_string())
# call leg too: the straddle study found always-call beats the straddle; does RSI route it?
B2 = B.assign(roc=B.call_only)
print("\ncall leg only, by bucket:"); print(table(B2, "bucket")[["n", "mean", "median", "win", "t_week", "ex_top1"]].to_string())
B3 = B.assign(roc=B.put_only)
print("\nput leg only, by bucket:"); print(table(B3, "bucket")[["n", "mean", "median", "win", "t_week", "ex_top1"]].to_string())

# ================= C. Ryan's RSI swing on SPY / QQQ (underlying; the LEAP/stock vehicle) =================
H = [5, 10, 21, 42, 63]
print("\n##### C. RSI SWING ON SPY / QQQ  (forward return from signal-day close, % ; excess = minus all-days mean)")
for t in ["SPY", "QQQ"]:
    f = feat[t].copy()
    f["qqq_up"] = qqq.reindex(f.index).qqq_above_200
    for h in H: f[f"fwd{h}"] = 100 * (f.close.shift(-h) / f.close - 1)
    sig = {"RSI<=30": f.rsi <= 30,
           "RSI<=35 & <lowerBB (Ryan)": (f.rsi <= 35) & f.below_bb,
           "Ryan + >200d": (f.rsi <= 35) & f.below_bb & (f.above_200 == 1),
           "RSI>=70 (overbought)": f.rsi >= 70}
    f = f[f.rsi.notna()]
    for era, (a, b) in {"full": (None, None), "to 2009": (None, "2009-12-31"), "2010+": ("2010-01-01", None)}.items():
        g = f.loc[a:b]
        rows = []
        for name, s in sig.items():
            s = s.reindex(g.index).fillna(False).astype(bool)
            for h in [10, 21, 63]:
                base = g[f"fwd{h}"].dropna()
                # non-overlapping events: after a fire, ignore fires for h days
                idx, last = [], -10**9
                pos = np.flatnonzero(s.values)
                for p in pos:
                    if p - last >= h: idx.append(p); last = p
                ev = g[f"fwd{h}"].iloc[idx].dropna()
                if len(ev) < 5: rows.append(dict(signal=name, h=h, events=len(ev))); continue
                ex = ev - base.mean()
                rows.append(dict(signal=name, h=h, events=len(ev), fwd=ev.mean(), base=base.mean(), excess=ex.mean(),
                                 hit=100 * (ev > 0).mean(), base_hit=100 * (base > 0).mean(),
                                 t_excess=ex.mean() / ev.std() * np.sqrt(len(ev)), worst=ev.min()))
        print(f"\n{t}  {era}  ({g.index.min().date()} -> {g.index.max().date()})")
        print(pd.DataFrame(rows).round(2).to_string(index=False))

A.to_parquet(SP + "rsi_putspread.parquet"); B.to_parquet(SP + "rsi_straddle.parquet")
