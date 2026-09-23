# Qullamaggie — "If you don't spend time studying historical stock moves over the weekend, you won't make it trading" (2020-07-02, 82 min stream)

_Reviewed 2026-09-23. A live stream the day before the July 4th weekend: failed parabolic shorts (WKHS, NKLA, NVAX
etc.), swing longs (PDD, SHLL, TSLA) managed live, and Q&A on trailing stops, position sizing, the
"undercut & rally", and why swing beats day trading. Timestamps are the start of ~45-s caption blocks (±45 s)
unless marked exact._

⚠ **The title is the homework speech at the end** (1:20:37–1:21:29: "go through a couple of hundred stocks…
memorize a thousand charts this weekend"). It isn't a study.

## Verdict: 2 / 5

**Useful for the spec.** It has the clearest primary-source statement that **the trailing MA depends on the kind
of stock** (exact 00:55:59–00:56:26), a concrete position-sizing rule, and an honest admission that a popular
setup (undercut & rally) is one he *can't* trade.

**Weak as evidence.** Live losses are stated again: −$70k NVAX, −$37k in about three minutes, −$18k PDD adds,
−$21k SHLL. The one conceptual claim with a mechanism ("study thousands of historical moves") is
outcome-selected by construction.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 0:02:17–0:03:52 | "I can't win on these shorts." WKHS and INO both made the parabolic move, pulled back 22–31% to the rising 20-EMA on the 60-min, then **ripped to new highs** | ✅ **Honest counter-evidence to his own parabolic short**, and it matches every short test here. Short-universe test: **0 of 10 short universes has a negative absolute return**; weak and extended names still drift up. Proxies FAIL (see the 2020-05-27 notes) |
| 0:13:58–0:14:45 | "I lost so much money shorting the **front side**… almost blown up several times"; short only the **backside** | Consistent with "wait for weakness" (2020-05-27 notes). No test separates front-side from back-side shorts. Low value: our short evidence is null at both |
| 0:05:23 | TSLA "always obeys the 10 and 20-day moving averages so well" | **Hindsight on one name.** Trend smoothness as a signal is **NULL**: share of closes above the 21 EMA, EMA slopes, the DINO profile (−0.64pp/20d vs other leaders) (`scripts_adhoc/trend_quality*_2026-09-22.py`). Smoothness describes past winners, it doesn't forecast |
| 0:29:33–0:30:19 | Buy only when it's **"surfing the rising 10 and 20"**. EEOM "broke out a long time ago… too extended"; backside names must reclaim the declining 10/20 on the 60-min first | **Location half AGREES:** the best single gate on the bimodal target is **distance to the 21 EMA** (+0.057R, t ~2), which confirms the 1-ADR location rule directionally, and the breakout buys **+0.52 ADR above the 20d high vs −2.09 for a random later entry**. ⚠ Neither clears the bar, and extension is a **timing** variable, not a **selection** one (within-date rank: less-extended candidates are *worse*, t −2.06…−0.95) |
| 0:34:24–0:35:28 | TSLA: "sold a third… down to half size". Selling partials into strength on a stretched winner | This is his partial exit in practice: **1/3 → 1/2, discretionary, triggered by extension, not by day count**. Our trims: **sell half at 2 / 3 ADR extension −0.33R / −0.25R (t −4.2 / −3.8)**, −25…−40% max DD, worse per unit DD than trading half size (`profit_lock_2026-09-20.md`) |
| 0:51:26–0:53:14 | **Sizing**: a new position ≈ **10%** of the portfolio, **15%** if it's a big one (it used to be larger); risk = entry to stop × shares, e.g. 50k shares, ~$1.20 stop = **$60k risk**; sometimes full size at once, sometimes adds | **A notional cap, not a risk-% rule.** The house uses fixed small risk per trade (Luk 0.3%). Our size-lever finding is that the lever is **exclusion** (A+B only +0.29R OOS), not a size spread (10× spread +0.08R). His 10–15% notional cap caps concentration, and nothing in our data argues against it |
| 0:54:12 | "Time to start raising stops… raising my stop on a lot of stocks" | Discretionary tightening. **"Extended → tighten" is INVERTED here**: BE once ≥2 ADR extended −0.19R (t −2.8); a 10-EMA trail once extended **−0.47R (t −4.8)** |
| **exact 00:55:59–00:56:26** | ⭐ **Trail rule by stock type**: "if it's an **institutional-quality** stock I use the **10 and 20 [day]**… if it's a pump or a small-cap total hype stock… I use the **intraday 20 and 65 EMA** [60-min] more aggressively" | ⭐ **A spec refinement the queued row lacks.** For liquid names the trail is the **10- or 20-day**. For hype small caps it's a **60-min 20/65-EMA**. Our universe is the institutional kind, so the daily 10/20 is the right comparison. The house uses a **20-EMA** close trail on everything; the 10 vs 20 choice is by speed (see the interview notes). The 60-min variant is outside our universe |
| 0:59:14–1:00:13 | "The key to big money is not trading all the time, it's **trading right and then waiting**" | ✅ **AGREES.** Exit timing: same-day exits are the negative bucket in both books (scalp −0.13R vs trail +0.89R); Gabe's 278 same-day cycles −$8.3k at a 19% win rate (`exit_timing_study_2026-09-18.md`) |
| 1:02:06–1:03:38 | "Only three setups… they occurred 10, 50, 100 years ago and **I have the proof because I've done my research**" | ⚠ **Not proof.** A hand-built catalogue of historical moves is outcome-selected. It shows the pattern preceded winners, never how often it preceded losers. That's the exact error behind the retracted Tito 17/17 fade (−0.26%/day when run honestly) and the UR band sweep (t 27.8, retracted) |
| 1:06:04–1:09:20 | **Undercut & rally**: in an uptrend, an undercut of the rising 10/20/50-day that's reclaimed fast is bullish. But "**you don't know if it's an undercut or a legit breakdown until after**… I haven't figured out how to trade that setup" | ✅ **His honesty matches our data.** It's the daily-bar shakeout in §10: **PARKED, low prior**. Nearest tests: PDL break/hold ≈ random minute (+0.03R); UR ~0R intraday and **NULL** as a trigger (+0.033pp vs a random minute, t −0.31) |
| 1:14:30–1:16:58 | Swing beats day trading: "the big moves take weeks and months" | ✅ **AGREES.** Stage A: every intraday arm negative, and only the swing trail is positive (+0.517R). Exit timing: the trail's mean is all right tail, median holding 10 sessions |
| 1:19:01 | "Most stocks I go long are **not** near all-time highs" | Mild contrast with house selection (within 15% of the 52-wk high in the precision tier). The tier itself is **NULL · REFRAME** on freeze-forward (a regime finding, not a selection finding), so no conflict worth pursuing |

## What I would take

1. **The trail-by-type rule** (exact 00:55:59): 10/20-day for institutional names. It goes into the README exit spec.
2. **His admission about the undercut & rally** is the most useful negative in the KB. Even he can't define
   entry/stop for it, so don't queue it on his authority.
3. **Nothing to adopt** beyond confirming house practice (hold, don't scalp).

## Not tested, could be

- Nothing new. The trail choice feeds the partial-then-trail test (README).
