# QQQ bull put spreads — own-IV-percentile gate test

*2026-09-08. `run_qqq_iv_gate_study.py`. Follow-up to the paid-to-wait study, where a "sell only when the name's 30-day IV is above its own 60th percentile" gate turned a losing single-name spread rule into +5.7% net. Question: does the same gate lift the QQQ bull put, the book's best-sampled positive row? Data: MySQL `options_cache` bid/ask 2018-01 → 2026-02, 412 Fridays, 20 DTE, 50% take / 2× stop, cost model on. QQQ IV = BS-inverted ~30-DTE ATM put mids (built from the cache, `qqq_iv30.parquet`), ranked against the trailing 252 sessions. Three delta pairs; VIX percentile shown as the comparison the regime gate implicitly uses.*

## Result: no. High own-IV is a mild veto on the index, not an edge.

Net ROC on max loss by QQQ's own IV percentile at entry:

| pair | all | IV pct < 30 | 30–60 | 60–80 | ≥ 80 |
|---|---|---|---|---|---|
| 0.25/0.15 | +2.5% (n 412) | +3.7% | **+6.2%** (t 2.5) | +1.9% | **−1.7%** |
| 0.35/0.25 | +3.0% | +1.5% | **+8.9%** (t 2.2) | +1.8% | +0.8% |
| 0.45/0.35 | +4.3% | +2.6% | **+12.8%** (t 2.3) | +5.5% | **−4.0%** |

The shape is the same across all three structures: the middle band pays, the top quintile loses, the bottom is modest. By VIX percentile the pattern is flatter and noisier, so the own-IV rank carries some information, but not the sign the single-name study found.

**Why the sign flips.** On a single stock a high own-IV percentile usually means an idiosyncratic premium (earnings, news) that decays; on the index it means the market is pricing a systematic move that then tends to happen. The ≥80 cohort is 2018 Q4, 2020 Q1, 2022 and early 2026: −13% to −31% in 2018 and 2022 on the 0.45/0.35 pair, +14% in 2020 (the V). It is a coin flip on a regime, not a premium harvest.

**Inside the current regime (Bullish_LowIV, 0.45/0.35):** IV pct < 30 +5.1% (n 127), 30–60 +4.9% (47), 60–80 **−5.3%** (21). Bullish_HighIV with IV 30–80 is the strongest cell in the table (+15 to +18%, n 16–23) and Bullish_HighIV with IV < 30 the worst (−23%, n 15), which is the "VIX is up but QQQ's own vol is not" configuration. Both cells are thin.

## Rule change

Keep the regime gate. Add one veto: **skip the QQQ bull put when QQQ's own 30-day IV percentile is ≥ 80, and in Bullish_LowIV skip at ≥ 60.** Do not add a "sell rich IV" entry gate on the index; the single-name finding does not transfer. Expected effect is small, a point or two of net ROC and fewer of the −13% to −31% years, which is what a veto should do. The 30–60 sweet spot is real in three structures but should not be over-read; t ≈ 2.3 on 83 trades is one strong year away from noise.

Live check needed before Friday: QQQ's current 30-day IV against the 2018–2026 distribution (median 20.2%). VIX at 15.7 suggests it sits low, which is the modest-positive band for the current regime.
