# TraderLion — Setup Knowledge Base

Archive of the **TraderLion** YouTube channel: interviews and case-study sessions with
momentum/growth traders, mostly in the O'Neil → Minervini lineage (VCP, Stage 2, leadership RS).

Same skeptic-default convention as `data/theta_profits/` and `data/options_with_ryan/`: the unit
of value is the **setup**, and the deliverable is an **objective** write-up of its risk/reward.

## Prime directive: skepticism — with a channel-specific twist

TraderLion guests are usually **educators selling a service** (private-access platforms, workshops,
alert products) rather than anonymous retail traders. That changes the failure mode:

> **The methodology is often genuinely sound — it's the EVIDENCE and the DIFFERENTIATION that are
> the problem.** These are real practitioners teaching a real, century-old momentum framework. But
> the case studies are winners-only, the returns are unaudited, and the parts presented as the edge
> are frequently **proprietary indicators you can only get by subscribing**. Separate the public,
> testable mechanics from the black box and the marketing.

Red flags to call out when present:
- **Winners-only case studies.** Near-universal on this channel. Note when losers are discussed
  only in the abstract ("all our losers look the same").
- **Headline dollar/return figures with no denominator** — no starting capital, no CAGR, no
  drawdown, no time-weighted return, no audit.
- **US Investing Championship citations.** Small self-selected accounts, marketing collateral;
  a real result but not evidence a method generalizes to a normal book.
- **Proprietary indicators as the mechanism** (RS ratings, custom "behavior analytics", extension
  alerts). If the rule can't be reconstructed from public data, it can't be tested — say so.
- **Mid-roll sponsor reads** for the platform being demonstrated. Note the commercial relationship.
- **Unfalsifiable joints:** "violations of the rules" where the rules aren't enumerated; "the
  market tells us what to trade."

**But don't over-correct.** The core O'Neil/Minervini framework is the same one this repo already
implements (`run_minervini_scan.py`, the breakout monitor, the scorecard). Where a guest states a
mechanical rule the repo can test, that is a genuine research lead — score it on the merits.

## Layout

```
README.md                  This file — convention + skeptic mandate.
SETUPS.md                  Index / leaderboard: setup · trader · conviction · risk · tested? · verdict.
setups/<slug>.md           One objective write-up per setup (the deliverable).
videos/interviews/<date>_<id>/   transcript.txt · meta.json · notes.md
backtests/<slug>/          (created on demand) test scripts + results.
```

## Adding a video

```bash
.venv/bin/python3 add_luk_video.py <url> --kb data/traderlion --type interviews
```
(the Luk script is generic — `--kb` retargets it; requires `yt-dlp` in the venv)

⚠ Auto-captions **mis-transcribe tickers and numbers constantly** — verify every ticker and every
dollar figure against the chart discussion before quoting it. Observed in this KB: "DCP" for VCP,
"three-quarters of a billion" for three-quarters of a *million*, "Mark Mervini/Menervini/Manini"
for Minervini, "DFW" for the Deepvue platform, "MoniLert" and "Iron/IREN" uncertain.

## Per-setup write-up structure

1. **Verdict box** — one line, conviction (0–5), risk (1–10), tested? (no/partial/yes).
2. **Who / what's being sold** — the commercial context, stated up front.
3. **Mechanics** — precise enough to backtest.
4. **Claimed edge & returns** — their numbers, quoted, with timestamps.
5. **Objective assessment** — red flags, real risks, what's unverifiable.
6. **What's genuinely sound** — the legitimate core.
7. **Testability** — EOD-testable now / needs intraday / proprietary-untestable.
8. **Overlap with the existing book** — what the repo already does, and what's actually new.
