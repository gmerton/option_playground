# Bear-Market Wheel — Fed-based regime timing + VIX-gated strategy switch

> **Verdict:** The strategy overlay (VIX-gated delta reduction + bear call spreads) is coherent and testable,
> but the load-bearing claim — "bear markets are easily predicted via the Fed" — fails a basic calendar check
> on his own 2022 example. Regime *response* rules: maybe. Regime *prediction*: no.
> **Conviction 1.5/5 · Risk 5/10 · Tested: no**
> Source: `videos/wheel/2024-11-27_lHMYnBi5sZY` ("The Wheel for Bear Markets and Recessions").

## Mechanics (his stated 2022 playbook)

Once "the Fed announces hikes," flip the income book bearish:
1. **Sell 20Δ CSPs only when VIX > 25** — assignments become long-term holds ("double/triple on the rebound").
2. **Sell 30Δ/15Δ bear call spreads, 30 DTE, when VIX < 23** (low-fear bounces within the downtrend), close at 50% PT.
3. **Covered calls 15–30 DTE when VIX < 23** on assigned/held shares.
4. Shore up cash at the top when the Fed turns hawkish; re-deploy risk-free (T-bills ~5%) while waiting.

Backtests shown (tastytrade tool, SPY, *inside the labeled 2022 bear window*):
bear call spread 30Δ/15Δ 30DTE = **+63% RoC** (74 trades, avg +$98) · long 70Δ put 90 DTE, 50% PT = **+142% RoC** ·
15Δ 30DTE short puts 50% PT = +6.8% RoC. Buy-and-hold comparison shown as negative.

## The calendar problem (checked)

His narrative: first hikes June 2022 = "first tell"; Powell's Dec 14, 2022 hawkish presser → "December,
January — that's when the bear market started." **Reality: the S&P peaked Jan 3, 2022; the first hike was
March 2022; by Dec 2022 the October low was already in.** The bear market *ended* within weeks of the point
his timeline has it *starting*. The 2008 and dot-com retellings are looser but directionally similar
hindsight narratives. The predictive framework demonstrably misfires on the one episode he traded — and his
forward call in the video ("next bear ~2027, I'll announce it") is the same unfalsifiable pattern.

> **Credibility addendum (2026-07-14, from the 2025-H1 recap audit):** in `recaps/2025-07-18_ttN5dCDDE5c` he
> retells the same 2022 episode with the market rolling over on Powell's **November 2021** hike signal —
> roughly correct, and incompatible with this video's "bear started Dec 2022/Jan" telling. Two versions of
> the same "I predicted it" story. See `recap_audit_2025H1.md`.

## Other red flags

- **Backtest conditioning:** every test runs inside a window labeled "bear market 2022" — the regime is known
  in hindsight. A strategy that's short calls "during the bear" isn't evidence you can *time entry into* it.
- RoC on spread margin ≠ portfolio return; the +63% used $11.5K of capital, not the book.
- "Made it through 2022 unscathed and very profitable" — unverifiable; he separately admits losing six
  figures in the 2020 crash (i.e., the system postdates the drawdown that motivated it).
- Fed-watching macro section (money printing, house prices) is narrative filler, not mechanics.

## Salvageable for us

- The **response** rules rhyme with our own regime gates (50MA×VIX in TLT/XLF/SPY playbooks): reduce put
  delta when vol is high, sell call-side into low-vol bounces beneath a downtrend. We already do this better,
  with tested gates and without pretending to predict the regime.
- His VIX 23/25 thresholds are a testable alternative gate vs our 50MA×VIX regime definition.

## Testability

**High.** All legs are EOD-clean on SPY: 20Δ CSP gated VIX>25, 30/15Δ BCS gated VIX<23, vs our existing
regime engine (`run_tlt_regime_switch.py` family) over 2018–2025 including *non*-bear years — the test his
backtests carefully avoid (a bear-only strategy that can't tell you when the bear starts loses its edge to
whipsaw in 2023-style recoveries).
