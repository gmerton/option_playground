# SMB Capital — "Revealing My Secret Relative Strength Breakout Strategy" (2026-08-20) — reviewed 2026-09-22

Video: https://www.youtube.com/watch?v=l7F9yIf8CeE (17:33, 31,166 views at review time)
Captions: yt-dlp auto-subs, clean pull, ~2,880 words. Last ~20% is an SMB recruiting pitch, not content.

**Score: 3/5** — the highest this cohort has scored here, and the reason is specific: his *mechanism* is
the one leadership-flavoured idea that has actually PASSED in our data, and his *process* (rank don't buy,
close-based trigger, stop at the day's low, calendar veto) independently matches the house process. It
loses points because the evidence is three hand-picked charts from one month with a known bottom, two of
his four filters are contradicted by our panel tests, and **he omits the one filter that decides the
outcome in our data** — volume confirmation.

## What he actually proposes

1. Wait for a genuinely weak market — QQQ down 2–3%, closing on lows, or a run of red days with VIX up.
2. Find names that *refuse to go down*: flat or green while QQQ flushes, **more than once**.
3. Filter: near 52-week/all-time high (explicitly NOT mid-range), and 10 SMA > 20 SMA both sloping up.
4. **Rank, don't buy.** "Relative strength on its own is not an entry. It's an alert." It reorders the
   watchlist; bandwidth is the real constraint.
5. Trigger = the first **close** over a clear higher-timeframe resistance level ("not the first tick").
   Initial stop = the low of that day. Trail under the 5 or 10 SMA it is "surfing". Take profits into
   extremes and gaps.
6. Veto any name with earnings or a scheduled event inside the holding period.

Mechanism claim: on down days, a name that doesn't fall is being accumulated — institutions work orders
over days and use weakness to fill. "Weakness in the market is what makes strength visible."

## Fact-check — every number in the video is accurate

Verified against Tradier daily bars:

| his claim | tape | ✓ |
|---|---|---|
| NASDAQ "a little more than 8%" 6/29→7/29 | QQQ 724.08 → 661.73 = **−8.6%** | ✓ |
| 7/27 QQQ open 691.68, low 675.95, close 682 | 691.68 / 675.95 / 682.12 | ✓ |
| 7/29 low close 661.73 | 661.73 | ✓ |
| 7/30 close 683.55, heaviest volume of the pullback | 683.55 on **66.8M** vs 57.2M / 42.7M | ✓ |
| HPE 8/3 open 47.51, close 50.24 | 47.51 / 50.24 | ✓ |
| SNOW 7/29 open 276.90, ran 293.56, close 283 | 276.90 / 293.56 / 282.90 | ✓ |
| DDOG ran to 292.72, gapped to 227.45 on earnings | 8/5 high 292.72, 8/6 open 227.45 | ✓ |

And all three genuinely had the property he claims, 6/29 → 7/29 against QQQ's −8.6%:
**SNOW +12.4%, DDOG +6.3%, HPE +0.1%** (flat — exactly as described). No cherry-picked misquotes, which
is more than most of this cohort manages.

## ⭐ The finding: his own three examples invert under our gates

Running his entries through the house lens (ADR20, 21 EMA, entry-day stop, RVOL vs 20d):

| name | entry | ADR% | stop% | **stop/ADR** | **ext21** | intraday run to entry | **RVOL** |
|---|---|---|---|---|---|---|---|
| **HPE** (he traded, "best trade in weeks") | 50.24 | 5.5 | 8.51 | **1.55** | +1.32 | **+5.75%** | **0.99** |
| **SNOW** (he skipped) | 282.90 | 4.9 | 2.17 | 0.45 | +1.43 | +2.17% | **1.97** |
| DDOG (he passed — earnings) | 288.15 | 5.2 | 6.09 | 1.17 | **+2.10** | +5.93% | 1.15 |

- **The trade he took broke out on RVOL 0.99 — below average volume.** Our most robust breakout result
  (299 names, 2006–2026) is monotone in RVOL: **<1.0 = −0.68% @21d**, 1.0–1.3 −0.59, 1.3–1.8 −0.44, and
  only **1.8–2.5 = +0.86 @63d (t 3.64)** and ≥2.5 +0.89 turn positive — *all breakouts pooled are
  negative* (−0.51, t −3.29). HPE was a draw from the worst bucket. It won; that is not evidence it was
  the right selection.
- **The one he skipped, SNOW, is the only one in the passing volume cohort (1.97)** — and it also had the
  cleanest entry (only +2.2% of intraday run bought, vs +5.8% on HPE).
- So his narrative ranking (HPE best, SNOW "illustrative") is **backwards relative to the one gate that
  sorts in our data**. He never mentions RVOL except one passing "or a breach of that level on volume."
- **All three entries sit +1.3 to +2.1 ADR over the 21 EMA** — the extension band our ledger identifies as
  the leak (breakout entries buy 2.6 ADR higher than a random later entry in the same name; control beats
  signal −0.21…−0.33R vs +0.13…+0.21R).
- **His stop rule produces a 3.4× range of stop widths** (0.45 → 1.55 ADR) and he never connects stop
  width to size. On HPE the "initial stop is the low of that day" is **8.5% below entry** on a day that
  travelled 9%. His only sizing line is "size it so a wrong read costs you a normal loss," which is right
  in spirit and unoperationalised.

## Claim-by-claim vs our evidence

| his claim | our evidence | verdict |
|---|---|---|
| Strength against a falling market = institutional accumulation | **Rotation study Part III**: volume-confirmed breakouts in *bottom-3* RS sectors beat top-3 by **+5.6pp paired, t 2.61**, and +6.1pp survives netting the stock's own sector ETF. "Idiosyncratic demand against a headwind is itself the filter" | **SUPPORTED** — our single passing leadership-type result, same logic at sector level |
| RS is an alert, not an entry; it reorders the watchlist | Our own conclusion on the cluster tool: "a lead-time/watchlist tool, explicitly NOT an edge; the name must still trigger" | **AGREES** |
| Trigger = first *close* over the level; stop = day's low | Entry study (2,439 name-days, 1-min bars): **buying the CLOSE beats every intraday entry** (paired −0.9 to −2.3pp, t −1.6 to −3.4); house rule is close entry, stop = day's low judged on the close | **AGREES** |
| 10 SMA > 20 SMA stacked and rising is a *requirement* | `sma_stacked` **fails to sort** on 43,970 breakouts (unstacked +0.022 vs stacked +0.009; spread 0.013 = noise) | **CONTRADICTED** (as a requirement; it is not a filter, it is a description) |
| Must be near the 52-week/all-time high | Best cohort is **middling, 3–15% off the high** (+0.95 @63d); "within 3% of 52wk high" has pooled mean and date-level t disagreeing in sign → **unresolved** | **NOT SUPPORTED** |
| The level break is the trade | Level-trigger test (20,148 name-days, 13 arms): every arm −0.06 to −0.10R, **break = hold**, the level picks the DAY not the minute, and **pivot break is the worst-timed of 13** (entry +2.0 ADR over the 21 EMA) | **CONTRADICTED as a trigger**, though the daily *close* version is our own rule |
| Skip anything with earnings inside the holding period | Not directly tested here for long breakouts. Mechanically sound: an earnings gap defeats a stop, and his DDOG example (−21% gap through the stop) demonstrates it | **PLAUSIBLE, untested** |
| Volume confirmation | Mentioned once, in passing | **OMISSION — the decisive gate in our data** |

## The structural critique

**The method is partly a market-timing bet wearing stock-selection clothes.** Every example is drawn from
a window he narrates with the bottom already known — "remember those two dates: the 29th was the bottom,
the 30th was the turn." In real time you do not know that. He half-concedes it ("the market turning isn't
necessarily a requirement, but it is a very strong tailwind"), but the payoff of buying high-RS names into
a turn depends heavily on the turn arriving. If it doesn't, you own breakouts in a downtrend. Our own
regime work cuts the other way on this: gating entries on **SPY above a rising 200 SMA** halves drawdown
and doubles CAGR, and his method deliberately does its shopping when that gate is closest to failing.

**Evidence standard: n = 3, one month, selected after the fact.** Better than the winners-only norm in
this cohort — he shows a pass (DDOG) that would have been profitable at the trigger, which is real
intellectual honesty — but three charts is an illustration, not a result.

## What is worth taking

1. **The mechanism, as a *selection* filter, not a trigger** — and this is already the shape our catalyst
   queue wants: filter first, enter later. Down-day RS is a cheap, daily-bar-computable version of the
   Part III sector finding, at the name level, which we have **not** tested.
2. **"Rank, don't buy"** — correct and consistent with everything we've found about states vs moments.
3. **The calendar veto** — cheap, and it protects a stop that an earnings gap would otherwise jump.

## Testable claim extracted (the one worth running)

**H:** On days QQQ falls ≥1.5%, names that close flat-or-green *and* within 15% of their 52-week high
have better forward returns than matched names, measured at the *next* breakout close — and the effect is
independent of RVOL.
**Design:** daily panel 2019–2026, `pattern_test` harness, control = `xname` (selection) and `post`
(timing), count of qualifying down-days as a dose-response. **Pre-register the RVOL interaction**, since
our prior says RVOL ≥1.8 is doing the work and his filter may just be a proxy for it.
**Bar:** beats both controls, both halves, |t| ≥ 3, and survives adding RVOL as a covariate.
~20 lines on the existing harness.

## Score rationale

**3/5.** Mechanism supported by our strongest leadership-type result; process matches the house process on
three of four axes; numbers all check out; shows a pass. Against that: two filters contradicted, the
decisive filter omitted, entries land in the extension band we know is the leak, stop-to-size link absent,
and his own worked example is the weakest of his three by our gates. Risk to a retail follower: **5/10** —
the process has stops and a calendar veto, but the stop width is unmanaged and the method encourages
buying after a 5–6% intraday run.

Related: [[project_rotation_detection_study]], [[project_entry_extension_finding]], [[project_entry_study]],
[[project_catalyst_queue]], [[project_smb_capital_kb]], [[project_traderlion_kb]].
