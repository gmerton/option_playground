# tastylive (Julia Spina) — "We Studied 539 Zero-DTE Iron Condors. The PDT Rule Was Costing Traders $166 a Trade." (2026-06-08, 11 min)

_Reviewed 2026-09-23. A "mini market measures" segment: a retroactive study of 0DTE iron condors managed intraday
(50% profit target / a credit stop) vs held to expiry, framed as what the pattern-day-trader rule cost small accounts.
The slides aren't in the transcript, so the numbers below are the ones spoken on air. Transcript (`en-orig`
auto-captions) in this folder._

## Verdict: 2.5 / 5

Better than most creator content: an actual sample, a **paired** design (the same 539 trades scored under two exit
rules), and tail measures (CVaR, losing streaks) alongside the mean. Two things she says herself are honest and useful:
the study had to be limited to the daily-expiry era, and time-based exits ("close at noon") were left out.

As evidence for "management saves $166 a trade", it's weak:
1. **The strategy's own expectancy is never shown.** We only get managed-minus-held, split by how each trade was
   managed. Nothing says whether either arm made money. Our closest analogue (the 21-DTE rule) first appeared to certify an exit that
   cut a *losing* trade's loss by ~60%; on re-run (FIX-1, 2026-09-24) the exit **cost** return (−$0.52/share vs
   hold, t −2.42) and only cut risk — exactly the managed-minus-held trap.
2. **"$166 saved per winning trade" conditions on the path.** The buckets are defined by which exit fired, and the
   dollar figure only means something next to the credit and the max loss, neither of which is given.
3. **The underlying, the dates, the pricing and the stop level are never stated.** She says "this particular
   underlying", and tastylive backtests are normally at mid with no fees; the description's disclaimer says
   performance is "not presented net of all commissions". The managed arm pays four legs of exit spread, while the
   held arm settles for free.
4. **Halving the standard deviation and cutting CVaR is mechanical for any early exit**, so it isn't evidence of
   edge.
5. **No test statistic.** At ~2 years of daily trades the sample is one regime.

**Replicable on our data? No, not either arm.** `silver.options_daily_v3` is one end-of-day row per contract per
`trade_date`, with no timestamp. A 0DTE contract's only row is its expiry-day close ≈ intrinsic (the MEIC review
counted 4,223 0DTE rows, all at expiry). The entry at the open, the 50% target and the stop are all unobservable.
What *is* on our data is the PDT workaround she mentions: open at the prior close, hold to settlement. That's our
1-day SPY fly / condor study. See below.

## Results / evidence audit

| item | what was said | problem |
|---|---|---|
| Sample | 539 "occurrences"; "$20 wide iron condors, 20 delta short strikes"; "that's all the data we have"; dailies "basically 2023" | ~539 trading days ≈ **2.1 years**, one regime. The underlying is never named ("this particular underlying"); $20 wide suggests SPX. Dates are never given |
| Entry time | not stated | The whole P&L depends on when a 0DTE is opened. It's unknown whether entries were at the open, 09:45 or later |
| Pricing | not stated | tastylive studies are normally at mid, and the disclaimer says results aren't net of all commissions. **The managed arm crosses four spreads at exit, and the held arm settles for free.** Under our cost model (25% of each leg's bid-ask + $0.65/leg/side), that difference is charged only to the managed arm, i.e. against the claim |
| Exits | 50% profit target; "credit stop" (level never stated; "2x loss" is mentioned only as an example of a rule) | We can't tell whether the stop is 1×, 2× or 3× credit. The result depends on it |
| Hit rates | ~70% hit the 50% target, ~28% the stop, ~3% neither | Descriptive. A 20Δ 0DTE condor touching one of two nearby thresholds on 97% of days is what short-dated gamma looks like; it isn't an edge statement |
| "$166 saved per winning trade, $93 per stop-loss trade" | managed minus held, within each exit bucket | ⚠ **Conditional on the path.** Implied total ≈ 0.70 × 166 + 0.28 × 93 ≈ **$142/trade** (my arithmetic, not hers). If quotes were fair, the optional-stopping argument says an exit rule can't change the expected P&L of a zero-edge position. Only the variance-risk premium earned in the time you're out, or a mispricing, can. So a ~$142/trade effect on a ~$2,000-risk condor needs one of three explanations: (a) **held 0DTE condors were losing money in this window**, and exiting early shortens exposure to a losing trade (our 21-DTE mechanism); (b) **noisy mid marks**, where "hitting 50%" or "hitting the stop" is triggered by a stale or wide mid that reverts, which is outcome conditioning on measurement noise; (c) a real intraday reversal pattern. None of these is ruled out, and (a) would mean the headline is "the unmanaged trade loses", not "management earns" |
| SD of P&L down ~50%; CVaR (worst 5%) "dramatically reduced" | managed vs held | **Mechanical.** Any rule that closes a position early truncates its distribution. Our 21-DTE rule cut sd the same way ($9.33 vs $17.09, worst −$291 vs −$617) while **earning less than holding** (−$0.52/share, t −2.42; corrected 2026-09-24, FIX-1 — the old "both arms lost money" was the buggy run). A risk reduction isn't evidence of edge unless the mean is reported with it |
| Losing streaks shorter | managed vs held | Follows from the 50% target turning some would-be losers into small winners. It's the same mechanism as above, not a separate finding |
| No significance test, no per-year split, no control | — | Against our bar (\|t\| ≥ 3, both halves the same sign, a control) nothing here can be scored |

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 01:38 | Before the rule ended (said: June 4), PDT traders "were not able to close their zero DTE positions same day" | **Overstated.** Under PDT, a margin account under $25k was limited to 3 day trades per rolling 5 sessions, not zero. Cash accounts weren't subject to it. The study really compares "managed" vs "never managed", which is a management study with a regulatory headline |
| 01:53 | The workaround: open the day before, manage on expiry day, at the cost of overnight/gap risk | ⭐ **This is the one arm we can price, and we have.** SPY ATM 1-day iron fly, prior close → next-day expiry, real fills on 4 legs: **every day = 0.0% on max risk** (1,942 days). **Positive-gamma days only = +5.8%, t 3.4, both halves, 14/17 yrs (PASS, candidate).** Negative-gamma days = −5.4% (t −3.1). A 16/5Δ 1-day iron condor on positive-gamma days = +1.8% (t 2.4). **The edge is at the money and in the gamma filter, not in the condor** (`gex_spy_ironfly_2026-09-21.md`, `gex_spy_condor_putspread_2026-09-21.md`). The unfiltered 1-day trade she's describing is flat |
| 05:35 | (Host) the overnight trick adds gap risk, "a different trade" | ✅ **Right, and we measured the split.** For SPY the overnight gap is **~half the day's variance** in both gamma regimes. On positive-gamma days the session tends to *reverse* the gap, which helps a fly centred on the prior close. So entering at the open **gives up ~half the edge** along with the noise. The 0DTE-at-the-open variant is logged only as secondary in the paper trade (`gex_spy_ironfly_2026-09-21.md` diagnostic) |
| 02:06, 04:15 | Stop losses matter much more at 0DTE than for longer defined-risk trades | **Untested at 0DTE; contradicted at every tenor we can price.** 20–45 DTE bull puts: "50% take + 2× stop" −4.3%/trade (t −5.4), while the take alone carried the result (`etf_put_spread_exit_rule_2026-09-16.md`, ⚠ source parquet since superseded). Straddle stops: **0 of 20 depth × timing cells beat no stop**, because the exit crossing peaks exactly when you want out. ⚠ The Theta Profits MEIC review claims the opposite for 1-DTE SPX condors ("the edge is the STOP"), but that bracket capped losses *at expiry*, so it never stops out a trade that later recovers. That's optimistic by construction, and its backtest folder is **no longer on disk** (`data/theta_profits/backtests/` has no `tammy_chambless_0dte_ic/`). Don't cite it as evidence |
| 03:00 | 50% of credit is a "very liberal" target at 0DTE; many use 20% | **Untested at 0DTE.** At 45 DTE the 50% take is the half of the managed rule that survives our data. A smaller target means more exits, so more exit spreads, and at mid that cost is invisible |
| 06:05 | Management saves money on both winners and losers | **Not shown as a mean.** See the audit: this is managed-minus-held within path-defined buckets. It needs the arm-level expectancy and the pricing to mean anything. Our paired exit test (21 DTE) found the same shape, better on every risk measure, and **worse on the mean** (A +$0.23, B −$0.29, paired Δ −$0.52, t −2.42; corrected 2026-09-24, FIX-1 from "both negative, Δ +$1.53, t 4.26") |
| 06:45–08:00 | CVaR of the worst 5% and SD cut ~50% even on defined-risk positions | **Mechanical truncation** (see audit). ✅ The point that defined risk doesn't make the tail irrelevant is right. Our naked 1-day SPY straddle's worst day was **−604% of credit**, and that's why we require the fly |
| 09:50 | (Host) the last hour carries the biggest swings; flexibility to manage matters there | **Adjacent data only.** Our GEX momentum test (first-30 → last-30 min on negative-gamma days) is right-signed but **UNDERPOWERED (t 2.0)**. Nothing here tests a time exit |
| 02:55, 08:50 | Closing at noon would help "even more"; this is "conservative" | **Unsupported: it wasn't run.** Calling an omitted rule "conservative" assumes its sign. The one fixed-time exit we have measured (21 DTE) helped on risk only; on return it cost −$0.52/share vs hold (t −2.42, corrected 2026-09-24 FIX-1). So even a time exit is not a return lever, and it's untested at 0DTE |

## What I would take

1. **Nothing to adopt, and no 0DTE condor.** The one short-dated index premium trade that survives our data is the
   **1-day ATM fly entered at the prior close, on positive-gamma days only** (+5.8%, t 3.4). The same trade every
   day is 0.0%, and an OTM condor is weaker than the fly. This video trades the unfiltered, OTM, open-entry version:
   the wrong structure, the wrong entry time, and no filter.
2. **The useful distinction is P&L-conditioned exits vs time-conditioned exits.** Our record: exits that react to P&L
   (stops, re-centres, profit locks) have mostly been costs. The one exit that certified cuts gamma at a fixed time.
   If we ever touch 0DTE, test a **time exit** before any profit target or stop.
3. **Always ask for the arm-level mean.** "Management saves $X" without "and the managed trade makes $Y" is the same
   omission our 21-DTE test caught.

## Not tested, could be

- **Forward 0DTE management log on SPY, riding on the GEX paper trade.** `run_gex_fly_paper.py --open` already logs a
  0DTE fly at 09:40–10:30. Extend it:
  - log a 20Δ / $5-wide SPY 0DTE condor every session at 09:45, from Tradier quotes;
  - poll the four legs every 5 min while `start_alerts.sh` is up;
  - score three arms at bid/ask: hold, 50% target + 2× stop, and close at 12:00 ET.
  - *Effort:* ½–1 day of build. *Results:* ~6 months (~125 sessions) buys a variance/CVaR answer, not a mean
    answer (underpowered for t 3 by design).
  - *Prior:* hold ≈ flat to negative unfiltered (1-day fly every day = 0.0%); the noon exit ≥ the target/stop arm
    once exit spreads are charged.
- **Historical replication** needs minute-level option *quotes* (not trade aggregates) for SPX/SPY 0DTE, 2022–2026,
  e.g. a ThetaData or CBOE DataShop purchase.
  - With them, the spec: all expiry days; entry at 09:45 at the quoted bid/ask; 20Δ shorts, $20 SPX wings; arms =
    hold / 50% target / stop at 1× and 2× credit / noon time exit; house cost model on every traded leg;
    session-clustered paired Δ vs hold; per-year signs.
  - *Effort:* 2–3 days plus the data cost. *Priority:* low. The certified trade isn't 0DTE, and our overnight split
    already says the open entry gives up half the edge.
- **Not possible on what we have:** v3 has no intraday rows. The 1-min cache is underlying-only (SPY/QQQ from
  2026-02-02), and v3 bid/ask ends ~Feb–Mar 2026, so there's essentially no overlap. Modelling intraday option marks
  from the underlying + prior-close IV would be a **mid-model**, which our rules bar from any verdict.
