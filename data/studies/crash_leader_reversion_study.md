# Buying the crash — the anti-Minervini, tested

Study run 2026-08-02. Question: **does buying a formerly-strong stock that has just been
massively sold off beat the tape?** Minervini buys strength near highs; this buys quality at
maximum discount. Both cannot be right about the same names at the same time.

**Short answer: it is not a stock-picking edge, it is a regime bet.** Deep-crash buying works
when the whole market is broken and *loses* when the market is healthy — the median trade in a
strong tape underperforms by −20% over a year. The "was it a strong stock" half of the premise
contributes almost nothing. Today's tape is not the regime this needs.

Scripts: `run_crash_leader_study.py` (event harness + sweep), `scratch_crash_leader_bias.py`
(survivorship/payoff), `scratch_crash_leader_regime.py` (per-year + breadth split).

---

## 0. Setup

| | |
|---|---|
| Universe | `broad_history/` — 2,674 names, daily OHLCV, 2006-01-03 → 2026-07-23 (9.7M rows) |
| Strength | measured *into* the peak: 252d high ≥ +25% above the close 252 bars earlier |
| Crash | close ≤ −DD% below the trailing 252d high, and that high was set within the last 126 bars |
| Entry | signal at close, **fill at the next bar's open**. Four variants (below) |
| Vehicle | 50d ADDV ≥ $10M, price ≥ $5 |
| Dedupe | one event per ticker per episode (63-bar suppression) |
| Measure | forward 21/63/126/252-bar return, and **excess vs the same-date cross-sectional median** of the eligible universe |

The same-date paired benchmark is what makes this readable at all: event names and benchmark are
drawn from the same survivors-only pool on the same date, so the market component cancels.

⚠ **Survivorship.** `broad_history` is the universe that exists *today*. Names that crashed and
never came back are absent, and this biases *this* strategy harder than any other tested here.
Section 3 shows the bias is not what generates the headline result — but every absolute number
below is an overstatement.

---

## 1. The sweep — depth matters, timing doesn't, "strong" doesn't

Excess vs same-date universe median, `arrival` entry (n = event count):

| Drawdown | 63d exc% | 252d exc% | 252d **median** | 252d win% |
|---|---:|---:|---:|---:|
| −20% | +1.76 | +5.29 | **−2.57** | 47.0 |
| −30% | +2.10 | +8.51 | **−3.01** | 47.1 |
| −40% | +3.99 | +15.41 | **−1.71** | 48.7 |
| −50% | +8.24 | +31.15 | **+5.22** | 53.4 |

Three readings:

**Deeper is monotonically better**, and only at −50% does the median turn positive. Everywhere
shallower, the mean is positive while the typical trade *loses to the tape*.

**Entry timing barely matters.** Waiting for stabilisation (`stab10`), an EMA20 reclaim
(`reclaim20`), or an RSI turn (`rsi_turn`) did not beat simply buying on arrival at the drawdown
threshold. At dd30/252d: arrival +8.51%, stab10 +12.91%, reclaim20 +14.07%, rsi_turn +10.38% —
the "patient" entries look better on the mean but all carry the same negative median (−2.6 to
−3.1%), i.e. they are selecting *more tail*, not more reliability. This is the opposite of the
pullback-short finding, where the arrival signal was outright negative EV.

**"Was it a strong stock" adds ~1pp and is not doing the work.** Running the identical sweep with
the strength filter removed (`--strength none`):

| Horizon | strong exc% | any exc% | strong med% | any med% |
|---|---:|---:|---:|---:|
| 63d | +2.10 | +1.59 | −0.04 | −0.34 |
| 252d | +8.51 | +7.55 | −3.01 | −2.98 |

The premise was "strong stocks that sold off." The data says the *strong* qualifier is nearly
inert — what is being measured is "deeply crashed stocks bounce," full stop.

---

## 2. Payoff shape — the mean is a lottery ticket

dd30 / arrival, excess return distribution:

| | 63d | 252d |
|---|---:|---:|
| mean | +2.10% | +8.51% |
| median | −0.04% | **−3.01%** |
| win rate | 49.9% | 47.1% |
| top 1% of trades carry | 72% of total excess | 52% of total excess |
| top 5% of trades carry | 187% of total excess | 130% of total excess |
| **mean excess EXCLUDING top 5%** | **−1.93%** | **−2.68%** |

Strip the best 5% of trades and the strategy is a **losing** strategy. That is an option payoff,
not a base-rate edge, and it directly contradicts the stated house preference for precision over
recall — this is a low-precision, tail-dependent structure. If traded at all it has to be sized
and structured like a convex bet (cf. the Sleeping Giants LEAP work), not like a swing book.

---

## 3. Is the edge survivorship? — no, but it isn't stable either

Survivorship makes a clean, falsifiable prediction: a 2008 event had 18 years to prove the company
survived, a 2024 event had 2. **If the excess is manufactured by selection, it must decay toward
the present.** It does the exact opposite:

dd30 / arrival, 252d excess by era:

| Era | n | exc% | med% | win% | t |
|---|---:|---:|---:|---:|---:|
| 2006-10 | 1000 | +0.62 | −3.74 | 44.7 | −0.35 |
| 2011-14 | 741 | +1.98 | −3.72 | 45.9 | 1.55 |
| 2015-18 | 911 | −0.95 | −7.11 | 42.5 | −0.78 |
| 2019-22 | 2560 | +8.86 | −2.66 | 47.4 | 4.08 |
| 2023-26 | 1849 | **+19.59** | +1.21 | 50.7 | 4.75 |

So the headline is not a survivorship artifact. But note what it *is*: **the entire effect lives
in 2019-26 and is absent for the first thirteen years**, including 2006-10, which contains the
single largest crash-and-recover episode in the sample. Per-year, dd50 swings from +93.8% (2020)
to −26.5% (2021) to −36.7% (2013). That is not an edge with a stable mean; it is something
switching on and off.

---

## 4. What it switches on — market breadth

Split every event by the **% of the liquid universe trading above its own 200sma on the signal
date** (terciles over the full history: weak < 0.562, strong > 0.724):

**dd50 / 252d**

| Tape at signal | n | exc% | med% | win% |
|---|---:|---:|---:|---:|
| weak | 579 | **+60.25** | **+29.17** | **74.1** |
| mid | 550 | +19.71 | −5.20 | 46.4 |
| strong | 557 | +12.20 | **−20.24** | **39.0** |

**dd30 / 63d** (much larger sample)

| Tape at signal | n | exc% | med% | win% |
|---|---:|---:|---:|---:|
| weak | 2629 | +2.69 | +1.85 | 54.5 |
| mid | 2551 | +2.41 | −0.46 | 49.4 |
| strong | 2589 | +1.20 | −2.41 | 45.8 |

Monotonic in both, and the *sign of the median flips*. The mechanism is intuitive: when breadth is
low, a −50% stock is falling with everything else — it is beta, and it rebounds with the index.
When breadth is **high** and a stock is still down 50%, the market is telling you something
idiosyncratic is broken about that specific company, and it keeps underperforming — median −20%
over the following year.

**Robustness — this is not just 2020 and the GFC.** Dropping those years entirely:

| dd30 / 63d, weak tape | n | exc% | med% | win% |
|---|---:|---:|---:|---:|
| all years | 2629 | +2.69 | +1.85 | 54.5 |
| ex-2020 | 1932 | +2.56 | +2.30 | 55.8 |
| ex-2020, 2008, 2009 | 1469 | **+3.50** | **+2.74** | **57.4** |

The weak-tape cell survives removal of every crisis year and actually improves — positive median,
57% win rate. This is the one cell in the whole study that is not tail-carried.

⚠ Survivorship hits the weak-tape cell *hardest* (crisis-era crashes are exactly where the dead
names are missing), so +60% at dd50 is badly overstated. But the bias works *in favour* of the
strong-tape cell too, which means the **strong-tape result (median −20%) is if anything
understated** — and that negative is the most trustworthy number in this study.

---

## 5. Conclusions

1. **This does not contrast with Minervini — it complements it.** Minervini works in a strong
   tape; deep-crash buying works in a broken one, and actively harms you in the tape where
   Minervini is firing. They are the same trade fund pointed at opposite regimes, not two
   competing stock-selection philosophies.
2. **Do not buy deeply-crashed names while breadth is healthy.** Median −20% over 252d at dd50,
   39% win rate. This is the study's most robust and most immediately usable finding, and it is a
   *veto*, consistent with the existing "veto below 200sma" rule from the rotation study.
3. **The "strong stock" premise is not what generates returns** — depth of drawdown and market
   regime are. Filtering for prior strength adds ~1pp and is inside the noise.
4. **Waiting for confirmation does not help here.** Unlike the short side, stabilisation / EMA
   reclaim / RSI turn entries add tail, not reliability.
5. **Current tape: breadth 0.630 as of 2026-07-23** — mid tercile, not the weak-tape regime this
   needs. There is no reason to deploy this today.

### If it gets built anyway

The only defensible configuration from this study is: **dd ≥ 40-50%, entered only when universe
breadth is in its bottom tercile (< ~0.56), structured convexly (long-dated calls / LEAPs rather
than stock), sized as a tail bet.** That is a rare-trigger, regime-gated overlay — it fires in
clusters around market bottoms and sits idle for years — not a standing screen.

### Open work (not done)

- **Fix survivorship** with a delisting-inclusive source before trusting any absolute number.
  Polygon has one; the key here is free-tier rate-limited. This is the single highest-value fix.
- Separate **gap-down (news/earnings) crashes from grind-downs** — PEAD says the former should
  keep drifting down, and pooling them may be hiding two opposite populations.
- Test the **breadth gate as a live trigger** rather than an in-sample split (it is a
  contemporaneous observable, so this is doable honestly).
- Check whether the weak-tape cell is just **beta** — compare against a levered index position
  taken on the same dates, which may capture the same return with none of the single-name risk.
