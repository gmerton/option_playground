# TraderLion × Pradeep Bonde (Stockbee) — "The $100 Million Catalyst Trade Setup: Episodic Pivot" (2026-07-22) — reviewed 2026-09-22

Video: https://www.youtube.com/watch?v=kCLiSsIZ7L4 (2:00:38, 41,646 views at review time)
Transcript: yt-dlp auto-subs, ~21,934 words. Reviewed for the catalyst queue ([[project_catalyst_queue]]).

**Score: 3.5/5 — the highest in this KB.** A coherent, internally consistent, risk-aware system from a
26-year practitioner, with an unusual density of *independent convergence* with our own tested findings —
including the uncomfortable one. It loses a point and a half for offering **zero quantitative evidence**
(no hit rate, expectancy, sample size or drawdown anywhere in two hours) and for resting its whole
structure on regime forecasting, which is the single most comprehensively failed claim in our ledger.

## The system, as actually specified

**Philosophy.** Magnitude not duration (80–200% in days/weeks, not months). Everything runs as a "trade
factory": fixed scans at fixed times, no in-the-moment decisions.

| setup | trigger | hold | size |
|---|---|---|---|
| **EP** (classic episodic pivot) | pre-market gap + game-changing catalyst on a *neglected* stock; MAGNA-53-CAP-10×10 checklist | 3–20 days | large |
| **EP9M** (his primary) | any stock trading **>9M shares** that day (≈ top 2% of ~13,000 tradables), *then* research why; mostly non-gap | 3–20 days | large on institutional-quality |
| **DR-EP** (delayed reaction) | a name that did EP9M within 25 days, pulled back in an orderly way; enter on the resumption from a 3–4 name watchlist | days | largest (stop <1%) |
| **Momentum burst** ("singles") | 1st leg ≥15%, linear; 3–7 day pullback; 2–4 tight bars; breakout closing near high on volume | 3–5 days | 20–25% of account |
| **Anticipation / reversal bullish** | tight bars, net change <1%, scanned 3:00–3:30, **entered at 3:58** | 1–3 days | 10% (overnight risk) |

**Risk.** Hard stops only, set on fill, never moved down. Stop = low of day (early entry) or half-of-day
(late entry). 5–6% on EP, <2.5% on momentum bursts. **Position size is a function of stop width.** Move
to breakeven fast. Scale out 80% by day 3–4, keep a 20% runner. Stop trading after 3 straight stop-outs.

**Regime ("situational awareness").** Every morning: *are breakouts likely to work?* Inputs: T2108
(% of NYSE stocks above the 40-day MA) — below 20 bullish, below 10 "extremely bullish"; a
stocks-up-20%-in-5-days oscillator as an overbought warning (>200 → pullback within 5–10 days); a
buying-vs-selling market monitor.

## ⭐ The empirical finding: EP9M is not the filter he describes

His stated mechanism is "top 2% of volume means institutions are there — find out why." Tested on our
liquid panel (1,729 names, 1,752 sessions, 2019-10 → 2026-09):

| | |
|---|---|
| EP9M name-days | 211,631 = **7.0%** of name-days, median **106 names/day** |
| Share of EP9M days where **RVOL < 1.0** (stock traded *below* its own average) | **43.9%** |
| Median RVOL on an EP9M day | **1.06** — i.e. a completely ordinary day for that name |
| Share of EP9M days that also clear **RVOL ≥ 1.8** (our only passing breakout cohort) | **15.8%** |
| Names whose *median* volume already exceeds 9M | 95 of 1,729 (5%) |
| **Share of all EP9M firings contributed by those always-9M names** | **59.2%** |

**Nearly 60% of the signal is "it's a mega-cap."** For those names, crossing 9M shares is not an event,
it is Tuesday. The stated rationale — unusual volume = institutional footprint — is false for the
majority of firings.

⚠ **Fair caveats.** Our panel is 1,729 liquid names; his universe is ~13,000 including ETFs and ADRs, so
his 2% is drawn from a broader base and is more selective in percentage terms. And **he clearly knows
this in practice** — "there are stocks which trade that kind of volume every day, but NFAS never trades
that kind of volume." But he never states it as a rule. His scan is just `volume > 9M`.

⟹ **The operative condition is unstated, and it is RVOL.** The honest specification of his own idea is a
*conjunction*: **absolute volume ≥ 9M (tradability, so you can size) AND RVOL ≥ ~1.8 (the actual event)**
— which is 15.8% of his firings and maps precisely onto our one robust breakout gate. That conjunction is
genuinely novel here: our RVOL work is purely relative, and we have never required an absolute floor.
Note this is the **second creator in two reviews** whose described filter isn't the one doing the work
(see [[project_smb_capital_kb]]).

## Claim-by-claim vs our evidence

| his claim | our evidence | verdict |
|---|---|---|
| **"Breakouts have an inherently very small edge… most of the time buying breakouts is a terrible business"** | ALL breakouts pooled are **negative** (−0.51%/21d, t −3.29); ledger signal −0.21…−0.33R vs control +0.13…+0.21R | **AGREES** — and this is a remarkable concession from a breakout trader |
| Only volume-confirmed breakouts work | RVOL monotone: <1.0 −0.68 · 1.3–1.8 −0.44 · **1.8–2.5 +0.86 (t 3.64)** | **AGREES** |
| "Situational awareness" can tell you *when* breakouts will work | **The paying months cannot be forecast** — own results, stop-out share, activity and SPY state all ≈ nothing ([[project_breakout_regime_feedback]]); the 5-session activity gate sorts (+0.81R, t 2.59) but has no plateau and fails the ledger correction → PARKED | **CONTRADICTED — and this is load-bearing** |
| Payoff is concentrated in a few good stretches | top 10% of months = **68% of R**; book +0.45R trade-weighted → −0.01R month-weighted | **AGREES** (he is right about the shape, wrong that it is callable) |
| T2108 < 20 → get bullish | Aug-2026 retro: weak breadth = **mild BUY** — direction agrees, but *every* trailing-30d breadth rule failed 2019–26 | **DIRECTION SUPPORTED, rule not** |
| Classic EP: buy the catalyst gap | **PEAD NULL**, earnings ledger closed; "buying the event fails" | **CONTRADICTED** — though *he agrees*: "EP is the least important setup for me today… the age on EP is less and less" |
| **DR-EP: wait for the orderly pullback after the catalyst, then enter** | Our retrace-entry test: B (retrace) beats A (breakout close) in **all 6 cells**, edge flips −0.101 → +0.065, both halves positive — but **t 0.48, PARKED** | **CONVERGENT, underpowered** — this is our own queued design, independently derived |
| Enter in the first 30–60 minutes, earliest is best | Stage A: every intraday arm −0.10…−0.13R ≈ a random minute; entry study: the **CLOSE** beats every intraday entry (paired t −1.6…−3.4) | **CONTRADICTED** |
| Anticipation/reversal entered at **3:58** | That *is* the close entry — our house rule | **AGREES** |
| Position size is a function of stop width | Breitstein C1 and our own 2026-09-22 stop work: widen to structure, cut size | **AGREES** |
| Faster move → tighter trail | Profit-lock study: **"extended → tighten" INVERTED** (−0.19 / −0.47R) | **CONTRADICTED** |
| Hard intraday stops, never mental | Entry study addendum: intraday stop *execution* makes tight stops worse; "cut losses early" holds at the daily level, not on 1-min bars | **PARTIALLY CONTRADICTED** (right about hard stops, wrong about intraday execution) |
| Stop trading after 3 losing breakouts | Own recent results do **not** forecast the next stretch | **UNSUPPORTED** (harmless as tilt control) |
| Buy only institutional-quality (1000+ funds) for reversals | Not tested here. Plausible (liquidity + real bids at support) but it is also his *sizing* constraint, not necessarily an edge | **UNTESTED** |

## The crux

Strip the video down and the argument is: *breakouts have no unconditional edge (agreed, we measured it);
the edge lives in regimes; I can identify the regime in real time.* **Everything rests on that last
clause, and it is the claim our ledger has failed to reproduce most consistently** — across own-results,
activity counts, SPY state, breadth rules and monthly forecasting. He offers no evidence for it beyond
narration of charts after the fact, and his own T2108 stories are told with the turn already known.

That is not proof he is wrong. He has 26 years and a real book of trades; our tests are of *mechanical*
regime rules, and his is discretionary pattern recognition over a market monitor, which we cannot test as
specified. But it means the video's central claim is exactly the part a reader cannot verify and we
cannot replicate — and it is the part everything else depends on.

## What is worth taking

1. **DR-EP is our queued catalyst design, already field-specified.** Catalyst as *selection*, then entry
   on the orderly pullback's resumption within ~25 days, from a 3–4 name watchlist, with a <1% stop. Our
   retrace-entry test found the same direction at t 0.48; his version adds the catalyst gate we never
   applied. **This is the highest-value extraction in the video.**
2. **The absolute-volume floor as a *sizing* filter**, conjoined with RVOL as the event filter. Novel
   here; makes "can I actually get size on" a first-class screen condition rather than an afterthought.
3. **Catalyst taxonomy worth stealing:** genuine turnaround (multi-quarter, fixed the business) vs
   cyclical turnaround vs one-quarter beat. He is scathing and specific about the difference (CBRL −5/3/5%
   "is not a turnaround" vs ANF's 244% profitability inflection). We have no catalyst classification at
   all; the earnings ledger treated all prints alike, which may be why it came back NULL.
4. **"Catalysts have a lifespan"** — he exits when the catalyst stops paying, not on a fixed clock.

## Testable claims extracted (queued)

**T1 (primary, serves catalyst queue #1).** EP9M-conjunction: on the liquid panel, does
`absolute volume ≥ 9M AND RVOL ≥ 1.8` select breakouts that beat (a) RVOL ≥ 1.8 alone and (b) the
`xname`/`post` controls? **Pre-register that the absolute floor adds nothing beyond RVOL** — our own
finding above says 59% of its firings are a size proxy.

**T2 (the real prize).** DR-EP: after a qualifying catalyst day, enter on the *resumption* of an orderly
pullback within 25 sessions rather than on the catalyst day. Direct upgrade of the PARKED retrace-entry
test (t 0.48) with a catalyst gate added — the gate is the new variable and is exactly what the catalyst
queue asks for.

**T3 (cheap, settles the crux).** T2108 (or our `%>50sma`) < 20 → forward 5/10/21d returns on the
breakout book vs unconditional. We already compute the breadth series in the regime report. Prior: weak
breadth = mild buy, but no trailing breadth rule has survived.

## Score rationale

**3.5/5.** Independent convergence on four tested findings including the base-rate one; a fully specified,
disciplined process; explicit stop→size linkage; candid about edge decay in his own flagship setup;
and it hands us a field-tested version of a design we had queued. Against that: no numbers of any kind,
survivorship in every example, the load-bearing regime claim is our most-failed hypothesis, three specific
rules are contradicted (morning entries, faster-move-tighter-trail, classic EP), and it is a two-hour
funnel for a paid site with a sponsor read in the middle. Risk to a follower: **6/10** — the risk
architecture is genuinely good, but 20–25% per position and "150% invested" in a regime he has called by
eye is where a reader gets hurt.

Related: [[project_catalyst_queue]], [[project_catalyst_studies]], [[project_earnings_2026_09_20]],
[[project_breakout_regime_feedback]], [[project_entry_extension_finding]], [[project_entry_study]],
[[project_profit_lock_study]], [[project_traderlion_kb]], [[project_smb_capital_kb]].
