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

---

## Results (run 2026-09-29, after the pre-registration above was committed in e4149be; `run_iv_efficiency_by_liquidity.py`, `.log`)

**Verdict: PASS on the pre-registered statistic → SUPPORTED as a MEASUREMENT: the mid IV of illiquid options is a much
worse forecast of realised vol, and the error is predictable. Mechanism NOT established — see the open alternative.**

213,448 ticker-months, 2,415 names, 2012–2026 (out-of-sample HAR).

| decile (option vol) | median contracts/day | β (share of IV's gap borne out) | mean log(IV/RV) | R² F → F+IV | RV − IV, gap Q5 − Q1 (vol pts) |
|---|---|---|---|---|---|
| **D1 least liquid** | 15 | **0.31** | +0.23 | 0.39 → 0.44 | **−28.8** |
| D2 | 61 | 0.50 | +0.15 | 0.41 → 0.50 | −17.2 |
| D5 | 547 | 0.69 | +0.10 | 0.50 → 0.62 | −10.1 |
| D9 | 8,426 | 0.81 | +0.09 | 0.55 → 0.69 | −4.9 |
| **D10 most liquid** | 33,483 | **0.92** | +0.07 | 0.63 → 0.76 | −3.0 |

**PRIMARY β(D10) − β(D1) = +0.61, t 17.2; halves +0.63 (t 16.4) / +0.54 (t 15.1).** Monotone across all ten deciles.
Robustness on chain-spot RV: +0.49, t 13.9, same gradient.

Reading: in the most liquid options, when IV sits above the public (past-RV) forecast, ~92% of that gap shows up in
realised vol. In the least liquid, only ~31% does; and the names whose IV looks richest vs the forecast realise ~29 vol
points less than IV, relative to the names whose IV looks cheapest. Illiquid IV is also biased high on average
(IV ≈ 26% above RV in logs vs ~7% for D10).

### ⭐ "A clean result is a bug until proven otherwise": checks run (not pre-registered, reported for the read)
1. **Quote noise (errors-in-variables)?** If the mid were random noise inside a wide quote, instrumenting the gap with
   LAST month's gap would restore β. It does not: D1 0.25 vs D10 0.82. And D1 gaps are MORE persistent month to month
   (autocorrelation 0.41 vs ~0.30), the opposite of iid noise. (A first attempt instrumented with NEXT month's gap; that
   instrument is mechanically invalid — next month's HAR includes this month's realised vol — and was discarded.)
2. **A few odd names (fixed effects)?** Within-ticker (demeaned) β: D1 0.38 vs D10 0.96. Holds inside the same stock.
3. **⚠ NOT YET EXCLUDED — horizon/event mismatch.** `call50_iv` uses the expiry nearest 30 DTE within 10–60; illiquid
   names often list only monthlies, so their IV can span ~50 days and include an earnings date the 21-session RV window
   misses. That would make IV look "too high vs what followed" persistently, most in illiquid names, with no mispricing.
   Next check: pull `skew_dte` and earnings dates; re-run on ticker-months with DTE 21–40 and no earnings inside either
   window. Until then this is a measurement, not a mispricing claim.

**What it means for the book now.** Nothing tradeable yet. If the effect survives check 3, the shape is "sell
illiquid-name vol when its IV is rich vs the realised-vol forecast" (−29 vol-pt gradient), and the follow-up is whether
that exceeds the spread (straddle bid-ask in these names is often 20–40% of premium).

## Addendum pre-registration: horizon / earnings check (written 2026-09-29 BEFORE the check ran; do not edit after)
Same panel, forecast, deciles-within-month (re-ranked on the subset) and PRIMARY statistic, restricted to ticker-months
where (a) the IV's expiry is 21–40 DTE (`options_iv_daily.skew_dte`, the same nearest-30-DTE expiry `call50_iv` uses),
and (b) NO earnings date (union of `earnings_yf.parquet` sessions and MySQL `earnings_report`) falls in
(month-end, month-end + max(DTE, 31) calendar days], and (c) the ticker has ≥ 1 earnings date on file within ±400 days
(so "no earnings" is not missing data). Earnings dates are scheduled in advance, so (b) uses no outcome information.
**Read:** β(D10) − β(D1) keeps |t| ≥ 3, both halves > 0 AND ≥ half its full-sample size (≥ +0.30) → the effect SURVIVES
the horizon/event explanation. Otherwise → horizon/earnings mismatch explains it (downgrade to NULL as a mispricing).

## Addendum results (run after 3896c68; `run_iv_efficiency_horizon_check.py`, `iv_efficiency_horizon_check_2026-09-29.log`)

**Read per the addendum: SURVIVES** — β(D10) − β(D1) = **+0.415, t 9.43**, halves +0.54 (t 6.8) / +0.34 (t 6.5), ≥ +0.30.
**But most of the original effect WAS the horizon/earnings mismatch**, and what remains is confined to the least liquid
tenth of a much more liquid subset:

- The mismatch was concentrated exactly where suspected: only **20%** of D1 rows had IV at 21–40 DTE vs **94%** of D10.
- Clean subset: 48,130 ticker-months, 1,304 names (the truly illiquid names mostly drop out: subset D1's median option
  volume is 126 contracts/day vs 15 in the full-sample D1). 
- β by decile: D1 **0.61**, D2–D10 **0.87–1.07** (flat, ≈ efficient). The monotone gradient is gone; one decile remains.
- Bias: D1 log(IV/RV) +0.105 (was +0.228). Tradeable shape in D1: gap Q5 − Q1 RV − IV **−7.7 vol pts** (was −28.8);
  D2–D10 −1.6…+3.5 (nothing).
- Note: per-decile clustered SEs are ~0.17 on the subset; the difference's t 9.4 is tighter because month shocks are
  shared across deciles (the pooled interaction nets them out).

**Final verdict: SUPPORTED, NARROW.** Mid IV is still measurably less efficient in the least-liquid decile of names that
have a ~30-DTE expiry (β 0.61 vs ~1.0), after removing horizon and earnings effects — but the effect is ~¼ of the
headline, lives in one decile, and the raw −29-vol-pt shape was mostly structural (longer-dated IV, earnings inside the
IV window). **For the book:** nothing tradeable yet. The follow-up, if pursued, is the harvest test on that one decile:
sell rich / buy cheap ATM vol at real bid/ask in D1 names with 21–40 DTE and no earnings, vs the −7.7 vol-pt gradient.
