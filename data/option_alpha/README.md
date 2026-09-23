# Option Alpha KB (Jack Slocum, optionalpha.com)

Option Alpha is an options-automation platform (no-code bots, a GEX chart tool, community bots such as "WiFly"). The
channel's videos are trading diaries and platform demos by its founder. ⚠ **Provenance: the channel sells the platform
that every trade and bot in the videos runs on.** Treat results as marketing until they are audited. Skeptic-default
scoring like every KB here.

Captions: yt-dlp, `en-orig` auto track. `videos/<date>_<id>/` holds `transcript.txt`, `meta.json` and `notes.md`.

| video | date | verdict |
|---|---|---|
| [GEX Day Trading Results ($1K Per Day Goal)](videos/2026-03-16_O2vTwL4R6kI/notes.md) | 2026-03-16 | **2/5.** Honest diary: a losing month and a tilt post-mortem. P&L/day fell $1,194 → $524 → $113 (YTD $681 on $50k, live, ~50 sessions). It is whole-account P&L mixing ≥4 bots, with no n, win rate or cost line. His GEX trades use the **pin/magnet half (NULL for us)**: fade to the biggest-gamma strike with SPX $5 debit spreads, first-Friday pin flies. The half that passed for us (positive gamma → sell 1-day ATM premium) is absent. His unfiltered WiFly 1-DTE fly going flat matches our "same fly every day = 0.0%" |

## Follow-ups

- Intraday GEX-strike reversion (overshoot → return within 60 min, distance-matched mirror control), underlying only.
  Our daily pin test does not cover it. Spec is in the notes. Not queued.
