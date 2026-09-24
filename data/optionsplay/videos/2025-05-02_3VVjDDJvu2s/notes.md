# OptionsPlay — "I Built the Ultimate Algorithm to Trade Earnings!" (Tony Zhang, 2025-05-02, 48 min)

_Reviewed 2026-09-24. This is the launch webinar for the **Earnings Navigator**, an emailed weekly list of
names that pass his three-step earnings screen. He says the algorithm was built "last week" (34:08), and
the first email went out the Friday before. The description promises "how the algorithm performed", but no
performance is shown. Transcript in this folder. The 2025-07-20 video with the same title
([RokhF9v62HE](../2025-07-20_RokhF9v62HE/notes.md)) is a **different session**, not a re-edit (see that
note). The 2026 successor is [yLQt8UZNS8Q](../2026-07-18_yLQt8UZNS8Q/notes.md)._

## Verdict: 1.5 / 5

The screen is mechanical except for the valuation leg: (1) absolute trend over the past week to month,
(2) relative strength against the S&P in the same direction, and (3) a valuation "disconnect" against the
industry. On names that pass, he buys a ~50Δ short-dated call or put **right before the print**. He calls
it "proven to make big moves on earnings" (08:19) but shows no sample, no hit rate, no control and no
track record. A tool built the week before cannot have a track record.

The two technical legs are the part we can check. An exploratory re-cut of our 4,477-event earnings set
(below) finds that **trend + RS alignment predicts the reaction's direction no better than a coin flip:
50.0% for bull setups and 49.6% for bear setups**. An ATM option bought in the trend direction at the ask
and settled at the front expiry returns **−16.6% of premium (date-clustered t −3.03)**. It does no better
than the same option bought in the *opposite* direction (−2.2pp, t −0.15). Aligned names do carry
**bigger implied moves** (8.2–8.7% vs 5.7%), but they realise **less** of them (0.91 vs 0.97 of implied).
So the "big move" is already in the price, and the buyer pays for it.

He also contradicts himself in Q&A. QCOM is on the list although the platform shows its trends bearish,
and his defence is "the most undervalued stocks are the most bearish stocks … buy low" (42:20–43:27). That
is the opposite of steps 1–2.

## Data audit

| item | what he shows |
|---|---|
| Backtest / sample | **None.** "these are the stocks that have been proven to make big moves on earnings" (08:19), with no numbers |
| Track record | **None.** Algorithm "built last week" (34:08); one email sent. The description's "how the algorithm performed" is not in the session |
| Pricing | Single platform quotes, at the mid (META 547.5C ~$23, MSFT 392.5C $10.80, QCOM 148C $5.65) |
| Statistic / control | None |
| Alignment rate | "only about 20% … 20 to 30% of the time" trend and RS align (13:58–14:18). Unverifiable without his definition. Ours: 82% of events align on sign alone, 44% at ≥ 5% / ≥ 5pp |
| "AI" | An LLM scores charts and fundamentals (19:57–20:42). Opaque, so it is not reproducible and not testable as built |

## Platform pitch vs testable rules

- **Pitch:** the Earnings Navigator email, the AI scoring, the liquidity-coloured calendar, the free trial.
  That covers roughly the first 7 minutes and 18:25–22:59.
- **Testable:** (a) liquid names only; (b) trend and RS agree over the past week to month; (c) valuation
  vs industry (forward P/E against net margin); (d) buy ~50Δ, short-dated, at the close before the print;
  (e) outright over vertical unless the stock is expensive; (f) exit when wrong, no stop, no hold to expiry.
  Only (a), (b), (d) and (e) can be checked with data we hold. Checking (c) needs point-in-time fundamentals, which the repo doesn't have.

## Claims against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 04:36–05:21 | Sort the earnings calendar by **options liquidity** and ignore illiquid names | ✅ **AGREES.** The earnings vol premium survives costs **only** in the top ~40% by volume (+0.284% at the bid, 7/8 years, t 1.1, PARKED), and the median straddle spread is 10.5% of mid (`earnings_vol_premium_2026-09-20.md`) |
| 07:39–09:09, 39:32 | **Trend + relative strength in the same direction = institutional accumulation/distribution**, "the sign of some edge" going into earnings | ❌ **Direction is a coin flip on our events** (exploratory, below): hit rate 50.0% bull / 49.6% bear. Bear-aligned names actually drifted **up** to the front expiry (+0.97% mean). Outside earnings, our RS evidence is also negative: the down-day RS selection filter is INVERTED (−3.51pp at 63d, t −3.33, `run_downday_rs_selection.py`), and RS12 as a sort is NULL (TT c9 −0.090, t −0.95, `trend_template_ablation_2026-09-22.md`) |
| 09:55–10:43, 15:19–17:38 | **A valuation "disconnect" (forward P/E vs industry, against net margin) is what earnings re-rates** | **UNTESTED.** We hold no point-in-time fundamentals. See "Not tested, could be" |
| 16:52, 28:27 | Names that pass all three "have the highest probability of making a big move on earnings" | ⚠ **The market already prices it.** Aligned names carry bigger implied moves (median 8.2% bull / 8.7% bear vs 5.7% mixed) but realise less relative to implied (0.91 vs 0.965, Welch t −2.36). "Big mover" is a vol forecast the options market has already made |
| 23:44–26:54, 41:55 | Buy a **~45–50Δ short-dated call** (META, MSFT, QCOM); "a 50 delta is usually a good starting point" | ❌ **Negative at real fills** (exploratory): an ATM option in the trend direction, bought at the ask the session before the print and settled at the front expiry, returns **−16.6% of premium, t −3.03**, with halves −25.2 / −8.0 and 7/8 years negative. At mid it is −9.3% (t −1.59). This is half of a long straddle, and the straddle buyer pays the **+0.601%-of-spot** event premium at mid before any spread (`earnings_vol_premium_2026-09-20.md`) |
| 26:45–26:54 | QCOM: a ~9% expected move against risking ~3% of the stock's value is attractive | ⚠ Framing error. The expected move **is** the price of the straddle (41:00), so both sides are already paid for. By 41:47 it had fallen to 6.5% on the same name |
| 33:27–33:59 | Buy **the day of / right before the close**, not a week or two early | ✅ **Consistent.** Buying days early loses to theta: the front-expiry straddle loses −3.4 / −6.9 / −14.3% **at mid** for entries −3/−5/−10 sessions before, with 8/8 years negative (`earnings_ramp_2026-09-20.md`) |
| 32:46–33:20 | Prefer the **outright call** ("unlimited upside"); use a vertical only to cut the capital outlay on a high-priced stock | ✅ **Consistent with our friction finding.** A second leg cost −27.1pp (t −5.51) in the event-spread test, and the cap bound on only 1.7% of trades (`event_spread_2026-09-20.md`). ⚠ That test was on **FOMC/election** events, not earnings. ⚠ The 2025-07-20 session reverses this preference (RokhF9v62HE 19:30) |
| 36:23 | You are "not too worried about time decay or volatility crush" because you are "just in and out" | ❌ **CONTRADICTED.** The crush happens **at the print**, which is exactly what he holds through. The event premium (+0.601% of spot at mid) is the measured cost of that crush to the buyer. In the ramp study, theta beats vega (`earnings_ramp_2026-09-20.md`) |
| 32:01–32:33, 35:33–35:48 | Credit spreads and short puts "with the standard guidelines" on navigator names | **PARTIAL.** Selling through the print on naked puts earned **more** than earnings-clear puts (within-week +0.19pp, t +3.6, but not beyond direction, excess t +1.3; `bci_csp_study_2026-09-17.md` §3). The ATM straddle sold at the bid is −0.43% (`earnings_vol_premium_2026-09-20.md`). Spreads through the print are untested |
| 34:25–34:48 | No stops: "just get out … doesn't matter whether you're down 10% or 30% or 50% or 70%" | Discretionary, untestable as stated. On a ~3-DTE ATM option through a gap, the practical exit is the next open, which is what the exploratory check approximates |
| 40:39–40:45 | "We are forecasting both" size (expected move) and direction (valuation) | Size is **the market's** forecast, not his. Direction from the technical legs is 50/50 above |
| 42:20–43:27 | QCOM is on the list although its trends are bearish; "the most undervalued stocks are the most bearish … buy low" | ⚠ **Internally inconsistent** with steps 1–2 (07:39–14:32), which require the trend to agree with the trade |
| 45:51–46:07 | An 8% expected move means "68% of the time" the stock stays within ±8% | ✅ **Roughly right.** On our 4,477 events the move to the front expiry stays inside the ATM straddle price **61.9%** of the time, and the reaction-day move stays inside it **70.3%** of the time (`earnings_vol_events.parquet`) |

## Exploratory check (2026-09-24, not pre-registered, local, ~1 min)

⚠ **Exploratory, one hypothesis, no multiple-testing charge. It is not a ledger row.** Data: the
existing earnings vol-premium event set (`data/cache/earnings_vol_events.parquet`, 4,477 events, 392
names, 2019–26; front expiry median 3 DTE), the chains cached with it (`earnings_vol_chains.parquet`,
real bid/ask), and `liquid_panel_2019.parquet` closes. 4,420 events matched.
**Proxy for his steps 1–2:** 21-session return ≥ +5% **and** 21-session excess over SPY ≥ +5pp → BULL.
The mirror image → BEAR. Everything else is mixed, and mixed is the control. Valuation (step 3) is **not**
applied. Trade: the ATM call (BULL) or put (BEAR) of the ATM straddle strike, bought the session before
the print and settled at intrinsic on the front expiry. Placebo: the same option in the **opposite** direction.

| group | n | median implied | median realised | realised/implied | direction hit | trend option mid | **trend option ask** | opposite option ask |
|---|---|---|---|---|---|---|---|---|
| BULL aligned | 1,093 | 8.16% | 5.58% | 0.921 | 50.0% | −2.0% | **−8.9%** | −19.2% |
| BEAR aligned | 824 | 8.75% | 6.13% | 0.896 | 49.6% | −18.9% | **−26.9%** | −8.0% |
| mixed | 2,503 | 5.68% | 4.55% | 0.965 | — | — | — | — |

Aligned, pooled: trend option at the ask **−16.6%, date-clustered t −3.03** (761 dates), halves −25.2 /
−8.0, 7/8 years negative (2024 +4.4). Trend minus opposite **−2.2pp, t −0.15**. With the loose
sign-only definition (82% of events aligned), the trend option returns −12.3% (t −2.59) and trend minus opposite is +2.2pp (t 0.79).

⚠ **Caveats.** A 21-day return is a proxy for his "previous week to previous month" and for the
platform's own RS score. The option is held to the front expiry (~1–2 sessions past the print), while he
says he would not hold to expiry (36:23), so our number carries a little extra theta and no exit spread. With no valuation leg, this tests steps 1–2 only.

## Not tested, could be

1. **The full navigator rule, as a codable spec (needs data we don't have).** Universe: names reporting
   in the next session with options-volume rank in the top ~10 that day. BULL = 21d return > 0 **and**
   21d return − SPY > 0 **and** forward P/E < industry median **and** net margin > industry median.
   BEAR is the mirror image (P/E above the median, margin at or below it). Entry: buy the ~50Δ call/put in the first
   weekly expiry after the print, at the ask, at the close before (AMC) or the prior close (BMO). Exit:
   the close of the reaction day, at the bid. Control: the same option on mixed names on the same dates,
   plus the opposite-direction placebo. ⚠ **Blocked on point-in-time fundamentals** (forward P/E and
   industry medians as of the report date). yfinance gives only today's values, which would be look-ahead. The
   technical legs alone are already answered (exploratory above), so this is only worth running if a PIT
   fundamentals source appears.
2. **⭐ New axis: trend + RS alignment as a selector for the earnings vol-premium SELLER.** This is
   the flip side of the finding above. Aligned names realise less of their (larger) implied move. In the same
   exploratory data, the short ATM straddle earns **+1.00% of spot at mid on aligned names vs +0.27% on
   mixed**, and **−0.23% vs −0.56% at the bid**. It is still negative at a real fill, but it moves in the direction of the
   PARKED liquid-name cell (`earnings_vol_premium_2026-09-20.md`). The earnings gates study tested IV/RV, term slope and volume
   (`earnings_gates_2026-09-20.md`), **not** trend or RS, so this axis is untouched. Spec: the
   primary cell is aligned (the ≥ 5% / ≥ 5pp definition above) ∧ volume top 40%, short ATM straddle at the
   bid, held to the front expiry, day-clustered t, halves and per year, bar |t| ≥ 3. Control: the same
   liquid cell, mixed names. Local and minutes long (all inputs are cached). **Not queued**; for Gabe to decide.

## Discrepancies found in our own docs while checking

- The shorthand "pre-event OTM calls win" (memory `project_catalyst_studies`, and how the catalyst results
  are sometimes summarised) comes from **FOMC + election** events only (`event_convexity_2026-09-18.md`). It is **not** evidence about earnings, and its 0.12Δ-over-0.25Δ preference is a mid-price
  artefact (+1.9pp, t 0.29 at real fills, `event_spread_2026-09-20.md`). Don't cite it for earnings-call buying.
- The memory index line "Catalysts: earnings yes, macro no, convexity yes" is stale. The body's own
  erratum (2026-09-18) says the earnings-proximity finding is **dead** (bucket mix).
