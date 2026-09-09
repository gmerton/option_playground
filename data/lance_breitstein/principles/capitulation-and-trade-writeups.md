# Capitulation quantified, and the trade-writeup template

> **Verdict:** One genuinely testable rule (2x/2x blowoff) buried in a process video; the template is the repo's journal, done by hand.
> **Type:** review-process + setup (blowoff/capitulation short)
> **Conviction:** 3/5 for the 2x/2x rule as a hypothesis · **Testability:** EOD ⭐ (daily bars + volume already on disk) · **Tested?** no
> **Source:** `TexislSXpjs`@07:31–08:23 — How to Do Trade Writeups Like a Pro! (2023-10-23, reviewing a mentee's write-up of a small-cap biotech blowoff)

---

## 1. Mechanics — the blowoff-top rule of thumb

- **Instrument / universe:** small/micro-cap parabolics (the example is a sub-$1 biotech that ran 20c → 80c in a week); he applies it on both the daily and the intraday chart.
- **Setup condition — "capitulation" is price AND volume, not price alone** [07:10–08:23]:
  - the blowoff bar's move is **≥ 2x the prior day's move** ("if the prior day went 10, we went 40, which is 4x");
  - the blowoff bar's volume is **≥ 2x the prior day's** ("it's not just 2x the volume, probably 5x");
  - the bars **accelerate** into it (5c, 5c, 10c, 12c, then 40c) [06:46].
- **Trigger for the trend break:** "I always look for a break of prior bar lows as far as the true break of trend" [10:04]; on a parabolic that level can be far away, so the blowoff itself raises the odds of "backside."
- **Timeframe alignment** [11:44–12:41]: the daily capitulated AND the intraday capitulated the same day → "both time frames aligning... super powerful." Swing short after the daily capitulation, intraday short the reversal and the pops against the highs.
- **Stop:** the highs of the move [16:37]. **Cover:** he wants pre-specified scale-outs for day 1 / day 2 / end of day and a cover plan for a violent flush ("what if this dumps to 40c intraday, are you really not going to cover that?") [16:02–16:37].
- **Veto — the no-news rule, again** [12:41–13:01]: "if there is a reversal of whatever news sent that down I might not want to fade that at all." Third source for the rule already logged in `remaining-five.md` / the Carter veto list.
- **Fundamental overlay, not a fundamental trade** [08:54–09:30]: an ATM/shelf capacity (dilution) makes the fade thesis stronger; he explicitly frames it as complementary to the technicals.

## 2. ⚠ The sizing-lever question

Not addressed numerically. The stop is "the highs of the move," which on a blowoff can be 30–50% away; the sizing answer is the day-1/day-2 scaling he asks the mentee to specify. Nothing here on intraday stop tightness.

## 3. Claimed edge & evidence

None. It is a review of a trade the mentee **missed**; no P&L, no base rate. The 2x/2x numbers are offered as "how I try to systemize and start to quantify" — a heuristic, not a statistic. No course pitch in this one (2023, pre-channel-monetization).

## 4. ⚠ Prop-infrastructure dependency

Low for the daily-bar version. The intraday version leans on Level 2 ("were there any real sellers, did buyers get exhausted") and borrow on a sub-$1 biotech, which a retail account may not get.

## 5. The template (what he says a write-up must contain) [03:38–04:24, 16:49–17:16]

Overview (float / market cap / what they do) · news or no news, and **what caused the big prior gap** · daily chart with the capitulation signs named · intraday chart, marked up by hand · Level 2 / tape · how you traded it or why you missed it · **exactly how you would trade it next time: entry, size on day 1 / day 2, stop, scale-outs, cover conditions** · a mentor's execution of the same trade · **analogs: comparable tickers that did the same move, building a database by pattern name** ("blowoff daily + intraday low, small-cap type move" becomes a playbook page). Do it fast, in shorthand, and share it with a pod for feedback.

## 6. Collisions with the repo

- ⭐ **Testable now:** define blowoff = (range_t ≥ 2 × range_{t−1}) & (vol_t ≥ 2 × vol_{t−1}) & up-day after a ≥N-day run; measure forward 1/3/5-day returns vs the run's other days. The daily panel (`liquid_panel_2019.parquet`) and the Minervini cache both carry OHLCV. Small caps are under-represented there — note the universe mismatch.
- **[[project_crash_leader_study]]** conditioned on regime, `setup-grading-chart-nuance.md` on decline shape; this adds a third candidate — **volume acceleration at the turn**. Same event set can carry all three.
- The template is what `run_daily_journal.py` + `journal_trade_reviews` already do, minus two fields worth adding: **the analog ticker** and **the prior-gap cause**.
