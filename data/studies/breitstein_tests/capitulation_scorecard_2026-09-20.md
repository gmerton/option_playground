# Breitstein capitulation scorecard: does stacking his variables raise the edge? — 2026-09-20

**Source:** SMB talk `P4Ijq-IJhE8` → `data/lance_breitstein/principles/capitulation-ten-variables.md`. His claim: the
more of the ten variables align, the higher the win rate and reward of fading the move ("right side of the V").
**Script:** `run_capitulation_scorecard.py` → `logs/capitulation_scorecard_2026-09-20.log`,
`capitulation_scorecard_summary_2026-09-20.csv`.

**Design.** Liquid panel (ADDV ≥ $50M), 2019-10 → 2026-09. Extreme day = close ≥ 2 ADR beyond the 20 SMA. Trigger =
next day breaks the extreme bar's low (short) / high (long). Entry next open +10 bps, stop = the extreme, risk ≥ 2%,
hold 10. Harness arms: stop_hold, t1R, t2R and trail_bar (his prior-bar trail). Score = count of 7 mechanical
variables at the extreme: acceleration, ≥ 3 same-direction days, ≥ 2.5σ beyond the 20 SMA, volume ≥ 3× the 50-day
average, ≥ 3rd leg, no small bars in 5, and top-tercile dollar volume ("boring" proxy for large cap). The news
variable was tested separately on earnings-covered names. Controls: `post` (same name, random later session) and
`xname` (random other name, same date). **Short fades: 33,295 signals; long fades: 38,061.**

## Result: no bucket works on either side, and stacking doesn't help

Mean R, trail_bar arm (his management); other arms agree:

| score | short n (dates) | short R | vs post | long n (dates) | long R | vs post | vs xname |
|---|---|---|---|---|---|---|---|
| 0–1 | 17,003 (1,476) | −0.17 | −0.05 | 17,741 (1,450) | −0.04 | −0.01 | +0.01 |
| 2 | 9,679 (1,400) | −0.15 | −0.02 | 11,595 (1,325) | −0.02 | −0.01 | +0.05 |
| 3 | 3,987 (1,068) | −0.14 | −0.01 | 5,218 (985) | −0.08 | −0.07 | +0.02 |
| 4 | 1,503 (641) | −0.12 | −0.04 | 1,976 (561) | −0.13 | −0.15 | +0.03 |
| **5+** | 592 (347) | **−0.22** | **−0.17** | 910 (304) | **−0.31** | **−0.32** | +0.07 |

- **Short side: negative in every bucket, every arm and every year** (5+ by year: −0.12 to −0.40R). The top bucket is
  the *worst*, 0.17R below its own later-session control. Fading euphoria in liquid single names loses steadily.
  That fits the rest of the repo: continuation (the Adhikary "exhaustion" bar is a continuation signal) and the failed
  bouncy-ball short.
- **Long side: monotone the WRONG way** (Spearman −0.7 to −0.9 across buckets). ⚠ **But that's one episode.**
  241 of the 910 score-5+ trades are **March 2020** at −1.30R, bought on the first bounce of a crash that kept going.
  Excluding the panic months, 5+ is **+0.055R** (t1R +0.014): flat, not inverted, and not an edge.
  **Effective n for the top bucket is a handful of market-wide panics, not 910 trades.**
- **The xname vs post split shows why.** The long buckets beat a random *other* name on the same date (+0.01 to
  +0.07) but lose to the same name on a *later* date. The name selection is fine; the date is the problem. High-score
  long fades cluster on market-wide panic days, and buying those days is a regime bet (same as the crash-leader study).

## Per variable (trail_bar, pooled): nothing turns a fade positive

| | short: R with vs without | long: R with vs without |
|---|---|---|
| v1 acceleration | −0.158 vs −0.159 | −0.080 vs −0.045 |
| v2 ≥ 3 days | −0.136 vs −0.168 | −0.036 vs −0.057 |
| v3 beyond band | −0.093 vs −0.163 | **−0.126 vs −0.048** |
| v5 volume ≥ 3× | **−0.037 vs −0.161** (n 591) | **−0.194 vs −0.048** |
| v6 3rd+ leg | −0.143 vs −0.168 | −0.065 vs −0.042 |
| v7 no consolidation | −0.156 vs −0.160 | **−0.185 vs −0.022** |
| v9 "boring" (large, liquid) | **−0.182 vs −0.126** | −0.060 vs −0.039 |

Volume and band distance make the SHORT less bad but never positive. On the LONG side the capitulation variables
(extension, volume, no consolidation) make it **worse**, the third time we've seen this (counter-trend long, boring/
violent). "Boring" (the liquidity proxy) doesn't help either side. ⚠ It's a dollar-volume proxy, not market cap or an
index, so his Berkshire/Nikkei version is still untested at the index level.

**v4 fresh news (241 earnings-covered names):** his veto isn't supported. Fading within ~3 sessions of earnings is
no worse: short −0.26 vs −0.21R, long +0.05 vs 0.00R.

## Verdict: FAIL (short) · FAIL (long; the apparent inversion is March 2020)
Stacking his variables does not produce a monotone edge on either side of liquid single names, daily, with his own
trigger and trail. The single-name capitulation fade is now **0 for 4** in the repo (bouncy-ball short, counter-trend
long, boring/violent, this). **YIELD (METHOD):** the `xname`-beats / `post`-loses split is the fingerprint of a
*date* effect. When a fade's signals cluster on market-wide panic days, report effective n in episodes.
**Open, and the only version left with a mechanism:** index/asset-class capitulation (his Nikkei trade). That's a
handful of events per decade, so it's closer to the FTD study than a pattern test.
