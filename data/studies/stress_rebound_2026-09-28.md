# Does the S&P rebound after stress Fridays? — NOT CONFIRMED out of sample (2026-09-28)

**Why:** the certified stress bucket's return is its delta's share of the post-selloff rebound (`stress_vehicle_h2h_2026-09-28.md`). The certification used 2010+ only, so 1990–2009 is a clean holdout for the mechanism itself.
**Script:** `run_stress_rebound.py` (pre-registered). **Log:** `logs/stress_rebound.log`. Fridays: `logs/stress_rebound_fridays.csv`.

## Design
- **Data:** ^GSPC and VIX, 1990 → 2026-09. 1,841 Fridays, of which 361 are stress Fridays (close < 50 SMA & VIX ≥ 20) in 61 episodes.
- **Outcome:** forward 20-session index return from the Friday close, vs non-stress Fridays in the same window. Clustered by episode, with an episode block bootstrap.
- **PRIMARY:** the 1990–2009 holdout must show excess > 0 at t ≥ 2, with the same sign in 2010–26.

## Result (20 sessions)
| window | stress mean | control | **excess** | t | episodes positive | worst |
|---|---|---|---|---|---|---|
| **HOLDOUT 1990–2009** | +0.11% | +0.68% | **−0.56pp** | **−0.68** | 71% of 28 | −28.2% |
| holdout without 2007-06…2009-06 | | | +0.25pp | 0.36 | 25 episodes | |
| 2010–2026 (certification era) | +2.66% | +0.68% | **+1.98pp** | **4.88** | 94% of 33 | −16.3% |
| ALL 1990–2026 | +1.12% | +0.68% | +0.44pp | 0.68 | 84% of 61 | −28.2% |

- **By decade:** 1990s +1.15pp, **2000s −0.84pp**, 2010s +2.00pp, 2020s +1.94pp.
- **Other horizons (holdout):** 5 sessions −0.06pp (t −0.21), 45 sessions −1.08pp (t −0.88).
- **Stricter controls in the holdout** (below the 50 SMA with low VIX; VIX ≥ 20 above the 50 SMA): −1.09 / −0.86pp.
- **2008 in particular:** the GFC stress Fridays averaged −2.26% over the next 20 sessions (worst −28.2%) and are 17% of all stress Fridays.

## Verdict
**NOT CONFIRMED · YIELD MECHANISM.**
- The stress-Friday rebound is a **post-2010 phenomenon** (+2pp/month, t 4.9). It does not appear in 1990–2009 (−0.56pp), and even without the GFC it is only +0.25pp (t 0.36).
- Stress-Friday returns are also about twice as volatile as the control's (SD 7.4 vs 3.5 in the holdout). So in 2000–02 and 2008 the regime marked **continued declines, not rebounds**.
- **By the pre-registered rule, the certified stress bucket's evidence rests on 2010+ only → recommend PARKED.**
- **Status is Gabe's decision** and is not changed in §0 here. If kept, keep it at token size, relabeled as "post-2010 stress-rebound regime, capped via the vertical". The capped vertical is the right vehicle for a bet whose failure mode (2008) is a continued decline.
