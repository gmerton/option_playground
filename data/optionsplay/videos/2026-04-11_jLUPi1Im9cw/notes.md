# OptionsPlay: "Stop Buying Options. Get Paid to Wait Instead." (Tony Zhang, 2026-04-11, 41 min)

_Reviewed 2026-09-24. Growth Lab session recorded during the Iran-war two-week pause. Transcript in this folder. The first ~1 min is a cold-open repeat of 06:48._

## Verdict: 1.5 / 5. The title promises a method and the video delivers a macro call

There is no "paid to wait" framework here. It is a week's positioning commentary: the Strait of Hormuz, oil at
$100, a 1970s stagflation analogy, and five trade ideas taken from the platform's watchlists. The selection rule,
as far as there is one, is: **form a macro thesis → open the matching themed watchlist → take the names with a
platform "buy/sell signal" (trend + RS 9/10) → sell a credit spread in the direction of the thesis, at a
"resistance" or "support" level, sized to ~2% of the account.** He picks a credit spread over a debit spread when
the quoted risk:reward is near 1:1 and switches to a debit spread when it isn't (ARM, ELV).

No backtest, no sample, no costs, and every risk:reward is read off the platform at the quoted price. All five
trades are n = 1 and live, and none has a stated exit. The one checkable structural claim (index call spreads are
unusually rich because "upside calls are juiced") conflicts with our results on the call side.

## Trades and claims against our ledger

| @ | Claim / trade | Our evidence |
|---|---|---|
| 09:01–12:15 | **Sell a QQQ May 615/630–635 call spread at resistance.** "Near 1:1 risk-reward, incredibly rare for index call spreads, the skew favours it" ($1,700 credit on $2,200 risk, 2 lots) | ❌ **Against on every axis we have.** (1) ETF bear-call side, 20 ETFs, 45 DTE, 0.35/0.25Δ: **nothing**, and the condor that nets direction out is +0.36%/trade, t 0.60 (`etf_condor_call_side_2026-09-16.md`). (2) Our 1:1 comes from **moving the strike toward the money**: a short strike ~$5 OTM on ~$610 is <1% OTM. Dialling credit/width with your own strikes is ARM B, flat (`2026-07-25_YfrZT_kTo_4/notes.md`: narrowest wing −0.04, the rest +2.66 to +3.10 with no trend). The ratio informs across names, not within one. (3) Skew as a signal: **NULL**, nothing beyond the VIX level (SPY 25Δ, vol t −1.22 vs vix_pct t +6.54) (`skew_signal_2026-09-22.csv`, TEST_INDEX §9). (4) Every call-spread screener strategy we costed is net negative: UVXY call leg −7.4% (t −3.65), UVIX −8.8% (t −2.81), SQQQ −2.3% (§1) |
| 12:48, 25:26 | **Sell upside instead of buying puts** as the hedge: "they don't need to go lower to profit" | ⚠ **PARTIAL.** A short call spread is not a hedge. It caps a small gain and gives up nothing on a crash beyond the credit. The only overlay we have measured, PMCC-style short calls, pays in down years (2022 +10.4pp, t 3.45) and costs in 6 of 8 up years (`pmcc_study_2026-09-23.md`). Paying months cannot be forecast (`breakout_regime_feedback`). Buying puts is no better: 5Δ same-expiry tail puts were −100% on all 75 trades [WL-5f] |
| 06:48–08:31 | S&P 650 / 690 and QQQ 613–615 are "the" levels, and a failure there means lower | **Untested as stated for the index.** On single names, level triggers are **NULL 0/12** (pivot, PDH, PDL, 21 EMA, 50 SMA, anchored VWAP, OR high, −0.06 to −0.10R) (§5) |
| 14:30–17:28 | **XLE short put spread on the pullback** after the oil spike ("better entry than chasing") | ⚠ **Blocked / weak.** The XLE bull put bearish-high-IV cell is **not reproducible** from our cache (§8, episodic only). Oil transmission map: no lag, **no continuation edge**, and the trade dies once the equity has run >10% (§7). Paid-to-wait, the closest structural test (30/15Δ put spreads under a pivot): generic **−3.3% net**. Only the IV ≥ 60th-pct subset is positive (+5.7% net, n 129, **not certified**, see the discrepancy note). Selling after an IV spike is the right *side* of that gate, but the gate is unproven |
| 17:28–19:39 | **CVX put spread** on a platform buy signal (RS 9/10, pullback), sized to **~2% of account at max loss** | ⚠ **PARTIAL.** Trend + RS signals add nothing on single-name short puts (BCI §2), and down-day RS **INVERTS** (−3.51pp t −3.33). Sizing to max loss is our own rule. 2% is 3× Brandt's 60–70 bp and is not tested here. The size lever that tests is *exclusion* (+0.29R OOS), not the risk fraction |
| 25:33–26:39 | **TLT bear call spread** (stagflation: long duration underperforms), "1.5:1 is rare" | ❌ **Our TLT bear call is TIER U**: +2.3% net, t 0.88 (`tierc_significance_2026-09-22.csv`), and **−0.93% even in its high-credit/width half** (`cw_rescue_2026-09-22.csv`). The TLT regime switch died after costs 2026-09-08. His "be aggressive with strikes" is again credit/width dialled by moving closer to the money |
| 31:21–32:22 | ARM: the put-spread risk:reward "isn't amazing", so **buy a call debit spread** instead (June 175), 2 lots | ✅ **PARTIAL AGREE.** On 4,742 paired entries the call debit 30/15 beat the put credit 30/20 per dollar at risk in **every IV-rank tercile** (NULL for the IV-rank flip itself, t 0.68). Against delta-matched stock the call debit leads **+$97/contract, t 2.29**, not adopted (fails its SPY < 200 SMA bar) (§9 vehicle rows) |
| 35:32 | ELV 310/350 call debit spread, "risk $1,600 to make $2,400" | n = 1 thesis trade (Medicare rate news). Catalyst-classification is our open residual (catalyst queue), and buying the event itself fails |
| 24:00–25:03 | 1972–73 embargo: oil +300%, gold +100%, S&P −50% | Descriptive history, not a signal. The book's regime work says the paying months cannot be forecast |
| 13:37, 20:18 | Portfolio "barbell": high-beta AI names + defensives | Untestable as stated (no rule) |

## What's new / test candidates

1. **None.** Index and ETF call spreads (`etf_condor_call_side`, UVXY/UVIX/SQQQ/TLT costing, `cw_rescue`), skew
   (`skew_signal`), levels (§5), selling put spreads on setup names (`paid_to_wait_study`) and vehicle choice
   (`ivrank_vehicle`, `vehicle_benchmark`) all have rows. The one idea with a new label, *call* skew richness as a
   bear-call selector, reduces to cross-sectional credit/width on a single name (QQQ). That gives it no
   cross-section to sort, and the within-name dial is the ARM B null.
2. **Lesson worth keeping:** his repeated "near 1:1 is rare" is the within-name credit/width dial again. Moving the
   short strike toward the money raises the ratio mechanically, and raises the loss rate with it (ARM B:
   realised win rate tracks the break-even win rate within 0.5–3pp).

## ⚠ Discrepancy found in our own docs (paid-to-wait, cited above)

`paid_to_wait_study.md` reports **trade-weighted** means: IV ≥ 60 **+5.7%** (n 129), IV < 60 **−0.5%** (n 253), all
**−3.3%** (n 1,548). The t-stats in `missing_tstats_2026-09-22.csv` are **month-weighted**: gated **+7.4% (t 1.53)**,
and "ungated" = the IV < 60 cohort at **−9.7%** (t −1.79). So "gated − ungated +16pp, t 2.29" (37 months) compares
IV ≥ 60 with **IV < 60**, not with the −3.3% pool. The trade-weighted gap for the same comparison is only
**+6.2pp** (+5.7 vs −0.5). `sosnoff_doctrine.md` C3 puts "+5.7% vs −3.3% ungated" next to "t 2.29", which mixes
the two framings. Neither changes the verdict (NOT CERTIFIED), but quote the gate as "+5.7% trade-weighted /
+7.4% month-weighted, t 1.53 on its own", and give the +16pp/t 2.29 only as the month-weighted gap against IV < 60.
Recomputed from `paid_to_wait_events.csv` 2026-09-24, with no new query.
