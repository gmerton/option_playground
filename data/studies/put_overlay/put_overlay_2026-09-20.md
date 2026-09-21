# Cheap-convexity overlay (index puts gated on low VIX) — 2026-09-20

**Question.** The book is net long; only the straddle is direction-neutral, and single-name shorts / ETF bear calls
both failed. Does a hedge of SPY/QQQ puts, bought only when protection is cheap, cut the book's drawdown by more than
it costs? (The "Burry lesson": buy protection when nobody wants it, and survive being early.)

**Data.** `run_put_overlay_study.py` → `put_overlay_2026-09-20.log`, `put_overlay_summary_2026-09-20.csv`,
`put_overlay_alone_2026-09-20.csv`. SPY/QQQ puts from `options_daily_v3` on the first trading day of each month,
2011-01 → 2026-01 (bid/ask ends 2026-02-20). Expiry nearest 75 DTE, strike nearest spot × (1 − m), spot from
put-call parity. **Buy at the ask, sell at the bid a month later**, then roll. Structures: 5% OTM put, 10% OTM put,
5%/15% put debit spread. Gates: always / VIX < 20 / VIX < 16 / VIX below its 1-year median. Budget = fixed premium
spend, 1–5% of the account per year.
**Book** (2018-04 → 2026-02, 95 months): straddle sleeve (`rsi_straddle.parquet`, 5,886 gated trades), 20-ETF bull
put roster (`rsi_putspread.parquet`, +5.68%/trade = the post-erratum figure) and the breakout book
(profit-lock BASE). Each sleeve is scaled to equal vol and the book to 4%/month. ⚠ This is a risk-parity model of
sleeve averages, not the live account.

## 1. The hedge alone: the cost is carry, not friction
Median bid/ask on the 5% put = **0.8% of mid**, so real fills cost ~1pp/month against mid. The carry is the problem:

| SPY | months held | mean / month on premium | months it pays | best month |
|---|---|---|---|---|
| 5% put, always | 181 | **−25.6%** | 21.5% | +403% |
| 5% put, VIX < 20 | 134 | −23.1% | 20.9% | +403% |
| 5/15 put spread, VIX < 20 | 134 | **−19.6%** | 22.4% | +373% |
| 10% put, always | 181 | −32.3% | 17.7% | +583% |

QQQ is 1–3pp worse on every row. The VIX gate barely changes the loss per month held (−23 vs −26%). What it saves is
the months you don't hold.

## 2. On the book: nothing moves
With a 2%/yr budget, every cell's Sharpe changes by −0.05…0.00 and max drawdown by −0.45…+0.63pp on a 25% base.
Even at 5%/yr the best cell (SPY, VIX < 20, 5% put) cuts max DD by **0.62pp** for −0.03 Sharpe. 2022 improves by at
most ~1.3pp of a −15.7% year. **The must-pass fails:** VIX was above 20 for most of 2022, so the gate was mostly
closed.

Book without the straddle (bull put + breakout only, corr with SPY 0.37): the best cell is the **VIX < 20 5/15 put
spread at 5%/yr: max DD 38.1 → 36.4 (−1.7pp), Sharpe unchanged, 2022 −21.4 → −19.9.** Free, but small.

## 3. Why: the book's bad months aren't market crashes
- Book vs SPY month: **corr 0.22** (0.37 without the straddle). Of the book's 10 worst months, **5 had SPY UP**
  (2018-11, 2019-04, 2018-09, 2022-11, 2020-08). No index hedge pays in those.
- The market's crash months are mostly already covered by the straddle: the book made **+32% in 2020**.
- The hedge does pay big in real crashes (2015-08 +403%, 2018-12 +345%, 2020-03 +391%). But the gate was **closed**
  for 2020-03 (VIX 33 at entry), 2011-09 and 2022-06, the moments protection was already expensive.
- **The straddle sleeve is worth ~13pp of max drawdown** (38 → 25). The best put overlay is worth ~1.7pp.

## Verdict: NULL
The index-put overlay neither helps nor hurts at budgets that fit the book (≤ 5%/yr). The VIX < 20 gate works as
theorised (it turns the DD change negative where always-on is positive), and the debit spread is the least-bad
structure. The effect is ≤ 2pp of drawdown. **The book's real bear leg is the straddle. Keep the pair balanced
rather than adding index puts.** Revisit only if the live book shifts toward pure long beta (e.g., the straddle
sleeve paused), where the VIX < 20 5/15 spread at ~5%/yr is the cell to run.

Also found: `data/cache/etf_putspread_recon.parquet` does NOT reproduce its own write-up (+6.92%, SPY +5.4%); its
take-50 cfg gives SPY −0.3%. `rsi_putspread.parquet` does reproduce the post-erratum +5.70%, so it was used here.
