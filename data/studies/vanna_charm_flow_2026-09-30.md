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

## Results

*(pending)*
