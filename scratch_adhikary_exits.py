"""True P&L for the 6 EARLY-EXIT trades: pull the inferred contract's price on Tito's actual
exit date (entry + Days_In_Trade) from Athena options_daily_v3, vs at-expiry intrinsic.
All 6 are split-free, so inferred strikes are direct. Fixes DJT (-100%@exp -> sold into pop)
and COST (-100%@exp -> cut day 1)."""
from lib.athena_lib import athena

# (csv_ticker, athena_ticker, strike, expiry, cp, exit_date, entry_px, ret_at_exp)
EARLY = [
    ("ARM",  "ARM", 108.0, "2024-02-16", "C", "2024-02-13", 3.00,  578.0),
    ("BRKB", "BRK", 430.0, "2024-08-16", "C", "2024-07-24", 2.40,  516.0),
    ("GEV",  "GEV", 200.0, "2024-09-20", "C", "2024-09-13", 3.40, 1237.0),
    ("BABA", "BABA", 95.0, "2024-10-18", "C", "2024-10-09", 0.95,  829.0),
    ("DJT",  "DJT",  48.0, "2024-11-22", "C", "2024-10-31", 6.00, -100.0),
    ("COST", "COST",945.0, "2024-11-15", "C", "2024-11-11", 2.23, -100.0),
]

conds = " OR ".join(
    f"(ticker='{at}' AND strike={k} AND expiry=DATE '{e}' AND cp='{cp}' AND trade_date=DATE '{xd}')"
    for (_t, at, k, e, cp, xd, _p, _r) in EARLY)
sql = f"""
  SELECT ticker, strike, CAST(expiry AS DATE) AS expiry, CAST(trade_date AS DATE) AS exit_date,
         ROUND(AVG(last),2) AS last, ROUND(AVG((bid+ask)/2.0),2) AS mid
  FROM silver.options_daily_v3
  WHERE ({conds})
  GROUP BY ticker, strike, expiry, trade_date
"""
df = athena(sql)
df["expiry"] = df["expiry"].astype(str); df["exit_date"] = df["exit_date"].astype(str)
df["strike"] = df["strike"].astype(float)
look = {(r.ticker, r.strike, r.expiry, r.exit_date): r for r in df.itertuples()}

print(f"{'trade':6} {'strike':>7} {'exit_date':10} {'entry':>6} {'exit_last':>9} {'exit_mid':>8} "
      f"{'ret_last':>9} | {'at-exp':>8}")
for (t, at, k, e, cp, xd, ep, rexp) in EARLY:
    m = look.get((at, k, e, xd))
    if m is None:
        print(f"{t:6} {k:7.1f} {xd:10} {ep:6.2f}  -- no Athena row on {xd} (try ±1 day) --")
        continue
    px = m.last if m.last and m.last > 0 else m.mid
    rc = (px - ep) / ep * 100
    print(f"{t:6} {k:7.1f} {xd:10} {ep:6.2f} {px:9.2f} {m.mid:8.2f} {rc:+8.0f}% | {rexp:+7.0f}%")

print("\nTrue exit (close-based) vs the misleading at-expiry intrinsic:")
print("  DJT: at-expiry -100% (expired worthless) -> actual close-of-exit return above")
print("  COST: at-expiry -100% -> actual (cut day 1) return above")
