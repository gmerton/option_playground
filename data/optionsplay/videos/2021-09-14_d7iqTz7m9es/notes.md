# OptionsPlay: "Index Options Strategies Backtested... Here's What We Found!" (Tony Zhang, 2021-09-14, 7 min)

_Reviewed 2026-09-24. A 7-minute trailer for a gated backtest report (trade.optionsplay.com/NDXbacktesting, not
reviewed here). Six "insights" read off 210+ backtests, with no method, no fills, no costs and no statistic._

## Verdict: 1.5 / 5

One thing here is right, and it is worth saying: **he benchmarks against the index's own drift.** "It's not good
enough that an indicator wins more than 50% of the time" when NDX is up 63.8% of 30-day windows (00:52–01:28). Most
creators never do that.

Everything after it is best-of-many with the method withheld:

- 210 option backtests × 4 strategies × "various expirations and strike prices", and the "optimal settings" are
  reported from the same 7 years with no hold-out.
- Returns are called "highest" or "lowest" but never given as a number.
- Fills, costs, exits and the entry trigger for the option trades are never stated.
- The two findings we can check (RSI-30 on the index, and put credit spreads as the best index structure) hold only
  in a narrower form than claimed.

**What was backtested, exactly (as far as the video says):**

| | backtest 1: technical indicators | backtest 2: option strategies |
|---|---|---|
| Underlying | NDX and SPX | NDX and SPX |
| Period | "21 years" (≈ 2000–2021) | "the last 7 years" (≈ 2014–2021) |
| What | **buy** signals on indicators (RSI crossing 30, SMA vs EMA, 100/200 EMA named). Forward index return over 7/14/21/30/45 days | "210 backtests": long calls (OTM and ITM), short puts, long debit verticals, short put credit verticals, "various expirations and strike prices" |
| Benchmark | 1,000 random dates: NDX 30d **+106 bp, up 63.8%**. SPX **+74 bp, up 65%** | none stated. Strategies are ranked against each other |
| Entry trigger | the indicator | **not stated.** "Armed with this data… we then tested" implies the signals, but it's never said |
| Fills / costs / exits | n/a | **not stated** |
| Metrics shown | win rate, "outperformance" (no number except NDX +15 bp over SPX) | win rate and streaks only; "absolute return" never quantified |

## Claims as spoken

| @ | claim |
|---|---|
| 00:37–01:28 | Benchmark = 1,000 random dates over 21 years: NDX 30d +106 bp, up 63.8%; SPX +74 bp, up 65% |
| 01:44–02:09 | Same indicators: NDX beat SPX by 15 bp, and beat its benchmark by more. 21- and 30-day holds beat the benchmark most |
| 02:09–02:34 | **RSI crossing up through 30 is "by far" the best indicator** on both indices. Rare, but "typically more than double the benchmark" |
| 02:34–02:57 | EMAs beat SMAs on indices, and **100/200-day EMAs beat shorter ones even for short holds**, "likely due to" managers watching them |
| 02:57–03:21 | Even the best indicators had "a surprisingly high number of consecutive false signals" → risk management |
| 03:21–03:48 | 210 backtests on NDX + SPX, 7 years, 4 strategies, to find "optimal settings" |
| 04:12–04:36 | **Buying OTM calls = highest absolute return, highest risk**: 60–65% losers, a 27-trade losing streak, "a few home runs" |
| 04:36–05:01 | Buying ITM calls: slightly lower return, 62% winners, 17-win streak, max 8-loss streak |
| 05:01–05:27 | **Debit call verticals: returns "almost as high" as OTM calls** with far less risk, ~60% win: "best of both worlds" |
| 05:27–05:50 | **Short puts: highest win rate (80–81%), lowest absolute return**, some of the largest drawdowns |
| 05:50–06:14 | **Put credit spreads beat short puts**: higher return, lower drawdown, 77% win, **longest losing streak only 4** |

## Claims vs our ledger

| @ | claim | tag | our evidence |
|---|---|---|---|
| 00:37–01:28 | Benchmark every signal against the index's own drift | **AGREES** (method) | Our rule: always have a control. His random-date benchmark is the right *kind*, but it doesn't hold the confound fixed (a same-VIX or same-trend date would). Exploratory arithmetic, not a test: NDX ≈ 3,700 (2000) → ≈ 15,500 (2021) is ~6.8%/yr geometric. Adding the variance term and ~30-trading-day windows makes +106 bp plausible, so the benchmark numbers look real |
| 02:09–02:34 | RSI crossing 30 is the best index signal, > 2× the benchmark | **PARTIAL · UNDERPOWERED** | `rsi_conditioning_study_2026-09-16.md` §C, index forward returns, de-duplicated events: QQQ RSI ≤ 30, 63d excess **+1.69%, t 0.61 (28 events)**, worst event −29.1%. SPY RSI ≤ 35 & below lower BB, 21d +0.60% t 0.84; QQQ +1.49% t 1.29. Best cut (+ above 200d, 63d): SPY +2.64% t 2.68 on 29 events, and it rests on pre-2010 events. "Mild mean reversion, too small and too few events to trade." The **option** version is just "sell puts when implied vol is high" (§A: RSI on put spreads = a VIX proxy). His signal is the *cross up* through 30, not the level, so it's not an exact replication; the event count would be similar and the power problem the same |
| 02:34–02:57 | EMA > SMA; 100/200 EMA best even for short holds | UNTESTED (not worth it) | No row. Our nearest: SPX bullish-high-IV **+ 200MA** condor is t 2.26 with 51% of trades in one year, NOT CERTIFIED (`multiple_testing_correction_2026-09-22.md`). The "managers watch them" mechanism is asserted, not shown |
| 02:57–03:21 | Even good signals come in long false-signal streaks | **AGREES** | Streaks here are regime clustering, not bad luck (Brandt review: a 19-of-21 losing streak at a 45% win rate, P ≈ 0.0006; TEST_INDEX) |
| 04:12–04:36 | OTM calls: highest return, 60–65% losers, 27-loss streak | UNTESTED as stated · consistent | On the index over 2014–21 (a bull sample), buying calls "wins" by beta. Our call project's benchmark rule exists for exactly this: **always-call +9.47%/trade, but −24.6% in 2022** (`call_strategy_project.md`), "a rule that beats the straddle but not always-call has discovered leverage, not edge". His window has no 2022 |
| 05:01–05:27 | Debit verticals: ~OTM-call returns at ITM-call risk | **MIXED** | Vs delta-matched stock, the 30Δ/15Δ call debit spread leads **+$97/contract, t 2.29**, mostly in down months (capped downside, not beta), but fails the SPY < 200 SMA bar (t 1.25): **not adopted** (`vehicle_benchmark_2026-09-22.csv`). As a replacement for an outright long option on an event, the second leg's friction costs **−27.1pp, t −5.51** (TEST_INDEX, event spread). Which one applies depends on fills he doesn't state |
| 05:27–06:14 | Put credit spreads beat short puts; 77% win; max 4 losses in a row | **PARTIAL (index, conditional) · CONTRADICTED (unconditional, after costs)** | Only the **bearish-high-IV** cell certifies: SPY bull put t 6.07, SPX condor t 5.21, the same stress episodes and so **one bet** (`tierab_significance_2026-09-22.csv`). QQQ bullish-low-IV is −4.8% month-weighted, t −0.87. The in-book 20-ETF 45-DTE bull-put roster **fails after costs**: hold −1.37%, 50% take −2.78% net, even though gross is +3.99/+6.28% (`putspread_exit_capital_time_2026-09-24.md` §1, §5). "Win rate 77% vs 80%" says nothing: win rate ≠ edge (premium-to-width: the win rate FALLS while net ROC rises). A 4-trade max losing streak over ~7 years is ≈ 1–2 stress episodes (2018-Q4, 2020-03), not a risk estimate |
| 03:21–03:48 | "Optimal settings" from 210 backtests | **METHOD FLAW** | Best-of-210 on one 7-year window, no hold-out and no multiple-testing charge. At our Šidák standard (M ≈ 210), the per-cell bar is ≈ \|t\| 3.7 and no t was reported |

## Not tested, could be

Nothing here is new. RSI-at-30 on the index is answered (§C, underpowered); index put spreads by regime are answered
(Tier A/B certification); vehicle choice vs delta-matched stock is answered (NOT ADOPTED). The report behind the
link might state fills and exits. If it ever did, the only thing worth checking is whether their "optimal" index
put-spread settings fall inside our certified bearish-high-IV cell or outside it. That's a read, not a test.
**No spec.**
