"""Step 3/3 of the straddle re-centering study (2026-09-10).
Usage (from repo root; DIR holds straddle_gated.parquet, paths/, results):
  mkdir -p data/cache/straddle_recenter
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 -c "from run_straddle_rebuild_wf import load; load().to_parquet('data/cache/straddle_recenter/straddle_gated.parquet', index=False)"
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_pull.py   data/cache/straddle_recenter
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_sim.py    data/cache/straddle_recenter [limit] [min_left=3]
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_report.py data/cache/straddle_recenter
Write-up: data/studies/long_straddle_playbook.md, section "Re-centering and the real stop".
"""
import sys, numpy as np, pandas as pd
SCR = sys.argv[1]; R = pd.read_parquet(f"{SCR}/recenter_results.parquet")
def t(x): x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
def line(lbl, x, base=None):
    x = pd.Series(x).dropna() * 100
    s = f"  {lbl:34s} mean {x.mean():+7.2f}%  med {x.median():+7.2f}%  win {100 * (x > 0).mean():5.1f}%  t {t(x):+5.2f}"
    if base is not None:
        dlt = (pd.Series(x.values) - pd.Series(base.values) * 100); s += f"  | vs hold {dlt.mean():+6.2f}pp (paired t {t(dlt):+5.2f})"
    return s
for arm, pop in [(7, "both"), (7, "fvr"), (14, "both")]:
    A = R[(R.arm == arm) & (R.both if pop == "both" else True)]
    if A.empty: continue
    print(f"\n===== {arm}-DTE, {'both gates' if pop == 'both' else 'FVR gate only (superset)'}: n={len(A):,}  median entry BA {100 * A["ba_pct"].median():.1f}% of mid =====")
    if arm == 7: print(line("hold, POOL payout (playbook), mid", A["hold_pool"]))
    print(line("hold, mid, no costs", A["hold_gross"]))
    print(line("clip -50% (playbook model)", A["clip"]))
    print(line("hold, after costs", A["hold"]))
    print(line("real path stop -50%, after costs", A["stop"], A["hold"]) + f"  stopped {100 * A["stopped"].mean():.1f}%")
    for kind, grid, lab in (("d", [0.35, 0.50], "|net delta|>="), ("m", [0.50, 0.75, 1.00], "move>=x implied")):
        for th in grid:
            print(line(f"flat-take {lab}{th}", A[f"take_{kind}{th}"], A["hold"]) + f"  fired {100 * A[f'took_{kind}{th}'].mean():.1f}%")
            for mx in (1, 99):
                print(line(f"re-center {lab}{th} max {mx if mx == 1 else 'unl'}", A[f"rc_{kind}{th}_{mx}"], A["hold"])
                      + f"  avg n {A[f'rcn_{kind}{th}_{mx}'].mean():.2f}  max cap {A[f'rccap_{kind}{th}_{mx}'].mean():.2f}x")
    print("  by year (hold / stop / re-center move>=0.75 max1 / flat-take move>=0.75), after costs:")
    for yr, y in A.groupby("yr"):
        print(f"    {yr}  n={len(y):5d}  hold {100 * y["hold"].mean():+7.2f}  stop {100 * y["stop"].mean():+7.2f}  rc {100 * y['rc_m0.75_1'].mean():+7.2f}  take {100 * y['take_m0.75'].mean():+7.2f}")
