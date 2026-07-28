# Theta Profits — Strategy Knowledge Base

An archive of the **Theta Profits** YouTube channel, which interviews different traders
about their options strategies. Unlike `data/martin_luk/` (one trader's philosophy), here
each video is a **different trader pitching a different strategy** — so the unit of value
is the **strategy**, and the deliverable is an **objective** write-up of its risk/reward.

## Prime directive: skepticism

> **Interviewees oversell.** Every guest claims their strategy is safe, simple, and highly
> profitable. The job is NOT to relay the pitch — it's to **separate the mechanics from the
> marketing**, name the real risks the guest glosses over, and flag claims that are
> unverifiable. Default conviction is LOW until a strategy is independently tested. That
> said — some may be diamonds; stay open, just demand evidence.

Red-flag checklist (call these out explicitly when present):
- "Risk-free / can't lose / bulletproof / guaranteed" — almost always false for an options
  structure with any expiration/gamma/pin risk.
- **No separable track record** — "I combine it with my other trades so I can't untangle the
  results." = no falsifiable evidence.
- **Admitted no edge** on the part the strategy depends on (e.g. direction) but a claimed
  edge somewhere fuzzy (adjustments, "feel").
- **Winners-only examples**, favorable payoff snapshots, no losing trade carried to the end.
- **Costs hand-waved** — adjustments/commissions/slippage that quietly eat a thin edge.
- "Beginner version vs. how I really trade it" — the shown strategy isn't the real one.

## Layout

```
README.md                  This file — convention + skeptic mandate.
STRATEGIES.md              Index / leaderboard: strategy · trader · conviction · risk · tested? · verdict.
strategies/<slug>.md       One objective write-up per strategy (the deliverable).
videos/interviews/<date>_<id>/   transcript.txt · meta.json · notes.md  (one per interview).
backtests/<slug>/          (created on demand) test scripts + results when a strategy is evaluated.
```

## Per-strategy write-up structure (`strategies/<slug>.md`)

1. **Verdict box** — one-line, conviction (0–5), risk (1–10), tested? (no/partial/yes).
2. **Mechanics** — precise enough to backtest (underlying, structure, widths, DTE, entry,
   profit target, stop, adjustments).
3. **Claimed edge & returns** — their numbers, quoted, with timestamps.
4. **Objective assessment** — red flags / oversell, the real risks, what's unverifiable.
5. **What's genuinely sound** — the legitimate core, if any (the "diamond" potential).
6. **Backtestability** — what's mechanically testable vs. discretionary; data needed; caveats.
7. **Open questions / next step.**

Cite the source as `<date>_<video_id>@<mm:ss>` (the video folder name).

## Workflow
1. Ingest: `.venv/bin/python3 add_luk_video.py <url> --kb data/theta_profits --type interviews`
2. Summarize the strategy into `strategies/<slug>.md` (objective, per the structure above);
   add a row to `STRATEGIES.md`.
3. **On Gabe's command only**, evaluate (e.g. backtest the mechanical core) under
   `backtests/<slug>/`, and update the verdict with the evidence.
