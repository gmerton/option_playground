"""Which fresh leaders DOUBLE? A pre-launch fingerprint, fit 2011-18, tested once 2019-25 -- PRE-REGISTERED 2026-11-17
(DISCOVERY track).

Why: the re-entry loop (leader_reentry_loop_2026-11-17.md) showed management can't create the right tail; selection
must. Goal = triple-digit returns, so the outcome is the 12-month RIGHT TAIL, not 20-60d mean R. New axis: no ledger
row predicts a 252-session doubling among fresh 52w-high names; the features' prior tests (ADR floors, base depth
veto, beaten-down long base, intermediate momentum, call bursts) were all 1-60 session horizons on mean returns.

DATA  chain_spot_daily closes + option volume, INCLUDING DELISTED, split-adjusted from pit/splits.parquet. NO
      segment deletion (run_dip_survivorship's >45%-break cleaning removes 26% of ticker-days and with them the
      explosive names). Unexplained |1-day| > 45% moves are flagged: an event is DROPPED if one falls inside its
      feature lookback (756 sessions back); events with one inside the forward window are kept and a sensitivity
      run excludes them.
EVENT as run_leader_reentry_loop: first close > prior 252-close max in 126 sessions, close > SMA50 > SMA200,
      50d mean option volume >= 1,000, close >= $5; per name no new event inside the previous one's 252 sessions.
OUTCOME fwd = close(t+252)/close(t) - 1 (delisting inside: last close). DOUBLE = fwd >= +100%.
      xs = fwd - SPY's simple return over the same dates.
FEATURES (at the event close; each converted to its percentile rank within the event-year):
  adr     20d mean |daily return| (volatility)          ret63   close / close(t-63) - 1
  logpx   log close                                     ret252  close / close(t-252) - 1
  depth3y close / max close of prior 756 - 1            baselen sessions since the previous 52w-high close (cap 756)
  optshift log(mean opt_vol last 20 / mean opt_vol t-270..t-21)
FIT   events dated 2011-01-01 .. 2018-12-31: logistic regression DOUBLE ~ all 7 ranks (no feature selection),
      month-clustered SEs reported for reading only.
TEST  events 2019-01-01 .. 2025-02-14 (the fit never sees them). score = fit linear predictor. Top quintile of score
      within each event-year (Q5) vs the other four (Q1-4).
PRIMARY  mean xs(Q5) - mean xs(Q1-4): average events within each event-month (both groups), difference per month,
      Newey-West t (lag 12). BAR |t| >= 3, both test halves (2019-21 / 2022-25) the same sign, a majority of test
      years the same sign. One pre-specified cell, so no Sidak charge.
REPORTED (not graded): DOUBLE rate Q5 vs Q1-4 and the ratio; test AUC; Q5 mean/median fwd; the sensitivity run without
      forward-break events; per-year.
Output: data/studies/leader_fingerprint_2026-11-17.md + _events.csv
"""
import sys
import numpy as np, pandas as pd, yfinance as yf
import statsmodels.api as sm

sys.path.insert(0, '.')
from run_leader_reentry_loop import nw_t

FIT_END, TEST_START, EV_START, EV_END = pd.Timestamp('2018-12-31'), pd.Timestamp('2019-01-01'), \
    pd.Timestamp('2011-01-01'), pd.Timestamp('2025-02-14')
H, BRK = 252, 0.45
FEATS = ['adr', 'logpx', 'ret63', 'ret252', 'depth3y', 'baselen', 'optshift']
OUT = 'data/studies/leader_fingerprint_2026-11-17'


def load():
    d = pd.read_parquet('data/cache/chain_spot/chain_spot_daily.parquet'); d['trade_date'] = pd.to_datetime(d.trade_date)
    C = d.pivot_table(index='trade_date', columns='ticker', values='spot').sort_index()
    V = d.pivot_table(index='trade_date', columns='ticker', values='opt_vol').reindex_like(C)
    sp = pd.read_parquet('data/cache/pit/splits.parquet'); sp['execution_date'] = pd.to_datetime(sp.execution_date)
    sp = sp[sp.ticker.isin(C.columns) & (sp.split_from > 0) & (sp.split_to > 0)]
    for r in sp.itertuples():
        C.loc[C.index < r.execution_date, r.ticker] /= r.split_to / r.split_from
    return C, V


def main():
    C, V = load(); idx = C.index
    spy = yf.download('SPY', start='2009-01-01', auto_adjust=True, progress=False)['Close'].squeeze()
    spy.index = pd.to_datetime(spy.index).tz_localize(None); spy = spy.reindex(idx).ffill().values
    ret = C / C.ffill().shift(1) - 1
    brk = (ret.abs() > BRK).astype(float)
    brk_back = brk.rolling(756, min_periods=1).sum() > 0
    s50 = C.rolling(50, min_periods=40).mean(); s200 = C.rolling(200, min_periods=160).mean()
    hi252 = C.shift(1).rolling(252, min_periods=240).max()
    newhi = C > hi252
    fresh = newhi & (newhi.astype(float).shift(1).rolling(126, min_periods=1).sum() == 0)
    liq = (V.rolling(50, min_periods=30).mean() >= 1000) & (C >= 5)
    M = (fresh & (C > s50) & (s50 > s200) & liq & ~brk_back).values
    inwin = (idx >= EV_START) & (idx <= EV_END)
    adr = ret.abs().rolling(20, min_periods=15).mean()
    hi756 = C.shift(1).rolling(756, min_periods=252).max()
    vol20 = V.rolling(20, min_periods=15).mean(); vol250 = V.shift(21).rolling(250, min_periods=150).mean()
    Cv, NH, B = C.values, newhi.values, brk.values
    A, H756, V20, V250 = adr.values, hi756.values, vol20.values, vol250.values
    rows = []
    for j in range(Cv.shape[1]):
        cand = np.flatnonzero(M[:, j] & inwin)
        if not len(cand): continue
        col = Cv[:, j]; last = np.flatnonzero(np.isfinite(col)).max(); next_ok = -1
        for i0 in cand:
            if i0 < next_ok: continue
            next_ok = i0 + H; i1 = min(i0 + H, last)
            if i1 <= i0: continue
            c0 = col[i0]; c1 = pd.Series(col[i0:i1 + 1]).ffill().values[-1]
            prev_nh = np.flatnonzero(NH[max(0, i0 - 756):i0, j])
            rows.append(dict(
                ticker=C.columns[j], date=idx[i0], year=idx[i0].year, delisted=i1 < i0 + H,
                fwd=c1 / c0 - 1, spy=spy[i1] / spy[i0] - 1, fwd_brk=bool(np.nansum(B[i0 + 1:i1 + 1, j]) > 0),
                adr=A[i0, j], logpx=np.log(c0), ret63=c0 / col[i0 - 63] - 1 if i0 >= 63 else np.nan,
                ret252=c0 / col[i0 - 252] - 1 if i0 >= 252 else np.nan, depth3y=c0 / H756[i0, j] - 1,
                baselen=(len(np.arange(max(0, i0 - 756), i0)) - prev_nh.max()) if len(prev_nh) else 756,
                optshift=np.log(V20[i0, j] / V250[i0, j]) if V250[i0, j] > 0 and V20[i0, j] > 0 else np.nan))
    ev = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    ev['xs'] = ev.fwd - ev.spy; ev['double'] = (ev.fwd >= 1).astype(int)
    n0 = len(ev); ev = ev.dropna(subset=FEATS + ['fwd']).copy()
    for f in FEATS: ev[f + '_r'] = ev.groupby('year')[f].rank(pct=True)
    R = [f + '_r' for f in FEATS]
    fit, test = ev[ev.date <= FIT_END], ev[ev.date >= TEST_START].copy()
    X = sm.add_constant(fit[R])
    res = sm.Logit(fit.double, X).fit(disp=0, cov_type='cluster', cov_kwds={'groups': fit.date.dt.to_period('M').astype(str).factorize()[0]})
    test['score'] = res.predict(sm.add_constant(test[R]))
    test['q5'] = test.groupby('year').score.rank(pct=True) > 0.8
    ev.merge(test[['ticker', 'date', 'score', 'q5']], how='left').to_csv(OUT + '_events.csv', index=False)

    def primary(t):
        m = t.groupby([t.date.dt.to_period('M'), 'q5']).xs.mean().unstack()
        d = (m[True] - m[False]).dropna()
        yr = t.groupby(['year', 'q5']).xs.mean().unstack(); yd = yr[True] - yr[False]
        h1 = d[d.index.year <= 2021].mean(); h2 = d[d.index.year >= 2022].mean()
        return d.mean(), nw_t(d.values), h1, h2, (np.sign(yd) == np.sign(d.mean())).sum(), len(yd), yd

    from sklearn.metrics import roc_auc_score
    L = [f'# Which fresh leaders double? Fingerprint fit 2011-18, tested 2019-25 ({pd.Timestamp.today().date()})', '',
         f'Pre-registration: docstring of `run_leader_fingerprint.py`. Events {n0:,} ({len(ev):,} with all features); '
         f'fit {len(fit):,} (double rate {fit.double.mean():.1%}), test {len(test):,} (double rate {test.double.mean():.1%}).', '',
         '## Fit coefficients (logit on within-year ranks; month-clustered z, for reading only)', '',
         '| feature | coef | z |', '|---|---|---|']
    for f in R: L.append(f'| {f[:-2]} | {res.params[f]:+.2f} | {res.tvalues[f]:+.2f} |')
    L += [f'', f'Fit AUC {roc_auc_score(fit.double, res.predict(X)):.3f}; **test AUC {roc_auc_score(test.double, test.score):.3f}**.', '']
    for label, t in [('PRIMARY (all test events)', test), ('Sensitivity: excluding forward-break events', test[~test.fwd_brk])]:
        mu, tt, h1, h2, same, ny, yd = primary(t)
        ok = abs(tt) >= 3 and np.sign(h1) == np.sign(h2) and same > ny / 2
        q5, rest = t[t.q5], t[~t.q5]
        L += [f'## {label}', '',
              f'- xs(Q5) − xs(Q1-4) = **{mu:+.2%}/event, t_NW {tt:+.2f}**; halves 2019-21 {h1:+.2%} / 2022-25 {h2:+.2%}; '
              f'years same sign {same}/{ny} → **{"PASS" if ok else "fail"}**',
              f'- DOUBLE rate Q5 {q5.double.mean():.1%} (n {len(q5):,}) vs Q1-4 {rest.double.mean():.1%} (n {len(rest):,}); '
              f'ratio {q5.double.mean() / max(rest.double.mean(), 1e-9):.2f}',
              f'- fwd 252d: Q5 mean {q5.fwd.mean():+.1%} median {q5.fwd.median():+.1%}; Q1-4 mean {rest.fwd.mean():+.1%} '
              f'median {rest.fwd.median():+.1%}; P(fwd ≤ −50%) Q5 {(q5.fwd <= -.5).mean():.1%} vs {(rest.fwd <= -.5).mean():.1%}',
              '', '| year | Q5 − Q1-4 xs |', '|---|---|'] + [f'| {y} | {v:+.2%} |' for y, v in yd.items()] + ['']
    open(OUT + '.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
