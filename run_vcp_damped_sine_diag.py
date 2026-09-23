"""Post-hoc diagnostic for run_vcp_damped_sine.py (2026-09-23): split the same-name +/-60 control into before /
after / far, plus a same-date cross-name breakout control. Showed the pre-registered pass was a control artefact."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
import run_vcp_damped_sine as V
P = V.load_panel()
hit, stop, plvl = V.vcp_signals(P, 3); hit[hit.index < V.START] = False
hb, hlvl = V.house_breakout(P); hbv, hlv = hb.values, hlvl.values
H = hit.values
# cache house breakout trade returns
bo = {}
for i, j in zip(*np.where(hbv)):
    c = V.pct_trade(P, j, i, P.low.values[i, j], hlv[i, j])
    if c: bo[(i, j)] = c[0]
bo_by_date = {}
for (i, j), r in bo.items():
    if not H[i, j]: bo_by_date.setdefault(i, []).append(r)
rows = []
for i, j in zip(*np.where(H)):
    v = V.pct_trade(P, j, i, stop.values[i, j], plvl.values[i, j])
    if v is None: continue
    inside, far = [], []
    for k in range(max(0, i - 125), min(len(hbv), i + 126)):
        if k == i or (k, j) not in bo or H[k, j]: continue
        (inside if abs(k - i) <= 60 else far).append((k - i, bo[(k, j)]))
    rows.append(dict(date=hit.index[i], vcp=v[0],
                     before=np.mean([r for d, r in inside if d < 0]) if any(d < 0 for d, _ in inside) else np.nan,
                     after=np.mean([r for d, r in inside if d > 0]) if any(d > 0 for d, _ in inside) else np.nan,
                     far=np.mean([r for _, r in far]) if far else np.nan,
                     xdate=np.mean(bo_by_date[i]) if i in bo_by_date else np.nan))
D = pd.DataFrame(rows)
def t(x, by):
    d = x.groupby(by).mean(); return d.mean() / d.std() * np.sqrt(len(d))
print(f"VCP N3 signals {len(D)}; mean {D.vcp.mean():.2f}%")
for c, lab in [("before", "same name, breakouts in the 60 sessions BEFORE (inside the base)"),
               ("after", "same name, breakouts in the 60 sessions AFTER"),
               ("far", "same name, breakouts 61-125 sessions away (outside base + trade)"),
               ("xdate", "OTHER names' house breakouts, SAME date")]:
    d = D.dropna(subset=[c]); diff = d.vcp - d[c]
    print(f"{lab:66s} n {len(d):5d}  ctl {d[c].mean():+.2f}%  diff {diff.mean():+.2f}pp  t {t(diff, d.date):+.2f}  "
          f"halves {diff[d.date < '2023'].mean():+.2f}/{diff[d.date >= '2023'].mean():+.2f}")
