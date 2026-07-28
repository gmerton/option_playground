# The Opening Gap (gap fade)

> **Verdict:** The headline fill statistic is real but is a composition artifact of gaps too small
> to trade. On the gaps Carter actually tells you to trade, the same-session fill rate is 27–35%,
> not ~70%. A weak positive expectancy survives without a stop, but it is concentrated in
> high-volatility days and mostly disappears once a stop is added.
> **Type:** intraday · **Instrument:** index futures (ES/NQ/YM/TF); tested on SPY/QQQ/IWM/DIA
> **Conviction:** 1/5 · **Risk:** 7/10 · **Tested?** yes (EOD-bar test, path-order unresolvable)
> **Source:** Ch. 7, pp. _–_ (3rd ed., 2019) — page refs and the book's own numbers still TO FILL

---

## 1. Mechanics

As read (⚠ mechanics below are reconstructed pending the user's chapter notes; the numeric
thresholds in particular are placeholders):

- **Universe / instrument:** index futures — ES, NQ, YM, TF.
- **Timeframe / session:** intraday, entered in the first 30 minutes, closed same session.
- **Setup condition:** regular-session open gaps away from the prior session's close by more than
  a minimum and less than a maximum, both stated by Carter in **index points**.
- **Trigger:** wait out the opening ~15–20 minutes; enter when the gap-direction move fails.
- **Entry:** against the gap (short a gap up, long a gap down).
- **Stop:** beyond the opening-range extreme.
- **Target / exit:** the prior session's close (the "fill"); flat by the close regardless.
- **Filters & vetoes:** don't fade news/earnings/Fed gaps, the day after a large trend day, or the
  first trading day of the month.

## 2. Claimed edge & returns

⚠ **TO FILL from the user's copy** — the specific fill percentages, per index, and the min/max
point thresholds. The test below was run against the *generic* form of the claim ("index gaps fill
same-session at a high rate"), which is the part that does not depend on the exact numbers.

## 3. Market-structure dependencies ⚠

- **Depends on:** intraday mean reversion in index prices being strong enough to retrace the
  overnight repricing before the close; on overnight price discovery being *incomplete*.
- **Changed since 2019?** **Yes, but not for the reason the KB predicted.** Fill propensity has
  declined materially — but the decline starts around **2010**, not 2022, so the 0DTE story does
  not fit the timing. SPY same-session fill on 0.25–0.5 ATR gaps by 5-year block:
  57.4% (1995) → 57.8% (2000) → 60.2% (2005) → 59.8% (2010) → **49.9% (2015)** → 54.6% (2020) →
  48.1% (2025+). A secular decline consistent with more complete overnight price discovery
  (globalised futures/ETF flow), not with a 2022 dealer-gamma break.
- **Hard-coded thresholds?** Yes, and they are dead. Carter's min/max gap filters are in index
  points against a ~2,500–3,000 SPX; the index has roughly doubled. Everything in the test below is
  restated in **ATR units** (gap ÷ 14-day ATR known before the open), which is the scale-free form.
- **Verdict on decay risk:** **medium-high**, and partially realised already.

## 4. Objective assessment

The chapter's central number does not mean what it is used to mean.

**The fill rate is a composition artifact.** Same-session fill collapses monotonically with gap
size (SPY, 8,257 days, 1993–2026):

| gap size (ATR) | SPY fill % | n | share of all gap days |
|---|---:|---:|---:|
| 0–0.25 | **85.4%** | 4,343 | 53% |
| 0.25–0.5 | 56.0% | 2,396 | 29% |
| 0.5–1.0 | **35.2%** | 1,283 | 16% |
| 1.0–2.0 | 26.7% | 217 | 3% |
| >2.0 | 11.1% | 18 | 0.2% |

The pooled ~67–70% figure is dominated by the 53% of days whose gap is under a quarter of an ATR —
a 28 bp median move that is not a trading opportunity. **The relationship runs the wrong way for
the strategy: precisely the gaps large enough to be worth fading are the ones that don't fill.**
Post-2022, on gaps ≥0.5 ATR, the fill rate across all four ETFs is **27.2%**.

**A high fill rate wouldn't imply an edge anyway, and the data shows it directly.** Gaps that open
*inside* the prior day's range fill 76.0% of the time versus 52.7% for gaps beyond it — yet the
beyond-range gaps have the *better* expectancy (+5.22 bp, t=3.61 vs +1.06 bp, t=1.30). Fill
frequency and profitability move in opposite directions here. This is the exact confusion the
chapter is built on.

**Adverse excursion eats the trade.** On 0.5–1.0 ATR gaps the median adverse excursion before
anything good happens is 0.60× the gap being faded, and the 95th percentile is 2.0×. You are
routinely risking the full size of your target to reach it.

**Stops are where it dies.** Daily bars cannot order the intraday touches, so every stopped variant
is a bracket (pessimistic = ambiguous days stopped out; optimistic = ambiguous days filled). SPY:

| stop | ambiguous days | pessimistic | optimistic |
|---|---:|---:|---:|
| 1.0× gap (1:1) | 40.1% | −6.84 bp (t=−11.7) | +8.95 bp (t=+15.6) |
| 0.5 ATR | 14.4% | −8.36 bp (t=−12.5) | +5.90 bp (t=+9.7) |
| 1.0 ATR | 3.1% | −1.89 bp (t=−2.5) | +2.88 bp (t=+4.0) |

Every bracket straddles zero. **The entire question of whether the stopped version is profitable
lives inside intraday path uncertainty that daily data cannot resolve** — which means the honest
answer is that the version Carter actually trades is unproven, not proven.

**Instrument robustness is poor.** All-gaps, no-stop, net of 2 bp: SPY +2.59 bp (t=3.51),
IWM +0.87 (t=0.83), QQQ +0.83 (t=0.72), DIA **−0.83** (t=−1.05). One of four instruments clears
t=2 over three decades.

**Some of the "edge" is just beta.** Fading a gap down is going long, and the days in question have
positive open→close drift. Excess over passive open→close on the same days: SPY +2.76 bp,
IWM +1.21, QQQ +0.15, DIA −2.69. On the short side (fading gap ups) the excess is negative for
three of four instruments.

**Red flags present:** the stated statistic is a base rate presented as an edge; the gap-size
filters that would fix the composition problem are given in units that have since become
meaningless; costs are survivable here only because index ETFs/futures are cheap — the same
strategy on anything with a real spread is dead on arrival.

## 5. What's genuinely sound

Three things survive, and one of them is a genuine finding.

1. **Conditional on high volatility, the fade is real.** SPY no-stop by prior-close VIX tercile:
   low −0.83 bp (t=−1.25), mid +1.71 (t=1.79), **high +6.90 (t=3.65)**. The edge is a
   volatility-mean-reversion payoff, not a gap-mechanics payoff.
2. **Carter's "don't fade the day after a big trend day" rule is backwards.** Days following a
   ≥1 ATR move: **+11.91 bp, t=6.53** (n=1,304) versus +0.84 bp, t=1.05 otherwise. This is the
   strongest mechanical filter in the study and it inverts his stated veto. It is *not* merely the
   VIX effect — inside the high-VIX tercile it still separates cleanly (+24.24 bp, t=5.71 on
   after-trend days vs +3.29 bp, t=1.57 otherwise). But note the flip side: it is also *only*
   present in mid/high VIX (low-VIX after-trend days: +0.51 bp, t=0.30).
3. **The largest gaps mean-revert even though they rarely fill.** The 1.0–2.0 ATR bucket returns
   +26.36 bp (t=2.99) despite a 26.7% fill rate — the money comes from partial retracement into the
   close, not from touching the prior close. If anything real is in this chapter, this is it, and
   it argues for a **time-based exit at the close rather than a price target at the prior close**.

The uncomfortable summary of all three: **5.7% of days (high-VIX, post-trend-day) carry roughly
half of the strategy's entire 33-year P&L.** That is not a daily setup. It is a rare-condition
volatility trade wearing a daily setup's clothes.

## 6. Testability

- **Class:** **EOD-testable — done.** Fill/no-fill, MAE and MFE are all exactly recoverable from
  daily OHLC. Only the *order* of intraday touches is not.
- **Data needed:** none beyond what was used — `gapdata.parquet` (SPY/QQQ/IWM/DIA daily,
  unadjusted OHLC, yfinance) + `vix.parquet`. No API cost.
- **Testable skeleton:** run in `backtests/opening_gap/` — `fetch_gap_data.py`,
  `run_gap_study.py`, `run_checks.py`.
- **What the skeleton can't capture:**
  - Carter's real entry is ~15–20 min after the bell after the gap move fails; this enters at the
    open, which is a **better** fade price. All results here are therefore optimistic on entry.
  - Stop-vs-target ordering (see the brackets above) — the one thing that needs 1-minute bars.
  - The discretionary vetoes (news gaps, Fed days) are not modelled; only the mechanical
    ones (first-of-month, after-trend-day) were tested.
  - Dividend-unadjusted prices are used deliberately, so ex-div gap-downs are real tradeable gaps
    and are included, as they should be.

## 7. Overlap / conflicts with the existing book

- **Conflicts with the house precision-over-recall rule** in its stated form: a 70%-win-rate
  setup whose win rate is manufactured by including untradeable days is exactly the kind of
  high-recall statistic the repo is set up to reject.
- **Overlaps the pullback-short screen's lesson** (`run_pullback_shorts.py`): there too, an
  intuitive arrival signal turned out to be near-zero-or-negative EV in raw form and useful only
  as a conditioning variable. Same shape of result.
- **The high-VIX conditioning result is the transferable part** and belongs with the vol work, not
  with the intraday setups. It says nothing about gaps specifically.
