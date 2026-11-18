"""POST-HOC re-score of run_leader_reentry_loop.py (2026-11-17), labelled as such: NOT the pre-registered metric.
Reason: the pre-registered metric sums LOG daily returns, which docks each arm ~sigma^2/2 per unit of exposure
(volatility drag of a single high-vol name). B1-A then mostly measures B1's extra exposure x drag, not the
re-entry rule. A diversified book of equal-dollar positions earns ~the ARITHMETIC mean, so the re-score uses, per
event, sum over in-position days of (stock simple return - SPY simple return), minus 10 bp per side. Same events,
arms, inference (month means, NW lag 12), halves and bars as the pre-registration.
Also reports excess per 100 in-position days (return per unit of exposure)."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd, yfinance as yf
import run_leader_reentry_loop as L
if len(sys.argv) > 1 and sys.argv[1] == 'liquid':      # robustness: liquid_panel_2009 (adjusted, survivors)
    def _load():
        p = pd.read_parquet('data/cache/liquid_panel_2009.parquet'); p['date'] = pd.to_datetime(p.date)
        C = p.pivot(index='date', columns='ticker', values='close').sort_index()
        return C, p.pivot(index='date', columns='ticker', values='dolvol').reindex_like(C)
    L.load = _load; L.OUT = 'data/studies/leader_reentry_loop_2026-11-17_liquid'
C, V = L.load(); idx = C.index
spy = yf.download('SPY', start='2009-01-01', auto_adjust=True, progress=False)['Close'].squeeze()
spy.index = pd.to_datetime(spy.index).tz_localize(None); spy = spy.reindex(idx).ffill()
spy_r = (spy / spy.shift(1) - 1).fillna(0).values
e21 = C.ewm(span=21, adjust=False, ignore_na=True).mean(); s50 = C.rolling(50, min_periods=40).mean()
hi50 = C.shift(1).rolling(50, min_periods=45).max()
ev = pd.read_csv(L.OUT + '_events.csv', parse_dates=['date'])
col_of = {t: j for j, t in enumerate(C.columns)}; pos_of = {d: i for i, d in enumerate(idx)}
Cv, E, S, Hh = C.values, e21.values, s50.values, hi50.values
for k in ('A', 'B1', 'B2', 'B3', 'C'): ev[f'ar_{k}'] = np.nan
out = {k: [] for k in ('A', 'B1', 'B2', 'B3', 'C')}
for r in ev.itertuples():
    j, i0 = col_of[r.ticker], pos_of[r.date]; i1 = i0 + r.days; sl = slice(i0, i1 + 1)
    c = pd.Series(Cv[sl, j]).ffill().values; sr = np.r_[0, c[1:] / c[:-1] - 1]
    for k in out:
        _, mk, tr = L.simulate(c, E[sl, j], S[sl, j], Hh[sl, j], k)
        out[k].append((sr[mk] - spy_r[sl][mk]).sum() - 2 * L.COST * tr)
for k in out: ev[f'ar_{k}'] = out[k]
ev.to_csv(L.OUT + '_events_posthoc.csv', index=False)
lines = ['', '## POST-HOC re-score: ARITHMETIC excess (not pre-registered; see run_leader_reentry_loop_posthoc.py)', '',
         '| cell | mean | t_NW | 2011-17 | 2018-25 | years same sign | bar |', '|---|---|---|---|---|---|---|']
for name, a, b, bar in [('B1 - A', 'B1', 'A', 3.0), ('B1 - C', 'B1', 'C', 3.2), ('B2 - A', 'B2', 'A', 3.2),
                        ('B3 - A', 'B3', 'A', 3.2), ('B3 - C', 'B3', 'C', 3.2)]:
    d = ev[f'ar_{a}'] - ev[f'ar_{b}']; mm = d.groupby(ev.date.dt.to_period('M')).mean(); t = L.nw_t(mm.values)
    h1, h2 = d[ev.year < L.SPLIT].mean(), d[ev.year >= L.SPLIT].mean(); yr = d.groupby(ev.year).mean()
    same = (np.sign(yr) == np.sign(d.mean())).sum(); ok = abs(t) >= bar and np.sign(h1) == np.sign(h2) and same > len(yr) / 2
    lines.append(f'| {name} | {d.mean():+.4f} | {t:+.2f} | {h1:+.4f} | {h2:+.4f} | {same}/{len(yr)} | {"PASS" if ok else "fail"} (|t|>={bar}) |')
lines += ['', '| arm | arithmetic excess per event | t_NW (vs 0) | excess per 100 in-position days | exposure |', '|---|---|---|---|---|']
for k in out:
    x = ev[f'ar_{k}']; mm = x.groupby(ev.date.dt.to_period('M')).mean()
    lines.append(f'| {k} | {x.mean():+.4f} | {L.nw_t(mm.values):+.2f} | {x.sum() / (ev[f"exp_{k}"] * ev.days).sum() * 100:+.4f} | {ev[f"exp_{k}"].mean():.0%} |')
txt = '\n'.join(lines) + '\n'; open(L.OUT + '.md', 'a').write(txt); print(txt)
