# Supplemental Notes — 2026-07-27 "EP72 | 27 Jul 2026" (oXZRlT1bh1k)

Human-added context not in the audio: on-screen actions, chart annotations, ticker fixes.

## Ticker decoding table (auto-caption fixes)

Auto-captions garble tickers. Conf: ✅ confirmed · 🟡 likely · ❓ unsure.

| Transcript said | Likely ticker | Conf | Notes |
|-----------------|---------------|------|-------|
| "SK high next" / "SKH Highix" / "skhinx" | SKHY | ✅ | Three manglings of one name; decode already confirmed in prior videos |
| "the kills" (19:35) | QQQ | ✅ | Listed straight after SPY and IWM; "cues" (= the Qs) used elsewhere in the same stream |
| "tunnel fish" (14:40) | — not a ticker — | ✅ | He is groping for "tunnel vision" (set up at 12:58). Logged so a future pass doesn't decode it as a symbol |
| "cues" | QQQ | ✅ | Used throughout |
| "MD" (68:31) | AMD | ✅ | Continuation of the AMD discussion |
| "Cypher" / "Cipher" (67:53) | CIFR | 🟡 | Cipher Mining; crypto-miner context |
| "A coin is coin still CN" (57:50) | COIN | 🟡 | Coinbase; listed in the short watchlist |
| "Naps" / "NPA" / "NPS" (57:26) | NBIS? | ❓ | ⬜ **Top pick of the short watchlist** — three renderings in 90s. Guess weakly supported |
| "this T" (59:12) | TSM? | ❓ | ⬜ Worked example for the 60min-50EMA / daily-9 entry. Single letter — not really decodable |
| "AMK" (76:16) | AMKR | 🟡 | Amkor; listed with SITM (clean) as weak-bounce evidence |
| "DTMI" (76:16) | ? | ❓ | ⬜ Does not resolve. MTSI? DTM? |
| "this a str" (95:25) | ASML or AMAT | ❓ | ⬜ Semi-equipment rollover context |
| "KAC" (95:25) | KLAC | 🟡 | Same passage |
| "ONDS" (16:33) | ONDS | ✅ | Ticker clear; ⬜ **DIRECTION unclear** — see below |

## On-screen actions (inaudible)

- [06:48] — Watchlist counts shown for leading / mediocre / lagging buckets. He says the leading
  and lagging figures have roughly **flipped** versus two weeks ago (leading was ~50-something,
  lagging ~20–30-something). Exact numbers are on screen, not spoken. ⬜ worth reading off.
- [16:33] — **ONDS**: "looks pretty strong… probably I may get stopped out." Reads most naturally
  as an existing SHORT being squeezed (fits his bearish book), but could be a long under its
  weekly EMAs. **Not logged as a trade until confirmed.**

## Other context

### ⭐ The most important passage in the stream (24:50–28:32)

On AMD, immediately after conceding the setup is mediocre — extended from the declining 9, and
"the more extended you are from the declining EMAs, the lower your win rate will be":

> "My reason AMD today will be a good short is **plainly because there's a tight stop**… the stop
> is only around 1%. **You can easily know you're wrong.**"

He takes a *worse* setup *because* the invalidation is cheap and unambiguous. This is the third
independent statement of the mechanism at the centre of
`carter_mastering_the_trade/backtests/risk_architecture/HOW_THEY_DO_IT.md` — Breitstein says it in
`WgRQWJq54OY`, and it is implicit in Qullamaggie's breakout-day-low stop.

### ⚠ Revises an existing principle

**"Sell into strength — it's never wrong"** currently carries 10 mentions / 10 videos in
`philosophy/principles.md`. Here (64:44) he explicitly declines to take a side: *"one of the most
debatable rules… both have a lot of supporters and both have their own merits and disadvantages.
You need to find the one that works for you."* Should be reflected at the next re-synthesis.

### Two genuinely new principles

- **Sector selection dominates stock selection** (51:34): *"my stock selection is not really that
  important. I just identify the weak sector to short… 99% of them just go down. So it doesn't
  matter actually which stock I pick."*
- **Entry aggression is conditioned on P&L state** (89:51): entered MSTR early, before the touch,
  because *"I got a huge chunk of profit cushions… If I am in a drawdown, if I'm red in a year, I
  will not be this aggressive."*

### Relevant to the repo's open backtest question

**No overnight or extended-hours stops** (32:51) — if it gaps through he lets it execute at the
open, reasoning that gap-up/gap-down probabilities are symmetric and "even out." So his ~1% stops
are live *intraday only*, and overnight gap risk is a separate, deliberately unmanaged exposure.
The EOD backtest in `risk_architecture/` conflated the two, which is the likeliest reason it could
not reproduce the tight-stop claim.

### Other

- Covers shorts on **index** extension, not the name's own support (62:06) — declined to cover
  SNDK at a pivot support zone because SPY/IWM were only "day one" into the reversal.
- Bull-trap warning (69:32): relative strength in a *weakening* tape is a trap he says has caught
  him repeatedly.
- Logged miss: **MARA** (41:23) — "I should have traded this one"; absent because he was "a little
  bit early and got stopped out on Thursday."
