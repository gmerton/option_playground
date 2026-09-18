# "Buy a QQQ LEAP every time QQQ is down ≥ 1%" (2026-09-17)

**Question (Gabe).** Is buying a QQQ LEAP call on every ≥1% down day better than buying one on any day?

**Verdict: no.** QQQ LEAPs bought any day made large returns in 2011–2025 because QQQ rose ~20% a year, and a LEAP
levers that. The down-day trigger adds nothing:
- **As traded:** not significant, and slightly worse at 12 months.
- **As a monthly timing tweak:** also nothing.
- **Shares back to 1999:** buying QQQ on down days did *worse* than buying any day over 12 months (−2.8 pp).
- **Clustering:** down days bunch up in bear markets (100 in 2000, 100 in 2002, 80 in 2008, 88 in 2022), so the rule
  commits the most capital exactly when leverage hurts most.

## Setup (set before running)

**Entry:**
- **Signal day close,** 2011-04 → 2025.
- **Contract:** QQQ call, expiry nearest 450 DTE (360–600), delta nearest 0.50 / 0.70 / 0.80.
- **Fill:** mid + ¼ spread + $0.0065/sh.

**Exit:**
- **When:** after 63 / 126 / 252 trading days.
- **Fill:** mid − ¼ spread, zero if bid is zero.
- **Missing quotes:** exits that couldn't be priced (4.1%; 2.6% for rule days, 4.4% for others) are dropped.

**Arms:**
- **Every day:** the benchmark.
- **Down ≥ 1%:** the rule.
- **Down ≥ 2%.**
- **All other days.**

**Also reported:**
- **Shares:** QQQ total return.
- **Levered shares:** delta × S / premium × QQQ move.
- **Stats:** t clustered by entry month.

Scripts: `run_qqq_dip_leap_pull.py` (cache `data/cache/qqq_dip_leap/`), `run_qqq_dip_leap_study.py`. Full output:
`qqq_dip_leap_study_2026-09-17.log`. Entry coverage is thinner before 2018 (~166 days/yr, when fewer LEAP expiries
fell in the window). That's calendar-driven, so it affects every arm equally.

## 1. QQQ shares, 1999–2026: down days are not better entries

Forward return after the day, by era. The "lift" is the rule minus all other days, t clustered by month:

| era | horizon | any day | after ≥1% down | lift (t) |
|---|---|---|---|---|
| 1999–2026 | 12 mo | +13.5% | +11.2% | −2.8 (−1.6) |
| 1999–2010 | 12 mo | +4.8% | +3.0% | −2.4 (−1.0) |
| 2011–2026 | 12 mo | +20.5% | +21.9% | +1.7 (+1.1) |
| 2011–2026 | 3 mo | +4.7% | +6.2% | +1.7 (+2.4) |

A down-day buyer did better only in the post-2011 buy-the-dip era, and never significantly. The option data
(2011+) covers only that friendly era.

## 2. The LEAP rule vs buying any day (0.70Δ shown; 0.50Δ and 0.80Δ agree)

| hold | any day | rule (≥1% down) | ≥2% down | rule lift, as traded (t) | 2022 entries: any / rule |
|---|---|---|---|---|---|
| 3 mo | +17.1% | +19.3% | +24.5% | +2.6 (+0.8) | −20.0 / −16.5 |
| 6 mo | +38.4% | +40.1% | +49.2% | +2.1 (+0.4) | −13.9 / −14.0 |
| 12 mo | +86.6% | +81.8% | +86.6% | **−5.8 (−0.7)** | +32.1 / **+21.4** |

Win rates are 69–82% either way; the worst trade is −100% in every arm. 0.50Δ at 12 months: rule +121% vs any day
+133% (t −1.1).

**Why the option doesn't rescue it:**
- **The rule buys dearer vol:** IV at entry is +2.7 vol points higher on down days (t +9.7).
- **The option structure adds nothing on rule days:** LEAP minus levered shares is −1.5 pp at 3 months (t −3.0) and
  ≈ 0 at 6–12 months.

## 3. The timing tweak doesn't work either

Comparing a down day with *other days the same month* shows +6 to +10 pp (t 5–10). But that compares against days
later in the month that you can't know in advance. The capturable version: buy one LEAP a month, on that month's
first ≥1% down day, else month-end (a dip came in ~81% of months):

| 0.70Δ | wait for the dip | first trading day | difference (t) | months better |
|---|---|---|---|---|
| 3 mo hold | +17.2% | +16.2% | +1.0 (+0.7) | 50% |
| 6 mo hold | +37.3% | +38.0% | −0.7 (−0.4) | 50% |
| 12 mo hold | +86.5% | +87.7% | −1.1 (−0.5) | 45% |

The same across 0.50Δ and 0.80Δ: |t| < 1 everywhere. Waiting for a dip costs about as much drift as it saves in price.

## What this means

- **The returns were QQQ's bull market × leverage,** not the trigger. A 0.70Δ LEAP bought on *any* day returned +87%
  over 12 months with 82% wins, and one bought in 2021 lost −53%.
- **The rule's real exposure is regime concentration:**
  - **Rule buys by year:** 88 in 2022, 52 in 2020, 38–40 in 2018 and 2011, but 11 in 2017.
  - **The history the option data lacks:** 1999–2010 had ~100 signals a year in 2000–2002 and 80 in 2008.
  - **In that regime,** a buy-every-dip LEAP rule would have stacked leveraged positions into a −80% drawdown.
- **If Gabe wants QQQ LEAP exposure:** size it as leveraged beta and scale in on a calendar. The dip trigger
  neither helps nor, at 3–6 months, hurts, but it lets bear markets set the size.
- **Related:**
  - **Options With Ryan LEAPS dip-buying** (`data/options_with_ryan/strategies/leaps_dip_buying.md`): the same idea,
    with RSI/Bollinger triggers.
  - **The RSI study, section C:** index RSI/Bollinger oversold signals give no reliable edge on the underlying.
