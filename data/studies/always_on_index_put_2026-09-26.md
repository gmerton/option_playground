# Always-on 45-DTE 12-delta SPY put vs the certified regime (2026-09-26)

`run_always_on_index_put.py` (pre-registered in its docstring, committed before the run). Log
`logs/always_on_index_put.log`; trades `always_on_index_put_2026-09-26.csv`. Source claim: Sosnoff's "one trade"
via Freedom Income `0f2kr2iOXzg` (ES 12Δ put, 45 DTE, 50% take, close at 21 DTE). SPY as the /ES proxy, v3 bid/ask,
house costs, 748 weekly entries 2010-01 → 2026-01, median spread 1.7% of mid. Return = net P&L ÷ Reg-T naked margin.

## Verdict: PRIMARY PASS, but the edge IS the regime · always-on adds only the crash tail

| ARM A (50% take / 21 DTE) | n | % of margin/trade | month-clustered t | yrs + | $/contract |
|---|---|---|---|---|---|
| **ALWAYS-ON (PRIMARY)** | 748 | **+1.33** | **+5.18** (halves +1.55 / +1.02) | 15/17 | +$38 |
| certified Bearish_HighIV subset (SPY < 50-day MA & VIX ≥ 20; 16% of weeks) | 122 | +3.38 | +11.33 | 14/14 | +$80 |
| **COMPLEMENT — key secondary** | 626 | **+0.67** | **+1.73** | 14/17 | +$30 |

Certified − complement: Welch t +5.56. ARM B (hold to expiry): always-on +2.72% (t 4.04); certified +6.95% (t 20.7,
100% win); complement +1.62% (t 1.70).

**The certified result is not a clustering artefact:** 32 separate stress episodes since 2010 (entries > 21 days
apart start a new episode); **all 32 positive in both arms**, episode-level t 15.6 / 15.9. It survived 2020 because a
12Δ put sold at VIX 40–66 is struck far below spot (e.g. 3/20/2020: K 175 vs SPY 231).

## Where the tail lives
- The worst trades are low-VIX entries made just BEFORE a crash: 2020-02-21 (VIX 17) −107% of margin / −$4,317 per
  contract (hold −142%); 2020-02-14 (VIX 13.7) −64%; 2018-11-30 −35%. None are in the certified regime, which by
  construction only sells after the drop.
- Crash windows, ARM A: 2020-02/03 −154% summed over 11 entries (B −506%); 2018-Q4 −28%; 2011-08 +25% (B −51%).
- ARM A vs B: the 50% take / 21-DTE close halves the mean (+1.33 vs +2.72) and cuts the 2020 tail (−107 vs −142 on the
  worst trade); in 2011 and 2018-Q4 it helped, in 2015/2018-02/2022 it cost. Consistent with the 21-DTE study: a risk
  reducer that costs return.

## Read
- **Always-on passes only because it contains the regime.** Outside it, the put earns +0.67% per trade (t 1.7), not
  significant, and carries every crash loss. Sosnoff's "one trade, always" is the certified trade plus a thin, fat-
  tailed complement.
- ⭐ **Cross-structure replication of the certified cell.** The regime edge now shows in a second structure: 45-DTE
  12Δ naked put (here) as well as the 20-DTE 0.25/0.15 bull put (t 6.07) and the SPX condor (t 5.21). Same stress
  episodes, so still ONE bet; but the mechanism (sell index puts after the drop, when VIX ≥ 20) is structure-robust.
- ⚠ Return on margin is leverage-sensitive: Reg-T here; SPAN on /ES is ~5× lower, which multiplies both the return
  and the blow-up (margin expands in a selloff; queued "margin expansion" item).

## Consequences
- Do NOT sell always-on. Keep selling only in the certified regime.
- The 45-DTE 12Δ put is a candidate alternative structure for the certified cell (fewer trades in the tail, far OTM
  at high VIX). Not a new bet; a sizing/structure choice for the same one. Pre-register a head-to-head (20-DTE spread
  vs 45-DTE naked, same regime entries, return on real capital incl. SPAN) before switching.
