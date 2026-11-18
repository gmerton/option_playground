"""Former-leader chart study (DESCRIPTIVE, hypothesis-generating only) -- 2026-11-17.

Source: data/top_gainers/*.csv (top 250 US gainers over 1Y / 3Y / 5Y windows ending 2026-06-03), bars from
data/cache/top_gainers_daily.parquet (run_top_gainers_pull.py, yfinance adjusted).

Prompt (Gabe, via Ariel Hernandez): study the charts of former leaders for entry/exit tactics -- EMAs, volume,
pullbacks vs breakouts -- at the daily/weekly level, from a human perspective first. Repeatable only: every
event below is defined on information available at that bar's close (no "buy the low").

⚠ OUTCOME-CONDITIONED BY CONSTRUCTION. Every name is a winner chosen by its end-point return. Anything that looks
like a rule here ("pullbacks held the 21 EMA") is also true of names that failed, at an unknown rate. These
statistics can only (a) describe what a winner's path looked like, (b) say what a rule would have COST on a
winner (shakeouts, giveback, missed move). They cannot show that a rule selects winners. That is a separate test
on the full population, and several have been run (TEST_INDEX rows on pullback-vs-breakout, volume at the low,
level triggers).

Run = window start close (S) -> the max close inside [S, 2026-06-03] (P). 'After' = P -> 2026-11-17.
Outputs: data/studies/top_gainers_chart_study_2026-11-17_runs.csv (one row per list x name)
         data/studies/charts/top_gainers/<list>_<rank>_<ticker>.png for the fixed 24-name sample.
"""
import glob, os, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

END = pd.Timestamp('2026-06-03')
STARTS = {'1y': '2025-06-04', '3y': '2023-06-05', '5y': '2021-06-04'}
CHART_DIR = 'data/studies/charts/top_gainers'; os.makedirs(CHART_DIR, exist_ok=True)

bars = pd.read_parquet('data/cache/top_gainers_daily.parquet')
bars['date'] = pd.to_datetime(bars['date']).dt.tz_localize(None)
bars = bars.sort_values(['ticker', 'date'])


def prep(d):
    d = d.set_index('date').copy()
    c = d.close
    d['e10'] = c.ewm(span=10, adjust=False).mean(); d['e21'] = c.ewm(span=21, adjust=False).mean()
    d['s50'] = c.rolling(50).mean(); d['s200'] = c.rolling(200).mean()
    tr = pd.concat([d.high - d.low, (d.high - c.shift()).abs(), (d.low - c.shift()).abs()], axis=1).max(axis=1)
    d['atr'] = tr.rolling(14).mean()
    d['v50'] = d.volume.rolling(50).mean()
    d['hi252'] = c.rolling(252, min_periods=120).max().shift(1)   # prior 52w high close
    d['hi50'] = c.rolling(50).max().shift(1)
    return d


def weekly(d):
    w = d[['open', 'high', 'low', 'close', 'volume']].resample('W-FRI').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    w['s10'] = w.close.rolling(10).mean(); w['s40'] = w.close.rolling(40).mean()
    return w


def pullbacks(r):
    """Pullbacks inside the run: from a closing high to the next new closing high, depth >= 1.5 ATR on closes.
    Support class = deepest MA the lowest CLOSE stayed above (a close-based, after-the-fact label)."""
    out, peak_i, peak_c = [], 0, r.close.iloc[0]
    for i in range(1, len(r) + 1):
        c = r.close.iloc[i] if i < len(r) else np.inf
        if c > peak_c:
            seg = r.iloc[peak_i + 1:i]
            if len(seg):
                lo = seg.close.idxmin(); x = seg.loc[lo]; atr = r.atr.iloc[peak_i]
                depth_atr = (peak_c - x.close) / atr if atr > 0 else np.nan
                if depth_atr >= 1.5:
                    lvl = ('above_e10' if x.close >= x.e10 else 'held_e21' if x.close >= x.e21 else
                           'held_s50' if x.close >= x.s50 else 'held_s200' if x.close >= x.s200 else 'broke_s200')
                    out.append(dict(depth_pct=1 - x.close / peak_c, depth_atr=depth_atr, days=len(seg),
                                    level=lvl, vol_ratio=seg.volume.mean() / r.v50.iloc[peak_i]))
            if i < len(r): peak_i, peak_c = i, c
    return out


def exit_rule(r_after, kind):
    """First trigger on/after the bar given; returns (date, close)."""
    if kind == 'e21': m = r_after.close < r_after.e21
    elif kind == 's50': m = r_after.close < r_after.s50
    elif kind == 's50x2': m = (r_after.close < r_after.s50) & (r_after.close.shift() < r_after.s50.shift())
    else: raise ValueError
    m = m[m]
    return (m.index[0], r_after.close.loc[m.index[0]]) if len(m) else (None, np.nan)


rows = []
for lst, start in STARTS.items():
    tbl = pd.read_csv(glob.glob(f'data/top_gainers/top250_gainers_{lst}_*.csv')[0])
    for _, t in tbl.iterrows():
        d = bars[bars.ticker == t.ticker]
        if d.empty: continue
        d = prep(d); S = pd.Timestamp(start)
        run = d.loc[S:END]
        if len(run) < 60 or run.atr.isna().all(): continue
        P = run.close.idxmax(); r = run.loc[:P]
        c0, cP = r.close.iloc[0], r.close.loc[P]
        logmove = np.log(cP / c0)
        frac_left = lambda dt: np.log(cP / d.close.loc[dt]) / logmove if dt is not None and logmove > 0 else np.nan
        # --- launch events (all knowable at the close) ---
        nh = r[r.close > r.hi252]; first_nh = nh.index[0] if len(nh) else None
        rc = r[(r.close > r.s50) & (r.s50 > r.s50.shift(5)) & (r.close.shift() <= r.s50.shift())]
        first_reclaim = rc.index[0] if len(rc) else None
        nh_day = d.loc[first_nh] if first_nh is not None else None
        # --- run behaviour ---
        pb = pullbacks(r)
        lv = pd.Series([p['level'] for p in pb]).value_counts()
        up, dn = r.close.diff() > 0, r.close.diff() < 0
        bo = r[r.close > r.hi50]
        w = weekly(d); wr = w.loc[S:P]
        ext = ((r.close - r.s50) / r.atr).max()
        # --- exits: shakeouts during the run, and giveback from P at the first trigger after P ---
        after = d.loc[P:]
        shake = {k: int(m.sum()) for k, m in {
            'e21': (r.close < r.e21) & (r.close.shift() >= r.e21.shift()),
            's50': (r.close < r.s50) & (r.close.shift() >= r.s50.shift()),
            'w10': (wr.close < wr.s10) & (wr.close.shift() >= wr.s10.shift())}.items()}
        gb = {}
        for k in ['e21', 's50', 's50x2']:
            dt, px = exit_rule(after.iloc[1:], k); gb[k] = 1 - px / cP if dt is not None else np.nan
        wa = w.loc[P:].iloc[1:]; wm = wa[wa.close < wa.s10]
        gb['w10'] = 1 - wm.close.iloc[0] / cP if len(wm) else np.nan
        last = d.close.iloc[-1]
        rows.append(dict(
            list=lst, rank=t['rank'], ticker=t.ticker, sector=t.sector, pct_gain=t.pct_gain,
            run_days=len(r), peak_date=P.date(), peak_frac_of_window=len(r) / len(run),
            start_vs_s200=c0 / r.s200.iloc[0] - 1 if pd.notna(r.s200.iloc[0]) else np.nan,
            start_off_hi252=c0 / r.hi252.iloc[0] - 1 if pd.notna(r.hi252.iloc[0]) else np.nan,
            days_to_first_52wh=(r.index.get_loc(first_nh) if first_nh is not None else np.nan),
            move_left_at_first_52wh=frac_left(first_nh),
            first_52wh_rvol=(nh_day.volume / nh_day.v50) if nh_day is not None and nh_day.v50 > 0 else np.nan,
            move_left_at_first_s50_reclaim=frac_left(first_reclaim),
            n_pullbacks=len(pb),
            pb_above_e10=lv.get('above_e10', 0), pb_held_e21=lv.get('held_e21', 0), pb_held_s50=lv.get('held_s50', 0),
            pb_held_s200=lv.get('held_s200', 0), pb_broke_s200=lv.get('broke_s200', 0),
            pb_median_depth_pct=np.median([p['depth_pct'] for p in pb]) if pb else np.nan,
            pb_max_depth_pct=max([p['depth_pct'] for p in pb]) if pb else np.nan,
            pb_median_depth_atr=np.median([p['depth_atr'] for p in pb]) if pb else np.nan,
            pb_median_vol_ratio=np.median([p['vol_ratio'] for p in pb]) if pb else np.nan,
            run_max_dd=(1 - r.close / r.close.cummax()).max(),
            pct_closes_above_e21=(r.close > r.e21).mean(), pct_closes_above_s50=(r.close > r.s50).mean(),
            pct_weeks_above_w10=(wr.close > wr.s10).mean(),
            updown_vol_ratio=r.volume[up].mean() / r.volume[dn].mean(),
            breakout50_median_rvol=(bo.volume / bo.v50).median(),
            max_ext_atr_over_s50=ext,
            shake_e21=shake['e21'], shake_s50=shake['s50'], shake_w10=shake['w10'],
            giveback_e21=gb['e21'], giveback_s50=gb['s50'], giveback_s50x2=gb['s50x2'], giveback_w10=gb['w10'],
            after_peak_to_now=last / cP - 1,
        ))

df = pd.DataFrame(rows)
df.to_csv('data/studies/top_gainers_chart_study_2026-11-17_runs.csv', index=False)
print('runs', len(df), 'names', df.ticker.nunique())


# ---------------- charts: fixed sample (top 4 of each list + 4 random from ranks 100-250, seed 17) ----------------
def chart(lst, rank, tk):
    d = prep(bars[bars.ticker == tk]); S = pd.Timestamp(STARTS[lst]); w = weekly(d)
    ws = w.loc[S - pd.Timedelta(weeks=52):]
    run = d.loc[S:END]; P = run.close.idxmax()
    dd = d.loc[P - pd.Timedelta(days=400):P + pd.Timedelta(days=120)]
    fig, ax = plt.subplots(4, 1, figsize=(14, 11), gridspec_kw={'height_ratios': [3, 1, 3, 1]})
    for a, x, cols in [(ax[0], ws, [('s10', 'tab:blue', '10wk'), ('s40', 'tab:red', '40wk')]),
                       (ax[2], dd, [('e10', 'tab:green', 'EMA10'), ('e21', 'tab:blue', 'EMA21'), ('s50', 'tab:red', 'SMA50')])]:
        up = x.close >= x.open
        a.vlines(x.index, x.low, x.high, color=np.where(up, 'g', 'r'), lw=0.8)
        a.scatter(x.index, x.close, s=3, c=np.where(up, 'g', 'r'))
        for c, col, lab in cols: a.plot(x.index, x[c], color=col, lw=1, label=lab)
        a.set_yscale('log'); a.legend(loc='upper left', fontsize=8); a.grid(alpha=.3)
        a.axvline(S, color='k', ls=':'); a.axvline(P, color='purple', ls='--'); a.axvline(END, color='k', ls=':')
    for a, x in [(ax[1], ws), (ax[3], dd)]:
        a.bar(x.index, x.volume, width=5 if x is ws else 1, color=np.where(x.close >= x.open, 'g', 'r'))
        a.plot(x.index, x.volume.rolling(10 if x is ws else 50).mean(), color='k', lw=0.8)
    ax[0].set_title(f'{tk}  {lst.upper()} #{rank}  weekly (window dotted, peak dashed)')
    ax[2].set_title(f'{tk}  daily around the peak {P.date()}')
    fig.tight_layout(); fig.savefig(f'{CHART_DIR}/{lst}_{rank:03d}_{tk.replace(".", "-")}.png', dpi=70); plt.close(fig)


rng = np.random.default_rng(17)
for lst in STARTS:
    sub = df[df.list == lst]
    pick = list(sub[sub['rank'] <= 4].itertuples()) + list(
        sub[sub['rank'] >= 100].iloc[rng.choice(len(sub[sub['rank'] >= 100]), 4, replace=False)].itertuples())
    for t in pick: chart(lst, t.rank, t.ticker)
print('charts ->', CHART_DIR)
