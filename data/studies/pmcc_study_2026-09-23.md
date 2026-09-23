# Poor man's covered call vs just holding the long call — **a regime hedge, not a grinder** (2026-09-23)

**Verdict: FAILS as specified (−20.55pp, t −4.93). ⭐ But the sign tracks the tape — it wins in down
years and loses in up years, which makes it a conditional hedge sold as an account-growth strategy.**
Pre-registered in `run_pmcc_study.py`. Trades: `pmcc_study_2026-09-23.csv`.
Claim source: [Galarnyk review](../nick_galarnyk/2026-06-16_small_account_strategies_review.md) (3/5).

## The claim

A $10K account cannot buy 100 shares of a mega-cap, so buy a long-dated ITM call and sell shorter-dated
calls against it, grinding the cost basis down each cycle. His worked example: NVDA ~210, buy the Sep 180
call (94 DTE) for $36 → breakeven 216; sell the Jul 220 for $4.50 → "12.5% on risk", ~31% in 31 days if
it pushes through. **One favourable NVDA path, no backtest.**

## Method

18 mega-caps, monthly entries, 2019 → 2026, **936 cycle-sets**. Long = DTE nearest 90 (median 79), delta
nearest 0.80 (median 0.80), median cost **$3,523**, bought at the **ask**. Short = the lowest strike
strictly above the long's breakeven (his rule), DTE nearest 30, sold at the **bid**, settled at its own
expiry at intrinsic, then rolled — 3 cycles. Commissions $0.65/contract/leg/side.

⚠ Settlement spot recovered from the **chain** (`lib.studies.chain_spot`), never a price panel: v3 strikes
are RAW, every panel we keep is split-adjusted, and that mismatch has already produced two wrong results.

## Primary — FAILS

**ARM B (PMCC) minus ARM A (hold the long): −20.55pp, month-clustered t −4.93, halves −16.56 / −20.46.**

The mechanism is right there in the cash flows: **credits collected $4,572, paid back $5,634 → net
−$1,062 per cycle-set** on a $3,523 long. The rolled shorts do not grind the basis down; they get run over.

## The tail — read before the mean (pre-registered)

| | A: hold the long | B: PMCC |
|---|---:|---:|
| mean | **31.3%** | 10.7% |
| median | 20.2% | 16.6% |
| win% | 60.4 | **62.6** |
| sd | 93.6 | **54.0** |
| **p10** | −100.0 | **−68.8** |
| **p90** | **148.0** | 70.7 |
| **p99** | **298.0** | 135.4 |

A **risk** result, not a return result — the third today, after the 21-DTE strangle exit and Tito's spike
branch. It cuts variance 42%, lifts the win rate slightly, and meaningfully limits total losses
(p10 −68.8 vs −100). It pays by surrendering **more than half the right tail**.

## ⭐ The regime slice — this is the real finding

| year | A (hold long) | B (PMCC) | edge | t |
|---|---:|---:|---:|---:|
| 2019 | +64.5% | +31.8% | −32.7pp | −6.0 |
| 2020 | +42.3% | +10.8% | −31.5pp | −4.5 |
| 2021 | +24.2% | +7.0% | −17.2pp | −3.1 |
| **2022** | **−30.5%** | **−20.0%** | **+10.4pp** | **+3.4** |
| 2023 | +53.7% | +17.4% | −36.3pp | −5.3 |
| 2024 | +41.5% | +18.0% | −23.5pp | −4.4 |
| 2025 | +25.2% | +10.5% | −14.7pp | −2.7 |
| 2026 ⚠ n=6 | −96.1% | −73.7% | +22.4pp | +3.9 |

**Six of eight years negative — every one an up year. Both positive years are down years.**
2022 alone: win rate 33% → 39%, p10 −100 → −84, edge **+10.4pp at t +3.45**.

⚠ **Conditional on the long losing money** (n=371, any year): A −56.6% → B −36.3%, **+20.2pp at t +20.13.**
That number describes the mechanism; it is **not a tradeable rule**, because you cannot know in advance
which cycles will lose. Quoting it as an edge would be the arm-C error from `reclaim_vs_pullback`.

## What this establishes

* **Settled: it is not a small-account grinder.** As specified, it costs 20.55pp per cycle-set against
  simply holding the long call, with t −4.93 and both halves negative. His claim is refuted.
* ⭐ **It is a real hedge.** The edge sign tracks the underlying's direction with a clean mechanism — the
  short calls pay when the name does not run. It converts a high-variance bullish position into a
  lower-variance one, and in 2022 that was worth +10.4pp.
* ⚠ **Which makes it unactionable for us anyway.** Its payoff requires knowing you are entering a down
  quarter — and if you knew that, you would not be buying the call. This is the standing finding restated:
  *the paying months cannot be forecast* (`breakout_regime_feedback`, where our own results, stop-out
  share, activity and SPY state forecast next-month performance at ≈ nothing).
* ⚠ **Sample is a historic mega-cap bull run** — arm A averaged **+31.3% per ~90-day cycle**. A flatter
  decade would narrow the gap. The 2022 and 2026 rows are the only bear evidence, and 2026 is n=6.
* ⚠ Untested: other short-strike rules (his "above breakeven" is aggressive), other deltas for the long,
  and rolling down after a drawdown.

## Process notes

**A schema-aware guard earned its place.** The first pull omitted `bid_iv`/`ask_iv`; when the query was
fixed, a plain `exists()` check silently kept the 2019 and 2020 files, which would have handed
`spot_from_chain` NaN IV and settled two years of trades on garbage. The puller now compares columns, not
just presence, and re-pulled exactly those two years.
