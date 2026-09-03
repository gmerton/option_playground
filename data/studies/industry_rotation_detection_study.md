# Can we detect an industry rotation early? — the 2026 insurance rally, forensically

Study run 2026-07-28, prompted by the ALL / TRV / AFL rally. Question: **what was observable
before the move, and does it generalize to other industries?**

Short answer: **the move was not reliably predictable from any signal tested.** The best-timed
real-time tell (a group breadth thrust) fails to generalize across 224 events and 11 sectors. The
signal the daily report already uses (63-day industry RS) was both *late* here and *has no
predictive edge* in testing. What did work was the existing per-name breakout machinery.

---

## 1. The move

Insurance constituent returns to 2026-07-28:

| | 21d | 63d | 126d | 252d |
|---|---:|---:|---:|---:|
| PRU | +16.3% | **+33.9%** | +18.7% | +25.8% |
| TRV | +24.7% | +31.6% | +44.0% | +53.9% |
| RLI | +19.1% | +29.9% | +20.7% | +5.2% |
| ALL | +16.2% | +27.1% | +40.4% | +41.6% |
| MET | +15.0% | +26.2% | +30.3% | +28.9% |
| AFL | +9.3% | +13.3% | +21.9% | +28.8% |

KIE rose ~+16% off its breadth trough while SPY did roughly a third of that.

## 2. Signal timeline — when each candidate would have fired

| Signal | Fired | KIE since | SPY since | **Excess captured** |
|---|---|---:|---:|---:|
| KIE 21d RS > 0 | 2026-03-23 | +21.5% | +13.5% | +8.0pp ⚠ false start |
| KIE/SPY ratio > its 50sma | 2026-03-26 | +21.3% | +15.4% | +6.0pp ⚠ false start |
| **Breadth: %insurers >50sma crosses 80** | **2026-06-10** | **+14.5%** | **+2.6%** | **+12.0pp** |
| KIE/SPY ratio at 63d high | 2026-07-02 | +3.4% | −0.3% | +3.8pp |
| **KIE 63d RS > 0** (what the daily report ranks on) | **2026-07-02** | +3.4% | −0.3% | **+3.8pp** |

Two things stand out:

- **The March signals were false starts.** The group rolled over again — KIE's 63d RS hit **−16.6%
  on 2026-06-02**, its worst reading of the year, *after* those signals fired.
- **Breadth led the RS confirmation by three weeks** and captured 3× the excess. On 6/10, breadth
  was 84% while the 63d RS was still **−2.2%**. The group had already turned internally before any
  RS screen could see it.

That ordering is mechanical, not lucky: breadth is a count of constituents crossing a 50-day line;
63-day RS is a 63-day lookback. The lag is built in.

## 3. Does any of it generalize? — three tests, all negative

### 3a. ETF-level RS timing — 32 sector/industry ETFs, 2011–2026

Forward excess return vs SPY, signal minus baseline (percentage points):

| Signal | 21d | t | 63d | t |
|---|---:|---:|---:|---:|
| 21d RS crosses >0 while 63d RS <0 ("early turn") | +0.28 | 2.55 | +0.08 | −0.15 |
| Ratio crosses above its 50sma | +0.30 | 2.15 | −0.01 | −0.43 |
| **63d RS crosses >0** (the conventional one) | **+0.10** | **1.95** | −0.03 | 0.32 |
| Ratio makes a 63d high | −0.02 | 1.15 | +0.10 | 1.42 |
| Early turn + laggard (63d RS < −8) | +0.41 | 0.13 | +0.18 | −0.57 |

Nothing economically meaningful, nothing that holds at 63d, and no era consistency (the best rule,
"early turn," has t=3.28 in 2010–15 and t=0.70 in 2021–26).

**The industry RS ranking is descriptive, not predictive.** It tells you what *has* led.

### 3b. Breadth thrust — 11 sectors, 2006–2026, 224 events

Exact 2026-06-10 configuration: breadth crosses 80 after a washout (≤40 within 20 days), sector RS
still negative. Constituent breadth built from the 299-name panel.

| | 21d | 63d |
|---|---:|---:|
| pooled mean excess | +0.40pp | +0.33pp |
| median | +0.09 | −0.10 |
| win rate | **50.9%** | **49.3%** |
| t (naive; events overlap) | 1.43 | 0.66 |

A coin flip. Sector-level results are inconsistent (XLK +0.88 / XLY −1.03 at 21d). The
insurance-only version (n=20, 2011–2026) agrees: +1.05pp at 21d, t=1.28, and its instance list is
wildly dispersed — including **2020-02-05, which was followed by −19.2pp over 63 days.**

**The 2026-06-10 thrust (+12pp) is a draw from the right tail of a distribution centred on zero.**

### 3c. Peer earnings-gap spillover — inconclusive, not negative

Hypothesis: when a group's first reporters gap up, not-yet-reported peers re-rate. Only **5 days in
15 years** had ≥2 insurers gapping ≥4% on ≥1.8× volume — too few to test. The ≥1-gapper version is
weakly positive at 5d (+0.25pp, t=1.76) and decays to zero by 21d. Worth retesting on a proper
multi-industry universe with a real earnings calendar before dismissing.

## 4. What to actually take from this

**Do not build a rotation-prediction screen.** Three signal families, one well-powered (224 events),
all fail. Any detector fit to this episode would be fit to noise.

**Do build sector/industry breadth — but label it correctly.** It is not an edge; it is a *faster
read of the same information*, worth roughly three weeks of lead time over the 63d RS ranking. Use
it to populate the watchlist earlier, never as an entry. Concretely:

- breadth = % of a group's constituents above their 50-day SMA
- flag a group when breadth crosses 80 while its 63d RS is still negative
- the output is a *place to look for setups*, and the individual name still has to trigger

**Requires:** a ticker→industry mapping, which the repo does not have. The Minervini matrix supplies
the prices for ~5,300 names; the mapping is the missing piece (yfinance `.info` sector/industry
resolved all 299 test names in ~1 minute at 16 threads, so this is cheap).

**What actually made money here was the existing machinery.** TRV and ALL were on the EOD scan near
their pivots before the July leg; WAB fired a confirmed breakout on 1.6× RVOL. The per-name trigger
caught the move without any view on the group. That is consistent with the house findings:
*arrival at a state is not the trade* (pullback-short screen, TTM Squeeze), and conviction selection
plus a volume-confirmed trigger is where the edge has repeatedly shown up.

---

# Part II — the individual names, and the falsification test (2026-07-28)

Follow-up question: did the *stocks* that popped share a pattern, and **did the insurance names
that didn't pop show the same buy signals?**

## 6. The winners' breakouts — and the control group

First volume-confirmed 50-day-high breakout (RVOL ≥ 1.3) per insurer, 2026-05-01 → 07-28:

| Name | Breakout | RVOL | Return since | Excess vs SPY |
|---|---|---:|---:|---:|
| ALL | 05-19 | **2.66** | +20.5% | +19.1pp |
| TRV | 06-23 | **2.46** | +25.2% | +24.0pp |
| **CINF** | **06-26** | **1.97** | **+0.6%** | **−1.2pp** ❌ |
| CB | 06-26 | 1.96 | +6.2% | +4.4pp |
| **PGR** | **06-23** | **1.72** | **+2.5%** | **+1.3pp** ❌ |
| AJG | 07-01 | 1.64 | +8.9% | +9.4pp |
| AIZ | 05-14 | 1.63 | +11.2% | +11.8pp |
| AFL | 07-17 | 1.60 | +3.6% | +3.7pp |
| RLI | 06-29 | 1.35 | +12.5% | +12.3pp |
| WRB | 06-23 | 1.33 | +11.3% | +10.1pp |
| **no signal** | — | — | — | PRU +27.9%, BRO +26.8%, AON +21.8%, GL +16.6%, LNC +14.1%, ERIE +13.7% |

**The premise is partially falsified, in both directions:**

- **False positives.** CINF and PGR broke out in the *same week* as TRV and WRB, on comparable
  volume (1.97× and 1.72×), and went nowhere — CINF's excess return is *negative*.
- **False negatives.** Six names — including **PRU (+27.9%), BRO (+26.8%) and AON (+21.8%), three
  of the eight best performers** — never produced a qualifying breakout at all.

The apparent "highest RVOL won" pattern (ALL 2.66, TRV 2.46 → the two best outcomes) **does not
survive a runway control**: ALL broke out on 5/19 with 70 days to run, TRV on 6/23 with 35. Spearman
of RVOL vs excess is +0.12 raw but **−0.37 once normalized per day of runway**, while runway itself
correlates +0.46 with excess. In-sample, the volume story is a time artifact (n=11).

## 7. Pre-move features had no cross-sectional power

All 19 insurers, feature snapshot at **2026-06-05** (before the group turned), Spearman vs the
return that followed:

| Feature | ρ |
|---|---:|
| ADR20% | +0.21 |
| base tightness | +0.16 |
| 21d RS vs SPY | +0.13 |
| vol20/vol50 | +0.02 |
| 63d RS vs SPY | −0.03 |
| vs 50sma | −0.04 |
| off 52wk high | −0.17 |
| vs 200sma | −0.18 |
| 126d RS vs SPY | −0.25 |

**Nothing reaches significance** (n=19 needs |ρ| ≈ 0.46). Worse for the premise: every
*leadership* feature — above the 200sma, near the 52-week high, strong 6-month RS — points the
**wrong way**. Four of the six best subsequent performers were deep laggards on 6/5: BRO (−46.8%
off its high, 63d RS −29.7), AJG (−35.1% off), RLI (−25.6% off), LNC (−24.1% off). The names that
screened *best* on momentum — MET, AIZ, GL — finished mid-pack.

Repeating at **2026-07-01** gives `21d RS vs SPY, ρ = −0.46`: the names that had already run did
*worse* over the following month.

## 8. What DOES generalize — 299 names, 2006–2026

The episode-level story is unreliable, so the same two questions were put to the 20-year panel.
Event = close above the prior 50-day high. Excess vs same-universe baseline.

### Breakout volume — a real, monotone effect

| RVOL at breakout | 10d | 21d | 63d | t63 | n |
|---|---:|---:|---:|---:|---:|
| < 1.0 | −0.35 | **−0.68** | −0.77 | −1.24 | 25,532 |
| 1.0–1.3 | −0.33 | −0.59 | **−0.98** | −2.28 | 16,193 |
| 1.3–1.8 | −0.31 | −0.44 | −0.58 | 0.37 | 11,594 |
| **1.8–2.5** | −0.20 | −0.19 | **+0.86** | **3.64** | 4,768 |
| **≥ 2.5** | +0.09 | +0.40 | **+0.89** | **3.00** | 3,378 |
| *all breakouts* | −0.30 | **−0.51** | −0.57 | −1.68 | 61,465 |

Two things worth acting on:

1. **Breakouts in aggregate are a losing signal** (−0.51pp at 21d, t=−3.29). Only the
   volume-confirmed subset works. This validates the house rule that a drift through a pivot is not
   a trade.
2. **The crossover is at RVOL ≈ 1.8, not 1.2.** The 1.3–1.8 bucket is still negative at every
   horizon. The current gate of ~1.2× admits the bucket where the edge does not yet exist.

### Leader vs laggard — the episode's pattern does NOT generalize

Breakouts with RVOL ≥ 1.3:

| Cohort | 10d | 21d | 63d | n |
|---|---:|---:|---:|---:|
| within 3% of 52wk high | −0.28 | −0.22 | −0.42 | 13,588 |
| **3–15% off high** | **+0.24** | **+0.23** | **+0.95** | 3,961 |
| >15% off high | −0.62 | −1.14 | +1.08 | 2,191 |
| above 200sma + 6mo return > 0 | −0.15 | −0.04 | +0.22 | 17,833 |
| **below its 200sma** | −1.33 | **−3.08** | **−3.32** | 792 |
| **6mo return < −10%** | −1.45 | **−3.34** | −1.44 | 621 |

The insurance episode's laggard-bounce (BRO, LNC, RLI, AJG) was **episode-specific luck**. Over 20
years, breakouts from names below their 200-day or down >10% over six months are the *worst*
cohorts by a wide margin. The best cohort is the *middling* one — 3–15% off the high — not the
extreme leaders pinned to the 52-week high.

### Era note

RVOL ≥2.5 breakouts by era: 2006–11 −0.89 (21d), 2012–18 −0.08, 2019–21 −0.37,
**2022–26 +1.80 (t=1.83), +3.05 at 63d (t=2.64)**. The volume edge is concentrated in the recent
era — the opposite of decay, but thin enough that it could be regime rather than structure.

## 9. Actionable conclusions

1. **Raise the RVOL gate from ~1.2 to ~1.8** on breakout entries. 1.3–1.8 is measurably negative.
2. **Add two vetoes:** no breakout entries in names below the 200-day SMA, or down >10% over six
   months. Both cohorts run about −3pp at 21 days.
3. **Don't require the 52-week high.** The 3–15%-off-high cohort outperforms the at-the-high cohort
   at every horizon.
4. **Accept the recall limit.** Six of the best insurance performers gave no breakout signal. The
   trigger is a precision tool; it will miss a third to a half of any group's winners. That is the
   intended trade-off ([[feedback-precision-over-recall]]) — but size expectations accordingly.

---

# Part III — does group strength help an individual setup? (2026-07-29)

## 11. A correction to Parts I–II first

Parts I and II tested two things: *can you predict which group will lead* (no) and *does the group
ETF outperform after an RS signal* (no). Neither is how the industry-RS table is actually used.
The operative claim — O'Neil/Minervini orthodoxy, and the reason the daily report ranks groups —
is **"fish for setups inside leading groups."** That was never tested, so the earlier shorthand
that the study "refuted top-down sector work" **overstated what the evidence showed.**

Tested properly, the answer is stronger than "no help" — it is **inverted.**

## 12. The test

Every volume-confirmed 50-day-high breakout (RVOL ≥ 1.8) on the 299-name panel, 2006–2026, tagged
with its **sector's 63d RS vs SPY rank** (1 = strongest of 11) on the breakout date. Forward
individual-stock returns bucketed by that rank.

| | 10d | 21d | 63d |
|---|---:|---:|---:|
| breakout in a **top-3** sector | +0.82% | +2.14% | **+7.11%** (n=2,997) |
| breakout in a **bottom-3** sector | +1.16% | +3.55% | **+14.55%** (n=672) |
| **difference** | +0.34pp | +1.41pp | **+7.44pp** |

Breakouts from the *weakest* sectors more than doubled the 63-day return of those from the
strongest. Against the study's own baseline, bottom-3 volume-confirmed breakouts run **+9.12pp
excess at 63d (t=4.57)** versus **+1.68pp (t=3.78)** for top-3.

## 13. Two controls — the result survives both

**(a) Is it just the weak sector mean-reverting?** Re-measured as the stock's return **net of its
own sector ETF**, which removes the sector's move entirely:

| 63d | vs SPY | vs OWN sector |
|---|---:|---:|
| top-3 sector breakout | +4.03% | +3.85% |
| bottom-3 sector breakout | +10.99% | +9.98% |
| difference | +6.96pp | **+6.13pp** |

Only ~0.8pp of the ~7pp gap is the sector bouncing. **The rest is stock-level alpha.**

**(b) Is it one clustered episode?** No. The 686 bottom-3 events span **503 distinct dates across
132 distinct months**, present in every year 2012–2026 (5–80/yr) and in **all 11 sectors**
(Tech 71, Healthcare 31, Financials 25, Cons. Cyclical 22, Industrials 19, …).

Strictest version — **pair top-3 against bottom-3 breakouts occurring on the *same date***, which
removes market timing completely: over 265 shared dates the difference is **+5.60pp at 63d,
t = 2.61.**

## 14. Why this is economically coherent

A stock that can break out on ≥1.8× volume *while its sector is among the three weakest* is
demonstrating genuinely idiosyncratic demand. The sector headwind acts as a filter — only real
strength clears it. In a hot sector, a breakout may just be the tide lifting everything, so the
individual bar carries less information about the individual name.

That also explains the scarcity: 686 bottom-3 events versus 3,131 top-3. **The signal is rarer and
better**, which is exactly the precision-over-recall trade this book prefers.

## 15. What this does and does not overturn

**Overturned:** using industry/sector RS to decide *where to hunt for entries*. On this evidence
the leading-group filter is not neutral, it is **costly** — roughly 5–7pp of 63-day return on
volume-confirmed breakouts. Ritchie II's *"not really… we're bottoms up"* is the better-supported
position, and the strongest single-name signal in the book is a volume-confirmed breakout **against**
its group.

**Not overturned:**
- **Sector RS as risk context.** Knowing five holdings are all SMH names is real information about
  correlated drawdown. Nothing here speaks to that, and the position radar's group alerts stay useful.
- **Stock-level trend requirements.** The Part II vetoes still hold and are about the *stock*, not
  its group: no breakouts below the 200-day SMA, none with 6-month returns < −10%.
- **Industry-level (finer) grouping.** This tests 11 sectors. Insurance is a sub-industry of
  Financials; a 20-industry version could behave differently and is worth running.

**Practical change:** stop using the industry-RS table to *gate* candidates. Keep it on the report
as correlation/risk context, and explicitly stop treating "weak group" as a veto on an otherwise
clean, volume-confirmed setup.

## 16. Caveats

- **Part III sector-rank drift:** XLRE (2015) and XLC (2018) did not exist for the whole window, so
  "bottom 3 of 11" is effectively "bottom 3 of ~9" before 2018. Most events are 2016+, limiting the
  distortion, but the early years are not strictly comparable.
- Part III uses **sectors, not industries** — 11 coarse groups. A 20-industry version is the
  obvious next refinement.
- Same survivorship-biased 299-name universe throughout; net-of-own-sector differencing removes
  most but not all of the composition effect.
- Part III says nothing about whether a *bottom-up screen would surface* these names in practice —
  only that once surfaced, weak-group membership is not a reason to skip them.
- **Part II sign check:** for the "within 3% of 52wk high" row the pooled mean (−0.42 at 63d) and
  the date-level t (+2.30) disagree in sign, because one weights observations and the other weights
  dates while signals cluster. Where they disagree, treat the cohort as *unresolved* — the leader
  cohort is best read as "no clear edge," not "negative."
- Part II n's are small at the episode level (19 names, 11 breakouts). The 20-year panel carries the
  conclusions; the episode only generated the hypotheses.
- ETF panel effectively starts **2011-09-29** (newer industry ETFs truncate the common window).
- Sector breadth uses a **survivorship-biased** 299-name universe (liquid today). Baseline
  differencing removes most of the level effect, not all of the composition effect.
- **Sectors, not industries.** Insurance is a sub-industry of Financials; a true industry-level
  test needs finer membership and would have more, smaller groups.
- Pooled t-stats are naive — thrust events cluster in time across sectors, so the true standard
  errors are wider than shown. That makes the negative conclusion *stronger*, not weaker.

## Reproduce

Scripts (scratch, 2026-07-28): `characterize.py`, `turn_detail.py`, `generalize.py`,
`breadth_test.py`, `breadth_multi.py`, `spillover.py`.
Data: `etfs.parquet`, `insurers.parquet`, `secmap.parquet`,
`data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet`.
