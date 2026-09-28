# Stress-bucket vehicle vs its BETA: the certified spread has no premium beyond the delta-matched SPY move (2026-09-28)

**Context:** a parallel session had already run a return head-to-head today (`stress_bucket_h2h_2026-09-28.md`, 12:13, commit c80deff: spread vs 45d 12Δ naked = EQUIVALENT on return). I missed it before starting, against the standing rule to check git log and TEST_INDEX first. This test adds the axes that one did not have: **the beta control**, **30-DTE low-delta naked legs**, and **the synthetic 2008 test**.
**Script:** `run_stress_vehicle_h2h.py` (pre-registered). **Logs:** `logs/stress_vehicle_h2h.log` and `logs/stress_bucket_beta_check.log` (the control applied to the parallel session's 113 spread trades). Trades: `logs/stress_vehicle_h2h_trades.csv`.

## Design
- **Days:** stress Fridays 2010–2026 from v3; 32 episodes.
- **CERT:** 20-DTE 0.25/0.15 vertical with a 50% take-profit (92% of trades hit it).
- **Naked:** 30-DTE 10Δ / 5Δ puts, held to expiry.
- **Measure:** return on capital (spread = max loss; naked = Reg-T) minus the return of the position's entry delta held in SPY over the trade's own window, carry-adjusted. Clustered by episode.

## Result
| arm | RoC / trade | beta part | **excess over beta** | t | halves |
|---|---|---|---|---|---|
| CERT (my rebuild, 119) | +5.03% | +5.44% | **−0.41%** | −0.33 | +0.99 / −1.24 |
| CERT (parallel rebuild, 113; net delta 0.10) | +8.15% | +8.05% | **+0.11%** | 0.06 | +1.22 / −0.44 |
| … at net delta 0.08 / 0.12 | | | +1.72 / −1.50% | 0.91 / −0.95 | |
| NAKED 30d 10Δ | +4.35% | +2.50% | **+1.85%** | **3.16** | +2.02 / +1.76 |
| NAKED 30d 5Δ | +2.73% | +1.53% | **+1.20%** | **4.19** | +1.03 / +1.29 |

**PRIMARY (pre-registered), paired NAKED10 − CERT excess:** +1.90pp/trade, **t 1.15**, halves −0.82 / +2.99 → **no switch; KEEP the certified vehicle**. NAKED05 − CERT +1.27, t 0.82.
**2008 synthetic** (hold to expiry, both arms), mean RoC: CERT −4.6%, N10 −2.3%, N05 −1.9% → naked PASSES on mean. ⚠ The naked put's worst trade was −192% of Reg-T margin, against CERT's −100% (capped).

## Verdict
**Vehicle: KEEP (no switch, t 1.15). MECHANISM, and it bears on the certification:**
- On two independent rebuilds, **the certified 0.25/0.15 vertical earns nothing beyond the SPY move its delta already carries.** Its return is the stress regime's post-selloff rebound, leveraged and loss-capped, not a volatility premium. The long 15Δ leg buys back the premium, and the 50% take-profit exits during the rebound.
- **Naked 30-DTE low-delta puts do carry a premium beyond beta** (+1.2 to +1.9% of Reg-T margin per trade, t 3.2–4.2, both halves). But they don't beat the vertical on the paired test, and their 2008 tail is uncapped.
- **Open question for Gabe (a status decision, not changed here):** the §0 certification (t 6.07) certified a rebound, not a vol premium. The underlying claim, "SPY rebounds after stress Fridays", is the real mechanism. It is untested on its own with 2008 included (the Steenbarger row in §10 is the nearest). It should be tested directly before the bucket is sized as a premium strategy.
