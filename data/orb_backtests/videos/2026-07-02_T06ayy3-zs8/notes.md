# Raghee Horner — "Why Most Traders Fail The ORB Trading Strategy (And How To Fix It)" (2026-07-02, 17:08)

_Reviewed 2026-09-23 as a **false-negative check on our ORB nulls**. Talking-head explainer, no charts in the
transcript, no trade shown. Raghee Horner is Managing Director of Futures Trading at Simpler Trading; the
description sells a live webinar and a phone number. Transcript (`en-orig` auto-captions) in this folder._

## Verdict: 2 / 5

**The same diagnosis as Fit Mom Trader (don't buy the break, buy the retest), with a different remedy
level (the 38–62% zone of a 30-minute range), a checklist of context filters, and zero evidence.** Of her
three "mistakes", the first is directionally supported by our data at t −8.50, and the remedy is refuted as
a *strategy* on our equity panel (−0.695pp vs a random minute, t −4.92, at the OR midpoint) and by Trading
Steady's own index backtest in this KB ("even worse"). The second and third are untested lists of levels
(PSC, 7 a.m. anchored VWAP, volume profile, initial balance, econ calendar) asserted as probability-stacking.

Scores below Fit Mom (3/5) because it adds nothing she didn't say except more unevidenced filters, asserts
a base rate ("most of the time they reverse") that our data contradicts, argues that 30 minutes "works so
much better" than 5 or 15 without any number, and casually cites **3% account risk per trade** as the
normal case. Scores above 1 because the break-vs-retest diagnosis is right and the context-first instinct
matches our own alert-funnel result.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:19 | Thousands trade the ORB daily and "most of them lose money … not because the setup doesn't work" | **Untestable as stated; half contradicted.** The retail loss rate is unsourced. Whether "the setup works" depends on the instrument: on single names, every ORB variant we ran fails (ORB9 break **−0.425pp vs a random minute, t −8.50**; ORB15 **−1.22pp vs the close entry, t −3.4**; Stage A ORB9 −0.25R). On the index it is **untested here** — see the section below |
| 01:10 | Mistake 1: entering on the break costs traders the most money | ✅ **Supported on single names.** Same diagnosis as Fit Mom, same evidence: ORB9 buys the break, so it buys high — +0.351% vs +0.775% for a random minute in the same name-day, **t −8.50, both halves** (`alert_triggers_2026-09-23`) |
| 01:48 | The open is "the most manipulated period"; institutions know where retail stops sit and sweep them for liquidity | **Narrative; its tradeable forms fail here.** The sweep-then-reverse short on single names (FBO) is **INVERTED, −0.148%/trade, t −3.80**, retired. On the index, ICT sweep → FVG reversion on QQQ 1-min 2007–26 is **FAIL, −0.109R paper (t −8.2), negative all 20 years**. If sweeps were the dominant event, fading them would pay; it doesn't. She does give the non-conspiratorial reading herself (02:57: no new buyers at the highs) |
| 03:01 | "Sometimes breakouts follow through, but **most of the time they reverse**" back into the range | ❌ **Contradicted on our equity panel** (her range is 30 min, ours 15, so scope-limited). Of 1,411 ORB9 breaks, only **39.1%** come back to session VWAP and only **14.4%** to the OR midpoint within 60 min (`orb_retest_vs_break_2026-09-23`). And the ones that *don't* come back are the good ones: break **+1.264%** on no-retest days. Not measured: the share closing back inside the range at all. Entry study, supporting her weakly the other way: a same-day exit on a close back under the OR high *hurts* ORB entries (+5.41 → +3.97%), i.e. re-entries into the range recover often |
| 03:47 | ⭐ The fix: "breach and retreat, not break and chase" — wait for a pullback to the **38–62% zone** of the 9:30–10:00 range and buy there; first target = the range high | **Right mechanism, fails as a strategy.** Our OR-**midpoint** arm (the centre of her zone, 15-min range) *when it fires* beats a random minute by **+0.58pp, t +6.68** — the entry-quality effect is real. But it fires on 14.4% of breaks, and as a strategy it earns **+0.032%** per opportunity, **−0.695pp vs random, t −4.92**. Trading Steady's index backtest (this KB) finds the midpoint entry "even worse" than his other variants. Her target (the OR high) caps the upside of exactly the trades the retest selects; with an unstated stop, R cannot be computed |
| 05:15 | "By design fewer entries"; you may not get the retreat | ✅ **Honest, and it is the whole problem.** She names the cost and never prices it. Priced here: the forfeited runaways are worth ~3–10× the salvaged failures |
| 05:36 | Follow-through is more likely if the 5-min chart is in an uptrend above the **previous session close (PSC)** at the breach; otherwise expect a retreat | **Untested — and it is the one piece that could rescue the remedy, see #3 below.** It turns the rule into a *hybrid* (buy the break in context, wait for the retreat otherwise), which is not what we tested. Low prior on single names: ORB9 alerts are overwhelmingly gap-up momentum names, so "above PSC" barely discriminates; ORB9's own context tags don't survive the control set: the 9-EMA hold sorted the curated names (+0.98/+0.35R vs +0.07/−0.05) and **inverted** on the control set (−0.40/−0.16 vs +0.20/+0.48); ORB9 already carries an index-context gate (SPY above VWAP or group leading) and "every ORB9 cell is negative on the control set regardless of the index" (`alert_filter_study_2026-09`) |
| 06:16 | Mistake 2: ignoring the trend; "context first" | **Partly supported.** Alert funnel: intraday alerts add **nothing** beyond the daily in-play state (alert day +3.85% vs no-alert +4.14%); the level-trigger study found "the level picks the DAY, not the minute". Both say context/selection matters and the trigger doesn't. Neither tests *her* context variables |
| 07:57 | Anchor a **7 a.m. ET VWAP**; price above it after 9:35 → higher probability | **Untested.** Our cached 1-min equity bars are RTH-only, so a 7 a.m. anchor needs pre-market bars we do not have for single names; for SPY/QQQ the IBKR pull is also RTH (`run_intraday_pull.py`). Not codable without new data |
| 08:31 | In choppy markets keep the entry, change the target: take profit at the range boundary | **Consistent with nothing specific.** Stage A: 1R / 2R targets **−0.127R / −0.122R** vs a stop-at-close −0.110R — no target rescues a trigger with no information |
| 09:01 | PSC above = bullish, below = bearish sentiment level | **Untested as an intraday gate.** Daily analogue: the per-name gap-down reclaim trait (close back above the prior close) is ~90% noise (`gap share` / per-name affinity rows, NULL) — different question |
| 09:13 | Check for 9:45 / 10:00 economic releases and FOMC speakers; they "kill a move" | **Untested intraday.** Our FOMC work is about daily drift (FOMC as a catalyst: **FAIL**, t < 2), not intraday range behaviour. The event-day intraday playbook is a parked idea (#5 in the QQQ intraday project). Harmless as a risk discipline |
| 09:46 | Volume candles, volume profile POC / VAH / VAL mark institutionally defended levels | **Untested; the price-level cousins fail.** Level triggers at PDH/PDL/21 EMA/50 SMA/anchored VWAP/OR high: **NULL 0/12**. Volume profile itself is not in our data |
| 10:58 | If context conflicts, pass or cut risk — "if you typically risk **3% per trade**, drop to 2–2.5%" | ⚠ **3% per intraday trade is not a baseline anyone here should accept.** The "pass on conflict" half matches `feedback_alerts_need_daily_context`; the sizing half is a red flag |
| 11:38 | Mistake 3: wrong range; 5- and 15-minute ranges are for experts; the "clearing range" takes ~30 min; "why does the 30-minute work so much better than the 5 or the 15?" | **Untested; asserted without a number.** Our ORB9 / ORB15 use 15 min. A longer range moves the trigger later and the level higher; on single names the extension mechanism predicts that is worse, not better. Fit Mom says 15 is the minimum. Two creators, two "right" windows, no data from either → the window is a free parameter |
| 14:36 | Mark the **initial balance** (9:30–10:30), "institutional fair value"; after 10:30 it overrides the OR | **Untested.** A 60-min OR is a codable variant but it is a parameter sweep, not a new mechanism |
| 15:28 | "It's not broken, it's just become predictable … fix the execution and the setup works" | **No evidence offered.** 35 years of screen time is the only support. Compare Trading Steady, who ran the retest fix and got a null |

## Red flags

1. **No evidence of any kind** — no trade, no chart outcome, no statistic, no backtest, in 17 minutes.
2. **Asserts a base rate** ("most of the time they reverse") that our equity data contradicts; the whole
   remedy rests on it.
3. **3% account risk per trade** mentioned as the normal case.
4. **Sales funnel**: Simpler Trading webinar, phone number, proprietary indicators (GRaB candles, 34EMA
   wave, Propulsion Dots) named in the description.
5. **Unfalsifiable stacking**: PSC + 5-min trend + 7 a.m. AVWAP + volume profile + econ calendar + initial
   balance. Any losing trade can be attributed to a filter not checked.

## What I would take

1. **Nothing to adopt.** The break-vs-retest diagnosis is already in the ledger (Fit Mom, ORB9 inverted);
   the retest remedy is already refuted as a strategy here.
2. **One codable idea she supplies that we haven't run:** the **hybrid** — buy the break when the day's
   context favours follow-through, wait for the retreat otherwise. It is the only version of the retest
   argument that does not automatically forfeit the runaways. Spec below; low prior.

## Does this overturn or refine our ORB nulls?

Our ORB tests (all single-name equities, curated or layer-2, 2026-02 → 09): ORB9 (15-min OR, 5-min close
over OR high + VWAP, pace ≥ 1.0, ≤ 12:00) in Stage A, the stop floor, the random-minute control, the retest
study (VWAP and midpoint arms); ORB15 in the entry study; the OR-high level trigger.

| # | Difference (her rules vs ours) | Plausible hidden positive? | Codable spec | Effort |
|---|---|---|---|---|
| 1 | **Instrument: index futures (ES/NQ, RTH 9:30 range) vs single names** | ⭐ **Yes — the same gap Trading Steady exposes.** No ORB of any kind has been run on SPY/QQQ here. Our ORB9 inversion is measured against a random minute on hand-curated up-drifting names; on an index the ORB is a *direction* call, which we never tested. Priors: noise-band (ORB's cousin) gross Sharpe 0.78, MARGINAL net; ICT sweep-fade on QQQ FAIL t −8.2 (the reversal story she tells fails on the index) | See the README's single best follow-up: SPY/QQQ 1-min 2007–25, 15- and 30-min OR both pre-registered, break arm vs *opposite-direction same-minute* and *random-minute same-direction* controls, plus her midpoint-retest arm as a secondary cell | ~½ day (engine + data exist) |
| 2 | **30-min opening range** (and 60-min initial balance) vs our 15 | **Only on the index, as a cell of #1.** On single names the extension mechanism predicts a later, higher trigger is worse. Adding windows is a sweep; charge Šidák | In #1: OR ∈ {15, 30} pre-registered, IB 60 exploratory | inside #1 |
| 3 | **Context-gated hybrid**: buy the break if the 5-min chart is trending above PSC; otherwise wait for the 38–62% retreat | **Low prior, but it is the only form of the retest argument not killed by the runaway-forfeit mechanism.** Worth a re-cut, not a new study | Re-cut `orb_retest_vs_break_2026-09-23.csv` joined to the alert metadata (`open_pct`, session price vs prior close at trigger, 5-min EMA slope from the cached bars): arm H = BREAK when (price > prior close AND 5-min 20-EMA rising at trigger), else RETEST_MID (no retest → no trade). Compare to RANDOM on the strategy view. Pre-register the two context definitions; Šidák over 2. ⚠ Expect little discrimination: ORB9 names are mostly gap-up | 1–2 h |
| 4 | Retest zone 38–62% of the range vs our VWAP / 50% midpoint | **No.** Her zone brackets our midpoint arm; widening to 38% raises the fire rate somewhat but it is still a retest, still forfeits the runaways, and the midpoint arm already failed at t −4.92 on the strategy view | — | — |
| 5 | Target = the OR high (first target) | **No.** Caps the payoff of the trades the retest selects; Stage A targets did not rescue any trigger | — | — |
| 6 | 7 a.m. anchored VWAP, volume profile, econ-release avoidance | **Not codable with our data** (RTH-only bars, no profile). Econ-release avoidance is harmless and untestable at our n | — | needs pre-market bars |

**Bottom line:** no — she does not overturn the single-name nulls; her central remedy is the arm we
already ran and it failed as a strategy. Like Trading Steady, she points at the one real gap (the index),
and she supplies one cheap re-cut (the context hybrid) with a low prior.
