# Qullamaggie — "THE best daytrading setup." (2020-06-04, 2.9 h Twitch stream)

_Reviewed 2026-09-23. A raw live-trading stream: short starters in airlines/financials and GNUS (Genius Brands),
swing longs managed live, then long stretches of chat about buying a BMW X5M. Timestamps are the start of ~45-s
caption blocks (±45 s). Transcript in this folder._

⚠ **The title doesn't match the content.** No setup is ever laid out. The implied "best daytrading setup" is the
GNUS parabolic short, taken live. Most of the stream (roughly 1:20–1:27 and 2:27–2:37) is off-topic.

## Verdict: 2 / 5

**One genuine plus:** real-time P&L, losses included, stated as they happen:
- −$117k on the airline/financial shorts (1:28:42);
- −$59k on SAVE (1:15:09);
- −$54k on DDOG (1:44:49);
- +~$300k on GNUS (1:29:28–2:04:01).

It's more honest than a winners-only recap, but it's one session and a sample of about seven trades. The rest
is live commentary, not claims. He does state a few rules of thumb (wait for full extension before shorting,
buy what's going up, don't pick tops), and the ledger mostly says they don't mechanise.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 0:12:24, 1:42:24–1:43:57 | Parabolic short timing: **let it squeeze out "as much as possible" before shorting**. GNUS was "a better short at 10–12 tomorrow" than at 5.50 the day before. "Setups where you almost can't lose money" | **Untested at his extremes; nearest proxies FAIL** (Tito exhaustion fade −0.26%/day t −0.59; bouncy ball −0.41…−0.67R). ⚠ "Almost can't lose" is exactly the hindsight framing our ledger keeps retracting (UR band sweep t 27.8, the Tito 17/17 fade). The GNUS call did work on camera: predicted the day before, filled live, ~+$300k. **n = 1** |
| 0:30:06, 0:36:53–0:38:48 | Starter shorts, add on the **first red 5-min candle** or a VWAP loss; "small starters… I'm going to build some huge size" | Intraday triggers ≈ a random minute (Stage A, all arms; `ledger_rerun_2026-09-19.md`). VWAP double-rejection short **−0.26R, t −6.2**, worse than random. No short test on +100% names |
| 0:38:48, 0:44:00, 1:28:42 | Most starters stopped out: SYF, DFS, LUV, SAVE. Net **−$117k** on airlines + financials vs +$200–300k on GNUS | **Descriptive, and the shape agrees**: many small losses, one fat winner. Same bimodality as our breakout book (23.6% hold = +1.27R). One session is not a rate |
| 1:00:10 | "Sometimes breakouts retest, it doesn't mean they failed… not all breakouts go straight up, **most don't actually**" | ✅ **AGREES, and our number is stronger.** **76.4% of house breakouts return to the breakout level** (`retrace_entry_2026-09-20.md`). ⚠ But the 76.4% that return average −0.374R, so "a retest isn't a failure" is true for some and not for the population |
| 1:01:56 | "Both types work, bottom breakouts and extended stocks… depends on the market environment" | Unfalsifiable as stated. Our reversion section is 0-for-5 on single names |
| 1:39:25–1:40:04 | Raising stops to **breakeven** on open winners; using the day's new low as the stop | **Breakeven moves cost us:** BE after +1R **−0.08R** (t −2.0) and give-back rises 39% → 46%. Only BE after a **+2R close** is harmless (+0.01R, t 1.3) (`profit_lock_2026-09-20.md`). See README exit spec |
| 1:50:15–1:52:36 | "Buy stocks that are going up and breaking out, short stocks going down; don't try to find tops or bottoms" | **Half supported.** Our counter-trend and capitulation longs all fail (0-for-4 single-name capitulation fades). But the breakout *entry* is our measured leak: **2.6 ADR paid vs a random later entry in the same name, control beats signal** (`entry_vs_stop_2026-09-20.md`). "Buy what's going up" selects well and enters badly |
| 1:54:17, 1:58:19–1:59:04 | Market call: software weakening, laggards in "full FOMO", "we are a day or two away from a pullback", sizing down defensively | One discretionary top call. From memory, not checked against the data here: the Nasdaq peaked around 2020-06-10 and fell sharply on 2020-06-11, about five sessions later, so it roughly worked. **n = 1.** Our tests of trailing-regime timing all fail (FTD, trailing-30d breadth, own P&L feedback) |
| 2:00:49, 2:21:31 | "Up at least $3M… probably $4–5M in the past two months"; doubled the account in under two months; "one of the top 3 best 2-month environments I've traded" | **Self-reported, unverifiable here.** Consistent in scale with the ~$12M long / ~$3M short exposure he quotes live (1:02:46, 0:26:24). It confirms his edge, if any, is regime-concentrated. Our analogue: **top 8 of 83 months = 68% of positive R**, and **the paying months cannot be forecast** (`breakout_regime_and_stop_distance_2026-09-17.md`) |
| 2:07:09, 2:13:33 | Airline short entry = break of the **low of the current 60-min candle** | The 60-min ORL/candle-low trigger is untested (Stage A used ≤15-min ranges). Low prior |
| 2:07:55 | Long VISL on a multi-hour range break with higher lows, stop 0.92, "no news" | One intraday range break. Level triggers are NULL 0/12 (`level_trigger_test_2026-09-21.md`) |

## What I would take

1. **The live loss disclosure is the model** for how a creator claim should be presented. It's still n ≈ 7.
2. **"Most breakouts don't go straight up"** is right, and our 76.4% retest rate quantifies it.
3. **Nothing to adopt.** The parabolic-short timing rule (wait for day 3–5 and maximum extension) is the one
   untested spec, and it needs a small-cap + delisted universe we don't have.

## Not tested, could be

- Nothing new beyond the parabolic-short item in the 2020-05-27 notes. **Not queued.**
