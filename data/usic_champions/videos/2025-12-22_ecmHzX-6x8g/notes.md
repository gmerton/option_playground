# USIC — "Interview of United States Investing Championship Star Christian Flanders" (Norm Zadeh, 2025-12-22, 21.5 min)

_Reviewed 2026-09-23. Norm Zadeh interviews Christian Flanders: +433.5% in the 2024 USIC and +162% in the 2025
$1M+ division (as of the recording, ~2025-11-26, so 2025 was incomplete). Ex-prop trader (firm blew up in
2008), then online poker pro for ~a decade, full-time trader since 2017. Transcript (`en-orig`
auto-captions) in this folder. Price checks are yfinance closes, pulled 2026-09-23. A separate TraderLion
interview of Flanders (`data/traderlion/videos/interviews/2026-02-07_6aOnCK1gv2w/`) is being reviewed
separately. It had no notes.md when this was written, so there's no cross-reference yet._

## Verdict: 3 / 5

(provenance 4 · process 3.5 · testable 2)

The best guest so far in this genre, for three reasons:
- **The record is two consecutive contest years, not one.** 2024 +433.5% and 2025 +162% compound to about
  **+1,298%** (captioned as "up ,8%"). Two years at the top is much harder to get by luck than one.
- **He describes his worst trades without being asked twice, and his diagnosis is correct.** He increased size
  after each loss (CRWV, "stopped maybe seven times"). He round-tripped a range three times (PONY). He cut a
  winner without a sell signal (IREN). All three are leaks our own data measures.
- **One claim is new, mechanical and cheap to test:** the % of stocks above their 5-day MA > 80 means "a
  pullback is likely", so wait before entering.

What caps the score:
- His favourite setup, the episodic pivot bought on the gap, is our most solidly negative entry: DR-EP arm A
  **−0.173R, t −4.70**.
- His 2025 is dominated by **one biotech binary**. ABVX went +586% on 2025-07-23 on phase-3 data (10.00 → 68.60)
  and was still **58% of his book** at the recording.
- The April-2025 "buy the leader at the 150-day in a 1929-style panic" call is one instance, justified by
  historical analogy.

## Provenance

| question | answer |
|---|---|
| What USIC audits | **Not described in this video.** The J Law interview (same host, 2025-01) says high performers' broker statements are "gone over carefully". For a record entry that meant an 85-page IBKR statement with its time-weighted return. Assume the same standard applies to Flanders, but **this video doesn't state it** |
| Account size | 2024: division not named (he "entered our million-plus division" in 2025, which suggests 2024 was a smaller-account division). 2025: **≥ $1M**. No starting balances given |
| Period | Two calendar-year entries. **2025 is incomplete** (recorded ~Nov 26: "it's what, November 26"). +162% is a year-to-date mark, not a final result |
| Multiple years | ✅ **Two consecutive years, both top-tier.** The strongest part of the record. Before 2024 there's no audited data: 7 years trading solo (2017–2024), his words, no numbers |
| Denominator | **Not stated.** "Star" and "up 433.5%" are rankings within an entrant pool of unknown size. The host's base rate (J Law interview): ">20 or 30% should be really happy" |
| Concentration / luck | ⚠ **High.** 2025: ~60% long, of which **58% is ABVX**, one stock bought on a phase-3 gap and pyramided 4–5 times. ABVX closed 10.00 on 2025-07-22 and 68.60 on 07-23; by 11-26 it was 125.68 (+83% from the gap close). He also owned QURE, which fell **−49% in one session** (67.69 → 34.29, 2025-11-03) and −61% within 3 sessions. The same book held both a +586% and a −49% one-day biotech binary in the same year. A +162% year with 58% in one binary is, in large part, the outcome of that one binary |
| Contest incentive | A return-ranked contest pays for variance. A 58% single-name biotech position is rational for a contest entrant and would be reckless in most other mandates. His wife's reaction on hearing it ("that's way too much") is the unconstrained view |
| Conflict | None visible. No course or service, just "I'm on Twitter". He pays for several services (Minervini, Fahmy, Rainking, Ciovacco) and is working with a coach |

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:00:11 | +433.5% (2024) and +162% (2025 YTD, $1M+ division) | ✅ **Contest-audited, ~two years.** The best provenance in any KB here, but see the concentration row above. Two years is still n = 2 annual draws from a variance-rewarding contest |
| 00:04:12 | Swing trader following O'Neil / Minervini / Weinstein: "buy stocks going up… get on the fastest horses" at a low-risk entry so you can size up | **The house thesis.** The book *selects* well and *enters* badly (`project_entry_extension_finding`: breakouts buy 2.6 ADR above a random later entry in the same name). "Fastest horses" is our volatility screen: HYB-B (TT at $100M + **ADR ≥ 4%**) +1.79pp, t 2.6, **PARKED**. The Trend Template by itself is the **weakest** of 5 universes (+0.56pp, t 1.3) |
| 00:05:31 | Favourite setup = **episodic pivot**: a large gap on huge volume with a game-changing catalyst, a stage-2 breakout (Qullamaggie's term) | ❌ **Contradicted on the mechanisable version.** DR-EP (2026-09-22): buy the catalyst day **−0.173R, t −4.70**, both halves negative, loses to both controls. Deferred entry (arm B) −0.067R, t 0.21. Bonde's 9M-volume floor adds nothing. PEAD NULL. ⚠ **The residual is catalyst CLASSIFICATION** (catalyst queue #1, KINFO review): his INSM and ABVX picks were *phase-3 biotech readouts*, a specific catalyst class. That's the untested part, and it is testable only going forward |
| 00:08:52 | INSM gapped out of a ~12-month consolidation (EP). USAR broke out of an "IPO VCP" and doubled in 8–10 days | **EP: as above. IPO base: structural blind spot.** Our SMA200 / 400-bar minimums exclude every IPO (TEST_INDEX §10 parked, IPO row). VCP damped-sine **NULL** (2026-09-23), pre-registered pass **RETRACTED**. (USAR +11% in 2024 and +8% in 2025 YTD, so the "doubled in 8–10 days" move was round-tripped. He says he sold on the way down) |
| 00:09:15 | ABVX: bought the phase-3 gap, **pyramided 4–5 times**, still holding almost the entire position | **Pyramid NULL.** O'Neil pyramid test (2026-09-22, 2,000 trades): adds earn +0.30…+0.66R on their own risk, t 0.4–1.5, and **no add condition beats the unconditional add** (best +0.15R, t 1.25). Adding scales the edge, it doesn't improve it. In a contest, scaling *is* the point |
| 00:09:37 | PLTR bought the day of the April-2025 low: leaders "resisted the decline", PLTR came into the **150-day MA**, S&P down 3–4 days ~4% ("not since 1929"). Analogy: TSLA at its 200-day in the 2020 COVID crash | **One instance, verified in shape.** PLTR's 2025-04-07 low 66.12 vs SMA150 67.59, close 77.84, and 92.01 two sessions later. ⚠ **Both halves of the reasoning are weak here:** (a) "leaders that held up" as a selector: down-day RS is **INVERTED** at 63d (−3.51pp, t −3.33, dose-monotone, 2026-09-23). (b) "Buy the panic day": the Breitstein capitulation long's buckets beat `xname` but lose to `post`, i.e. **a DATE effect (panic clustering), not selection**. The crash-leader study says the same: a regime bet, pays only in a broken tape. The index-level version ("buy QQQ on the panic low", he did that too, 00:16:10) is the one capitulation form not yet refuted (Nikkei row). Queued neighbour: "stocks that hold up in a weak tape" (§10, ½ day) |
| 00:12:06 | Worst trades: CRWV bought "3–4 times along the lows", stopped ~7 times, and **"I increased my size with every loss to try to make back what I should have gained"**, then the stock went 5×. "The trades themselves were fine, it was the sizing" | ✅ **Correct diagnosis, and it's the revenge-sizing fingerprint.** It's exactly arm 0(b) of the queued Cameron test (risk-per-trade vs own median after consecutive losses). Size lever: **exclusion beats amplification** (A+B only +0.29R OOS; a 10× risk spread +0.08R with more drawdown). "Stopped 7 times, then it ran 5×" is the bimodal breakout book: 76.4% of breakouts retest (−0.374R), 23.6% never do (+1.273R), and the split **can't be called at entry**. Re-entry after a stop repairs only part of the loss (entry study) |
| 00:13:13 | PONY: oversized on earnings out of frustration, exited before the stop, re-bought, sold, re-bought, "traded inside that range like three times" | ✅ **Same-day / short round trips, our largest measured leak.** Exit-timing study: same-day exits are the negative bucket in both books (scalp −0.13R vs trail +0.89R; Gabe's 278 same-day cycles −$8.3k at 19% win). Exiting before the stop = the intraday-execution problem: the close entry beats every intraday entry (t to −3.4) |
| 00:13:52 | IREN: sold at ~45 with **no sell signal**, then it flagged 50→42 and ran to the 70s. "Arguably my worst trade because I lost the most in potential gains" | ✅ **Agrees.** Profit-lock study: trims −0.25…−0.33R; "extended → tighten" **INVERTED** (−0.19R, t −2.8; 10-EMA −0.47R, t −4.8). Qullamaggie review: "overriding the trail loses ¾ of the time". The 20-EMA close trail keeps power moves (+7.1R in the 8-week test). The rule he broke is the rule our data supports |
| 00:14:45 | Shorts rarely. 99%+ of his gains are from longs, "the math… hard to make very large gains on the short side" | ✅ **Agrees.** Short-selectable universe: **0 of 10 cells**; weak names still drift up in absolute terms |
| 00:17:32 | Top-down: watching fiber optics (LITE, COHR, CIEN), memory (SNDK, MU, WDC), GOOG/AVGO, biotech as potential leaders | ⚠ **Group-level leadership is INVERTED here.** Industry rotation: bottom-3 sectors beat top-3 (t 2.6). Multi-month group moves are measurable but not front-runnable |
| 00:18:20 | ⭐ **Breadth timing: "% of stocks above the 5-day MA. When that gets above 80 you're likely going to get a pullback."** It was >90 at the recording, so he's waiting for a pullback before taking positions | **UNTESTED, and the only new mechanical claim in either USIC video.** Neighbours: (1) breakout-activity gate (2026-09-22): the 5-session breakout-count percentile sorts the *other way* (Q5 +0.86R vs Q1 +0.06R, t 2.59, PARKED, fails Šidák), i.e. busy tapes pay the breakout book more; ⚠ **"breadth above the 20 EMA does nothing (−0.33, t −1.23)"** in the same study. (2) Every trailing-30d breadth rule FAILS 2019–26; weak breadth is a mild BUY. (3) The queued T2108 (%>40d) extreme gate from Bonde is the oversold mirror. Prior: his claim is a short-horizon *timing* claim (defer entry 1–5 sessions), which fits our finding that extension is a TIMING variable (within-date ranking, 2026-09-22). But the activity-gate result points the opposite way. Spec below |
| 00:19:22 | ABVX as buyout target (data-room email error messages). QURE −65% on FDA news. His wife: "you're 60%? that's way too much" | **Anecdote, and a fair warning about binaries.** QURE verified −49% day one, −61% in 3 sessions. No stop or disaster stop survives a −49% gap: our 1-ADR resting stop fires on 4–6% of days but "worst cases identical (multi-day gaps)" (entry study, disaster-stop addendum). **A single-name biotech binary is a sizing decision only.** Precision over recall says don't hold 58% through one |
| 00:10:59 | Expect 7–10 years to become consistently profitable | **Untestable. Agrees in spirit** with the journal power ceiling: n ≈ 1,854 trades needed for t = 3 at a plausible Sharpe-per-trade vs 272 campaigns (§10 lived-experience row) |

## What I would take

1. **His three self-diagnosed leaks are ours, measured the same way:**
   - increasing size after losses (Cameron arm 0b);
   - trading in and out of one range (same-day round trips, Gabe's −$8.3k);
   - cutting a winner with no signal (profit-lock INVERTED).

   That a two-year contest winner names the same three leaks is not evidence. It's a clear, first-person
   framing to use in the journal ("it was the sizing, the trades themselves were fine").
2. **Nothing to adopt as a selector.** The EP-on-the-gap entry is our strongest negative (t −4.70). The
   residual he points at, *which* catalysts (phase-3 biotech readouts), is catalyst-queue #1 and forward-only.
3. **Binary-event concentration is a sizing rule, not a stop rule.** ABVX (+586%) and QURE (−49%) in one book in
   one year is the clearest illustration we have that a stop doesn't bound a gap.
4. **One cheap new test**, the 5-day breadth-thrust deferral, below.

## Not tested, could be

- ⭐ **5-day breadth thrust as an entry-deferral gate on the breakout book** (his 00:18:20 claim).
  - *Signal (strictly prior):* `b5(t)` = share of the liquid panel whose close > its own 5-day SMA at the close
    of t. Thresholds pre-registered: **b5 ≥ 0.80 (primary)** and ≥ 0.90.
  - *Universe / trades:* the precision-tier house breakouts already in `breakout_activity_gate_2026-09-22.csv`
    (1,996 trades, 2019-10 → 2026-09), close entry, 20-EMA close trail, R vs the day-low stop, cap 20.
  - *Arms:* **A** enter at the breakout close on a b5 ≥ 0.80 day. **B** same name, defer to the first close
    within 10 sessions where b5 < 0.60 **and** close ≤ 1 ADR above the breakout level. Abandon otherwise, and
    count abandoned trades at 0R *and* report them separately (the retrace-entry survivorship trap:
    runaways never come back).
  - *Controls:* (1) the paired A-vs-B difference on the same names, which holds the name fixed and moves only
    the clock, the way ORB9 had to be fixed. (2) breakouts on b5 < 0.80 days, ADR-matched by decile, for the
    gate-as-filter reading. (3) A date-level check on equal-weight panel returns +1/+5 sessions after
    b5 ≥ 0.80 vs all days, in ADR units.
  - *Bar:* |t| ≥ 3 date-clustered on the primary, both halves same sign, per-year shown. 2 thresholds × 2
    readings → Šidák k = 4 (|t| ≳ 2.8 for the non-primary cells).
  - *Also report:* the rank correlation of b5 with `cnt5_pct` (the activity gate). If they're highly
    correlated, his claim directly contradicts the PARKED activity result, and one of the two must fail.
  - *Prior:* low-moderate. %>20 EMA did nothing (t −1.23), and the correlated activity count points the other
    way. It's worth running because it is a *timing* claim, which is where our entry evidence says the leak is.
  - *Effort:* **~½ day** (b5 is a one-liner on the liquid panel; the trades and R already exist).
- **Phase-3 biotech readout EPs as a catalyst class** (INSM, ABVX). Catalyst classification needs headline
  labels. Forward-only: LLM-label ≥ 3-ADR gappers' press releases before the close (the KINFO idea), and
  score the biotech-readout class separately. Blocked on the forward log. **Not queued separately.**
- **Leader-at-the-150-day during an index panic** (his PLTR/TSLA analogy). Mostly covered by the capitulation
  scorecard (a date effect) and the queued "stocks that hold up in a weak tape" row. Add a `touch SMA150 within
  0.5 ADR` arm to that row rather than a new test. ~1 hour on top of the ½ day.
