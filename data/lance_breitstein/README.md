# Lance Breitstein — Trading Knowledge Base

Channel: [`@TheOneLanceB`](https://www.youtube.com/@TheOneLanceB) — 132 videos, manifest in
`channel_videos.txt`.

Professional prop trader (ex-Bright Trading / SMB lineage), **intraday**, primarily
catalyst-driven momentum in parabolic small caps and high-attention names. Public output is
heavily weighted toward *process*: playbook construction, trade review, execution quality,
risk sizing, and performance psychology.

## ⚠ Why this KB exists, and why it is different from the others

The other creator KBs answer "does this setup work?" This one exists to answer a **specific
open question** the repo has already isolated and cannot currently resolve:

> `carter_mastering_the_trade/backtests/risk_architecture/HOW_THEY_DO_IT.md` found that the only
> mechanism large enough to explain the gap between a simulated ~11% CAGR and the returns real
> momentum traders post is the **sizing lever**: position = risk% ÷ stop%. A 1.5% stop buys a 20%
> position where a 9.2% ATR stop buys 3.3% — same risk, ~6× the account impact. On daily-bar
> entries a 1.5% stop is hit **91%** of the time, which destroys it. The whole thesis rests on
> whether **intraday entry location** decouples stop *tightness* from stop *fragility*.
>
> **Breitstein is the most credible public source on exactly that skill.** He is an intraday
> trader whose stated edge is execution quality, not setup discovery.

**⚠ Corrected 2026-07-26 (Gabe):** an earlier draft of this file said execution material
*outranks* setup material. That was wrong. **Setups and execution are co-equal focuses here.**
Two reasons the setups matter in their own right:

1. The named setups are the only part that can be **tested against data already on disk** — the
   execution question is blocked on minute bars that don't exist yet. Setups keep the KB
   productive in the meantime.
2. `HOW_THEY_DO_IT.md` found the sizing lever is only available *downstream of* a qualifying
   setup. Precision without a setup worth applying it to earns nothing — they are complements,
   which is exactly the finding that killed the "risk architecture creates edge" hypothesis.

So: capture both. Where a video gives a setup, write up the setup. Where it gives entry
location, stop placement or sizing, write that up too — and note when one video supplies both,
because a setup *with* its invalidation specified is worth more than either half.

Note also that he is a genuine counterexample to the intraday base rates — most retail day
trading loses money, and he is one of the few with an identifiable mechanism (a flow niche where
he can name the counterparty: retail chasing catalyst-driven spikes). Do not let the base rate
dismiss him, and do not let him dismiss the base rate.

## Prime directive: skepticism, plus one structural caveat

Standard house rule — **separate the mechanics from the marketing**, conviction LOW until
independently tested. Additional caveats specific to this source:

- **He sells a course** (`Magnum Opus`). Treat any claim that doubles as a sales argument with
  the usual discount, and note it explicitly in the write-up when present.
- **⚠ Prop infrastructure is part of his edge and is NOT transferable.** Locates, borrow, fee
  structure, rebates, execution routing, capital, and risk oversight. Where a technique depends
  on any of these, say so — this is the most likely way to mistake his edge for a method.
- **Attention/flow niches decay fastest of anything in this repo.** Parabolic small-cap
  behaviour in 2021 is not 2026. Date every claim.
- Much of the corpus is psychology/process, which is **valuable but largely unfalsifiable**.
  File it honestly as such rather than pretending it can be backtested.

## Testability triage

Every principle gets sorted into one of:

- **Testable on daily bars** — rare here; most of his material is finer-grained than EOD.
- **Needs intraday data** — the majority, and the reason this KB matters. Tag these with the
  data that would settle them (1-min bars, tape, level 2) so they can be batched if minute data
  is ever purchased.
- **Process / unfalsifiable** — review routines, journaling, sizing discipline, psychology.
  Record faithfully, do not fake a backtest.

## Layout

```
README.md                  This file — convention, the open question, the skeptic mandate.
PRINCIPLES.md              Index / leaderboard: principle · type · conviction · testability · verdict.
principles/<slug>.md       One objective write-up per named principle (the deliverable).
principles/_TEMPLATE.md    Copy this to start one.
notes/<slug>.md            Raw per-video notes (input, not deliverable).
notes/_TEMPLATE.md         Copy this to start one.
channel_videos.txt         Full channel manifest (id\ttitle), 132 videos. GENERATED via yt-dlp.
videos/<type>/<YYYY-MM-DD>_<videoId>/
    transcript.txt  meta.json  notes.md
```

Video types in use: `talks` (solo/educational), `interviews`, `trade_reviews`.

## Ingesting a video

The Luk ingest script is already KB-agnostic via `--kb`:

```bash
.venv/bin/python3 add_luk_video.py <url-or-id> --kb data/lance_breitstein --type talks
```

That scaffolds `videos/<type>/<date>_<id>/` with a deduped timestamped transcript, `meta.json`,
and a `notes.md` stub. ⚠ `build_luk_extracts.py` and `build_luk_inventory.py` are still
hard-coded to `data/martin_luk` (module-level `KB` constant) — they would need generalizing
before the aggregate pipeline works here. Not required to start taking notes.

## Highest-value videos to ingest first

Ordered by relevance to the open question above, not by view count:

1. **The Anchored VWAP Edge Most Traders Never Discover** (`D2P-0xh6aEM`) — AVWAP is precisely
   an intraday entry-location tool, and Luk independently cites AVWAP for stop placement.
   **This is the single most on-point video on the channel.**
2. **What Is a Trading Playbook? (and Why YOU Need One)** (`bKvEfCGJS4g`) — his framework for
   defining a setup precisely enough to size it.
3. **How a Pro Trader Thinks — $MULN Layup Trades Dissected** (`-x1nbxasFcE`) — a worked
   execution example rather than a pattern claim.
4. **How to Do Trade Writeups Like a Pro** (`TexislSXpjs`) — the review loop; connects to the
   Luk principle "study your trades every weekend."
5. **Can YOU Spot the 4 KEY Days!?** (`vGqaqTUxMG4`) — setup identification.
6. **Best Practices to Navigate High-Volatility Markets** (`mjfONTBf6M0`) — regime handling,
   testable against the regime results already in the repo.
7. **MADAZ MARTINGALER!? Dissecting a 7-Figure Trader's Data** (`TzLtTTcDp9M`) — he analyses
   someone else's real trade data; useful for how he reasons about evidence.

## Relationship to the rest of the repo

- **The open question** lives in
  [`data/carter_mastering_the_trade/backtests/risk_architecture/HOW_THEY_DO_IT.md`](../carter_mastering_the_trade/backtests/risk_architecture/HOW_THEY_DO_IT.md).
- **Martin Luk** ([`data/martin_luk/`](../martin_luk/)) is the swing-side counterpart; where the
  two agree on entry location or sizing, that agreement is worth more than either alone. Where
  they conflict, note it — don't merge.
- Anything that graduates to live goes to `data/studies/` and the allocation framework, per the
  house rule. This directory is research.
