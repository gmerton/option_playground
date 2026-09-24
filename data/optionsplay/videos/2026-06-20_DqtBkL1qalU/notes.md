# OptionsPlay — "Why Cutting Winners Too Early Destroys Your Edge" (Tony Zhang, 2026-06-20, 51 min)

_Reviewed 2026-09-24. Session 3 of his four-part Growth Lab series "Why winning trades are not enough". It is the
**same thesis as the already-reviewed [iXOULnIGEKk](../2026-09-05_iXOULnIGEKk/notes.md)** (2026-09-05, "Why
You're Selling Winning Stocks Too Early", 2.5/5), but it is **not a re-edit**. A word-level check found only 482
of 9,189 words in matching runs and 0.45% shared 8-grams, so it is a different talk on the same subject. What is new here is
**numbers**: a 56% base win rate, a 68% win rate on adds, a 4:1 winner-to-loser dollar ratio and the "fixed vs
exponential" add sizing. The earlier talk had none of them. Transcript in this folder._

## Verdict: 2.5 / 5 (consistent with iXOULnIGEKk)

The diagnosis is the same, and it agrees with our exit ledger again: cutting winners early is the most expensive
management error we have measured. The cure is also the same: add exposure when a winner fires a new platform
signal. **We tested that cure on 2026-09-22 and it was NULL** (row 121). What this talk adds is data, and every
figure is **win rate or dollars from his own published daily plays over "the last couple of months"**. He says
himself that this was "one of the strongest runs in the market". There is no cost, no control, no horizon and no t-stat. The
headline, "adds win 68% vs 56% for fresh ideas, so the true edge is in pressing winners", has the shape our
ledger warns about. The add is only possible on trades that are already working, so the add sample is selected
by the outcome so far. On our own book the add's **win rate** does rise, but its **R does not beat a fresh
trade or an unconditional add**. The win-rate framing is the error. It is the same metric that makes cutting
winners *look* good.

**Pitch vs rules.** The pitch is the Early Breakout Detector, the "confirmed outperformer" list, daily plays and
the portfolio "new signal today" filter. Those are proprietary and untestable as stated. The testable rules are: (1) add only to a
position that is already profitable, (2) add on a **fresh entry signal that needs a pause/pullback**, never into a
parabolic run, (3) up to ~4 adds, and (4) size adds flat (2% + 2% + 2% …) or "exponential" (1% → 3% → 5%).

## Data audit

| item | what he shows | problem |
|---|---|---|
| Sample | His own daily-play trades, "the last couple of months" (≈ Apr–Jun 2026) | One regime, which he calls one of the strongest runs. There is no year, no second regime and no n. Our base book is **−0.007R month-weighted vs +0.448R trade-weighted**, and its edge lives in busy breakout months (row 121) |
| Baseline | "Randomly pick S&P 500 stocks → 50/50" | Horizon, exit and cost are undefined, so it is not a control for anything. The 56% is his platform's buy/sell accuracy, also with no horizon |
| Adds 68% (79%, ">80%" in strong periods) | Win rate of the add trades | Adds exist **only** on names that kept working and kept firing signals. The sample is conditioned on the path. He compares it with a fresh idea, not with an unconditional add to any live trade |
| $44k vs $10k (4:1) | Dollar P&L of pressed winners vs losers | Winners are "trades where we pressed", so they are defined partly by having been pressed, which needs a rise. Dollars, not R. Vehicles mixed (put credit spreads and call debit spreads) |
| Vehicles | GOOGL: put credit spread → call debit spread → more; AVGO: 4 put credit spreads, the 4th into earnings | Win rates of short-premium spreads are **priced by the strike**, so a win-rate average across structures is not comparable (row 281, "20Δ win rate is priced") |
| Pricing | Not stated | No fill model, so it is effectively the mid |

## Claims as spoken

| @ | Claim |
|---|---|
| 03:21–04:11 | "Adding to a winning trade is the hardest trade to make", and it is the single skill that separates profitable traders |
| 12:16 | Cut losers as fast as possible so that your mental capital goes to managing winners |
| 13:43–14:49 | Random S&P 500 picks = a coin flip; OptionsPlay technical signals = **56%** accuracy |
| 15:29–16:31 | "The best strategies top out at 56–60% winning"; anything > 60% fires only once or twice a year |
| 17:49–18:34 | **56% of fresh trades win, but 68% of adds to winning trades win**, so "the true edge comes from … trades that are profitable", not fresh ideas |
| 19:34–19:49 | In strong periods adds win > 80% (79% a week earlier) |
| 23:36 | Add only when the previous trade is profitable, never to a loser |
| 24:51 | GOOGL: 4 adds on ~$2,000 risk each → +$6,600 |
| 30:48–31:15 | AVGO: 4 put credit spreads, the 4th just before earnings; the stock gapped 470 → < 400; −$3,000 on $8,000 risked. "I would take the exact same trade every single time" |
| 32:39–32:43 | Pressed winners +$44k vs losers −$10k, **≈ 4:1**, from 56%-accurate ideas |
| 34:45–36:07 | Need a target; adds usually "top out" at about the 4th; the signal needs a pause/pullback, so do not add to parabolic names (MU, SNDK) — "that's where you're chasing" |
| 42:57 | "Only about 10% of your trades will end up being these home runs", and they outweigh the losers |
| 43:18–44:48 | Add sizing: flat (2% each add) for beginners; "exponential" (1% → 3% → 5%) for experienced traders. All his results assume flat |

## Claims vs our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 03:21 / 17:49 | **Adding to winners is where the edge is**; adds win 68% vs 56% fresh | ⚠ **Direction reproduced on win rate, NOT on expectancy.** Row 121 (`run_oneil_pyramid_8wk.py`, precision tier, 2,000 trades, 2019-10→): adds at session 3/5/10 earn **+0.30…+0.66R** on their own risk (t 0.4–1.5), about the same as the base trade (**+0.448R**). **No condition (up ≥ 1R, held the pivot, both) beats the unconditional add** at the same k (best +0.15R, t 1.25). Exploratory re-cut of `oneil_pyramid_adds.csv` for this review (no re-run, win rates only): the base book wins **30.8%**; unconditional adds win **32.8 / 36.0 / 36.5%** at k = 3/5/10; "up ≥ 1R" adds win **35.7 / 38.0 / 39.3%**. So his gap (+12pp) shows up on our data as **+3 to +9pp of win rate with no gain in mean R**. ⚠ Our add stop is breakeven (tighter than the base), which lifts R per unit risk and lowers the win rate, so the win-rate levels are not his. The sign of the gap is the comparable part. And the *positions* that allow an add do win far more often (**base win 59–85%** on those same trades, +3.4R vs +0.35R). That is the gain already banked, not the add's future: the endogeneity trap named in row 121 |
| 15:29 / 32:43 | Win rate tops out at 56–60%, and the process turns it into profit | ❌ **Wrong metric, and the ledger shows why.** Win rate is a property of the structure and the exit, not of the edge. The house book wins **30%** with median −1.08R and is our one equity pass (+0.4R, row 16). Selling 30Δ/20Δ bull puts wins **75.7–79.6%** and the ranking inside it is what pays (YfrZT notes). Exiting the same breakouts at the same-day close **wins 47% and earns −0.13R**, while the 20-EMA trail wins 31% and earns +0.89R (`exit_timing_study_2026-09-18.md`). Cutting winners early is what *raises* the win rate, so a talk against cutting winners that measures itself by win rate is arguing against its own point |
| 42:57 | ~10% of trades are home runs and they carry the book | ✅ **Agrees in shape.** Precision tier: 4.5% of trades exceed 10R and **the top 1% carry 26% of gross gains** (`breitstein_tests/precision_tier_control_2026-09-19.md` §Verdict 1) |
| 20:05 (implicit) | Taking profits early and recycling into a new idea is the leak | ✅ **Confirmed.** Trims cost −0.25…−0.33R; "extended → tighten" INVERTS (−0.19R, t −2.8; 10-EMA trail −0.47R, t −4.8); only breakeven-after-+2R is harmless (`profit_lock/profit_lock_2026-09-20.md`, row 114). Qullamaggie's partial-then-trail loses −1.87pp/trade, t −4.39 (row 100). Same-day exits are the negative bucket in both books, and Gabe's own log has **278 same-day cycles, −$8,291, 19% win** (`exit_timing_study_2026-09-18.md`). ⚠ His log is admissible here only as an execution/conformance fact, not as evidence about any setup |
| 34:45–36:07 | Add only on a pause/pullback signal; never into a parabolic run | ⚠ **Not tested as an add.** As an *entry*, waiting for the retrace is PARKED (t 0.48, row 16), the reclaim is NULL (row 97, edge −0.004…+0.108R, pre-2023 negative), and daily EMA pullbacks FAIL vs the breakout (row 123). "Don't add to parabolic names" matches the entry-extension mechanism (entry location worth ~2.6 ADR, row 16). But the profit-lock study says that holding an extended winner is right. Extension is a reason not to *buy more*, not a reason to *sell* |
| 30:48 | AVGO: the loss was small because early credit spreads banked income. "Take it every time" | ⚠ **The vehicle works against the thesis.** On precision-tier breakouts, the 0.30/0.15 put spread loses to the house stock trade (**P − S −0.336 per $ risk, t −1.77**) because it sells the right tail that *is* the edge (stock winners +3.50R vs spread +0.23; p95 +6.2R vs +0.36). That is row 25, `breakout_putspread_vs_stock_2026-09-24.md`. Pressing a winner with **credit** spreads adds exposure that cannot hit the home run he is selling. The 4th add was sold straight into earnings. Adding through a print is untested here |
| 32:39 | 4:1 dollars, pressed winners vs losers | **Unfalsifiable as presented.** One regime, his own trades, winners defined as pressed. Our pooled book gives the regime-dependence directly: the edge lives in busy breakout months, and the base book is flat month-weighted (row 121 METHOD). Strategy "good stretches" are not predictable (ρ −0.011, row 195) |
| 43:18–44:48 | Flat 2%-per-add vs exponential 1 → 3 → 5% | **Untested as a schedule.** Row 121 says adds scale the same edge rather than improve it, so the schedule is a risk choice, not an edge. The size-lever result is that the lever is **exclusion** (+0.29R OOS), not a risk spread (+0.08R, row 124). His "exponential" adds 5% risk on the 3rd add, **2.5× the 2% base**, on a signal whose conditional edge is +0.15R at t 1.25 |
| 12:16 | Cut losers fast | ✅ Agrees in spirit with the stop rules. But "fast" must not mean intraday: the house tight stop is judged **on the close** (CLAUDE.md, stop rules), and only the 1-ADR disaster stop rests intraday |

## Not tested, could be

Specs only. Nothing here is queued or run.

1. **Signal re-fire inside a live winner vs the same signal on a fresh name (his 68% vs 56%, measured in R).**
   Pool = the house precision-tier breakouts. Event = a **second** precision-tier breakout signal in a name whose
   first trade is still open **and** above its entry at that close. Arm A buys that re-fire at the close with
   the house stop and exit. Control 1 = same-date precision-tier breakouts in names with no open trade (`xname`,
   same date, so regime is held fixed). Control 2 = the unconditional session-k add from row 121 at a matched k.
   Primary = A − control 1 in % per trade (not R, since stop widths differ), date-clustered, both halves same
   sign, per-year table. **What makes it new:** row 121 added at *fixed session counts*. His trigger is a **fresh
   signal**, and his comparison is **vs a fresh idea**, which is the xname control. Prior low: the first-vs-later
   pullback cut was +0.06 vs 0.00R (`pullback_entry_study_2026-09-17.md`), and the entry-extension mechanism
   predicts that the re-fire is bought extended. ⚠ Overlaps the "add on a RETEST" item iXOUL queued. Run them
   as one test with two trigger arms, or not at all.
2. Nothing else. The exit claims are settled (rows 100, 114, 115). The add-sizing schedule is a risk choice
   once row 121 is accepted. The 4:1 and 68% figures cannot be reconstructed without his trade list.
