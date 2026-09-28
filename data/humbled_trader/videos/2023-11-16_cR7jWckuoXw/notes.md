# Verified 8-Figure Trader Explains Statistics & Trader Psychology (Humbled Trader x Steven Dux)

**Video:** `cR7jWckuoXw` · 58 min · published 2023-11-16 · reviewed 2026-09-28 · auto-captions

> **2.5/5 · no runnable test (one new axis specced, blocked on data) · METHOD yield: the capture ratio.** Steven Dux
> ("Ducks"), a low-float short seller, talks statistics better than the genre: buckets that vary one factor [15:57],
> 3–4 trades a month, and a fixed-size theoretical book to grade himself against. But **no number carries an n, a loss
> distribution or a control**; the headline figures are win rates, and his sizing rule (10x on 90% patterns) is one this
> ledger contradicted. His <$300M-runner universe is outside our panel, so most pattern claims are untested here.

## Guest and credentials (as stated)

- Steven Dux, started at 19 with ~$25k of tuition money, lost half, borrowed and restarted [04:17]; "27,000 to 900,000
  first year… second year 2.7 million" [04:17–05:22]. 2023 "still up in the seven figures… lower seven" [02:07].
- DWAC short: "$6 million on the first day… that week total I made 17 million" [32:00]. Host calls it the 2022
  single-day retail record [01:02].
- Verification: posted broker statements [52:11]. Worst loss ~$1M, biotech squeeze [30:58]. Verified dollars from one
  survivor of an unstated denominator: verified ≠ edge (KINFO row 313, USIC row 303).

## Statistical / process claims

| @ | claim (verbatim where short) |
|---|---|
| 03:14 | "shorting has 90%… much higher winning percentage compared to buying" |
| 15:57–17:01 | 25 buckets (mcap 0–10M, float 0–1M, gap >50%…); hold everything fixed so "there's only one factor that's different" |
| 19:07–20:11 | Short when day's volume x avg price reaches "how much money retail can pour into a ticker"; the threshold fell from ~$1B (2021) to ~$200M (2023) [31:47] |
| 23:24 | Only names starting below $300M market cap; ideal gap 100–170% [25:32]; biotech blacklisted, "every time I trade biotech I lose" [26:35] |
| 27:38 | First red day: avg fade **−26%**, day two −15%, low "typically 10:30" (no n) |
| 33:02 | Win rates 70/80/90% by pattern; "higher winning percentage… bigger size"; 90% patterns get **10x** the 60% size |
| 34:07 | Scale in "under 1% of the volume"; beginners "one entry, one exit" [36:13]; disagrees with "add to winners" [37:17] |
| 38:20–39:23 | Overtrading fix: per pattern win rate x avg profit x frequency at FIXED size = "your true expected return"; read it every morning |
| 41:28 | Annual statement review: filtering "what I'm not supposed to trade" would have made **4x** |
| 42:33–43:36 | Realised ÷ theoretical book: 37% (2021, best), 29% (2022), ~20% (2023); quits at 85% |

## Against the ledger

| claim | verdict | row |
|---|---|---|
| Shorts win more, so shorts hold the money | **UNTESTED** on his universe; on liquid names **CONTRADICTED**: 0/10 short universes, all have positive absolute drift | §4 short-universe (row 227) |
| High win rate = size up 10x | **CONTRADICTED** as sizing: grading by a risk spread +0.08R with more drawdown vs exclusion +0.29R. A win rate is priced (SMB row 349), and his $1M loss came on a sized-up "high winning percentage" entry [30:58] | row 33, row 31 |
| Trade fewer, filter the trades you "shouldn't" take | **AGREES**: exclusion is the lever; same-day round trips are the book's largest measured leak (Aug −$7.9k, 278 cycles −$8.3k at 19% win) | rows 33, 169 |
| One entry, one exit; don't add | **AGREES** (O'Neil pyramid NULL; add-to-winners NULL) | rows 164, 360 |
| Retail $-capacity threshold (short at exhaustion) | **UNTESTED** (no turnover or market-cap axis in the ledger); his own threshold fell 5x in two years, so the parameter is non-stationary | none; cf. localisation ρ −0.011 (row 259) |
| First red day −26% / 10:30 low | **UNTESTED**, blocked on small-cap panel (same blocker as Mari, Veprek) | rows 437, 498 |
| "Statistics keep changing" by year | **AGREES** in spirit: outcomes cluster, but trailing performance does not predict | rows 259, 260 (adaptive trader NULL) |
| Float caps supply at resistance [21:16] | **UNTESTED** (float never tested) | row 491 |

No claim can meet the |t| ≥ 3 bar: none carries an n. The "4x" is a filter chosen after the outcome.

## METHOD yield

**Capture ratio.** Realised P&L ÷ the P&L of the same rule's signals at fixed size over the same period. It is a
conformance/execution measure, so admissible on Gabe's journal: precision-tier signals at fixed 1R vs journal
campaigns, same months; split the gap into skipped signals, off-rule trades, slippage. Fold into the queued
lived-experience stats row (§10, row 459) rather than a new row.

## New test: retail dollar-capacity exhaustion short (PARKED, blocked on data)

New axis: the ledger has short interest (row 254) and gap fades but never turnover relative to size. **Spec:** runners
with pre-run market cap < $300M and day-one gain ≥ 50%; event = first session whose dollar volume ÷ pre-run market cap
≥ the top tercile of that year's events (threshold re-fit per year on prior years only, since he says it drifts).
Arm A: short next open, cover the close. **Control:** same-date, same-gain-bucket runners below the threshold (holds
date and run, varies only turnover). Costs: house model plus borrow/locate; unborrowable events count as zero, not
dropped. Primary = A − control, date-clustered, |t| ≥ 3, both halves and ≥ 2/3 of years same sign. **Blocked** on a
small-cap panel with shares outstanding; run with Mari and Veprek when it exists. A liquid proxy would not test it.
