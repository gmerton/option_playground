# tastylive / Market Measures: "Why Volatility Gets 42% Worse the Longer You Hold Your Strangle" (2026-03-10, 9:29)

_Reviewed 2026-09-24. A live-show segment: two hosts read research slides between market chatter (a "240 point handle
move" the day before). Transcript (`en-orig` auto) is in this folder. Slides aren't in the transcript; every number
below was spoken, and several were garbled in the speaking._

## Verdict: 2 / 5

The core claim is **P&L volatility grows the longer you hold a short strangle or straddle, and it grows faster the
closer the strikes are to ATM.** It is correct and mechanical: gamma rises into expiry, and a longer window adds more
variance. Our own 21-DTE data confirms the direction and gives a size (exploratory check below): closing at 21 DTE cuts
the per-share P&L sd by **45%**, which is *more* than holding for half as long would cut it on its own.

Four problems cap it:

- **Variance isn't the objective.** At 07:25 the hosts say managing early "can further improve the balance between
  profitability and volatility". No profitability number is shown. On our data the 21-DTE close **earns less than
  holding** (−$0.52/share, t −2.42), and it is worse **per unit of risk** too (mean/sd +0.014 held vs −0.032 managed).
  Lower variance bought with a lower mean isn't a better trade. It's a smaller one.
- **The metric is weekly P&L change as a % of the underlying.** That's a mark-to-market measure: no fills, no costs, no
  exit spread. The second round trip is exactly what makes our managed arm lose.
- **No n, no period, SPY only.** The title's "42%" is spoken as "the 42% reduction is if you manage those trades at 21
  days or at 28 days versus the 21 days at 33%" (07:32). We can't tell which structure or exit the 42% belongs to. The
  title turns a *reduction from managing* into "gets 42% **worse** the longer you hold". That's the same number read
  backwards.
- **Straddle vs strangle is framed as a risk preference, not an edge.** That framing is fine. But "straddles yield higher
  P&L per contract" (01:36) is stated without costs, and the ATM short straddle is NULL on our single-name panel.

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY only |
| period | **not stated** |
| n | **not stated** |
| structure | 45-DTE short strangles at **16Δ, 30Δ** and the **50Δ straddle** |
| metric | **weekly P&L change as a % of the underlying price** (02:50): a path-volatility measure, not terminal P&L |
| management | hold vs exit at **21 DTE** (and **28 DTE** for the straddle, 07:23) |
| fills | none; mark-to-market. Channel disclaimer: "not presented net of all commissions" |
| control | the same structure held longer. That's the right control **for a variance claim**, and it says nothing about return |
| win rate / avg / tail | one slide (01:51) compares median P&L and win rate for 16Δ vs 50Δ. **No numbers spoken** |
| significance | none |
| selection | none visible. With no period stated, the regime mix can't be checked |

## Numbers as spoken

| @ | number |
|---|---|
| 00:48–00:54 | "Rolling at 21 days … takes a big part of it [P&L volatility] out of the equation" |
| 01:51–02:13 | SPY 16Δ strangle vs 50Δ straddle: strangle median P&L lower, win rate higher, "about **25% swings** in either direction" vs wider for the straddle |
| 02:41–02:53 | study: SPY, 45-day, deltas **16 / 30 / 50**, weekly P&L change as % of underlying |
| 03:37–03:44 | P&L vol "gradually rises as we approach expiration, but this increase **slows down** closer to" expiry (16Δ: the legs go to ~0Δ if OTM) |
| 04:57–05:02 | "by expiration, the volatility of a **30Δ** strangle is **double** that of a 16Δ strangle" |
| 05:40–05:45 | "after the first two or three weeks, your P&L volatility is going to be **40 or 50% higher** than what you started with" |
| 06:33–06:46 | straddle weekly swings: "**$50** … **$75** … **$150** … **$200** … and then **300**" (illustrative, units unstated) |
| 07:17–07:27 | exiting at 21 DTE "can significantly reduce the volatility"; for straddles, managing "even earlier can further improve the balance between profitability and volatility" |
| 07:32–07:43 | "the **42%** reduction is if you manage those trades at 21 days or at 28 days versus the 21 days at **33%**" (garbled; best reading: straddle −42% at 28 DTE, −33% at 21 DTE) |
| 09:18–09:22 | "We're not really holding any trades to expiration … rarely, if ever" |

## Claim by claim, against our ledger

| @ | claim | our evidence |
|---|---|---|
| 03:37 / 05:40 | P&L volatility grows with holding time | ✅ **Agrees, and checked on our own data** (exploratory, below). The 21-DTE close vs hold on 14,367 paired 45-DTE 20Δ strangles: sd **$9.33 vs $17.09/share (ratio 0.55)**, IQR $1.55 vs $2.75 (0.56), worst −$291 vs −$617. Holding for half as long would give ~0.71 if variance accrued evenly. **0.55 means the back 21 days carry more variance than the front 21**, which is their gamma-into-expiry mechanism. |
| 07:17 | Managing at 21 DTE reduces P&L volatility | ✅ **True, measured by us** (TEST_INDEX §1, "21-DTE management on a 45 DTE / 20Δ short strangle", FIX-1 re-run 2026-09-24): **RISK-REDUCER only**. |
| 07:25 | Managing earlier improves "the balance between profitability and volatility" | ❌ **Contradicted on our data.** Same row: **B − A = −$0.52/share, month-clustered t −2.42**, halves −0.63 / −0.40. Hold **+$0.23/share, 74% win**; 21-DTE close **−$0.29, 64% win**. Per-trade mean/sd: **+0.014 held vs −0.032 managed**, so the risk-adjusted balance is worse as well. The mechanism is the second round trip at real fills. It's the same as the 9/24 ETF put exit test. **Lower variance is not higher expectancy.** |
| 01:36 / 07:04 | Straddles carry more P&L per contract and more P&L volatility than OTM strangles | Variance half: mechanical, and not disputed. "More P&L" half: **not supported**. Our short 7-DTE ATM straddle is **NULL as a strategy**: −1.83% ungated, **at mid, before costs**, and every positive cell's 95% CI includes zero (TEST_INDEX, "Short 7-DTE ATM straddle, pre-registered H1/H2/H3"). The index exception is the SPY 1-day short straddle (t 5.6, TEST_INDEX "Ledger-wide multiple-testing correction" row), a different tenor and a dealer-gamma cell. |
| 02:05 | The strangle has the higher win rate | True, and not evidence. Win rate isn't edge: on our bull-put panel **win rate falls 79.6→75.7% as net ROC rises −2.96→+4.07%, t 3.74** (More Tom row). |
| 04:57 | A 30Δ strangle ends with double the P&L volatility of a 16Δ | Plausible (closer to ATM = more terminal gamma). Untested by delta here; our 21-DTE panel is 20Δ only. |

### Exploratory check (not a ledger row)

Computed locally from `data/studies/exit_21dte_2026-09-23_fixed.csv` (the FIX-1 output of `run_21dte_exit_test.py`): all
14,367 rows resolve in both arms, median hold **42 days (A) vs 21 days (B)**. Nothing is pre-registered. It's a
descriptive dispersion comparison on an existing file, and it runs in seconds.

| measure | A: hold to expiry | B: close at 21 DTE | B/A |
|---|---|---|---|
| mean $/share | +0.231 | −0.294 | — |
| sd $/share | 17.09 | 9.33 | **0.55** |
| IQR $/share | 2.75 | 1.55 | 0.56 |
| MAD $/share | 1.43 | 0.78 | 0.55 |
| p1 / worst $/share | −45.8 / −617 | −22.7 / −291 | 0.50 / 0.47 |
| sd per credit, credit ≥ $0.25 (n 13,990) | 2.78× | 2.04× | 0.73 |
| sd per credit, credit ≥ $0.50 (n 12,779) | 2.68× | 1.59× | 0.59 |
| per-name sd ratio (44 names, roc) | — | — | median 0.74; <1 in 68% of names |
| halves (split 2022-07), $ sd | H1 21.8 / H2 9.4 | H1 12.0 / H2 4.9 | 0.55 / 0.52 |

Reading: the variance cut is robust. It shows up in sd, IQR and MAD alike, and in both halves. By year it is **not
uniform**: the ratio is 0.53–0.92 in 2018–2023 and 2025, and **above 1 in 2024 (1.36)** and the 78-trade 2026 stub,
measured per credit. So "managing always cuts variance" is a tendency, not a law. **Caveat on per-credit figures:** the
raw per-credit sd ratio is 1.03 because a few rows carry implausible credits. XLP 2026-01-02, XLU 2025-09-19 and XOP
2025-12-26 book a **$0.007** credit on a 20Δ strangle, giving ROC of −800 to −2,200× credit. That's why the table uses a
credit floor. Those rows barely move the $ headline (ex-credit<$0.10 the paired diff is −$0.524, vs −$0.52 in full).

## What I would take

1. **Short gamma's variance clusters in the last three weeks.** It's worth knowing for sizing a held strangle. But
   the answer to it is **size**, not the 21-DTE exit: the exit gives up expectancy to buy the variance back.
2. **Their implied trade-off, stated honestly:** managing at 21 DTE turns a small positive-mean, fat-tailed trade into a
   small negative-mean, thinner-tailed one (on our 44-name panel at real fills). If the book needs the thinner tail, the
   cost is about $0.52/share per strangle.

## Not tested, could be

- **Weekly P&L-vol curve by delta (16/30/50) and week-to-expiry, at marks, on SPY.** It would replicate their slide
  directly. It needs a daily mark path per contract (the SPY put cache `data/cache/SPY_puts_v3_2018_2026.parquet` covers
  puts only; calls need a v3 pull with `cp='C'`). Recover spot from the chain, since v3 strikes are RAW. ~2–3 hours.
  **Low value:** it's descriptive, and the decision it feeds (manage or hold) is already answered on P&L by the 21-DTE row.
- **Is the per-year variance cut predictable?** 2024's ratio > 1 suggests managed exits can *add* variance in some regimes
  (e.g. closing into a spike instead of letting it decay). A test would regress the per-month B/A dispersion ratio on
  entry VIX level / term structure. That's a risk-management question, not an edge one. Specced only.
