# Is IV mispriced in illiquid options? IV efficiency by option liquidity, spread aside (2026-09-29)

## Pre-registration (written BEFORE any data pull; do not edit this section after the results)

**Question (Gabe, 2026-09-29).** Setting the bid-ask aside: is the mid implied vol itself a worse, *predictably wrong*
forecast of subsequent realised vol in illiquid options, where fewer people look? Prior ledger work only asked whether
premium survives crossing the spread (it doesn't); IV accuracy by liquidity has never been measured.

**Unit.** Ticker × month-end, 2010-01 → 2026-02.
- **IV** = `silver.options_iv_daily.call50_iv` (50Δ call IV, quoted legs, expiry nearest 30 DTE) on the month's last
  session. Log IV.
- **Realised vol (PRIMARY)** = annualised √(252 × mean r²) of daily close-to-close log returns over the NEXT 21 sessions,
  from REAL closes: `liquid_panel_2009` ∪ `smallcap_panel_2009` (yfinance, ~2,960 names). ⚠ Not chain-spot: parity-implied
  spot is noisier for illiquid options, which would inflate RV exactly where we look.
- **Option liquidity** = trailing 21-session mean of `call_vol + put_vol` from `silver.options_flow_daily`, ranked into
  **deciles within each month** (D1 = least liquid).
- **Public forecast F** = HAR model of log RV_fwd on log past RV over 1, 5, 21 and 63 sessions, fit **out of sample**
  (each year's predictions use coefficients fit on all prior years only; predictions from 2012 on).

**Statistic (per decile).** gap = log IV − log F; outcome = log RV_fwd − log F.
OLS outcome ~ gap, SEs clustered by month. β = 1 means IV's departures from the public forecast are fully borne out;
**β < 1 means IV over-reacts (mispriced), and the part not borne out is predictable.**

**PRIMARY.** β(D10, most liquid) − β(D1, least liquid): **> 0 with |t| ≥ 3** (month-clustered, via a pooled regression
with a D1 × gap interaction), same sign in both halves (2012–2018 / 2019–2026). Pass = IV is measurably less efficient
in illiquid options.

**Reported, not in the bar.** β for every decile (the trend); mean log(IV/RV) by decile (the bias / variance premium);
R² of RV on F alone vs F + IV by decile (how much information IV adds); a **tradeable-shape diagnostic**: within D1 and
D10, sort on gap into quintiles and report mean (RV − IV) in vol points, Q5 − Q1 (how much "IV looks too high" is
wrong); the same PRIMARY with chain-spot realised vol (robustness, noise caveat above); names/months per decile.

**Known confounds.** Illiquid options sit on smaller, more volatile stocks, where HAR is also worse — the β framework
normalises by F but not perfectly; the decile rank is within-month, so level shifts across eras are removed. Survivor
panels for the primary RV. Spread is deliberately ignored here; a pass says the MID is mispriced, not that it's
harvestable (that is the follow-up).

**Cost.** Two queries on Glue summary tables (`options_iv_daily` month-ends, `options_flow_daily` monthly means),
~15 s/yr each; local regression. Approved by Gabe 2026-09-29.
