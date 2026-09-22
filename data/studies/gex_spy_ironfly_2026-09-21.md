# SPY 1-day iron butterfly on positive-gamma days: does the short survive with defined risk? (2026-09-21)

## Pre-registration (written BEFORE any code ran; do not edit this section after the results)

**Why.** The naked 1-day SPY short straddle on positive-GEX days passed (+13.7% of credit, t 5.6;
gex_spy_straddle_2026-09-21.md) but its worst day was −6× the credit. Before any live use it has to work as a
defined-risk structure.

**Trade.** Same days, entry, expiry, GEX sign and ATM strike K as the straddle test (day t−1 close → expiry on day t;
call delta nearest 0.50). Sell the K call and K put; buy a call at K + W and a put at K − W, where W = w × the ATM
straddle mid, rounded to the NEAREST LISTED strike on each side (w fixed at **1.0** and **2.0**, the only two arms).
Payoff at expiry = min(|S_t − K|, W_c or W_p on that side). Max loss = wing distance − credit.

**Fills.** House model: short legs at mid − 25% of their bid-ask, long wings at mid + 25%, $0.0065/share/leg, four
legs; no exit cost at expiry. Skip a day if a wing strike has no two-sided quote or the net credit ≤ 0.

**Measures.** Return on MAX RISK (the capital a broker holds) and on credit; win rate; worst day; mean $ per fly;
the share of positive months and the longest losing streak (days) for lived-experience context.

**Pass bar (per wing width, positive-gamma days, return on max risk at the real fill).** Mean > 0, |t| ≥ 3 (days),
positive in both halves (2010–2017 / 2018–2026-02), AND positive-gamma days beat negative-gamma days with the same
structure. Negative-gamma days and all days reported alongside.

**Not tested:** other wing widths, broken-wing or skewed flies, stops/early exits, other tickers, sizing rules.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_gex_spy_ironfly.py`, log `.log`, table `.csv`)

**Verdicts: wings at 2× the implied move PASS · wings at 1× FAIL (t 2.0). The gamma filter is the whole edge: the
same fly on every day earns 0.0%.** 1,942 days (928 positive-gamma), real fills on all four legs.

| wings | gamma | days | median credit / width | return on max risk | t | 2010–17 | 2018–26 | win | $ per fly (mean / worst) | positive months | longest losing run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **2×** | **positive** | 928 | $2.10 / $5 | **+5.8%** | **3.4** | +7.7% (t 2.0) | +5.4% (t 2.8) | 61% | +$19.8 / −$709 | 67% | 6 days |
| 2× | negative | 1,014 | $2.97 / $6.6 | −5.4% | −3.1 | −1.6% | −6.5% | 50% | −$18.6 / −$2,048 | 43% | 12 days |
| 2× | all | 1,942 | $2.37 / $5 | 0.0% | 0.0 | | | 56% | −$0.3 / −$2,048 | 52% | 9 days |
| 1× | positive | 928 | $1.40 / $2 | +6.8% | 2.0 | +13.1% (t 1.9) | +5.3% (t 1.4) | 49% | +$6.5 / −$274 | 55% | 8 days |
| 1× | negative | 1,013 | | −12.0% | −3.7 | | | 40% | −$12.1 / −$586 | 39% | 13 days |

2× wings by year on positive-gamma days: up in 14 of 17 years (down 2011 −1.3%, 2018 −7.9%, 2022 −1.2%).

- **Defined risk works at 2×:** max loss per fly ≈ $290 (vs −$1,060 on the naked straddle's worst day), 61% winners,
  two-thirds of months positive, no losing run longer than 6 trading days.
- **1× wings are too tight:** the wings eat most of the credit, and at t 2.0 it doesn't clear the bar.
- **Negative-gamma days are significantly negative** for the short fly (t −3.1 / −3.7). That's an observation, not a
  tested long strategy: the long straddle on those days already failed (fairly priced).
- **Economics:** ~+$20 per 1-lot fly on ~$290 of risk; ~100 positive-gamma expiry days a year in the daily-expiry era
  → roughly +$2,000 a year per fly held each qualifying day, before taxes.

## Status

**PASS at the pre-registered bar → candidate, not yet live.** Remaining before sizing: (1) live GEX from Tradier chains
at ~15:50 ET (v3 lost OI/gamma in 2026); (2) paper trade forward from 2026-09-22 (lockbox); (3) the first half is only
t 2.0, so the forward sample matters.

## Diagnostic: overnight vs trading hours (2026-09-21, descriptive, log `gex_overnight_split_2026-09-21.log`)

Realised variance per unit of implied, split into the overnight gap and the session: positive-gamma days 0.50 + 0.62
(cross −0.08); negative-gamma days 0.68 + 0.81 (cross +0.01). The overnight gap is ~half the day's variance in both
regimes, the positive-gamma shortfall is split evenly (−0.19 overnight, −0.19 session), and on positive-gamma days the
session tends to REVERSE the gap (negative cross term), which helps a fly centred on the prior close. So a 0DTE fly
entered at the open sheds noise but also ~half the edge and the reversal benefit → kept as a secondary, logged-only
variant; the close-entry 1-day fly stays primary.

## Forward paper trade (built 2026-09-21, starts 2026-09-22)

`run_gex_fly_paper.py`: `--close` (≥ 15:30 ET, run by `daily_desk.sh` step 0) computes live SPY GEX from the Tradier
chain (32 expiries, ~30 s), logs the signal to `data/paper/gex_fly_signals.csv` and, if positive, a paper `close_1d`
fly to `data/paper/gex_fly_trades.csv`; `--open` (09:40–10:30 ET, launched in the background by `start_alerts.sh` at
09:45) logs the `open_0dte` variant after a positive close; every run settles due trades at SPY's close and prints the
running tally. Idempotent (one signal / one 0DTE per day). Dry run 2026-09-21 18:50 ET: GEX +$10.7bn per 1% move
(POSITIVE; the 2025–26 v3 history ran median −1.2, 10th pct −15.0, 90th pct +9.3, 45% positive → same scale), fly
774 straddle for 9/22 with 767/781 wings, credit $2.90, max risk $4.10. ⚠ Live gamma is Tradier/ORATS, the backtest's
was the v3 vendor's; there are no overlapping dates, so watch that ~40–50% of days read positive. ⚠ A desk run after
16:15 prices at closing quotes (like the backtest) but couldn't actually be filled; the log records the time.
