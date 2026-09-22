# Review: "Claude Tested Over 25,000 ICT Strategies (Here's What Works)" (AI Pathways, Brendan, 2026-08-06, KML09tRtHM8) — 3/5

Reviewed 2026-09-21. 19:34, public. Funnels to a paid Skool community (guides + "premium futures data").
Transcript: `videos/education/2026-08-06_KML09tRtHM8/`.

## What was done

ICT "Silver Bullet" (liquidity sweep → displacement → fair-value-gap retrace entry → target the opposite liquidity,
traded 03–04 London / 10–11 / 14–15 NY) turned into explicit dials (what counts as liquidity, gap size, entry, stop,
window, bias). The dial space is ~258M versions; a **uniform random sample of 25,000** plus three named versions
(textbook 5-min, textbook 1-min, the loose "as-traded" version). 16 years of 1-min NQ and ES, ~10M simulated trades.

Guardrails, as described: commission on every trade, slippage on every stop, stop-and-target in the same minute = a
loss, every config vs a coin flip with the same risk, a correction for luck across the 25,000, survivors re-run cold on
ES with no retuning, and **the last 2 years locked away and run once**.

## What they found

- Funnel: 25,000 → 9,481 with ≥ 100 trades → 6,190 profitable after costs → 2,191 past a risk-adjusted bar → 1,614
  past the luck correction → **420 profitable cold on ES (1.7%)**.
- Textbook 5-min dies at the risk bar; textbook 1-min dies on ES; the loose as-traded version survives everything.
- Quoted 70–80% win rates are false: 34–48% for the top versions, ~52% for survivors.
- The famous hours aren't special (10–11 NY slightly negative); every other hour sits in the same pack.
- Rule-by-rule: gap alone 0.33 → **+ sweep 0.69 (the only rule that adds)** → displacement, the hours and the
  15-minute bias each make it worse (bias → 0.16). A look-ahead "perfect bias" would win, i.e. the bias is only useful
  if you can forecast the day.
- Holdout: loose version +$251k over 2 years on 1 contract; best survivor +$455k, Sharpe 13, 24/24 months positive.
- Their summary: it's mean reversion after a stop-run on the 1-min chart, with a small per-trade edge that needs
  frequency (~2,000 trades a year).

## Against our evidence and our rules

**What's better than most creator content.** Pre-committed dials, a random sample instead of hand-picked variants, a
null (coin flip), a multiple-testing correction, a second market, and a sealed holdout run once. That's close to our
own honesty rules (pre-registration, controls, both halves, effective n).

**Where it's weaker than it looks:**
1. **Fills decide the answer, and they admit it.** The entry is a limit order into a 1-minute gap. On paper every
   touch fills; in practice touches that bounce often don't fill (queue) and touches that run through always do.
   With a small per-trade edge at ~2,000 trades a year, adverse fill selection can erase it. A Sharpe of 13 on
   1 contract is a fill-model artefact until shown otherwise.
2. **The holdout winner is picked on the holdout.** "Best survivor made $455k" is the max over ~420 configs on the
   sealed data, which re-introduces the selection the lockbox was meant to remove. The honest holdout number is the
   median survivor, or the pre-named loose version (+$251k), not the best.
3. **ES is not an independent market.** NQ and ES move together (~0.9); 420 of 1,614 surviving on ES is weaker
   evidence than it sounds. Their "420 strategies" are also highly correlated neighbours in dial space.
4. **One regime.** The 2 holdout years were a strong rising market, which they flag as a ceiling.

**Consistency with our findings:**
- "The hours aren't special" matches our time-of-day work (only the first 10 minutes of the cash session stood out,
  negatively).
- "More rules made it worse" matches "gates don't stack" (entry-extension, capitulation scorecard).
- "Bias only works with a crystal ball" matches "the paying months can't be forecast".
- **The sweep-and-reclaim is the one thing that also shows faintly in our data**: in today's level-trigger test the
  prior-day-LOW break and hold arms (a reclaim after a sweep of the low) were the only ones that beat their own
  days' random minute (+0.03–0.04R), though still negative overall. Our UR detector (undercut and reclaim VWAP) is
  the same idea on single stocks and averaged ~0R. On single stocks at our fills, the sweep doesn't make money; on
  index futures with their fills, they say it does.
- Our QQQ intraday project found index intraday MOMENTUM (the noise band) as the only credible intraday edge; a 1-min
  reversion edge would be a different, faster effect, not a contradiction.

## Score: 3/5

The best-built test we've reviewed from a creator: it kills most of its own subject honestly (win rates, hours, bias,
textbook rules). It stops short of 4 because its one positive result rests on paper limit fills, its headline number
is chosen on the holdout, and the second market isn't independent. Gabe doesn't trade index futures, so the practical
value is the method, and the negative findings, which agree with ours.

## Follow-up (parked, not queued)

Replicate the loose sweep → 1-min FVG retrace on QQQ 1-min (2007 onward, already in hand for the QQQ project) with a
queue-aware fill (fill only if price trades THROUGH the limit by a tick) vs a same-day random-minute control. That one
change is the test of whether the edge survives. Parked in TEST_INDEX §10.

## Replication result (run 2026-09-21, same day) — `data/studies/ict_sweep_fvg_qqq_2026-09-21.md`

Pre-registered reading of their loose survivor on 20 years of QQQ 1-min: **paper fills −0.109R/trade (−0.046R even
before commission), queue-aware fills −0.205R, negative in all 20 years under both**, including 2024–26. Paper fills
beat a same-day random minute by +0.06R (the sweep times entries slightly better than chance), and the realistic fill
takes ~0.10R/trade and turns that negative. Their positive result doesn't carry over to QQQ; the review score stays 3/5
for method, and the "sweep → FVG reversion" survivor is treated as NULL here.
