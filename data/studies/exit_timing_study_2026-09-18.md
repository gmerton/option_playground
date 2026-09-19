# Same-day exits vs holding: Tito's book, our universe, and Gabe's own trades (2026-09-18)

**Question.** Tito's hold times say he is in and out the same day on most trades. Our playbook says "no same-day
exits unless the stop is hit". Combine, or run a separate Tito playbook?

**Answer: don't run an intraday book. Take his loss-cutting, not his hold times.** Both tests point the same way.

---

## 0. What Tito's own numbers say (`Adhikary_PNL_by_duration.csv`, n=2,712)

Expectancy computed from his win rate and average win/loss:

| hold | trades | win% | expectancy | share of total profit |
|---|---|---|---|---|
| 0–10 min | 920 (34%) | 44.7% | **−$26** | −2% |
| 10–30 min | 467 | 51.2% | +$232 | 8% |
| 30–60 min | 239 | 56.1% | +$549 | 10% |
| 1–2 h | 184 | 57.6% | +$611 | 9% |
| 2–4 h | 146 | 58.9% | +$606 | 7% |
| **4+ h** | 756 (28%) | 67.5% | **+$1,146** | **68%** |

His sub-10-minute third loses money **by design** — that is the stop. His 4+ hour trades earn 5× per trade and
two-thirds of the profit. The frequency of same-day exits is a by-product of cutting fast, not the edge.
⚠ Duration is endogenous in this table (winners last because they win), so it cannot be read as "hold longer".

## 1. What a same-day exit costs on our universe (`run_exit_timing_study.py`)

Precision-shaped breakouts, 2019-10 → 2026-09. Entry at the **next open** (the intraday-entry proxy, since our
own process enters at the close and cannot exit the same day). Same stop for every policy — the breakout day's
low — so R is comparable across rows. 5 bps per side.

| policy | n | mean R | median R | win% | t (by date) |
|---|---|---|---|---|---|
| exit same-day close | 1,962 | **−0.13** | −0.05 | 47% | −0.3 |
| sell into strength (+1 ADR touch, else close) | 1,962 | **−0.12** | −0.04 | 47% | 0.1 |
| hold 2 sessions | 1,962 | −0.09 | −0.09 | 46% | 0.1 |
| hold 3 | 1,962 | −0.04 | −0.06 | 48% | 0.9 |
| hold 5 | 1,962 | −0.04 | −0.04 | 49% | 0.3 |
| **20-EMA close trail** | 1,962 | **+0.89** | −1.08 | 31% | 2.9 |
| **our book** (enter at the breakout close, same trail) | 1,962 | **+0.79** | −1.08 | 31% | **4.3** |

All breakouts (n=7,954) say the same thing more weakly: same-day −0.03R, trail +0.13R, our book +0.20R (t 3.8).

**The shape is Tito's barbell, in our data.** The scalp wins more often — it beat the trail on **62%** of the same
trades — but the trail's median is −1.08R and its mean is +0.89R: a minority of trades carries everything, and
they need 10 sessions (median trail hold) to happen. **Exiting the same day is how you delete the tail that pays
for the stops.** Even the optimistic "sell into strength" version (assumes a +1 ADR touch fills) doesn't rescue it.

By year, the trail is positive in 5 of 8 years and carries 2024–25 (+1.48 / +3.60 R); the scalp is between −0.30
and +0.11 every year — small and mostly negative, never a business.

## 2. Are Gabe's same-day round trips bad *per se*, or bad because unplanned? (`run_roundtrip_split_study.py`)

340 closed stock cycles, 2026-08-13 → 2026-09-17 (the sessions with alert logs), flat-to-flat from
`journal_trades`, entries matched to the alert engine the same way the journal grades them.

| | cycles | total | mean | win% |
|---|---|---|---|---|
| **same day** | 278 | **−$8,291** | −$30 | 19% |
| held overnight | 62 | +$2,764 | +$45 | 40% |

Split by whether an alert actually fired the entry:

| | cycles | total | mean | win% |
|---|---|---|---|---|
| same day, **alert-triggered** | 60 | −$2,377 | **−$40** | 18% |
| same day, no alert | 218 | −$5,914 | −$27 | 20% |
| overnight, alert-triggered | 3 | +$226 | +$75 | 67% |
| overnight, no alert | 59 | +$2,538 | +$43 | 39% |

**Planning the trade does not rescue the same-day exit.** Alert-triggered same-day round trips are, if anything,
slightly *worse* than unplanned ones (−$40 vs −$27), and grade-B entries closed the same day still average −$30.
The 19% win rate on same-day cycles is the tell: these are trades cut before they can work.

Holding period of the same 340 cycles:

| held | cycles | total | mean | win% |
|---|---|---|---|---|
| same day | 278 | −$8,291 | −$30 | 19% |
| 1 day | 25 | −$825 | −$33 | 32% |
| 2–3 days | 11 | +$789 | +$72 | 36% |
| 4–7 days | 19 | −$165 | −$9 | 32% |
| **8+ days** | 7 | **+$2,964** | **+$423** | 100% |

⚠ Same endogeneity caveat as Tito's table, and the long buckets are tiny (7 cycles). This is not "hold everything
8 days". It is evidence that the *left* side of the table — the 278 same-day cycles — is where the money leaks.

## Verdict

1. **No separate intraday playbook.** We can't even backtest one honestly: the 1-minute cache is ~1 month of 2026
   against 8 years of daily bars. And in both datasets the same-day exit is the negative bucket.
2. **One selection engine, one management book, two exit regimes — declared at entry, not after the move:**
   - **grind** → stop at the entry-day low on the close, then the 20-EMA close trail (mean +0.79R in our data)
   - **spike** → sell into strength / GTC +200–300% (today's MSTR roll)
   The rule that matters is not "when do I exit" but "which regime did I declare before the trade moved".
3. **What to take from Tito:** the fast cut. His sub-10-minute bucket is a stop, and our own stop study already
   says the same thing (stop = entry-day low, on the close). His intraday P&L is an execution skill on an
   11-trade-a-day book, in one regime, with no losers' log we can audit.
4. **What our data says to stop doing:** treating a swing entry as a scalp when it moves. That is what the 278
   same-day cycles are, and they cost $8.3k in five weeks.

Scripts: `run_exit_timing_study.py` (log + `data/cache/exit_timing_trades.parquet`),
`run_roundtrip_split_study.py` (log + `roundtrip_split_2026-09-18.csv`).
