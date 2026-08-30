# Supplemental Notes — 2026-08-03 "EP75 | 3 Aug 2026" (Flrm2Y_qB_M)

Human-added context not in the audio: on-screen actions, chart annotations, ticker fixes.

Live stream, ~100 min, market open through midday. Mic problems acknowledged at [04:57]; audio
quality is poor and auto-captions are correspondingly rough. No pre-set agenda ("today um no no
plans") — position review, then Q&A off chat.

## Ticker decoding table (auto-caption fixes)

Auto-captions garble tickers. Conf: ✅ confirmed · 🟡 likely · ❓ unsure.

| Transcript said | Likely ticker | Conf | Notes |
|-----------------|---------------|------|-------|
| "crowd" | **CRWD** | ✅ | Open position, entered on stream |
| "net" | **NET** | ✅ | Cloudflare; entered Wed just after the stream ended |
| "FPNT foret" / "fortunat" / "FT&T" | **FTNT** | ✅ | Stopped out Thu, re-entered Fri |
| "handw" | **PANW** | ✅ | Confirmed by Gabe 2026-08-03. Entered Thu on 60-min candle breakout, ~317, stop = low of that candle |
| "BMR" / "BNN" | **BMNR** | 🟡 | Bitmine; stopped out for a small loss, later re-added to watchlist as crypto firmed |
| "the queue" / "cues" | **QQQ** | ✅ | |
| "Sammy" / "semif" / "semi" | semis / **SMH** | ✅ | Used loosely for both the group and the ETF |
| "sock sock" | **SOXX** | ✅ | "still above the weekly 21, well above the weekly 50" |
| "SNDK" | **SNDK** | ✅ | SanDisk; cited as down >55% from highs and *still* an ordinary pullback |
| "HP" / "HPE" | **HPE** | ✅ | Main discussion name; RS through the whole semi correction |
| "CBRS" / "CPRS" / "CPR" | **CBRS** (Cerebras) | 🟡 | ~1-month post-IPO base, ~160–170 support, earnings pending, anchored-VWAP overhead |
| "snow" | **SNOW** | ✅ | |
| "DOC" / "duck" / "do" | **DOCN** | 🟡 | He names "Digital Ocean" explicitly at [74:59], which resolves the earlier garbles |
| "MSTR and corner" | **MSTR**, **COIN** | ✅ | On the radar if crypto keeps improving |
| "ADA" | **ADA** (Cardano) | ✅ | Only alt showing RS vs BTC/ETH |
| "SUV" | **LUV** | ✅ | Southwest; cited as the *weak* airline |
| "AL" | **AAL** | 🟡 | Also cited as weaker |
| "SE" | **SE** | 🟡 | |
| "Shopify" / "Affirm" / "Adobe" | SHOP / AFRM / ADBE | ✅ | Software breadth walk-through |
| "IGV" | **IGV** | ✅ | Software ETF — his sector-strength check |
| "Dell, AMD" | DELL, AMD | ✅ | Semi leaders he tracks for a turn |
| "set" | ❓ | ❓ | Software name, earnings next day, choppy weekly base — passed on it |
| "Rafian" / "Rathian" | **RIVN**? | ❓ | "technically it's just bad"; theme mismatch |
| "Nap" / "Napius" [45:08] | **NBIS** (Nebius) | ✅ | Gabe 2026-08-03. Endorsed as "a pretty good candidate for the long side" on the semi/AI side — weekly pin bar into the prior swing high + 50 EMA, back above rising 9 and 21 |
| "X8" / "XE" [41:41]–[43:26] | ❓ | ❓ | ⚠ **Do not assume this is NBIS.** He skips this one as "a little bit illiquid… under hundred million dollar volume in a day" — which does **not** describe NBIS. Either a separate low-base name he passed on, or he misspoke. Needs the on-screen chart at [42:47] |
| "SpaceX" / "SpaceX Rock" | SpaceX | 🟡 | Trades publicly in this timeline; exact ticker not stated |
| "HA" | ❓ | ❓ | Viewer question, "similar to SpaceX" |
| "Horn" / "Q&T" / "SOS" | HON + spin-offs | 🟡 | Honeywell split; "SOS = the materials part" — likely Solstice |
| "PBF" | **PBF** | 🟡 | Viewer's trade, not his |

Non-ticker garbles: "riptos" = cryptos · "stall" = stop · "16-minute" = 15-minute ·
"anchor VW web" / "angle V web" = anchored VWAP · "FCP" = **VCP** · "lockout rally" is his own term.

## Open positions as described

| Ticker | Entry | Stop / state |
|---|---|---|
| CRWD | on stream, earlier | Held; nearly stopped Thu, back above 9/21; likes the weekly 9 EMA undercut-and-rally close |
| NET | Wed, just after stream end | Bought after 15-min EMAs converged and held the 50; helped by a strong 15-min market reversal ~12:15 |
| **PANW** | Thu | Breakout of prior 60-min candle, **stop = low of that candle**, ~317 |
| FTNT | Fri (re-entry) | Stopped Thu on a 5-min entry; re-entered on a 15-min breakout after the post-earnings pullback into daily 9/21 |
| BMNR | Thu | Stopped out Fri, small loss |

## ⭐ Methodology worth distilling into `philosophy/principles.md`

- **[85:10] ⭐⭐ Explicit claim that the market regime has changed the *entry type* that works.** He
  says that for the past one-to-two years, once a stock pulls back into support it moves straight
  off the lows — it does *not* linger, chop, and build a tight range for a clean breakout, which he
  calls "really uncommon in the past one or two years." Hence his stated preference for **pullback
  entries over breakout entries**, "following what the market is doing right now."
  ⚠ This is a **decay claim about range contraction itself** and it bears directly on
  (a) the repo's VCP/breakout scorecard work and (b) Breitstein's "range contraction before the
  trigger" nuance in `lance_breitstein/principles/setup-grading-chart-nuance.md`. Two practitioners
  now disagree about whether pre-breakout tightening is still available. **Testable on daily bars.**
- **[50:12] Risk is defined by stop × risk-per-trade, and nothing else.** Asked about controlling
  beta, he says a 20% ADR name and a 5% ADR name carry the *same* risk if he uses the same risk per
  trade — size follows the stop. ⚠ Confirms the constant-risk-per-trade reading of Luk and sharpens
  the standing conflict with Breitstein's 10× A/B/C/D risk grading.
- **[51:03]–[57:41] ⭐ Why several small positions in one sub-theme instead of one large one.**
  ⭐ **The sub-theme is CYBERSECURITY — his open book is CRWD + FTNT + PANW** (PANW confirmed by
  Gabe 2026-08-03; the transcript garbles it as "handw"). This is what the viewer's question is
  actually about, and it makes the exchange legible: he is not diversified across the market, he is
  concentrated in one industry and spread *within* it. Consistent with [24:50], where he says the
  cyber names are stronger than the rest of software so he is "trying to focus on the strongest
  names at this time."
  He answers with an extended supermarket-crisps analogy — four small packs rather than one family
  size — which is partly personal preference, but the operative reason arrives at the end and is
  supplied by a *viewer*, which he endorses: **you never know which one will be the true leader
  from this stage.** So the position count is a hedge against leader-selection error *inside* a
  theme he has already committed to.
  ⚠ Note the risk this actually carries: three cyber names sized independently at his usual risk
  per trade is one **thematic** bet at ~3× the intended unit risk if the industry turns together.
  He does not address correlation anywhere in the answer. Directly relevant to the repo's own
  correlation/cap rules in `data/studies/capital_allocation_framework.md`.
- **[17:55] / [67:10] Two independent reasons he will not short the semi bounce.** (1) Last week
  printed a bullish weekly pin bar with a long lower wick at rising weekly EMAs — he won't short
  into the *first* weekly candle of support. (2) Structural: after a large rally, straight-up-
  straight-down is unlikely; a stage-four decline normally needs sideways time and failed breakouts
  first. He'd want a reclaim of the declining 50, then a tighter right-side range, and would short
  the *failed* breakout instead.
- **[36:54] No special handling for earnings season** — "what's the difference?"
- **[77:32] Re-entry discipline.** After the FTNT earnings-day stop-out he moved to the 15-min chart
  and found successive lower highs with no higher high after the opening fade, so there was no
  trigger to re-enter on. Absence of a breakout *is* the reason.
- **[78:02] How he judges sector strength** — no indicator: walk the watchlist and screeners daily,
  and when four-to-six names in the same industry act well plus the sector ETF (IGV here) is above
  clustered rising EMAs, call the sector improving.
- **[98:06] Declines a gap-up ORB entry** for the next session because QQQ/SPY/IWM are already
  extended from the 9/21 and heading into resistance — prefers to wait for a pullback.
  ⚠ Contrast with Breitstein's ORB material and Qullamaggie's OR-break entry.
- **[21:25] Study advice** — for any question of this kind, go through the charts yourself; the
  by-product observations are worth more than the answer.

## Other context

- Market view: constructive. Mag7 leading, AMZN breaking to all-time highs, MSFT gapping post-
  earnings with two-day follow-through, IWM breaking a descending trendline. Wants a *sideways*
  session or two before adding exposure rather than chasing.
- Crypto: watching for confirmation from smaller alts before committing; likes that BTC's early-July
  low held as a shakeout of the Feb/June lows.
- ⚠ **Ingest backlog:** two streams between the last ingest and this one are still missing —
  `fGPCqWLQ-Qk` (2026-07-28, "Locking in profits") and `xZ5LigAsWec` (2026-07-29, "Bleeding
  slowly"). `videos/livestreams/_channel_streams.tsv` is also stale (72 rows, newest 2026-07-27);
  regenerate per the command in `data/martin_luk/README.md`.
