# Ariel Hernandez — Knowledge Base

Archive of Ariel Hernandez's nightly **watchlist videos** (YouTube channel `Ariel Hernandez`,
UCn8hF9X6MGDtbTBb6w3JUYA; most are **members-only, "RS Insider" tier**) plus any interviews.
Discretionary swing/momentum trader in the O'Neil → Minervini lineage with a heavy intraday
execution layer (VWAP reclaims, opening-range logic, leveraged single-stock ETFs as the vehicle).
Runs a live "desk" on Discord.

Same skeptic-default convention as `data/traderlion/`, `data/theta_profits/`, `data/martin_luk/`:
the unit of value is the **setup or rule**, the deliverable is an objective read of it, and every
nightly call gets scored against what the chart actually did.

## Skeptic mandate — channel-specific

- **Paid tier + Discord desk.** The videos are the funnel for a membership. Calls are cheap to make
  nightly; treat the hit rate as unknown until we score enough of them (see `analysis/`).
- **Headline P&L is unaudited.** The "$100K → $3M" story circulating in interviews has no
  denominator, drawdown, or time-weighted return attached.
- **Leveraged ETFs as the default vehicle** (MSFU, NVDL, a SanDisk 2x). Path-dependent decay and
  wider spreads are never discussed. Our vehicle study (`data/studies/august_2026_vehicle_study.md`)
  is the check on this.
- **Jargon is borrowed, not proprietary:** "620 setup" is Gil Morales's 5-minute 6/20 EMA cross with
  a MACD(6,20) (Virtue of Selfish Investing). Fully public and mechanical, so it is testable; it is
  also the same object as the 5-minute pullback triggers in Luk's KB and our `fade_watch.py`.
- **Winners-only recall:** in this video the only losers mentioned are a flat HOOD and a SanDisk
  ETF sold on a weak close. Keep a running tally of stated positions and how they resolved.

**Don't over-correct.** His core rules in the first video are conservative, explicit, and overlap
almost one-for-one with the August lens (`data/studies/august_2026_luk_tito_lens.md`): no gap-up
buys into a declining 50-day, no chasing a third up day into supply, an extension ceiling of ~4 ATR
above the 50-day, pullback entries with a low to risk off, group participation as a sizing input.
Those are testable and several are already implemented here (the VWAP-reclaim entry is
`ibkr_bot/fade_watch.py`).

## Layout

```
README.md                          This file.
philosophy/principles.md           Rules extracted so far, each cited <video_dir>@<mm:ss>, with a
                                   support tally. Hand-maintained (small corpus); regenerate later
                                   with the Luk tooling if the corpus grows.
videos/<type>/<date>_<id>/         type = watchlists (default) | interviews | livestreams
    transcript.txt                 Auto-captions, lightly paragraphed by timestamp.
    meta.json                      ids, title, dates, duration, access tier, capture method, tickers.
    notes.md                       Ticker resolution, stated positions, unresolved jargon.
analysis/<date>_<topic>.md         Per-video scoring: his call per ticker vs our lens read, and the
                                   follow-up (what the chart did). This is where the hit-rate accrues.
```

Video folder date = the evening the video was recorded/uploaded (his "9/8 watchlist" is filed
under 2026-09-07). `for_session` in meta.json carries the session it was made for.

## Capturing a members-only video

`add_luk_video.py <url> --kb data/ariel_hernandez --type watchlists` works for public videos
(yt-dlp auto-captions). It fails on members-only videos: yt-dlp gets "available to this channel's
members", and the caption `baseUrl` returns an empty body without the player's proof-of-origin
token. Recipe that works, from a Chrome session logged in as the member:

1. Open the video in Chrome (Claude-in-Chrome extension, or by hand).
2. In the page context, monkey-patch `fetch` and `XMLHttpRequest` to capture any response whose
   URL contains `timedtext`, then click the CC button so the player requests its own track.
3. Parse the captured json3 body (`events[].segs[].utf8`, `tStartMs`) into `[mm:ss] text` lines.
4. Paste into `transcript.txt`; fill `meta.json` from `ytInitialPlayerResponse.videoDetails` and
   `microformat.playerMicroformatRenderer` (title, uploadDate, lengthSeconds).

Do not use `yt-dlp --cookies-from-browser` for this: it triggers a macOS keychain prompt and copies
the browser cookie jar.

## Ticker resolution (auto-caption artifacts)

Palunteer → PLTR · Marll → MRVL · Octa → OKTA · SNX / SNXX → SanDisk leveraged ETF (exact symbol
unconfirmed) · MSFU → MSFT 2x · NVDL → NVDA 2x · poet → POET · "620 setup" → 5-min 6/20 EMA cross (Morales).
