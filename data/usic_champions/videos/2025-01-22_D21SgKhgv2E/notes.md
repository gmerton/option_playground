# USIC — "Interview of United States Investing Champion J Law" (Norm Zadeh, 2025-01-22, 26.5 min)

_Reviewed 2026-09-23. Norm Zadeh (runs the United States Investing Championship) interviews J Law (Hong Kong,
"JLaw Stock" YouTube channel), winner of the 2024 $1M+ division at +359.3%, billed as breaking Mark Minervini's
division record. Answers go through an interpreter. Transcript (`en-orig` auto-captions) in this folder. Price
checks below are yfinance closes, pulled 2026-09-23._

## Verdict: 2 / 5

(provenance 4 · process 2 · testable 1)

The return is real in the narrow sense that matters most for a contest: Zadeh says he read the 85-page IBKR
statement himself, and IBKR computes a time-weighted return. What the interview doesn't give is anything that
separates skill from one year of concentrated exposure to the year's two biggest large-cap movers. **PLTR
returned +340% in calendar 2024 and MSTR +358.5%.** His audited +359.3% is almost exactly a buy-and-hold of
MSTR. Zadeh says a "significant percentage" of the gain came from PLTR, and the other named position was
MSTR. The method he describes (Minervini student, leader of the leading group, VCP / bull-flag breakout, sell
at the stop "with no mercy") is the one our ledger has already tested most. The parts that are specific enough
to test are NULL here. The rest is narrative (AI "monopoly", Bitcoin momentum, tax-cut expectations).

## Provenance

| question | answer |
|---|---|
| What USIC audits | **Broker statements, for high performers.** [00:00:47] "when anybody has a high performance… particularly if they set a new record, we go over their statements carefully." Here that meant an 85-page IBKR statement, with IBKR's own time-weighted return. ✅ That beats a self-reported P&L or a leaderboard of realised dollars (cf. KINFO). ⚠ The check is described for *high* performers; how rigorously other entries are checked isn't stated |
| Account size | **≥ $1M division** (the "million-plus division"). Zadeh mentions "a three or four million-dollar account at some point" [00:15:59], so the account compounded during the year. The starting size isn't stated |
| Period | **One calendar year (2024).** One number, the TWR for the year. No drawdown, no monthly path, no Sharpe |
| Other years | He says he has traded 15 years, lost heavily in 2008 and blew up shorting Brazil. **No other audited year is shown.** 2024 is the only data point |
| Denominator | **Not stated.** It's the top entrant of one division in one year. The host's own base rate [00:21:26]: "anybody that can do more than 20 or 30% should be really happy". The winner of a return-ranked contest is the right tail of the entrants' *variance*, not their mean |
| Contest incentive | ⚠ **He says it himself** [00:14:15]: his worst trade (CRWD) "if it's not this competition, I don't think I would have done". A rank-by-return contest pays for variance, so the winner is selected on it. That is the survivorship mechanism in the contestant's own words |
| Conflict | Sells nothing on camera, but plugs a 5-year-old YouTube channel whose content is his trading. An educator with a channel, like the TraderLion guests |
| Luck of one year | **High.** The two named winners each returned ~+340–360% in 2024 (PLTR +340%, MSTR +358.5%; SPY +24.9%). A concentrated, momentum-following book holding either one at size finishes near the top by construction. Nothing here separates *picking* PLTR/MSTR in advance from *being in* the names that happened to go vertical |

⚠ Caption checks: Minervini's prior record is captioned "338.4%". The figure usually quoted for his 2021 USIC
is 334.8%. I haven't verified either, and the captions often transpose digits. Zadeh later says "353%"
[00:20:58] against "359.3%" at the open. Treat 359.3% (read off the statement) as the number.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:00:47 | 359.3% TWR in 2024, $1M+ division, verified from an 85-page IBKR statement | ✅ **Audited, one year.** Real as a number, but it matches the calendar-year return of MSTR (+358.5%) and PLTR (+340%) held flat. That fits concentration in two names, not a repeatable selection rate (see Provenance) |
| 00:06:53 | "A lot of the profits in the market come from respective big winners… buy and hold on some big winners" (2024 ≈ 2019) | ✅ **Agrees, and it's the book's own shape.** The house breakout is **bimodal**: 23.6% never retest (+1.273R), 76.4% do (−0.374R), and the split **can't be called at entry** (9 features, `project_entry_extension_finding`). The O'Neil 8-week test found the 20-EMA trail already keeps power moves (+7.1R). Base book +0.448R trade-weighted vs −0.007R month-weighted (TEST_INDEX §4 pyramid row), so the edge lives in a few busy months. "Big winners pay for everything" is true. It doesn't say how to find them in advance |
| 00:07:49 | PLTR chosen as "market leader… monopolizes… AI is the buzzword", traits like GOOG/SHOP | **Narrative, n = 1, chosen after the fact.** No fundamental-quality or "monopoly" screen exists in our ledger to test against. The testable neighbour is leader selection: our **Trend Template is the weakest of 5 universes** (+0.56pp 20d ADR-matched, t 1.3, universe test 2026-09-21), and the TT ablation certifies no criterion |
| 00:09:39 | Initial PLTR buy 2024-03-06, sold next day on the stop ("sell with no mercy"). Pattern "not very stable" | ✅ **Consistent with the house stop rule** (stop = session low judged on the close; disaster stop 1 ADR resting). PLTR closed 26.16 on 03-06 and 26.46 on 03-07 (yfinance), so the stop was intraday or very tight. Not scoreable from one fill |
| 00:10:41 | Re-entry 2024-06-04 at 21.95 on "a VCP pattern or a bull flag" breakout, "very clear signal" | ❌ **VCP = NULL here.** VCP damped-sine test (2026-09-23, 1,704 signals / 688 names): +0.28%/trade vs +0.57% for all house breakouts, same-date cross-name control −0.37pp (t −0.70), and the pre-registered t 3.43 pass was **RETRACTED** as a control artefact. Minervini's full spec (volume dry-up) is still untested, at low prior. PLTR closed 22.96 on 06-04, and it's a hindsight pick from the year's top decile |
| 00:11:17 | MSTR: "leading stock in crypto", buys Bitcoin with its profits → momentum cycle | **Narrative.** MSTR +358.5% in 2024 and **−39.4% in 2025 to 11-26**. He says he'd cleared it. The 2025 path is the other half of "holding the leader of a hype" |
| 00:12:35 | SOFI: fintech is the hot group (UPST, AFRM); SOFI had the strongest momentum + fundamentals, "especially after it released its earnings" | ⚠ **Post-earnings momentum is NULL here.** Earnings ledger (2026-09-20): PEAD NULL. Tito's "good earnings, delayed bump" loses to the same-name control (−0.19 to −0.36R). DR-EP arm A (buy the catalyst day) **−0.173R, t −4.70**. SOFI returned +54.8% in 2024, a winner but a modest one next to PLTR/MSTR |
| 00:13:32 | "Pick the leading group, and the leader out of the leading group" | ❌ **The group half is INVERTED here.** Industry-rotation study: leading-group filtering **INVERTED** (bottom-3 sectors beat top-3, t 2.6). Stock-level leadership: the universe test says the universe carries the return, not the trigger. HYB-B (TT at $100M + ADR ≥ 4) is PARKED at t 2.6. The best version we have is a volatility screen, not a "group leader" screen |
| 00:13:48 | Shorts only in bear markets, never his focus. Worst loss ever = shorting Brazil | ✅ **Agrees.** Short-selectable universe test (2026-09-23): **0 of 10 cells pass**; weak names underperform on excess but **still drift up in absolute terms**. There's nothing to short outright |
| 00:14:04 | Worst 2024 trade: CRWD, "betting on a rebound", aggressive, broke his rules | ✅ **That's our crash-leader veto.** CRWD fell −44% from 2024-07-01 to 2024-08-02 (the outage) in a **healthy** tape (SPY +24.9% for the year). Crash-leader study: buying a deep drawdown while breadth is healthy has a **median of −20%**, which is "the most trustworthy number in the study". Breitstein counter-trend long: FAIL every arm. He learned the lesson our data teaches |
| 00:15:11 | "Control on the maximum drawdown has always been my priority"; max loss from one trade **≤ 0.3% of the portfolio** | ⚠ **Plausible only as initial risk with house-money adds, and he doesn't say which.** 0.3% of equity per trade and a ~340% year in two names needs very tight stops or very large adds on open profit. At PLTR's ~4–5% ADR, a 1-ADR stop at 0.3% risk is a ~6–7% position. Our results on the tight-stop route: stops < ~0.5 ADR executed intraday are what the entry study rejects (close entry beats every intraday entry, t to −3.4). The pyramid route: adds scale the same edge, they don't improve it (pyramid NULL). He was never asked about position size, leverage or the add schedule, which is the question that would matter |
| 00:17:54 | Cut exposure in Dec 2024 on inflation / "insane" tax-cut expectations. "2025 won't be easy" | **Macro narrative, one call.** Directionally right (April 2025), but not falsifiable as stated. Our FOMC / macro catalyst work is noise. Trailing-30d breadth / regime rules all **FAIL** 2019–26 |
| 00:23:07 | Paper trading misses the psychology. Learn with real money, small size. His early years lost almost all his savings | **Process advice, untestable.** Consistent with "size small" in every KB. The biography (2008 bank stocks −50%, Brazil short) is the usual survivor's story: a blow-up, then a system |

## What I would take

1. **Nothing to adopt.** The two mechanical claims (VCP / leader breakouts, post-earnings momentum) are already
   NULL here, and "leading group" is INVERTED.
2. **A clean provenance example for the README.** Audited, TWR-based, a $1M+ floor. That's the best
   *verification* of any KB guest so far, and it still carries almost no information about *edge*. The winning
   return equals one name's calendar return. Use it as the reference case for "verified ≠ edge".
3. **CRWD, one more time.** A top trader's worst trade was the exact trade our crash-leader veto forbids (a
   deep drawdown in a healthy tape). Worth one line on the desk as a live illustration, not as evidence.
4. **The contest-incentive quote** [00:14:15], "if it's not this competition I wouldn't have done this trade".
   Cite it whenever a contest result is offered as evidence.

## Not tested, could be

- **Nothing new worth queuing.** Every mechanical claim maps to a row we already have (VCP NULL, PEAD NULL,
  catalyst-day −0.173R, leading-group INVERTED, shorts 0/10, crash-leader veto).
- *If* position sizing were ever disclosed: **"0.3% initial risk + pyramid on open profit" vs flat sizing on the
  precision-tier book**, return per unit of max drawdown. Mostly answered already: the pyramid test is NULL and
  the size lever says exclusion beats amplification. **Not queued.**
