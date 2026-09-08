# Paid-to-wait put spreads — 2019–2026

*2026-09-08. `run_paid_to_wait_study.py`. Question from the buying-power discussion: when a stacked name is sitting just under its pivot and you would rather wait for the trigger than buy, can you sell a 30/15-delta put credit spread 25–45 days out and get paid to wait? The August vehicle study said yes on one month of the book's own trades; this is the seven-year test on real quotes with the cost model.*

**Method.** Events = SETUP Fridays on the liquid panel (10>20>50 SMA stacked, close within 5% under the prior-15-session high, 10-day range ≤ 0.6× the prior 20-day, 5-day volume ≤ 0.8× average, ADR ≥ 3%), 2019-10 → 2026-05, 3,241 events on 918 names. Entry legs from `options_daily_v3` bid/ask on the entry date: expiry nearest 35 DTE, short put nearest −0.30 delta, long put nearest −0.15. 1,548 spreads survived the leg and split-basis checks (median credit $1.63 on a $7.50 width, 23% of width, short-leg bid-ask 14%). Two exits: hold to expiry (settled on the panel close), or convert on the pivot break (close the spread at real bid/ask the first day the stock closes above the pivot, which is when you would buy the stock). Costs per `lib.studies.costs`. IV gate = the ticker's own trailing-252 percentile of 30-day put IV from `fwd_vol_daily`, known for only 18% of events (the table covers 1,051 names and ends 2026-02).

## Results (ROC on max loss)

| cohort | n | broke pivot before expiry | hold to expiry, gross → net | win, net | convert on break, net | stock to the same exit |
|---|---|---|---|---|---|---|
| All | 1,548 | 78% | +3.2% → **−3.3%** | 73% | **−8.3%** (t −5.8) | +1.0% |
| IV percentile ≥ 60 | 129 | 82% | +12.3% → **+5.7%** | 78% | −9.3% | +2.6% |
| IV percentile < 60 | 253 | 79% | +5.9% → −0.5% | 74% | −5.5% | +1.2% |
| IV unknown | 1,166 | 77% | +1.6% → −4.9% | 72% | −8.8% | +0.8% |

By regime state at entry (hold to expiry, net): up/B+ −5.2% (n 824), up/B− −0.8% (244), chop/B+ −8.2%, chop/B− +5.0%, bear/B+ −3.0%, bear/B− +10.9% (50). With the IV gate on: up/B− +10.9% (25), bear/B+ +14.7% (15), chop/B− +24.1% (12), up/B+ −2.3% (62).

By year (hold, net): 2019 +15%, 2020 +13%, **2021 −17%, 2022 −19%**, 2023 −0.5%, 2024 −2.7%, 2025 +0.8%, 2026 (Jan–May entries) −45% on 46 events.

## Reading

1. **As a generic rule it loses after costs.** +3.2% gross becomes −3.3% net because the credit is 23% of width and the round trip on two legs costs about 12% of it. The August book's +$1.1k on 24 closed spreads was the 2025 tape, which is the one recent year that was flat-to-positive.
2. **Never close it on the break.** Converting to stock by buying the spread back costs a second round trip and gives back the theta you were paid to wait for; every cohort is worse under that rule, t −5.8. If the stock triggers, buy the stock and let the spread expire.
3. **The IV gate is the whole edge.** Sell only when the name's 30-day IV is above its own 60th percentile: +5.7% net, 78% win, positive in every regime state except up/B+. That is a small sample (129) because the IV table is thin, and it needs the print-based IV rebuild (`run_straddle_iv_gate.py`) to be usable live.
4. **Regime matters the way the conditioning rule says it should.** Weak-breadth states pay; the most common state, uptrend with strong breadth, is where the spreads lose, because the premium is thin and the setups that fail there fail to max loss. 2021 and 2022 are the warning: in a chop or bear year the pullback names break down instead of out, and a 23%-of-width credit does not cover it.
5. **The stock alternative is not better.** Buying the SETUP name at the close and holding to the same exit averaged +1.0%, +2.6% with the IV gate. The spread with the gate beats the stock on a risk-adjusted basis; without the gate neither is worth the capital.

## Rule that survives

Sell the 30/15-delta put spread 25–45 DTE on a SETUP name **only if** its 30-day IV percentile is ≥ 60 and the regime state is not up/B+, size to max loss, hold to expiry, and buy the stock separately if the pivot breaks. Expect roughly +5 to +10% on max loss net, 78% win, and a 2021/2022-type year to be negative. Today's state is up/B−, and MU, SNDK, ALAB and LITE carry 57–81% IV, so the memory names qualify on state and on level; the percentile check is the missing piece before entry.
