# Review: "3 Opening Range Breakout Mistakes Every Trader Makes" (Fit Mom Trader, 2026-07-24, 1OJZVLBOhvc) — 3/5

Reviewed 2026-09-23. 13:58, public, 4,370 views. Transcript: `videos/education/2026-07-24_1OJZVLBOhvc/`.
Description links a paid mentorship waitlist; the video is not gated.

⚠ Captions are machine-translated from Spanish — wording below is paraphrase, not quotation.

## What it says

Three mistakes, then chart examples:

1. **Chasing the break.** Retail places buy-stops at the range high and sell-stops at the low;
   institutions know where that liquidity sits and push through it just far enough to trigger the orders.
   Her remedy: **do not trade the break. Wait for the pullback and trade the retest** — specifically the
   New York-anchored VWAP or the 50% midpoint of the opening range, which she notes usually coincide.
   Explicitly accepts the cost: you will miss the days that run and never come back.
2. **Ignoring higher-timeframe context.** Check the 1h/4h picture, key levels (prior-day high/low, Asia
   and London high/low), and VWAP slope before taking a break. If signals conflict, **don't trade.** If
   price is inside a larger range, trade the *failed* breakout instead.
3. **Wrong range length.** 5-minute is too noisy; 15 minutes is her minimum, and she also trades the
   60-minute (initial balance). Emphasis on **consistency** over which length is chosen.

## Evidence quality — nil

No track record, no trade log, no equity curve, no statistics of any kind. Two illustrative stop sizes
from one chart (78 vs 149 NQ points) and one "155 points" result. Every example is a winner shown after
the fact on a chart with the outcome visible.

⚠ **She asserts a backtest she never shows**: *"if you backtest this, you'll see that the number of times
you avoid the loss exceeds the number of gains."* That is precisely the claim worth testing, and it is
stated as settled.

## ⭐ Against our evidence — claim 1 is the strongest creator/data alignment we have

**Our 2026-09-23 result is that ORB9 — which buys the break of the opening-range high — is INVERTED.**
Holding the name-day fixed and moving only the entry minute:

| | per trade |
|---|---:|
| random other curated name, same minute | +1.029% |
| same name, random minute in ORB9's window | +0.775% |
| **ORB9 trigger (buys the break)** | **+0.351%** |

−0.425pp against a random minute, **t −8.50**, both halves agreeing. We concluded it *"buys the break, so
it buys high — the entry-extension finding in intraday form."* Her mistake #1 is the same diagnosis, from
screen time rather than from data, and she published it two months earlier.

Supporting it from the daily side: the house breakout enters **+2.6 ADR above** a random later entry in
the same name, and `entry_vs_stop_2026-09-20` identifies that gap — not the stop — as the entire −0.4R.

⚠ **But her REMEDY is not established.** We tested the daily analogue the same day
(`reclaim_vs_pullback_2026-09-23`, 42k–58k pullbacks): the pullback entry earns +0.070R (t 2.04, edge over
control +0.043) and the reclaim +0.178R (t 2.69) — **neither clears the |t| ≥ 3 bar**. The earlier
`run_retrace_entry.py` arm is **PARKED at t 0.48**. So "wait for the pullback" is *directionally* right
and *statistically* unproven on our data. One point in her favour: in that study the pullback entry beat
the reclaim on win rate (39% vs 31–34%), which is her argument exactly.

**Claim 2 (context):** partially supported. Our alert-funnel test found intraday alerts add nothing beyond
the daily in-play state, and Stage A priced every intraday arm at −0.10 to −0.13R ≈ a random later minute.
That supports "context dominates the trigger" while undercutting the idea that any of these triggers is
itself an edge. Her specific tools (VWAP slope, Asia/London levels) are untested here. ⭐ Her
"if signals conflict, don't trade" matches our own `feedback_alerts_need_daily_context` rule.

**Claim 3 (range length):** untested. Our ORB9 already uses a 15-minute opening range, i.e. we sit at her
stated minimum. The consistency argument is unfalsifiable as stated.

## Red flags

1. **Asserts a backtest as fact without showing it** — the single biggest issue, because it is the one
   claim that would settle the video.
2. **Survivorship in the examples.** Every chart shown is a trade that worked. The failure mode she warns
   about (missing the day that runs) is acknowledged verbally and never quantified.
3. **The remedy has a selection problem she does not address.** Waiting for a retest means you only ever
   trade breaks that come back. That is the bimodality issue flagged in our own reclaim study — the
   retest arm cannot buy the cohort that ran away, so comparing it to the break arm mixes entry timing
   with a change in which trades get taken.
4. **Paid indicator + mentorship funnel.** The VWAP anchoring she uses is free to reproduce; she says so.
5. **No instrument or session stats**, despite trading one instrument in one session where they would be
   easy to produce.

## Testable claim extracted (the one worth running)

⭐ **Does entering on the retest of the anchored VWAP / range midpoint beat entering on the ORB break?**
This is directly runnable and cheap — we already have every component:
* the ORB9 alert set (1,411 curated alerts, 153 sessions) with trigger minute and price,
* 1-minute bars **with a `vwap` column** in `data/cache/intraday_1min`,
* the control harness built for `run_orb9_trigger_control.py` (same name-day, random-minute and
  cross-name arms).
Arms: (a) break entry = the ORB9 trigger, (b) retest entry = first close back to session VWAP or the
range midpoint after the break, (c) random-minute control, (d) no-retest cases reported as their own
bucket, never dropped.
⚠ Pre-register that (b) can only trade breaks that come back — report the no-retest share, and compare
(b) to (a) **on the events where both fire**, or the result is the reclaim study's arm-C error again.
Prior: (b) beats (a), because (a) is already known to be inverted at t −8.50; the open question is
whether (b) beats the random-minute control, which nothing intraday has yet done.

## Score rationale — 3/5

Equal-highest with SMB's RS-breakout video, for a different reason. **Her central claim is the single most
data-aligned thing any creator in these KBs has said**: don't buy the break, and the mechanism is the
liquidity sitting at the obvious level. Our strongest intraday result of the year says the same at
t −8.50. Her process instincts are also sound — context over trigger, refuse to trade on conflict,
consistency, "there's always tomorrow."

It does not score higher because there is **zero evidence** in 14 minutes, the examples are winners only,
and she asserts a backtest rather than showing one. The remedy she prescribes is PARKED on our data, not
confirmed — and it carries a selection problem she never mentions.

⚠ **Scope:** NQ futures intraday. We have no futures data. Her mechanism transfers to our equities; her
instrument does not, so nothing here can refute her on her own book.
