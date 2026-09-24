# Trading Steady — "I Backtested the ORB Breakout + Pullback Strategy (5 Years of Data)" (2025-09-27, 10:45)

_Reviewed 2026-09-23 as a **false-negative check on our ORB nulls**. Solo screen-share: recap of his own ORB
rules, the breakout-pullback-continuation variant, a Python/Jupyter backtest on "5 years of S&P 500 data",
three follow-up variants, then a diagnosis. Transcript (`en-orig` auto-captions) in this folder. Description
funnels to Patreon / GitHub Sponsors for the backtest code; the video itself is not gated._

## Verdict: 3 / 5

**The first creator in these KBs to publish a null from his own backtest, and his diagnosis is ours.** He
tests the retest remedy that Fit Mom Trader and Raghee Horner sell, gets a flat-to-poor equity curve, tries
three rescues (bigger targets, a stop order at the OR high, a midpoint entry), watches each get worse, and
concludes: *"by sitting and waiting for a pullback, I'm essentially skipping out on the strongest breakouts,
trading only those that were weak enough to come back down."* That is, nearly verbatim, the mechanism in
`orb_retest_vs_break_2026-09-23` (the break earned **+1.264%** on the 860 name-days that never came back to
VWAP; waiting forfeits all of them).

It does not score higher because the backtest is **thin and unaudited on camera**: no costs mentioned, no
control or benchmark other than his own unshown baseline, n = 130 for the headline variant, a target sweep
chosen in-sample, and no statistics beyond an equity curve and a win rate. His **baseline** claim ("steady
profits for 6 months", "consistently profitable") is asserted here and deferred to another video we have not
reviewed. The null is credible *because* it is a null (no incentive to fake a loss); the baseline is not
evidenced by this video at all.

## Backtest-methodology audit

| item | what he says / shows | assessment |
|---|---|---|
| **Instrument** | "S&P 500 data", "SPX data" (description). Talks in "pips" at 08:41 → most likely a CFD / index feed, not ES futures or SPY. Never named precisely | ⚠ **An index, not single names** — the one dimension where our ORB nulls have no coverage (see below) |
| **Period** | "5 years" to ~Sep 2025 → roughly 2020–2025. Exact dates not shown | Includes 2020 and 2022, which is good; but see the regime note below |
| **n** | **130 trades** in 5 years for the pullback variant (05:15); baseline n not given | ~26/yr. Too few to separate a 1.5R-target edge from zero at any useful t. No t-stat given |
| **Costs / slippage** | **Never mentioned** | ✗ On an index with a 15-min stop at the OR extreme the per-trade risk is large relative to the spread, so costs probably do not flip the sign here, but the omission is total |
| **Fill assumptions** | Baseline: enter at the *open of the next* 15-min bar after a close outside the range (01:14) — a realistic, non-look-ahead fill. Pullback variant: 5-min bars, entry on a break of the pullback bar's high (i.e. a buy-stop). Stop and target presumably intrabar; tie-break rule (bar touching both) not stated | Baseline fill is honest. ⚠ Same-bar stop/target ambiguity on 5-min bars is unaddressed; with 1.5R targets this matters |
| **Stop / target** | Stop = opposite side of the OR (alt: pullback-bar low). Target = 1.5R; swept 2.5 → 4.5R in 0.5 steps | Fixed-R target. Our comparable arms (Stage A 1R / 2R) were −0.127R / −0.122R on single names |
| **Filters** | Baseline: no entries after the 12:00 bar; skip ranges "too small or too big based on recent ATR" (thresholds not given). Pullback variant: breakout must extend ≥ 1 × ATR beyond the range (04:31); a pullback that closes back *inside* the OR invalidates the setup | The ATR range-size filter is the one piece of his baseline we have never tested — its thresholds are undisclosed |
| **Direction** | Only long examples shown; baseline presumably both directions (not stated) | Unknown |
| **Control / benchmark** | ✗ **None.** Each variant's equity curve is compared to *his own baseline strategy's* final balance (05:51) — which is not shown in this video | The comparison is variant-vs-variant with no buy-and-hold, no random-entry, no same-day-other-minute control. Our ORB9 result shows why this matters: the break looked +0.352%/trade until a random minute on the same name-day earned +0.775% |
| **In-sample optimisation** | TP ratio swept 2.5–4.5 on the full sample; "each increment made the strategy perform that little bit better" (05:41) | A monotone improvement with target width on a losing entry is the usual signature of *fewer, larger winners on trend days* — the same "three trend-day outliers" shape our `alert_filter_study` found in ORB9's early mean. Still poor after the sweep, so no selection claim results |
| **What the equity curve is compared to** | Time: "sideways for the first 3 years, okay from 2023" (04:49). Level: "far less than what my current strategy does" | ⚠ **Regime in the back half.** A variant that only worked 2023–25 is exactly the case CLAUDE.md warns chronological halves miss; he flagged it himself from the curve, to his credit |

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:01 | "I've been trading the ORB for 6 months and made steady profits"; the 15-min ORB (next-bar-open entry, OR-opposite stop, 1.5R, 12:00 cutoff, ATR range filter) is "consistently profitable" | **Not evidenced in this video, and never tested by us on his instrument.** Six months of live P&L is one regime. Every ORB variant we ran is on **single names**: ORB9 break **−0.425pp vs a random minute, t −8.50** (`alert_triggers_2026-09-23`); Stage A ORB9 intraday arms −0.25R, t −5 to −12; entry study ORB15 **−1.22pp vs the close entry, t −3.4**. None of those touches SPX / SPY / QQQ. ⚠ **This is the gap** — see "Does this overturn…" below |
| 01:53 | Big breakouts force a big stop (stop at the far side of the range), which is the problem the pullback solves | ✅ **Agrees in mechanism.** ORB9's structural stop was pathological in the *other* direction on single names (median **0.15 ADR**, 96% under 0.4, 73% stop-outs → the 0.6 ADR floor, ADOPTED for mechanics only). Both say the OR-derived stop is badly scaled; ours says judge that in % not R |
| 02:55 | "Price will often make a pullback and return to the ORB" | **Partly.** On our 1,411 curated ORB9 breaks, a return to **session VWAP within 60 min** happens on **39.1%**, to the **OR midpoint on 14.4%** (`orb_retest_vs_break_2026-09-23`). "Often" for VWAP, not for the range itself |
| 04:49 | The breakout-pullback-continuation variant: flat 2020–22, OK 2023–25, poor overall, n = 130, win rate ≈ baseline | ✅ **Agrees — same sign as our strategy view.** Wait-for-retest **+0.125%** per opportunity vs every break +0.351% and a random minute +0.726% (**−0.601pp vs random, t −5.56**). His confirmation entry (break of the pullback bar's high) is not an arm we ran; ours enters on the first close at the level |
| 05:41 | Raising the target 2.5 → 4.5R improves each step, still poor | **Consistent, and not evidence.** In-sample sweep; monotone-in-target on a bad entry = trend-day outliers carry it (cf. ORB9 without its top 3 winners −0.14R, `alert_filter_study_2026-09`) |
| 06:04 | Real setups rarely look like the textbook; confirmed pullbacks often fail anyway; his pullback entry lands at about the same price as the break entry | ⭐ **A useful observation we had not made explicit.** On a *15-min-close* breakout, the 5-min pullback-and-confirm entry is often no better in price than the baseline's next-bar-open fill — so the "better price" the retest promises may not exist once the break itself is confirmed on a close. Our retest arms enter at the level (VWAP/midpoint), which *does* guarantee a lower price; his confirmation gives much of it back |
| 07:39 | A buy-stop at the OR high (no confirmation) is "even worse" | **Consistent.** Level triggers at the opening-range high, break and hold: **NULL 0/12**, every arm −0.06 to −0.10R, none beats a random minute by > +0.04R (`level_trigger_test_2026-09-21`) — single names |
| 08:15 | Buying the **OR midpoint** on a stop order with a tighter stop "performed even worse"; for every clean midpoint bounce "plenty of others barrel all the way through" | ✅ **Agrees on the strategy view; our data adds the conditional nuance.** Our midpoint arm fires on 14.4% of breaks; *when it fires* it beats a random minute by **+0.58pp (t +6.68)**, but as a strategy it is **+0.032%** per opportunity, **−0.695pp vs random, t −4.92**. His tighter stop at the midpoint is the difference: a tight stop at the midpoint gets run through, while our 0.6 ADR stop held to the close lets the bounce play out. Neither version is a strategy |
| 09:47 | ⭐ "The best breakouts have strong momentum and don't pull back to the opening range … I'm trading only those weak enough to come back" | ⭐⭐ **Our finding, independently.** Break earned **+1.264%** on the 860 no-VWAP-retest days vs **−1.076%** on the retest days; the forfeited runaways are worth ~3–10× the salvaged failures. Same shape as the daily breakout bimodality (23.6% never retest, +1.27R; 76.4% do, −0.37R) |
| 10:22 | Next idea: filter for breakout *strength/momentum* to avoid fakeouts and catch the strongest breaks | ⚠ **Our prior is against it on single names.** ORB9 already requires volume pace ≥ 1.0 and a 5-min close above VWAP and the OR high; it is still inverted. RVOL did not rescue the down-day RS or catalyst tests either. On an index it is untested |

## What I would take

1. **His null as corroboration, not new evidence.** An independent index backtest, with a different
   confirmation rule and a fixed-R exit, reaches the same verdict as our single-name test: the retest
   remedy fails because it deselects the runaways. That makes "wait for the retest" a settled no on two
   instruments, not one.
2. **The confirmation-price observation** (06:04): a close-confirmed break plus a confirmed pullback can
   leave you no better off on price. Worth one sentence in any future ORB spec.
3. **The one real gap he exposes:** his *baseline* is an **index** ORB with a 1.5R target and an ATR
   range-size filter. We have never run an ORB on SPY/QQQ, although we hold 1-min bars for both from
   2007. See the section below and the README.

## Does this overturn or refine our ORB nulls?

Our ORB tests: **ORB9** (15-min OR, 5-min close above OR high and VWAP, volume pace ≥ 1.0, ≤ 12:00,
long-only, curated single names, 2026-02 → 09) in Stage A, the stop-floor study, the random-minute control
and the retest study; **ORB15** in the entry study (1-min close over the 15-min OR high, stop = OR low,
layer-2 single names, multi-day management); the **opening-range-high level trigger** (break and hold,
20,148 name-days). Every one is single-name equities over ~7 months of 2026.

| # | Difference (his rules vs ours) | Plausible hidden positive? | Codable spec | Effort |
|---|---|---|---|---|
| 1 | **Instrument: S&P 500 index vs curated single names** | ⭐ **Yes — the only one that matters.** Our ORB9 inversion is measured *against a random minute on a hand-picked up-drifting name*; on those days any earlier entry wins, so the break's loss is partly the selection. An index has no curation, and the ORB's job there is **direction**, which none of our tests asked. Our index intraday priors are mixed: noise-band momentum (ORB's cousin: breakout from an open-anchored band) is **MARGINAL**, gross Sharpe 0.78 / net 2.5%/yr at $10k, dead 2009–17; negative-gamma arm **UNDERPOWERED t 2.92**; ICT sweep reversion on QQQ **FAIL t −8.2** (i.e. the sweep-and-reverse story fails on the index too, which *favours* continuation). Unverified recollection: Zarattini & Aziz (2023) report a profitable 5-min ORB on QQQ — not checked, do not cite as evidence | SPY and QQQ 1-min, 2007-01 → 2025-12 (2026 held out). 15-min OR; signal = first 15-min bar closing outside the OR at or before 12:00; enter next bar open, both directions; stop = opposite OR side; exit 1.5R target or 15:59 close. ATR range filter **pre-registered at fixed thresholds** (e.g. skip OR/ATR14 < 0.15 or > 0.6) as a *secondary* cell. Controls: (a) **same entry minute, opposite direction** (tests direction, nets drift); (b) **same direction, random minute 09:45–12:00** (tests timing — the ORB9 control); (c) always-long open→close. Costs 1bp/side + $0.005/sh. Bar: \|t\| ≥ 3 vs (a), both halves, per-year incl. 2020 + 2022, Šidák over the cells | ~½ day: data and noise-band engine exist (`run_noise_band.py`, `data/cache/intraday_hist/`) |
| 2 | Timeframe: 15-min signal bar, next-bar-open entry (baseline); 5-min for the pullback | **No, for single names.** ORB9 uses a 5-min close and ORB15 a 1-min close; both fail against the close entry or a random minute, and a coarser bar only delays the entry further up the move — the extension mechanism says that is worse, not better | Folded into #1 as the index spec | — |
| 3 | 1.5R fixed target (and 2.5–4.5R sweep) vs hold-to-close / swing trail | **No.** Stage A priced 1R and 2R targets on single names at **−0.127R / −0.122R**, both ≈ a random minute. A target changes the payoff shape, not whether the entry has information. His own sweep did not rescue the variant | In #1 as the pre-registered exit; report hold-to-close alongside | — |
| 4 | ATR range-size filter (skip too-small / too-big ranges) | **Weak.** Never tested by us. Plausible as a *stop-scaling* fix (our ORB9 pathology was stops too tight), which the 0.6 ADR floor already addresses on single names. Thresholds undisclosed → any value we pick is ours, charge it as a new cell | Secondary cell in #1; on single names, re-cut the existing ORB9 control CSV by OR width / ADR tercile (the columns exist in the alert metadata) | 1–2 h re-cut, exploratory only |
| 5 | Breakout must extend ≥ 1 ATR before a pullback counts | **No.** It selects breaks that already ran, i.e. more extended entries; the pullback variant still failed | — | — |
| 6 | Retest entry with confirmation (break of pullback-bar high) | **No.** Same selection problem as our arms (only trades breaks that come back); he shows it also gives the price back | — | — |
| 7 | Both directions (shorts on downside breaks) | **Only inside #1.** On single names our short mirror (FBO, sweep-and-fail short) is **INVERTED, −0.148%/trade, t −3.80**; on the index the short side is untested | In #1 | — |

**Bottom line:** nothing here overturns a single-name ORB null — his own null *agrees* with ours. It
**refines their scope**: every ORB test we have is single-name, curated, 2026-only. The index ORB (#1) is
a genuine untested cell with a cheap test and a modest prior (noise-band gross Sharpe 0.78, but dead
2009–17 at our costs).
