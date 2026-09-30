# Harvesting the illiquid-decile IV mispricing at real fills (2026-09-29)

## Pre-registration (written BEFORE the pull; do not edit this section after the results)

**Why.** `iv_efficiency_by_liquidity_2026-09-29.md` (+ its horizon/earnings addendum): on ticker-months with a 21–40 DTE
expiry and no earnings in the window, mid IV is less efficient only in the least-liquid option-volume decile (β 0.61 vs
~1.0), with a gap-sorted RV − IV shape of −7.7 vol points. Question: does selling the rich / buying the cheap there
survive the spread?

**Population (frozen).** The addendum's clean subset (IV expiry 21–40 DTE, no earnings within max(DTE, 31) days, earnings
coverage), deciles re-ranked within month on 21-session option volume, **D1 only**. Within each month's D1, rank on
gap = log IV − log F (the out-of-sample HAR forecast): **RICH = top third, CHEAP = bottom third.**

**Trade.** At the month-end close, the ATM straddle in the same expiry `options_iv_daily` used (the v3 expiry with
21–40 DTE nearest 30): strike = the call strike with delta nearest 0.50, put at the same strike. **Short** the straddle
for RICH names, **long** for CHEAP. Held to expiry, settled at intrinsic on the RAW chain-implied spot
(`chain_spot_daily`, unadjusted) of the expiry date (or the last session before it). Unhedged.
**Fills:** PRIMARY = house model (mid ∓ 25% of each leg's quoted spread) + $0.0065/share/leg; also mid (gross) and full
crossing (bid/ask). Return = P&L ÷ straddle mid at entry (so vol-point-comparable across names).

**PRIMARY.** Monthly long-short return = mean(short-RICH returns) + mean(long-CHEAP returns) at house fills;
month-clustered t **≥ 3**, both halves positive (2012–2018 / 2019–2026), positive in a majority of years.
**Reported:** each leg alone; short-RICH minus short-ALL-D1 (does the gap sort add anything beyond the decile's average
variance premium?); median straddle spread as % of mid; the same trade in D10 as a reference.

**Limits.** Unhedged straddles carry some directional noise; ~30 names/month in D1, so ~10 per side. Survivor-biased
close panel defined the population; option prices are v3 (all names).
**Cost.** One Athena join on v3 (temp table of ~3–4k ticker × month-end pairs, ATM ±2 strikes) + the cached chain-spot.
Approved by Gabe 2026-09-29 ("go").
