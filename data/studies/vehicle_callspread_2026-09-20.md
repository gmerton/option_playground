# Debit call spread as a vehicle (2026-09-20)

**Queued from** the Ravish "super bull call spread" review. The August 2026 vehicle study compared
long stock, ATM call, short 30Δ put and a 30/15Δ put credit spread on identical entries and never
tested a **debit call spread**. This adds that arm: **long 30Δ call / short 15Δ call**, same expiry,
mirroring the put spread's geometry (and close to Ravish's ~30Δ + short leg further OTM).

**Verdict: it does not change the ranking.** Risk-equalized it is the **worst** option vehicle in
the set, and it carries the lowest win rate of all five. The original conclusion — vehicle follows
entry quality — survives the new arm.

**Method.** `run_vehicle_study.py --lens-csv ... --pull`. 166 closed bullish stock trades
(2026-08-03 → 2026-09-02, 86 names), repriced Black-Scholes off ATM IV backed out of
`options_daily_v3` prints. 158 repriced; the call spread is constructible on **93** of those, so
every cross-vehicle number below is on the **matched 93 where all five vehicles exist**. Comparing
the call spread's 93 rows against the other arms' 158 would be composition, not vehicle.

Regression check: the pre-existing arms reproduce the 2026-09-06 study (extended entries — stock
−12,725 / call −17,197 / short put −2,663 / put spread −2,390 here, against −13,026 / −17,422 /
−2,743 / −2,466 there).

## Matched sample, 93 trades

Per contract vs 100 shares:

| vehicle | total | win | mean | worst | best |
|---|---|---|---|---|---|
| stock | **+7,897** | 33% | +85 | −4,432 | +9,992 |
| ATM call | −3,601 | 19% | −39 | −3,269 | +5,590 |
| short 30Δ put | +917 | 30% | +10 | −864 | +2,486 |
| put spread 30/15 | −177 | 28% | −2 | −617 | +1,251 |
| **CALL spread 30/15** | **+37** | **17%** | **+0** | −212 | +1,144 |

Risk-equalized to the stock's 2% stop risk:

| vehicle | total | mean |
|---|---|---|
| stock | +7,897 | +85 |
| short put stopped 2x | −57 | −1 |
| put spread | −199 | −2 |
| ATM call | −1,779 | −19 |
| **CALL spread (debit)** | **−2,605** | **−28** |

By bucket (matched):

| bucket | n | stock | call | short put | put spr | CALL spr |
|---|---|---|---|---|---|---|
| same-day | 45 | −7,107 | −6,090 | −4,444 | −1,993 | −1,309 |
| 1–3 days | 18 | +9,387 | +4,510 | +1,858 | +846 | +846 |
| 4+ days | 30 | +5,617 | −2,021 | +3,503 | +970 | +501 |
| extended | 29 | +9,007 | +1,479 | +3,014 | +1,348 | +1,072 |
| not extended | 64 | −1,111 | −5,080 | −2,097 | −1,525 | −1,035 |

## Reading

- **Worst option vehicle once risk is equalized.** Its max loss is the debit (median $1.79 on a
  $2.20 width), so equalizing to the stock's 2% risk means holding many spreads — which multiplies
  an 83% loss rate. Per contract it looks harmless (+37); that is position size, not quality.
- **Lowest win rate of the five (17%).** It is a *directional* vehicle like the long call, not a
  defensive one like the short put or put credit spread. On a book of flat-to-slightly-down entries
  it loses the way the call loses, and then caps the rare winner that would have paid for it.
- **It forfeits the upside where the upside existed.** On the extended bucket stock made +9,007 and
  the call spread +1,072.
- **Every vehicle keeps the same sign in every bucket** — negative same-day and not-extended,
  positive 1–3 days and extended. That is the original finding intact: the vehicle follows the entry.

## ⚠ Limits, and they all point the same way

- **Friction is invisible here.** `options_daily_v3` after mid-July 2026 carries prints only — no
  bid/ask — so costs are a flat % of premium (5% for spreads), not a bid/ask crossing. The
  2026-09-20 event-spread study found friction, not capping, is what destroys a debit spread
  (−27.1pp, t −5.51). **That effect cannot appear in this test**, so the real result is worse.
- **Skew is ignored.** A 30/15Δ call spread priced off one ATM IV overprices the short 15Δ call,
  inflating the credit and shrinking the debit. That flatters this arm.
- **The matched 93 is not representative**: stock is +7,897 on it against −15,568 across all 158.
  Constructibility needs dense strikes above spot, which selects the larger, more liquid names.
- One month, 93 trades, median hold 0 days, one trader's entries. Per the house rule, this book is
  evidence about execution and vehicles, never about setup selection.

**Both data limitations bias in the call spread's favour and it still finishes last.** That is the
strongest form the conclusion can take on this data.
