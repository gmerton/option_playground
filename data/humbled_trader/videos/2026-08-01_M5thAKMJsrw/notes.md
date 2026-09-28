# Mari's Full Story: from beginner to $1.6M day trading (Humbled Trader interview)

**Video:** `M5thAKMJsrw` · 61 min · published 2026-08-01 · reviewed 2026-09-28 · guest KB: [data/mari_trades/](../../../mari_trades/README.md)

> **2/5 · no new test.** This is a career biography, not a setup video. Its value is that she's candid: she names
> the losses in dollars (−$20k first red month, −$100k Tesla options in one day, −$50k HOOD, −$50k MRNA panic-dip),
> she walks away from a strategy when it stops working, and she admits her best year came from "a really good time"
> [08:24]. The "$1.6M verified" figure is cumulative dollars, mostly from the 2021 OTC run ("700,000 ... in one month"
> [19:50]). It isn't a return, has no denominator and wasn't shown on screen. Her current book is "$30 or $50,000"
> accounts [24:01] targeting "$10,000 a month" [46:56], and none of that is verified. Her one mechanical market claim
> (size up when recent runners follow through) is the breakout-activity gate, which was RETRACTED out of sample.
> Process 2.5/5, claims 1/5.

## What's NEW relative to the existing Mari KB (1 recap video, DFNS first-green-day, 2/5)

- **Strategy history (a sequence of regimes):** 2019 OTC panic-dip buys + OTC breakouts → end-2021 small caps (big
  losses adapting) → 2022 TSLA pre-split + options (−$100k) → 2023–24 **small-cap gapper shorts** → late 2025
  "gappers just weren't fading ... squeezers" [25:03] → back to **small-cap longs, day trades only** [41:43].
- **Selection:** a separate watchlist of names that "have been running in the past like 15 days", scanned each
  morning for "which one is building on the daily" [27:09]. Timeframes: 6-month daily, 15-min for levels, 1-min to
  execute [36:36].
- **Anticipate/confirm sizing:** a starter "before anybody else is in" and an add on the confirmation, because "if you
  buy the breakout, guess who else is buying the breakout? Everybody" [34:25]. The adds come once "the dips hold and
  then dips hold again" [35:30].
- **Risk rule:** after the Tesla loss she caps the day at **2% of the account** and risks about **1% per trade** [30:16].
- **Regime-sized aggression:** she stays at constant size and only sizes up "when the market starts to show a little
  bit more follow through" among the runners [38:37, 40:42].
- **Stats tracking:** printed-screenshot binders. Two months of journaling narrowed 8 strategies to 2 [14:40].
- **Verification:** the host says "verified track record" [02:05] and Mari says "I have everything verified" [50:05].
  The platform is never named (the KINFO mention [49:01] is the *host's* own account).

## Claims vs the ledger

| # | @ | claim (verbatim where short) | ledger verdict |
|---|---|---|---|
| 1 | 38:37 | Size up only when runners show follow-through; "rising tide" | **CONTRADICTED** (liquid): the breakout-activity gate was RETRACTED because it reverses on the 2010-19 holdout, −0.69R, t −2.59 (TEST_INDEX §2, rows "Breakout activity as a live regime gate" / "…2010-19 HOLDOUT"). WL-2b localisation also came back NULL ×3 (persistence ρ −0.01) |
| 2 | 34:25 | Anticipation starter, then add on confirmation | **CONTRADICTED / NULL**: O'Neil pyramid NULL (no add condition beats the unconditional add, +0.15R t 1.25). The confirmation ladder buys safety (13→59% of lows hold) but pays for it 1-for-1 in price. Reclaim-vs-pullback also NULL |
| 3 | 34:25 | "Everybody's buying the breakout" → enter early | **AGREES in shape**: the house breakout overpays by 2.6 ADR ([[project_entry_extension_finding]]). But "earlier" intraday triggers are no better than a random minute (Stage A, 11,227 alerts) |
| 4 | 28:11 | Recent-runner watchlist as the universe | **UNTESTED**: row "Catalyst as a SELECTION filter" is queued, not run. Buying the event itself fails (DR-EP arm A −0.173R, t −4.70) |
| 5 | 28:11, 41:43 | Take the day's 15–30% and leave; day trades only | **CONTRADICTED** (liquid): same-day exits are the negative bucket in both books (exit-timing row, scalp −0.13R vs trail +0.89R) ⚠ timeframe caveat |
| 6 | 30:16 | 2% daily max loss, ~1%/trade | **UNTESTED**: Cameron max-loss row, arm 0 queued. Under i.i.d. outcomes a daily limit carries no information. It's sound hygiene, not an edge |
| 7 | 30:16 | "The losses never come from a strategy. They always come when you get emotional" | **CONTRADICTED**: the 9/25 audit certifies one strategy out of the whole ledger. Most losses here *are* the strategy |
| 8 | 25:03 | Small-cap gap shorts stopped working late 2025 (squeezes, expensive locates) | **UNTESTED there**: the liquid analogue, a gap-up fade in the stock's own downtrend, is a PRIMARY PASS but cost-fragile and PARKED (t 3.87, dies at +20 bp). The short-selectable universe came back NULL 0/10. Small caps are blocked |
| 9 | 43:49 | MRNA "panic dip buy long that literally never bounced" | **AGREES**: crash-leader veto. Breitstein capitulation FAIL both sides |
| 10 | 45:54 | Don't force breakthrough years; good years can't be forced | **AGREES**: breakout paying months are unforecastable. The month-weighted book is ~0 (pyramid row METHOD note) |
| 11 | 02:05 | $1.6M verified | **Verified ≠ edge** (USIC and KINFO rows: survivorship, cumulative dollars not return, no denominator). Profits came in one regime (2021 OTC) that "the SEC just literally caught up to" [17:47] |

## Evidence quality

The dollars are concentrated in a dead market (OTC 2021), and five forced strategy changes followed. The loss figures
don't agree with each other: "first $50,000 loss" [19:50] vs "red 20,000" in the same August [20:52]. Her current
"consistency" claim [40:42] comes with no stats. The candour about losses and burnout is real and rare. It's why she
scores 2 rather than 1.

## New test?

**No.** Every mechanical claim maps to an existing row: claim 1 = activity gate (RETRACTED), 2 = pyramid/ladder (NULL),
4 = the catalyst-selection filter (already queued; add her as a proponent there), 6 = Cameron arm 0 (queued). The only
axis the ledger hasn't touched is **#8: whether small-cap gapper fades decayed in late 2025**. Testing it needs a
point-in-time sub-$50M-ADDV panel including delisted names, plus borrow/locate costs. Both are the data blind spot that
already blocks row "First green day" (PARKED) and WL-5i (dilution fade). If that panel is ever built, run it after the
first-green-day row as a **per-year gap-fade series with the same-date non-gapper control and borrow charged**. That's a
regime-decay descriptive, not a strategy. Don't queue it.
