# Golden One-Day Options Trade (0/1-DTE long strangle at the expected move) — Jeff Tompkins

Source: `2026-09-13_l5LqokEA0A4` — "Inside a 0DTE Options Strategy Targeting 50–100% in 24 Hours"
([watch](https://www.youtube.com/watch?v=l5LqokEA0A4)). Guest: Jeff Tompkins, Altos Trading (education + live trade
room) / Altos Capital. Host: John. OptionStrat affiliate read mid-video.

## Verdict

> **Conviction: 1 / 5 · Risk: 3 / 10 per trade (defined debit) but 8 / 10 as a program (negative expectancy) · Tested: YES (EOD floor, SPY 2018–2026)**
>
> A long OTM strangle at ± the expected move on SPY, 0DTE from the open or 1DTE from the prior close, exited at
> +50–100% intraday, no stop. The claim is 75–80% wins with winners and losers both in the 50–100% range, i.e. an
> expectancy of roughly +45% of the debit per trade. The EOD-testable version (buy at the close for the next session,
> settle at intrinsic) is **−26% of the debit per trade, 22% win, median −100%, every year 2018–2026 negative**; his
> IV-percentile-below-35 filter makes it *worse* (−37%, 19% win) because cheap options are cheap for a reason. Realized
> next-day moves average 0.90× the implied move: the variance risk premium is exactly what a long strangle pays. The
> intraday profit-take is the entire claimed edge and cannot be tested on daily data, but it would have to turn a −26%
> floor into +45%. Twenty of the last twenty-five trades, undated and self-reported from a paid trade room, is not
> evidence for that. The "adjust a loser into an iron fly" step adds undefined short-gamma risk to a trade sold as
> defined-risk.

## Mechanics
- Buy an OTM call and an OTM put on the same 0DTE (entered near the cash open) or 1DTE (entered near the prior close)
  expiry; strikes = spot ± expected move (broker's number, or the ATM straddle price). SPY / QQQ / XSP / ES options.
- Keep put and call premium roughly equal (skew); debit cap ~$1.15 on SPY, $1.30–1.40 on QQQ; skip if pricier.
- Filters: IV percentile < ~35 and rising; daily "range expansion" (widening candle ranges); never into an earnings
  print; VIX rising during the session = be greedier on the target.
- Exit: +50% (elevated / flat vol) to +100% (low, rising vol) of the debit, separate limit orders per side; optionally
  trail the winning side. No stop: size the position for a total loss. Loser adjustments: sell the ATM straddle
  (iron fly) or a one-strike-out strangle (iron condor) against the position when the credit ≈ the original debit.
- Claimed record: 20 / 25 recent, 75–80% over "years", ±50–100% per trade either way.

## EOD floor test (2026-09-16, `data/cache/golden_strangle_spy_1dte.parquet`)
SPY, every session 2018-01 → 2026-02 with a next-session expiry (n = 1,519), strangle at close ± ATM straddle bought at
mid + 25% of the spread per leg + commissions, settled at intrinsic on the next close (his 1DTE variant, held).

| | all | VIX 1y pct < 20 | 20–35 | 35–50 | 50–75 | > 75 |
|---|---|---|---|---|---|---|
| n | 1,519 | 404 | 202 | 160 | 308 | 297 |
| mean ROC on debit | **−26%** | −44% | −23% | −28% | −23% | −19% |
| win (P&L > 0) | 22% | 18% | 23% | 18% | 22% | 27% |

Finishes in the money 32% of the time; wins 22% after the debit; median −100%; p95 +314%. By year: 2018 −2, 2019 −40,
2020 −28, 2021 −47, 2022 −6, 2023 −28, 2024 −24, 2025 −27. Cost averages $0.95 (0.23% of spot); realized |move| /
implied move = 0.90. The floor is the same sign in every year and every IV bucket, and his own filter selects the
worst bucket.

## What would have to be true
The intraday exit must convert most of the 78% of losing sessions into +50–100% winners. A 0DTE OTM option can double
on a modest move toward it early in the session, so some conversions are real -- but the same gamma cuts the other
way on the reversal, and over 1,500 sessions the close-to-close premium is priced. Testing it needs intraday option
quotes (IBKR minute bid/ask, `project_intraday_option_quotes`), not EOD data; not queued -- the floor is too far below
zero and the claim too thin to justify the pull.

## Relation to the rest of the KB
The mirror image of the channel's 0DTE *sellers* (and of Boomer Dan's burrito fly): where they collect the 0DTE
variance premium and carry the gamma, he pays it and hopes to sell the spike. The "transform a loser into an iron fly"
adjustment is the DC Time Machine move in reverse. Same sales structure (live room, education company).
