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

---

## Results (run 2026-09-29, after 74c772e; `run_iv_mispricing_harvest.py`, `.log`, trades `logs/iv_mispricing_harvest_trades.csv`)

**Verdict: FAIL → NULL as a trade · MECHANISM confirmed at mid. The illiquid-decile IV mispricing is real in actual
option prices, and the bid-ask spread is almost exactly its price.**

9,700 straddles priced (of 9,749 ticker-months). D1 median straddle spread **33.5% of mid** (D10: 5.1%).

| D1, per straddle, % of mid | long-short / mo | t | halves | short-RICH | long-CHEAP | short-RICH − short-ALL-D1 |
|---|---|---|---|---|---|---|
| at mid (gross) | **+11.9%** | **3.77** | +9.1 / +14.1 | +10.2 (t 3.30) | +1.7 | **+7.4 (t 4.46)** |
| **house fills (25% of spread) — PRIMARY** | **−10.7%** | **−3.47** | −13.1 / −8.9 | −3.4 | −7.3 | +4.3 (t 2.69) |
| full crossing | −33.4% | −9.97 | | −17.1 | −16.3 | +1.2 |

D10 reference: no effect at mid (L/S −6.9%, t −1.45), as the efficiency test predicted.

- At mid the trade does what the efficiency test said: shorting the RICH-IV illiquid straddles earns +10%/month of
  premium and beats shorting the decile at random by +7.4pp (t 4.46), 14/15 years positive for the long-short.
- **Break-even fill:** the long-short loses ~0.9% of premium per 1% of spread paid; it breaks even at **~0.13 of the
  spread** (short-RICH alone at ~0.19). Our measured real fills were 0.13 — but on liquid names; illiquid names fill
  worse. At the house 0.25 it loses.
- The long-CHEAP leg adds cost without edge (+1.7% at mid); the information is in the RICH side.

**What it means for the book now.** Nothing to trade as a taker. The only possible route is a MAKER strategy — resting
sells of RICH D1 straddles near mid — whose fill rate and adverse selection cannot be measured on end-of-day data.
If Gabe wants it, the next step is a forward paper log of limit orders (price, fill/no-fill, fill time), not a backtest.
Answer to Gabe's question: **yes, illiquid options are mispriced in a predictable direction — and the spread is what
the market charges to trade against it.**
