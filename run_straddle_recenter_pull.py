"""Step 1/3 of the straddle re-centering study (2026-09-10).
Pull daily near-ATM chains (bid/ask/delta) for every gated straddle trade, entry..expiry, from options_daily_v3.
Arm 7  = FVR-passing playbook trades (7 DTE, pool file strike K1).
Arm 14 = both-gates trades, same Friday entry, next weekly expiry (exp+5..exp+9 days), strike chosen at entry by delta.
Writes <scratch>/paths/paths_<year>.parquet.
Usage (from repo root; DIR holds straddle_gated.parquet, paths/, results):
  mkdir -p data/cache/straddle_recenter
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 -c "from run_straddle_rebuild_wf import load; load().to_parquet('data/cache/straddle_recenter/straddle_gated.parquet', index=False)"
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_pull.py   data/cache/straddle_recenter
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_sim.py    data/cache/straddle_recenter [limit] [min_left=3]
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_report.py data/cache/straddle_recenter
Write-up: data/studies/long_straddle_playbook.md, section "Re-centering and the real stop".
"""
import sys, uuid, time, pandas as pd, awswrangler as wr
from datetime import timedelta
sys.path.insert(0, "src")
from lib.athena_lib import athena, _ensure_glue_db, _drop_temp_targets_table
from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
SCR = sys.argv[1]
g = pd.read_parquet(f"{SCR}/straddle_gated.parquet").reset_index(drop=True)
g["entry_date"] = pd.to_datetime(g.entry_date); g["expiry"] = pd.to_datetime(g.expiry)
a7 = g[g.pass_fvr].copy(); a7["row_id"] = a7.index.astype("int64"); a7["exp_lo"] = a7.expiry; a7["exp_hi"] = a7.expiry
a14 = g[g.pass_both].copy(); a14["row_id"] = (1_000_000 + a14.index).astype("int64"); a14["exp_lo"] = a14.expiry + timedelta(days=5); a14["exp_hi"] = a14.expiry + timedelta(days=9)
tg = pd.concat([a7, a14])[["row_id", "ticker", "entry_date", "exp_lo", "exp_hi", "strike"]]
tg["k_lo"] = tg.strike * 0.85; tg["k_hi"] = tg.strike * 1.15
for c in ("entry_date", "exp_lo", "exp_hi"): tg[c] = tg[c].dt.date
tg = tg.drop(columns="strike"); tg["yr"] = pd.to_datetime(tg.entry_date).dt.year
print(f"targets: arm7 {len(a7)}  arm14 {len(a14)}", flush=True)
import os; os.makedirs(f"{SCR}/paths", exist_ok=True)
_ensure_glue_db(DB)
for yr, t in tg.groupby("yr"):
    out = f"{SCR}/paths/paths_{yr}.parquet"
    if os.path.exists(out): print(yr, "cached", flush=True); continue
    t0 = time.time(); name = f"tmp_targets_{uuid.uuid4().hex}"; path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    wr.s3.to_parquet(df=t.drop(columns="yr"), path=path, dataset=True, database=DB, table=name, compression="snappy", mode="overwrite",
                     dtype={"row_id": "bigint", "ticker": "string", "entry_date": "date", "exp_lo": "date", "exp_hi": "date", "k_lo": "double", "k_hi": "double"})
    try:
        d = athena(f"""
        SELECT t.row_id, o.trade_date, o.expiry, o.cp, o.strike, o.bid, o.ask, o.delta
        FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
          ON o.ticker = t.ticker AND o.expiry BETWEEN t.exp_lo AND t.exp_hi
         AND o.trade_date BETWEEN t.entry_date AND o.expiry AND o.strike BETWEEN t.k_lo AND t.k_hi
        WHERE o.trade_date BETWEEN DATE '{yr}-01-01' AND DATE '{yr + 1}-01-31'""")
    finally:
        _drop_temp_targets_table(DB, name, path)
    d.to_parquet(out, index=False)
    print(f"{yr}: {len(d):,} rows, {d.row_id.nunique():,} trades, {time.time() - t0:.0f}s", flush=True)
print("DONE", flush=True)
