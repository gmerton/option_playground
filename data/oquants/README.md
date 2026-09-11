# Option Quants (oquants.com) — knowledge base

Paid platform (Gabe's subscription) from the founder of the **Volatility Vibes** YouTube channel.
Focus: harvesting volatility risk premia (VRP, earnings, skew, forward vol) with systematic,
backtested rules plus a screener/dashboard stack. Ingested 2026-09-10 from the **Posts** nav.

⚠ The posts are paid, copyrighted content. This folder holds **condensed notes, rules and our
cross-checks only**, never copies of the posts. Public YouTube companion videos are stored as
auto-caption transcripts (same practice as the other creator KBs).

## Layout
```
README.md              this file
STRATEGIES.md          one table: every strategy, its signal/structure/sizing/exit, claimed evidence,
                       how it relates to OUR studies, and what to test first
posts/<slug>.md        one file per Posts-nav entry (7): thesis, rules, claimed evidence, cross-check
videos/<date>_<id>/    transcript.txt + meta.json for the public companion videos (5)
```

## Posts-nav inventory (7, all ingested)
| Post | Date | Content | Companion video |
|---|---|---|---|
| VRP Strategy | 2025-06-02 | long written guide + video | `MAQBCz9ChkY` (transcribed) |
| Earnings Strategy | 2025-06-06 | long written guide + video | `oW6MHjzxHpU` (transcribed) |
| Momentum-Skew Strategy | 2025-09-17 | long written guide + video | `6I5a3QQX4y0` (transcribed) |
| Forward Factors Strategy | 2025-10-26 | long written guide + video | `6ao3uXE5KhU` (transcribed) |
| Livestream Aug 13, 2025 | 2025-08-15 | blurb + members-only video | none public; ⚠ no captions on the oquants player |
| Site Walkthrough | 2025-06-06 | blurb + members-only video | none public; ⚠ no captions |
| Livestream Jun 13, 2025 | 2025-06-25 | blurb + members-only video | none public; ⚠ no captions |

Also transcribed (not a post, but the same author's rules for the site's "pre-earnings long vol"
Play): `0YfQpYhMNH0`. The three members-only videos are hosted on Mux with only cue/chapter
tracks, so they would need an audio pull + transcription to process (not done; needs Gabe's OK).

## Site tools the posts rely on
Screener (VRP ETF scanner, Momentum-Skew top plays, Forward-Factor screener), Earnings Calendar +
Earnings Dashboard (implied vs realized move history, straddle backtests), Volatility Dashboard
(VRP chart, skew z-score, FF time series, term structure), Relative Value Dashboard (IV/RV vs SPY
or a peer), Calculators (forward vol / FF max-debit), Research Workspace (signal regressions,
model builder with train/test split). Signal definitions: see memory note on their
"Flat Fwd Ratio" (≠ our `fvr_put_30_90`).

## Initial verdict (skeptic default, like the other creator KBs)
**Preliminary 3.5/5 — the most rigorous creator material ingested so far, still vendor-reported.**
Good: every edge is framed as a risk premium with a reason it persists, tested with costs,
slippage and capacity caps, a held-out test set or walk-forward, deciles checked for monotonicity,
fractional-Kelly sizing, and a "falsify, then exit on falsification" trade-management rule.
Weak: all numbers are the vendor's own; headline returns (27% CAGR, "$10k to $1M") come from Kelly
and Monte Carlo framing; the platform is the product being sold. Replicate before trading any of it.
