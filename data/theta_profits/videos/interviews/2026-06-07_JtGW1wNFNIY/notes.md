# Supplemental Notes — 2026-06-07 "How Steve turns Double Calendar Spreads Into Risk-Free Iron Condors" (JtGW1wNFNIY)

Human-added context not in the audio: on-screen actions, slides, corrections, the
interviewed trader's name/handle, and anything to verify.

## Interviewee

- Name / handle: **Steve Bernich** (surname is from auto-captions `@00:25`, treat as approximate) —
  founder/educator at **NavigationTrading** (`@02:57`). Trading since 1999, options since 2006, teaching
  since 2016. **NOT** Steve Gunn of `strategies/flyagonal.md` (sjgtrades.com) — different person, firm,
  and strategy despite the shared first name and the "double calendar / risk-free" overlap.
- Strategy in one line: **"DC Time Machine"** — enter an SPX double calendar, then once it's ~5–10% up,
  convert it in one order into an iron condor whose net credit ≥ wing width, so the condor can't lose
  ("risk-free") and frees the broker's buying power.

## Corrections & context

- [00:25] "Steve Bernich" — guest's name as heard in auto-captions; spelling unverified. NavigationTrading
  is the reliable identifier.
- [05:54], [06:06] "7480 / 7570 / 7485 / 7560 strike" etc. — these are **SPX** strikes (index ~7500 in
  this recording), not stock prices.
- [13:10] "Friday-Monday combination… backwardation" — sell the Friday expiry, buy the Monday expiry;
  "backwardation" = front IV > back IV (his preferred setup).
- [15:11] **"Flux"** — his self-built, members-only tool plotting front-IV ÷ back-IV ratio (named for the
  "Back to the Future" / time-machine theme). Proprietary to NavigationTrading; not testable externally.
- [07:52]–[09:04] **Sponsor read — IGNORE.** Host plugs a free Theta Profits live "wheel" course taught
  by Paul Gambleson (June 16). Unrelated to Steve's strategy.
- [18:36] "only available exclusively for our members at Navigation Trading" — soft sales reference to his
  paid program; the Flux tool is gated.
- On-screen tools referenced: **thinkorswim** (Schwab) risk-profile graph for the live trade demos;
  he also names **OptionStrat** and **Option Omega** as risk-graph tools to "play with transforms."
- [48:12] Host cross-links the **Boomer Dan** episode ("zero-DTE levitation trades") as a similar
  "make trades risk-free by end of day" idea → see `strategies/burrito_butterfly.md`.
- Returns are quoted in **dollars only** (Feb–Apr 2026), on undisclosed position sizes (examples use
  20-lots); no ROC / % of capital is given, so they can't be normalized.
