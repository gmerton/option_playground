# Brief: trade log from Ariel Hernandez's daily recap transcripts (v2)

You are building a trade log for a swing trader, Ariel Hernandez, from the auto-caption transcripts of his daily
YouTube market videos. For each video in your batch, extract every statement about HIS OWN positions and trades and
write one JSON file per video. Accuracy matters more than volume: the log will be scored against prices later, so a
row that is not really his trade does damage, and a wrong date does too.

## Input
Your batch file is a JSON list of videos: `dir` (absolute folder), `dirname`, `video_id`, `upload_date`, `title`,
`words`. Each folder has `transcript.txt` with lines like `[mm:ss] text`. Read each transcript IN FULL. Treat each
video on its own: never carry a fact (a direction, a date, a ticker) from one video into another video's rows.

## What to log
- Only what he says HE did or holds: bought, sold, trimmed, added, got stopped out, is holding ("one that I own",
  "my position"), shorted, covered, re-bought.
- Do NOT log: watchlist ideas, alert levels, "I'd like to buy if...", hypotheticals, market commentary, names he walks
  through without saying he owns them, or anything a viewer did.
- Second-person narration ("you get the entry... it stops you out") is often how he tells his own trade. Log it only
  when an adjacent first-person sentence anchors it as his, with confidence "inferred". A bare "if you own X" is not a
  row.
- One row per distinct action per ticker per video ("bought yesterday" and "trimmed some today" are two rows).
- "Tried X with no luck", "didn't keep it", "didn't close well enough to keep", "it doesn't work": that is his normal
  way of reporting a failed attempt. Log an `entry` row AND an `exit` row (or `stopped_out` if he says stopped), both
  confidence "stated", when he says in the first person that he tried or bought it. If he only says it "doesn't work"
  without saying he was in it, no rows.
- `hold` row: one per ticker per video, only when he says he still holds it and that video has no other row for it.
  On every row, also fill `position_after`.
- `reentry` only when he says again / retry / rebought; otherwise `entry`.

## Rules
1. Use ONLY the transcript of that video. No price lookups, no web, no other files.
2. Every row needs a VERBATIM `quote`: at least 6 consecutive words copied exactly from the transcript (keep the
   caption's garbles; no `[mm:ss]` markers). A quote MAY run across two adjacent caption blocks, and should include
   the ticker word and the action when the transcript allows. Quotes are machine-checked.
3. Captions garble tickers and prices. Known decodes: "Palunteer" = PLTR, "Marll" = MRVL, "Octa" = OKTA, "poet" = POET,
   "PNW" = PANW, "I bit" / "High bit" / "I bet" = IBIT, "SNX"/"SNXX" = a SanDisk 2x ETF (underlying SNDK), MSFU = 2x
   MSFT, NVDL = 2x NVDA, TNA = 3x small caps. "SpaceX" = SPCX. Resolve a ticker only when the company is clear from
   context; otherwise "?" and add it to `ambiguous_tickers`.
4. An ETF traded as itself (IBIT, GDX, IGV, IWM, QQQ...) goes in `ticker` with `vehicle` null. A leveraged or inverse
   product goes in `vehicle`, with its underlying in `ticker` (TNA -> IWM, NVDL -> NVDA). If he does not say which
   instrument, `vehicle` null and say so in notes.

## Dates (important)
- `session_date`: the trading session the video is about, YYYY-MM-DD. He usually says it at the top ("September
  23rd"). The upload date is often a day later. A weekend video is about the Friday session. If he never says the
  date, use the upload date (or the prior Friday for a weekend upload) and set `session_date_basis` to "upload".
- `fill_timing`: HIS words for when the action happened, lower case ("today", "yesterday", "monday", "the 17th",
  "thursday the 17th", "middle of august", "a few days ago"), or "" if truly not indicated.
- `timing_basis`: "stated" if those words are in the sentence; "implied" if you set "today" because the passage is
  plainly about this session's actions (a recap of the day); "" if fill_timing is "".
- `fill_date_stated`: YYYY-MM-DD ONLY when his words pin a calendar day given the session date ("the 17th", "Monday
  the 14th", "yesterday", "today", a weekday within the past week). Otherwise "". Never guess.
- `is_retrospective`: true when he is recounting an older trade (pointing at a chart: "bought it way down here",
  "shares from the 14th", "middle of August") rather than reporting an action from this session or the one before.

## Output: write `<dir>/auto_extract.json` for each video
```
{
 "video_id": ..., "title": ..., "upload_date": <from the batch file>,
 "date": <session_date>, "session_date": <session_date>, "session_date_basis": "spoken" | "upload",
 "observed_trades": [ {
    "date": <session_date>,
    "ticker": "SYMBOL" or "?",
    "ticker_as_captioned": the word(s) the caption used,
    "vehicle": string or null,
    "direction": "long" | "short" | "unknown",
    "action": "entry" | "add" | "trim" | "exit" | "stopped_out" | "hold" | "short" | "cover" | "reentry",
    "fill_timing": ..., "timing_basis": ..., "fill_date_stated": ..., "is_retrospective": true | false,
    "position_after": "open" | "partial" | "closed" | "unknown",
    "setup": one or two sentences in your words, as he describes it,
    "entry_basis": the trigger he names ("VWAP reclaim after a morning washout", "break of 173", "pullback to the 10-day") or "",
    "stop": what he says about the stop (location, level, distance) or "",
    "size": what he says about size ("5% position", "half", "a little bit", "took off 10%") or "",
    "price": a number he states, or null,
    "price_kind": "fill" | "level" | "basis" | "stop" | null,
    "source": "<dirname>@mm:ss"  (the block where the quote starts),
    "confidence": "stated" | "inferred",
    "quote": "<verbatim span>",
    "notes": brief: ambiguity, garbles, where the ticker is named if the quote lacks it, what happened next
 } ],
 "principles": [],
 "ambiguous_tickers": [ {"timestamp": "mm:ss", "caption_text": ..., "context": ..., "guess": "SYMBOL or ?", "confidence": "likely" | "unsure"} ]
}
```
A video with no own-trade statements still gets a file, with an empty `observed_trades` list.

## Before finishing
Re-open each file you wrote; confirm it is valid JSON, that every quote is found in that video's transcript once the
`[mm:ss]` markers are removed and whitespace is collapsed, and that every `source` starts with that video's dirname.
Then reply with: rows per video, total rows, how many "inferred", how many `is_retrospective`, tickers left as "?",
and any video where the session date was unclear. Do not paste the rows into your reply.
