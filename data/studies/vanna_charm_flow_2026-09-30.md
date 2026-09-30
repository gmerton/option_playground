# Dealer vanna and charm hedging flows: do they move SPY? (2026-09-30)

## Pre-registration (written BEFORE any vanna/charm number was computed; do not edit this section after the results)

**Why.** Every non-delta greek on this desk has been tested as a *position* (VRP, straddles, FVR, skew) or as a
*dealer regime* (GEX, certified mechanism, SPY t 7.7). The two second-order dealer greeks have never been
touched (TEST_INDEX has no vanna/charm/opex row, checked 2026-09-30). Practitioners (SpotGamma et al.) claim:
- **charm:** as time passes, OTM option deltas decay toward 0, so dealers mechanically re-hedge; the flow is
  largest into monthly expiry ("opex tailwind", then the "window of weakness" after);
- **vanna:** when IV falls, OTM option deltas shrink, so dealers re-hedge in the same direction as the vol move
  ("vol crush → dealers buy"); this amplifies the spot move that accompanies a vol change.

**Data.** `data/cache/spy_chain_v3/<year>.parquet` (from `run_spy_chain_v3_pull.py`: every SPY contract DTE 0–70,
bid/ask IV, OI, delta), 2010-01-04 → 2026-02-27 (the feed loses OI in 2026-03). No new Athena pull. SPY 1-min bars
(`data/cache/intraday_hist/SPY_1min.parquet`) for returns and dollar volume, ^VIX from yfinance.
⚠ DTE ≤ 70 truncation: longer-dated vanna is omitted; charm is concentrated short-dated so it is barely affected.
⚠ OI in 0DTE opened and closed the same day is invisible (same blind spot as GEX).

**Greeks.** Per contract on day t−1: σ = mid of bid_iv/ask_iv (rows with either ≤ 0 dropped), T = calendar days to
expiry / 365 (floor 0.5 day), S = raw spot from the chain (`lib.studies.chain_spot.spot_from_chain`), r = q = 0.
Black–Scholes: vanna = ∂Δ/∂σ = −φ(d1)·d2/σ (same for calls and puts);
charm = the change in Δ as time passes, computed as Δ(T − n/365) − Δ(T) by finite difference at fixed S and σ
(no sign-convention risk from the closed form; n defined below). Strikes within ±20% of S.
Expiring-today contracts (DTE 0 on t−1) are excluded: they are gone by day t.

**Dealer position.** The SAME naive convention as the GEX study, so the two are comparable: customers long calls
and short puts, so dealers are **short calls, long puts**: pos = −OI (calls), +OI (puts), ×100 shares.
⚠ The true sign is unobservable and practitioners use the opposite one for puts. **Therefore both primary tests are
TWO-SIDED**: the coefficient's size is the test; its sign tells us which convention the data favour. A significant
negative coefficient is reported as "consistent with dealers short puts", not as a failure.

**Flows, known at the t−1 close, in $ of SPY the dealers must BUY (negative = sell), ÷ SPY 20-day avg $ volume:**
- **CF_t (charm flow)** = −Σ pos · 100 · [Δ(T − n/365) − Δ(T)] · S, n = calendar days from t−1's close to t's close
  (3 over a weekend). The hedge is minus the dealer delta change.
- **VEX_{t−1} (vanna exposure)** = −Σ pos · 100 · vanna · 0.01 · S = $ the dealers must buy per **+1 vol point** in
  IV (parallel shift, sticky strike). Flow on day t: **VF_t = VEX_{t−1} · ΔVIX_t** (VIX points, a proxy for the
  chain's parallel IV change).
Both winsorised at 1/99%.

**Test 1 — CHARM (PRIMARY A).** r_t = SPY log return close t−1 → close t, bps.
r_t = a + b·CF_t + FE(trading days to the monthly 3rd-Friday expiry, 0…15, 15 = "15+") + FE(weekday)
      + c·log VIX_{t−1} + d·r_{t−1} + e·NEG_t (GEX < 0, from the GEX study's cache) + ε, Newey-West 5 lags.
**What the control varies:** the opex-cycle fixed effects absorb the *calendar* (the average opex-week drift), so b
is identified only from how BIG the charm flow is on a given cycle day versus the same cycle day in other months,
i.e. from open interest and moneyness, which is the mechanism. Without that FE, b would just re-measure the opex
calendar effect.

**Test 2 — VANNA (PRIMARY B).** Same-day mechanism test (not tradeable, like the GEX regime):
r_t = a + b·VF_t + g·ΔVIX_t + h·ΔVIX_t·log VIX_{t−1} + k·ΔVIX_t·NEG_t + c·log VIX_{t−1} + e·NEG_t + ε, NW 5 lags.
**What the control varies:** ΔVIX_t alone absorbs the ordinary spot–vol correlation (which runs both ways); the two
interactions absorb "the spot–vol beta is different in high-VIX and negative-gamma regimes". What is left for b is:
does the return response to a vol change scale with the *pre-known* dealer vanna book.

**Bar (both tests).** |t| ≥ **3.2** (Šidák over the 2 primaries at the house t 3 level), the same sign in both halves
(2010–2017 / 2018–2026-02), and the same sign in ≥ 10 of the 16 full years (per-year table reported: chronological
halves do not catch a back-half regime). Effect size reported as bps of SPY per 1 SD of the flow.
Verdicts: PASS → MECHANISM (like GEX), not a trade; below the bar → NULL / UNDERPOWERED by the house scheme.

**Exploratory, reported, no verdict:** the opex-cycle FE profile itself (the calendar "tailwind / window of weakness"
claim, one descriptive table); b for Test 1 without the opex FE; Test 1 on the open→close return; CF split by the
flow's DTE bucket (0–7 / 8–70); 2022+ only (daily expiries).

**Not tested (named so they can't be added quietly):** alternative dealer conventions beyond the sign read-off above,
any trading rule, QQQ (only if SPY passes a primary, as a replication), single stocks, per-contract IV changes instead
of ΔVIX, intraday timing of the flows. One definition per test, one run.

**Where it runs.** Local: the chain cache is on disk (~11M rows), no Athena, minutes of CPU.

---

## Results (run 2026-09-30, after the pre-registration above; `run_vanna_charm_flow.py`, log `logs/vanna_charm_flow.log`, daily panel `logs/vanna_charm_flow_daily.csv`)

**Verdicts: Test 1 (charm) NULL · Test 2 (vanna) NULL.** 3,981 SPY sessions 2010-01-05 → 2026-02-23, 7.49M chain rows.

| test | full-sample b | NW t | bps of SPY per 1 SD of flow | halves (t) | years same sign |
|---|---|---|---|---|---|
| **T1 charm** (CF → r_t, opex-cycle FE) | +34.1 | **0.89** | +1.7 | −1.64 / +1.30 (flip) | 9 / 17 |
| **T2 vanna** (VEX·ΔVIX → r_t, spot–vol controls) | −63.1 | **−1.18** | −6.9 | **+3.00 / −2.26 (flip)** | 10 / 17 |

Neither is near the 3.2 bar and both flip sign between halves, so neither dealer convention is favoured.
T2's per-year t is dominated by 2024 (−7.7), a single-year spike (the 2024-08-05 VIX event sits in it), and 2018
(−3.4); 2010–17 goes the other way. That is instability, not a mechanism.

**Sanity:** under the naive convention CF is negative every day (dealers short calls / long puts, so decay makes
them sell), mean −0.076 of 20-day ADV; VEX correlates −0.70 with log VIX, which is why the spot–vol interactions
with log VIX were in the control.

**Exploratory (no verdict, charged at 16+ cells):** T1 without the opex FE t 1.48; T1 on open→close t 2.14; charm from
DTE ≤ 7 only t 0.76; 2022+ (daily expiries) T1 t 1.09, T2 t −2.15. The opex-cycle calendar profile shows expiry day
itself at **−21.6 bps, t −3.13** and 3 sessions before at **+22.8 bps, t 3.21**, the other 14 cells |t| < 2. With 16
cells the Šidák bar is ~3.4, the two extremes are adjacent-but-opposite, and the charm flow does not explain them
(T1 with the FE is null), so this is a calendar lead at most. It is **not** evidence for the charm story.

**YIELD: METHOD.** BS vanna/charm from the v3 chain (mid IV, chain spot, finite-difference charm) is now reusable
in `run_vanna_charm_flow.py`; the daily flow panel is cached.
