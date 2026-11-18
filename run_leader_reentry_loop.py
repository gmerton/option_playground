"""Re-entry loop on fresh leaders vs single-trip and buy-and-hold -- PRE-REGISTERED 2026-11-17 (DISCOVERY track).

Origin: top_gainers_chart_study_2026-11-17.md section 3.3. On the top-250 winners a single trip from the first
52w-high close kept only 3% (close < 21 EMA) to 19% (weekly < 10wk) of the move, so the hypothesis is that on
a leader the tactic that matters is RE-ENTRY. That study was outcome-conditioned; this test runs on the full,
survivorship-free population of names making a fresh 52-week high. New axis: no ledger row measures a
same-name re-entry loop (the exit tests were all single-trade; TEST_INDEX rows 157-162, 205).

DATA  silver.chain_spot_daily closes (local cache), INCLUDING DELISTED, split-adjusted and cleaned with
      run_dip_survivorship.adjust_and_clean (unexplained >45% one-day breaks drop the earlier segment). Closes only.
      Liquidity: 50d mean option volume >= 1,000 and close >= $5 (same as run_dip_survivorship). SPY: yfinance adj.
EVENT (all on the event close) close > max of the prior 252 closes (>= 240 valid), no such close in the prior
      126 sessions (FIRST new 52w high in 6 months), close > SMA50 > SMA200, liquid. Per name, a new event only
      after the previous event's horizon has ended (no overlap within a name). Event dates 2011-01-01 ->
      2025-02-14 (every event has a full horizon unless the name delists).
HORIZON H = 252 sessions after the event close. Delisting / series end inside H: flat at the last close.
FILLS  at the signal close, 10 bp per side (log), every entry and exit; a position open at H is closed at H.
ARMS   all enter at the event close.
   A   single trip: exit at the first close < EMA21; flat (0) thereafter.
   B1  PRIMARY loop: exit at a close < EMA21; re-enter at the next close > max of the prior 50 closes
       (new 50-day-high close); repeat until H.
   B2  loop, re-enter on the 21-EMA reclaim: a close > EMA21 with close > SMA50 (after an exit).
   B3  loop, looser exit: exit at a close < SMA50, re-enter on a new 50-day-high close.
   C   buy and hold to H.
METRIC per event, sum of in-position daily log returns minus costs, MINUS SPY's log return on the same in-position
       days (beta-1 exposure match; cash days earn 0 in both). Raw (no SPY subtraction) reported alongside.
PRIMARY  B1 - A, excess, mean per event. Inference: average events within each event-month, then a Newey-West t
       (lag 12; horizons overlap by up to 12 months) over months. BAR |t| >= 3, both halves (event date 2011-17 /
       2018-25) the same sign, a majority of event-years the same sign.
SECONDARY (Sidak over 4 cells, |t| >= 3.2): B1 - C, B2 - A, B3 - A, B3 - C.
EXPLORATORY: exposure, trades per event, the right tail (share of events > +100% raw, p90), by SPY > SMA200 at
       the event, by year. Not graded.
Output: data/studies/leader_reentry_loop_2026-11-17.md + _events.csv
"""
import sys
import numpy as np, pandas as pd, yfinance as yf

sys.path.insert(0, '.')
import run_dip_survivorship as DS

EV_START, EV_END, SPLIT = pd.Timestamp('2011-01-01'), pd.Timestamp('2025-02-14'), 2018
H, COST = 252, 0.001
OUT = 'data/studies/leader_reentry_loop_2026-11-17'


def load():
    d = pd.read_parquet('data/cache/chain_spot/chain_spot_daily.parquet')
    d['trade_date'] = pd.to_datetime(d.trade_date)
    C, V = DS.adjust_and_clean(d)
    return C, V


def simulate(c, e21, s50, h50, kind):
    """c etc. are 1-D arrays for one event, index 0 = event close. Returns (log path ret, in-day mask, trades)."""
    n = len(c); inpos = True; trades = 1; logr = -COST; mask = np.zeros(n, bool); was_out_flag = False
    for k in range(1, n):
        if inpos:
            mask[k] = True; logr += np.log(c[k] / c[k - 1])
            exit_now = (kind in ('A', 'B1', 'B2') and c[k] < e21[k]) or (kind == 'B3' and c[k] < s50[k])
            if kind == 'C': exit_now = False
            if exit_now:
                inpos = False; logr -= COST
        elif kind != 'A':
            reenter = (c[k] > h50[k]) if kind in ('B1', 'B3') else (c[k] > e21[k] and c[k] > s50[k])
            if reenter:
                inpos = True; trades += 1; logr -= COST
    if inpos: logr -= COST
    return logr, mask, trades


def nw_t(x, lag=12):
    x = np.asarray(x, float); x = x[np.isfinite(x)]; n = len(x)
    if n < 10: return np.nan
    u = x - x.mean(); g0 = (u @ u) / n; s = g0
    for l in range(1, lag + 1):
        s += 2 * (1 - l / (lag + 1)) * (u[l:] @ u[:-l]) / n
    return x.mean() / np.sqrt(s / n)


def main():
    C, V = load()
    idx = C.index
    spy = yf.download('SPY', start='2009-01-01', auto_adjust=True, progress=False)['Close'].squeeze()
    spy.index = pd.to_datetime(spy.index).tz_localize(None)
    spy = spy.reindex(idx).ffill(); spy_lr = np.log(spy / spy.shift(1)).fillna(0).values
    spy_trend = (spy > spy.rolling(200).mean()).values
    e21 = C.ewm(span=21, adjust=False, ignore_na=True).mean()
    s50 = C.rolling(50, min_periods=40).mean(); s200 = C.rolling(200, min_periods=160).mean()
    hi252 = C.shift(1).rolling(252, min_periods=240).max(); hi50 = C.shift(1).rolling(50, min_periods=45).max()
    newhi = (C > hi252)
    fresh = newhi & (newhi.astype(float).shift(1).rolling(126, min_periods=1).sum() == 0)
    liq = (V.rolling(50, min_periods=30).mean() >= DS.OPTVOL_MIN) & (C >= DS.PX_MIN)
    ev_mask = fresh & (C > s50) & (s50 > s200) & liq
    ev_mask = ev_mask & (idx >= EV_START)[:, None] & (idx <= EV_END)[:, None]
    Cv, E, S, Hh, M = C.values, e21.values, s50.values, hi50.values, ev_mask.values
    rows = []
    for j in range(Cv.shape[1]):
        cand = np.flatnonzero(M[:, j]); next_ok = -1
        col = Cv[:, j]; valid = np.flatnonzero(np.isfinite(col))
        if not len(cand): continue
        last = valid.max()
        for i0 in cand:
            if i0 < next_ok: continue
            i1 = min(i0 + H, last); next_ok = i0 + H
            if i1 - i0 < 2: continue
            c = pd.Series(col[i0:i1 + 1]).ffill().values
            sl = slice(i0, i1 + 1)
            r = dict(ticker=C.columns[j], date=idx[i0], year=idx[i0].year, days=i1 - i0, delisted=i1 < i0 + H,
                     spy_up=bool(spy_trend[i0]))
            for kind in ('A', 'B1', 'B2', 'B3', 'C'):
                lr, mk, tr = simulate(c, E[sl, j], S[sl, j], Hh[sl, j], kind)
                r[f'raw_{kind}'] = lr; r[f'xs_{kind}'] = lr - spy_lr[sl][mk].sum()
                r[f'exp_{kind}'] = mk[1:].mean(); r[f'tr_{kind}'] = tr
            rows.append(r)
    ev = pd.DataFrame(rows); ev.to_csv(OUT + '_events.csv', index=False)

    lines = [f'# Re-entry loop on fresh leaders -- results ({pd.Timestamp.today().date()})', '',
             f'Pre-registration: docstring of `run_leader_reentry_loop.py`. Events: {len(ev):,} on '
             f'{ev.ticker.nunique():,} names, {ev.date.min().date()} -> {ev.date.max().date()}; delisted inside H: '
             f'{ev.delisted.mean():.1%}.', '',
             '## Cells (excess vs exposure-matched SPY, log, per event; month-averaged, NW t lag 12)', '',
             '| cell | mean | t_NW | 2011-17 | 2018-25 | years same sign | bar |', '|---|---|---|---|---|---|---|']
    cells = [('B1 - A (PRIMARY)', 'B1', 'A', 3.0), ('B1 - C', 'B1', 'C', 3.2), ('B2 - A', 'B2', 'A', 3.2),
             ('B3 - A', 'B3', 'A', 3.2), ('B3 - C', 'B3', 'C', 3.2)]
    for name, a, b, bar in cells:
        ev['_d'] = ev[f'xs_{a}'] - ev[f'xs_{b}']
        mm = ev.groupby(ev.date.dt.to_period('M'))['_d'].mean()
        t = nw_t(mm.values)
        h1 = ev.loc[ev.year < SPLIT, '_d'].mean(); h2 = ev.loc[ev.year >= SPLIT, '_d'].mean()
        yr = ev.groupby('year')['_d'].mean(); same = (np.sign(yr) == np.sign(ev._d.mean())).sum()
        ok = abs(t) >= bar and np.sign(h1) == np.sign(h2) and same > len(yr) / 2
        lines.append(f'| {name} | {ev._d.mean():+.4f} | {t:+.2f} | {h1:+.4f} | {h2:+.4f} | {same}/{len(yr)} | '
                     f'{"PASS" if ok else "fail"} (|t|>={bar}) |')
    lines += ['', '## Arms (per event)', '',
              '| arm | raw mean | raw median | raw p90 | P(raw > +100%) | excess mean | exposure | trades |',
              '|---|---|---|---|---|---|---|---|']
    for k in ('A', 'B1', 'B2', 'B3', 'C'):
        raw = np.expm1(ev[f'raw_{k}'])
        lines.append(f'| {k} | {raw.mean():+.1%} | {raw.median():+.1%} | {raw.quantile(.9):+.1%} | '
                     f'{(raw > 1).mean():.1%} | {ev[f"xs_{k}"].mean():+.4f} | {ev[f"exp_{k}"].mean():.0%} | '
                     f'{ev[f"tr_{k}"].mean():.1f} |')
    lines += ['', '## Exploratory: B1 - A and B1 - C by SPY trend at the event, and by year', '']
    for g, sub in ev.groupby('spy_up'):
        lines.append(f'- SPY {"above" if g else "below"} SMA200 (n {len(sub):,}): B1-A {(sub.xs_B1 - sub.xs_A).mean():+.4f}, '
                     f'B1-C {(sub.xs_B1 - sub.xs_C).mean():+.4f}')
    yr = ev.groupby('year').apply(lambda s: pd.Series({'n': len(s), 'B1-A': (s.xs_B1 - s.xs_A).mean(),
                                                      'B1-C': (s.xs_B1 - s.xs_C).mean(), 'C raw': np.expm1(s.raw_C).mean()}))
    lines += ['', yr.round(4).to_markdown(), '']
    # right tail: on events where buy-and-hold more than doubled, what share did each arm keep?
    big = ev[np.expm1(ev.raw_C) > 1]
    if len(big):
        lines += [f'## Right tail: the {len(big):,} events where buy-and-hold > +100%', '',
                  '| arm | median share of C\'s log return kept |', '|---|---|']
        for k in ('A', 'B1', 'B2', 'B3'):
            lines.append(f'| {k} | {(big[f"raw_{k}"] / big.raw_C).median():.0%} |')
    open(OUT + '.md', 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
