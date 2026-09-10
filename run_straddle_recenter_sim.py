"""Step 2/3 of the straddle re-centering study (2026-09-10).
Path-dependent long-straddle simulator: hold vs real path stop vs re-centering vs flat-take.
Marks = daily close mid; executions = mid +/- 25% of that day's bid-ask + $0.0065/sh/leg (house cost model).
Expiry settles at |S_T - K| (no exit cost). S_T from expiry-day put-call parity at the strike with the smallest
|C-P| mid, both arms. (The pool file's payout = call_last_exp + put_last_exp counts a stale print on the OTM leg;
it is kept as hold_pool for reconciliation only.) Re-center/flat-take triggers act only with >= MIN_LEFT trading
days to expiry (default 3 = decision day + 2): net-delta trigger |dC + dP| >= th, move trigger |S_t - K| >= m x entry mid.
Usage (from repo root; DIR holds straddle_gated.parquet, paths/, results):
  mkdir -p data/cache/straddle_recenter
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 -c "from run_straddle_rebuild_wf import load; load().to_parquet('data/cache/straddle_recenter/straddle_gated.parquet', index=False)"
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_pull.py   data/cache/straddle_recenter
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_sim.py    data/cache/straddle_recenter [limit] [min_left=3]
  PYTHONPATH=src .venv/bin/python3 run_straddle_recenter_report.py data/cache/straddle_recenter
Write-up: data/studies/long_straddle_playbook.md, section "Re-centering and the real stop".
"""
import sys, glob, numpy as np, pandas as pd
SLIP, COMM = 0.25, 0.0065
SCR = sys.argv[1]
g = pd.read_parquet(f"{SCR}/straddle_gated.parquet").reset_index(drop=True)
g["entry_date"] = pd.to_datetime(g.entry_date); g["expiry"] = pd.to_datetime(g.expiry)
P = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{SCR}/paths/paths_*.parquet"))], ignore_index=True)
P["trade_date"] = pd.to_datetime(P.trade_date); P["expiry"] = pd.to_datetime(P.expiry)
P = P[(P.ask > 0) & (P.bid >= 0) & (P.ask >= P.bid) & (P.ask < 9999)]
P["mid"] = (P.bid + P.ask) / 2; P["ba"] = P.ask - P.bid
# a few days carry duplicate rows per strike/side (e.g. adjusted roots); keep the tightest quote
P = P.sort_values("ba").drop_duplicates(["row_id", "trade_date", "expiry", "cp", "strike"], keep="first")
DELTAS = [0.35, 0.50]
MOVES = [0.50, 0.75, 1.00]
MIN_LEFT = int(sys.argv[3]) if len(sys.argv) > 3 else 3   # decision day + >=2 more trading days incl. expiry

def buy(c, p):  return c.mid + p.mid + SLIP * (c.ba + p.ba) + 2 * COMM
def sell(c, p): return c.mid + p.mid - SLIP * (c.ba + p.ba) - 2 * COMM

def run_trade(rid, d, meta):
    arm = 14 if rid >= 1_000_000 else 7
    if arm == 14:
        exp = pd.Timestamp(d.expiry.min()); d = d[d.expiry == exp]
    else:
        exp = pd.Timestamp(meta.expiry)
    days = sorted(pd.Timestamp(x) for x in d.trade_date.unique())
    if len(days) < 3 or days[0] != pd.Timestamp(meta.entry_date) or days[-1] != exp: return None
    # book per day: dict strike -> (call row, put row)
    book = {}
    for td, x in d.groupby("trade_date"):
        td = pd.Timestamp(td)
        c = x[x.cp == "C"].set_index("strike"); p = x[x.cp == "P"].set_index("strike")
        ks = c.index.intersection(p.index)
        book[td] = (c.loc[ks], p.loc[ks])
    def atm(td, exclude=None):
        c, p = book[td]
        if c.empty or c.delta.isna().all(): return None
        k = (c.delta - 0.5).abs().idxmin()
        return None if (exclude is not None and k == exclude) else k
    # settlement
    c, p = book[exp]
    if c.empty: return None
    k = (c.mid - p.mid).abs().idxmin(); ST = k + c.loc[k, "mid"] - p.loc[k, "mid"]      # expiry-day parity, both arms
    if arm == 7:
        K0 = meta.strike
    else:
        K0 = atm(days[0])
        if K0 is None: return None
    c0, p0 = book[days[0]]
    if K0 not in c0.index: return None
    entry_mid = c0.loc[K0, "mid"] + p0.loc[K0, "mid"]
    if entry_mid < 0.50: return None
    entry_cost = buy(c0.loc[K0], p0.loc[K0])
    dec = days[1:-1]                                  # decision days (strictly between entry and expiry)
    settle = lambda K: abs(ST - K)
    out = dict(row_id=rid, arm=arm, ticker=meta.ticker, entry_date=meta.entry_date, yr=meta.entry_date.year, both=bool(meta.pass_both),
               entry_mid=entry_mid, entry_cost=entry_cost, ba_pct=(c0.loc[K0, "ba"] + p0.loc[K0, "ba"]) / entry_mid)
    out["hold_gross"] = (settle(K0) - entry_mid) / entry_mid
    out["hold_pool"] = (meta.payout - entry_mid) / entry_mid if arm == 7 else float("nan")   # playbook's sum-of-last-prints payout
    out["hold"] = (settle(K0) - entry_cost) / entry_cost
    out["clip"] = max(out["hold_gross"], -0.5)       # the playbook's model
    # real path stop at -50% of mid value
    pnl = settle(K0) - entry_cost; stopped = 0
    for td in dec:
        c, p = book[td]
        if K0 in c.index and c.loc[K0, "mid"] + p.loc[K0, "mid"] <= 0.5 * entry_mid:
            pnl = sell(c.loc[K0], p.loc[K0]) - entry_cost; stopped = 1; break
    out["stop"] = pnl / entry_cost; out["stopped"] = stopped
    # re-centering and flat-take. Triggers need >= MIN_LEFT trading days to expiry after acting.
    #   delta trigger: |call delta + put delta| of the held pair >= th
    #   move trigger : |S_t - K_held| >= m x entry straddle mid (the implied move), S_t from parity at K_held
    def spot(td, K):
        c, p = book[td]
        return K + c.loc[K, "mid"] - p.loc[K, "mid"] if K in c.index else None
    def fire(td, K, kind, th):
        c, p = book[td]
        if K not in c.index: return False
        if kind == "d":
            if pd.isna(c.loc[K, "delta"]) or pd.isna(p.loc[K, "delta"]): return False
            return abs(c.loc[K, "delta"] + p.loc[K, "delta"]) >= th
        S = spot(td, K); return S is not None and abs(S - K) >= th * entry_mid
    for kind, grid in (("d", DELTAS), ("m", MOVES)):
        for th in grid:
            elig = [td for j, td in enumerate(dec) if (len(dec) - j) >= MIN_LEFT]   # trading days left incl. expiry
            for maxn in (1, 99):
                K, cash, n, capital = K0, -entry_cost, 0, entry_cost
                for td in elig:
                    if n >= maxn: break
                    if not fire(td, K, kind, th): continue
                    K2 = atm(td, exclude=K)
                    if K2 is None: continue
                    c, p = book[td]
                    cash += sell(c.loc[K], p.loc[K]); cash -= buy(c.loc[K2], p.loc[K2]); K = K2; n += 1
                    capital = max(capital, -cash)
                out[f"rc_{kind}{th}_{maxn}"] = (cash + settle(K)) / entry_cost; out[f"rcn_{kind}{th}_{maxn}"] = n
                out[f"rccap_{kind}{th}_{maxn}"] = capital / entry_cost
            v = (settle(K0) - entry_cost) / entry_cost; took = 0
            for td in elig:
                if fire(td, K0, kind, th):
                    c, p = book[td]; v = (sell(c.loc[K0], p.loc[K0]) - entry_cost) / entry_cost; took = 1; break
            out[f"take_{kind}{th}"] = v; out[f"took_{kind}{th}"] = took
    return out

meta_all = g.copy(); meta_all["row_id"] = meta_all.index.astype("int64")
m7 = meta_all.set_index("row_id"); m14 = meta_all.copy(); m14.index = 1_000_000 + m14.index
rows, errs = [], []
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else None
for i, (rid, d) in enumerate(P.groupby("row_id", sort=False)):
    meta = m7.loc[rid] if rid < 1_000_000 else m14.loc[rid]
    try:
        r = run_trade(rid, d, meta)
    except Exception as e:
        errs.append(repr(e)); r = None
    if r: rows.append(r)
    if LIMIT and i >= LIMIT: break
    if i % 2000 == 0: print(f"  {i:,} trades simulated", flush=True)
print(f"errors: {len(errs)}", errs[:3])
R = pd.DataFrame(rows); R.to_parquet(f"{SCR}/recenter_results.parquet", index=False)
print(f"simulated {len(R):,} trades (arm7 {int((R.arm == 7).sum()):,}, arm14 {int((R.arm == 14).sum()):,})")
