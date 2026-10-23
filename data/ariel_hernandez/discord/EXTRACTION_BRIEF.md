# Brief: trade log from Ariel Hernandez's Discord channel #live-long-ideas (MarketPulse)

Every message in this channel is posted by Ariel himself, live, during the session. They are short and terse:
"SNDK long 1315.18 10%", "stop LOD", "trimming 20% of TQQQ 72.93", "closed 20% of CRM 250.27", or a bare price on its
own line that belongs to the message just before it. Build one row per trade ACTION he reports. Accuracy matters more
than volume: the log is scored against prices later.

## Input
Your batch file (`batch_N.json`) has `context_before` (the 40 messages preceding your batch, for resolving open
positions and continuation lines; do NOT emit rows for them) and `messages` (yours). Each message: `msg_id`, `ts_utc`,
`ts_et` (US/Eastern wall clock; the market opens 09:30), `text`, `reply_to`, `attachments` (count of images/links;
you cannot see them). Read every message in order.

## What to log
- His own actions: entry, add, trim, exit, stopped_out, short, cover, reentry, and `stop` (a stop he sets or moves on
  a position he holds, e.g. "stop LOD", "stop at flat on the rest", "final stop against the 50sma").
- `watch` rows ONLY for an explicit alert to the members that is not a fill ("watching HUT over 22.60. stop LOD",
  "TWLO alert just triggered, going to pass"). Keep these: they are the channel's signals even when he didn't fill.
- Skip pure commentary ("Keep losses small!", "Trade them well") — no row.
- One message can carry several actions or tickers: emit one row each. Several consecutive messages often make ONE
  action (ticker in one, price in the next, size/stop in a third): emit one row and list every msg_id used.
- "^AAOI" or "SPCX ^" means the line above was about that ticker.
- A bare price / size / stop line attaches to the most recent action in the preceding minutes. If it is unclear which,
  say so in notes and set confidence "inferred".
- Ticker missing from the action message ("stopped out", "closed at flat 13.28") → resolve from context (the open
  position it must refer to), confidence "inferred", and say which message gave the ticker.
- "Cut my recent adds 120.19" → exit of the add tranche; position_after "partial".

## Fields (one JSON object per line, JSONL)
```
{"msg_ids": ["..."],            # every message the row is built from, first = the action message
 "ts_et": "YYYY-MM-DD HH:MM:SS",# ts_et of the action message
 "ticker": "SYMBOL",            # as traded. Leveraged ETFs (TQQQ, SOXL, TNA, NUGT, SQQQ, ETHU, XXRP, MAGS...) are
                                # logged AS THEMSELVES here, with `underlying` filled (TQQQ->QQQ, SOXL->SOXX, TNA->IWM,
                                # SQQQ->QQQ with direction short exposure noted). "?" if unresolvable.
 "underlying": "SYMBOL" or null,
 "direction": "long" | "short",
 "action": "entry"|"reentry"|"add"|"trim"|"exit"|"stopped_out"|"short"|"cover"|"stop"|"watch",
 "price": number or null,       # the fill/level he states for THIS action
 "size_pct": number or null,    # % of portfolio when he says it ("10%", "5% position", "3% size")
 "size_text": "",               # his words on size: "half size", "quarter size", "20% of my position", "a third",
                                # "down to half of my original", "another 1k shares"
 "fraction_of_position": number or null,  # for trims/exits: share of the CURRENT position sold, if derivable
                                # ("trimming 20%" -> 0.2, "a third" -> 0.333, "closed"/"gone"/"done with" -> 1.0)
 "stop_text": "",               # "LOD", "yesterday's lows", "50sma", "flat", "HOD", "$61", ...
 "stop_price": number or null,  # only when he states a number
 "setup": "",                   # his setup words: "U&R", "20sma MAU&R", "6/20", "HVC", "higher low", "5min ORB",
                                # "mean reversion", "flat base breakout", "7x ATR extension trim" ...
 "position_after": "open"|"partial"|"closed"|"unknown",
 "confidence": "stated"|"inferred",
 "quote": "verbatim text of the action message (or the decisive part, >= the whole message if it is short)",
 "notes": ""}
```

## Rules
1. Use only the batch file. No price lookups, no web, no other files.
2. `quote` must be an exact substring of the `text` of msg_ids[0] (machine-checked; keep his typos).
3. Prices are as he wrote them. "Long BABA $120.80s" -> 120.80. "$1 risk", ".12 loss", "-3.5% away" are NOT prices.
4. Times are ET; do not shift them.

## #live-short-ideas batches (`short_batch_N.json`)
The same brief applies, with these differences:
- The default direction is **short**. "Short X 53.60, stop HOD" → `short`; "covered", "closed", "out of" → `cover`
  (or `stopped_out` if he says he was stopped); trimming a short → `trim` with direction short.
- An inverse ETF held LONG (SQQQ, SOXS, TZA, SPXU, NVD...) is logged as `ticker` = the inverse product, direction
  **long**, action entry/trim/exit, with `underlying` set and the notes saying it is short exposure. Do not flip it.
- If he posts a LONG in this channel, log it as long and say so in notes.
- A stop for a short sits ABOVE price ("HOD", "yesterday's highs", "the 20sma").
- Output: `short_extract_N.jsonl`.

## Output
Write `/Users/gmerton/options_playground/data/ariel_hernandez/discord/extract_N.jsonl` (N = your batch number).
Re-open it, confirm every line parses and every quote is a substring of its first message's text. Reply with:
rows by action, rows marked inferred, tickers left "?", and any messages you could not interpret (msg_id + text).
Do not paste the rows.
