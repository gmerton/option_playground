"""Low share price among fresh leaders, volatility held fixed -- PRE-REGISTERED 2026-11-17 (DISCOVERY track).

Lead: leader_fingerprint_2026-11-17.md (exploratory, 2019-25): low price predicted doubling (AUC 0.67) but not halving
(0.51), unlike volatility (0.75 both). New axis: nominal share price has no ledger row (the small-cap test sorted on
dollar volume, TEST_INDEX 'SMALL CAPS').

CONTAMINATION, declared: 2019-25 is SEEN (the asymmetry was observed there). In 2011-18 only the multivariate logit
doubling coefficient was seen (logpx -2.09, z -3.43); neither excess returns nor halving rates by price were looked
at. So the graded sample is 2011-18 and the graded outcome is EXCESS RETURN. 2019-25 is reported as a seen reference.

EVENTS  leader_fingerprint_2026-11-17_events.csv (chain_spot incl. delisted, split-adjusted without break deletion;
        fresh 52w high, close > SMA50 > SMA200, opt-vol >= 1,000, close >= $5; 252-session forward window).
CELLS   within each event-year, ADR terciles; within each year x ADR tercile, price terciles (LOW / MID / HIGH).
        The comparison varies PRICE with VOLATILITY held at the same tercile, same year.
PRIMARY  2011-18: mean xs (12-month return minus SPY over the same dates) of LOW minus HIGH, pooled across ADR
        terciles; event-month means of each group, difference per month, Newey-West t (lag 12). BAR |t| >= 3, halves
        2011-14 / 2015-18 same sign, a majority of years same sign.
GATE (must hold too for the lead's claim): P(fwd <= -50%) LOW - HIGH in 2011-18 not significantly positive (two-
        proportion z < 2). If LOW blows up more, the result is a volatility re-run, not the asymmetric lead.
REPORTED: P(double), median fwd, per ADR tercile, per year, the seen 2019-25 sample, excluding forward-break events.
Output: data/studies/low_price_leaders_2026-11-17.md
"""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from run_leader_reentry_loop import nw_t

ev = pd.read_csv('data/studies/leader_fingerprint_2026-11-17_events.csv', parse_dates=['date'])
ev = ev.dropna(subset=['adr', 'logpx', 'xs']).copy()
ev['adr_t'] = ev.groupby('year').adr.transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=False))
ev['px_t'] = ev.groupby(['year', 'adr_t']).logpx.transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=False))
ev['grp'] = ev.px_t.map({0: 'LOW', 1: 'MID', 2: 'HIGH'})
ev['half'] = (ev.fwd <= -0.5).astype(int); ev['dbl'] = (ev.fwd >= 1).astype(int)


def cell(t, a, b):
    m = t.groupby([t.date.dt.to_period('M'), 'grp'])['xs'].mean().unstack()
    d = (m[a] - m[b]).dropna()
    yr = t.groupby(['year', 'grp'])['xs'].mean().unstack(); yd = (yr[a] - yr[b])
    return d, nw_t(d.values), yd


def ztest(x1, x2):
    p1, p2, n1, n2 = x1.mean(), x2.mean(), len(x1), len(x2); p = (x1.sum() + x2.sum()) / (n1 + n2)
    return (p1 - p2) / np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))


L = [f'# Low share price among fresh leaders, volatility held fixed ({pd.Timestamp.today().date()})', '',
     'Pre-registration: docstring of `run_low_price_leaders.py`. Graded sample 2011-18; 2019-25 is SEEN.', '']
for label, t, graded in [('2011-18 (GRADED)', ev[ev.year <= 2018], True), ('2019-25 (seen, reference)', ev[ev.year >= 2019], False),
                         ('2011-18 excluding forward-break events', ev[(ev.year <= 2018) & ~ev.fwd_brk], False)]:
    d, tt, yd = cell(t, 'LOW', 'HIGH')
    lo, hi = t[t.grp == 'LOW'], t[t.grp == 'HIGH']
    z = ztest(lo.half, hi.half)
    if graded:
        h1 = d[d.index.year <= 2014].mean(); h2 = d[d.index.year >= 2015].mean()
        same = (np.sign(yd) == np.sign(d.mean())).sum()
        ok = abs(tt) >= 3 and np.sign(h1) == np.sign(h2) and same > len(yd) / 2 and z < 2
        verdict = (f'halves 2011-14 {h1:+.2%} / 2015-18 {h2:+.2%}; years same sign {same}/{len(yd)}; halving gate z {z:+.2f} '
                   f'→ **{"PASS" if ok else "fail"}**')
    else:
        verdict = f'halving z {z:+.2f}'
    L += [f'## {label}', '', f'- LOW − HIGH xs **{d.mean():+.2%}/event, t_NW {tt:+.2f}**; {verdict}',
          f'- n LOW {len(lo):,} / HIGH {len(hi):,}; median price LOW ${np.exp(lo.logpx).median():.1f} vs HIGH ${np.exp(hi.logpx).median():.1f}',
          '', '| group | mean xs | median fwd | P(double) | P(halve) | n |', '|---|---|---|---|---|---|']
    for g in ('LOW', 'MID', 'HIGH'):
        s = t[t.grp == g]
        L.append(f'| {g} | {s['xs'].mean():+.1%} | {s.fwd.median():+.1%} | {s.dbl.mean():.1%} | {s.half.mean():.1%} | {len(s):,} |')
    L += ['', '| ADR tercile | LOW − HIGH xs | LOW P(double) / P(halve) | HIGH P(double) / P(halve) |', '|---|---|---|---|']
    for a in (0, 1, 2):
        s = t[t.adr_t == a]; l, h = s[s.grp == 'LOW'], s[s.grp == 'HIGH']
        L.append(f'| {["low", "mid", "high"][a]} | {l['xs'].mean() - h['xs'].mean():+.1%} | {l.dbl.mean():.1%} / {l.half.mean():.1%} | '
                 f'{h.dbl.mean():.1%} / {h.half.mean():.1%} |')
    L += ['', '| year | LOW − HIGH xs |', '|---|---|'] + [f'| {y} | {v:+.1%} |' for y, v in yd.items()] + ['']
open('data/studies/low_price_leaders_2026-11-17.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
