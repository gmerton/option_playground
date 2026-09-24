import pandas as pd, numpy as np
tr = pd.read_parquet('data/studies/logs/putspread_exit_capital_time_trades.parquet')
tr['exit_date'] = pd.to_datetime(tr.exit_date)
YEARS = (tr.expiry.max() - tr.entry_date.min()).days / 365.25
ARMS = ["HOLD", "T25", "T50", "T75", "FAST50", "ANN100"]
def slot(g, start):
    free = start; out = []
    for r in g.itertuples(index=False):
        if r.entry_date > free:
            out.append((r.roc, r.roc_gross, r.exit_date)); free = r.exit_date
    return out
res = {}
for fri in (True, False):
    for arm in ARMS:
        x = tr[tr.arm == arm]
        if fri: x = x[x.entry_date.dt.weekday == 4]
        per_phase = []  # annual net, annual gross, trades/yr, monthly series
        for k in range(30):  # 30 staggered start offsets (calendar days) -> phase average
            tot, totg, n, mon = 0, 0, 0, []
            for t, g in x.sort_values('entry_date').groupby('ticker'):
                start = g.entry_date.min() + pd.Timedelta(days=k) - pd.Timedelta(days=1)
                o = slot(g, start)
                tot += sum(a for a, _, _ in o); totg += sum(b for _, b, _ in o); n += len(o)
                mon += [(d.to_period('M'), a) for a, _, d in o]
            ms = pd.DataFrame(mon, columns=['m', 'r']).groupby('m').r.sum() / 20
            per_phase.append((tot / 20 / YEARS, totg / 20 / YEARS, n / 20 / YEARS, ms))
        ann = np.mean([p[0] for p in per_phase]); anng = np.mean([p[1] for p in per_phase])
        spread = np.std([p[0] for p in per_phase])
        ms = pd.concat([p[3] for p in per_phase], axis=1).fillna(0).mean(axis=1)
        res[(fri, arm)] = ms
        print(f"{'Fri' if fri else 'any':4s} {arm:7s} trades/yr {np.mean([p[2] for p in per_phase]):5.1f}  "
              f"net/yr {100*ann:7.2f}%  (phase sd {100*spread:5.2f})  gross/yr {100*anng:7.2f}%  worst mo {100*ms.min():7.2f}%")
print("\npaired monthly t vs the incumbent (Fri, T50) and vs (Fri, HOLD):")
for k, ms in res.items():
    out = []
    for base in [(True, 'T50'), (True, 'HOLD')]:
        if k == base: out.append('   --  '); continue
        j = pd.concat([ms, res[base]], axis=1).fillna(0); d = j.iloc[:, 0] - j.iloc[:, 1]
        out.append(f"{d.mean()/d.std()*np.sqrt(len(d)):+6.2f}")
    print(f"  {'Fri' if k[0] else 'any'} {k[1]:7s} vs Fri-T50 {out[0]}  vs Fri-HOLD {out[1]}")
