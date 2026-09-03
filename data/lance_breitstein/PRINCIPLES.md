# Lance Breitstein — Principle Index

Skeptic-default leaderboard. Conviction 0–5 (independently-earned, LOW until tested) ·
Testability: EOD / intraday-needed / process · Tested? no/partial/yes.
Convention and the standing open question: [README.md](README.md).

| Principle | Type | Conviction | Testability | Tested? | One-line verdict |
|-----------|------|:---------:|-------------|:------:|------------------|
| [Qullamaggie's complete system, as relayed](principles/qullamaggie-system-relayed.md) | setup + execution + regime | 3/5 (as record) | mostly EOD ⭐ | no | **⭐ Most valuable document ingested.** His entry/stop/partial-exit/trail/market-filter rules in his own quoted words. Entry = **ORB high of the breakout day**, stop = **that day's low** (intraday — which is why my next-open `bar low` test wasn't his rule). Exit = **sell ⅓–½ on day 3–5, stop to breakeven, THEN trail 10-day (fast) / 20-day (slow), exit on first CLOSE below**. Market filter = 10-day vs 20-day cross + slope, graduated. ⚠ Collides with `risk_architecture/` in 3 places; my "fast trails always lose" finding tested a *full* exit, not his partial-then-trail — **not a fair comparison**. |
| [The 2 swing strategies](principles/swing-strategies.md) | setup (swing) | 2.5/5 | EOD ⭐⭐ | partial | Mean-reversion "right side of the V" (capitulation volume → enter on trend break → trail prior bar lows; his $10M Nikkei trade) and continuation (multi-month breakout + catalyst + hot theme). ⚠⚠ **Contradicts Luk on stop width**: says tight intraday stops on daily setups were his biggest early mistake, "if your stop is 3× wider your size needs to be 3× smaller" — which **corroborates this repo's swing results** and narrows the 6× lever to intraday only. Also admits swing has **less absolute edge** than intraday. |
| [Stops and exponential bet sizing](principles/stops-and-sizing.md) | stops / sizing | 3/5 | partly EOD | partial | Stop where EV goes negative; match stop to the setup's timeframe; **backtest the stop, don't guess**; volatility widens stops so **size down**, never tighten. ⭐ States the mechanism behind the sizing lever: a setup whose bar is *naturally* tight against resistance "gives far better expected value." **Tested — not confirmed at EOD** (Q1−Q5 = +2.8/+4.1 bp, t≈0.3–0.4), but tightest quintile stops out 88–90% in 1–2 days = overnight-gap artifact, so untestable rather than refuted. ⚠ **10× variable risk by A/B/C/D grade — directly contradicts Luk's near-constant 0.3%.** |
| [Bollinger Bands](principles/bollinger-bands.md) | volatility context | 2.5/5 | EOD ⭐ | no | ✅ **Passes the skeptic check** — does NOT repeat Carter's Squeeze. Band contraction = "no man's land" = **stop trading**, the opposite of buy-the-coiled-spring, agreeing with our 3-way kill of the Squeeze. Uses: pendulum/mean-reversion, overextension (only in *trending, expanding* regimes), and contraction-as-veto. Refuses bands as levels, same as AVWAP. ⭐ Gives the repo its first mechanical **short** rule. |
| [In-play stocks (universe gate)](principles/in-play-stocks.md) | universe gate | 3/5 | EOD ⭐⭐ | no | ⭐ **Strongest independent corroboration that selection IS the strategy**, from inside multiple prop firms: *"5-10 stocks make up 90% of the firm's profits"*, *"~25 stocks/day offer positive EV, fewer than 5 move your P&L."* In-play = news catalyst / technical catalyst / **range expansion RELATIVE to the stock's own normal** — which is a concrete upgrade over the repo's absolute ADR≥3.5% gate, testable with no new data. ⚠ Claim is ex-post firm P&L, not evidence the criteria identify those names in advance. |
| [Right side of the V](principles/right-side-of-the-v.md) | entry timing (unifying concept) | 3/5 | EOD ⭐⭐ | no | ⭐⭐ **His single unifying concept — every other setup is a special case.** "The same price does not always equal the same expected value." Left side (still falling) = no true stop + marginal win rate; right side (after the turn) = real stop at the day's low + higher win rate → his arithmetic gives **4× the EV**. Turn triggers: break of prior bar high / trendline break / MA break. ⭐ **Retro-explains the gap study**: the unconditional fade was textbook left-side; the two conditions that worked (post-1ATR move, high VIX) are exhaustion proxies. Clean A/B test available, no new data. |
| [Opening Range Break](principles/opening-range-break.md) | entry / intraday setup | 3/5 | intraday | no | ⭐ **First time a practitioner corroborated a repo statistic instead of contradicting one.** His 3 ORB use cases map onto the gap study's only two winning conditions: exhaustion gaps ↔ post-≥1ATR move (+11.9bp, t=6.5), macro-panic days ↔ high-VIX tercile (+6.9bp, t=3.7). Difference = he requires the **opening range to fail first**, a confirmation the EOD test couldn't implement. Also **Qullamaggie's stated entry**, so 2 of 3 traders enter on the OR break — sharpens the minute-bar test into a concrete spec. |
| [The 4 IPO strategies](principles/ipo-strategies.md) | setup (event-driven) | 2.5/5 | 2 of 4 EOD ⭐ | no | Lands on the repo's **structural blind spot** — SMA200 + 400-bar minimums mean no IPO can ever appear in any result produced so far. Opening drive / counter drive / later-day breakout / **overnight momentum (EOD-testable)**. Structural argument is the strongest in the KB: no overhead resistance, constrained float, documented underpricing. ⚠ But the pop accrues to *allocation holders*, not open-market buyers, and he slides between the two. **Lockup expiry (90–180d) is a clean mechanical event study.** |
| [Risk framework (long-form)](principles/risk-framework-longform.md) | sizing / risk philosophy | 3/5 | partly EOD | no | ⚠ **Deflates the 6× thesis.** He caps position at **~25% of account independently of risk** ("at max 25%… I don't want to be 50% in just because my risk-reward"), so the stop-tightness lever is **bounded** — and my sim's 30% cap was if anything generous. But it isolates the lever the sims genuinely lack: **conviction risk varies 10× by grade** ($10k B → $100k A) while every backtest holds risk flat at 0.3%. ⟹ **test tier-weighted risk before buying minute bars.** |
| [No man's land + bobblehead + epistemics](principles/no-mans-land-and-process.md) | veto / process | 3/5 | EOD ⭐ (the veto) | no | **Third independent statement against Carter's Squeeze**: contracting volatility = "price action that looks tradable but isn't" = stand aside. Second-order argument is the good one — paper cuts shrink risk tolerance so you *skip the real setup* (the Nikola story). Epistemics come out **well**: he defines TA as non-predictive EV-hunting, names mechanisms (big-order absorption, forced liquidation) and counterparties. ⚠ His critique that academic TA studies use "simple rules on stocks that are not in play" **partly lands against my own method.** |
| [MTF, news, playbook, tape, scalping](principles/remaining-five.md) | mixed | 2.5/5 | 1 EOD ⭐ | no | ⭐ **Testable rule 3 sources now agree on**: fade outsized moves **only when there is NO fresh news** — he says it twice, Carter's veto list leads with news gaps, and the repo's gap study never conditioned on catalyst at all. Could rescue a setup currently written off at 1/5. Plus: intraday chart gets **80% weight** over daily when trading intraday; playbook step 2 = **"who's trapped"** (the counterparty question as a routine field — steal it). Tape/scalping ⚠ prop-dependent, parked. |
| [Setup grading — chart nuance](principles/setup-grading-chart-nuance.md) | setup quality / entry grading | 2.5/5 | EOD ⭐⭐ | no | ⭐ **Most operationalizable setup material in the KB, weakest evidence in it.** 12 hand-drawn charts, 4 archetypes (breakout / trend-break bounce / turtle soup / **bouncy-ball short**), each graded with a reason. Discriminators the repo's scorecard does NOT have: **pullback depth vs the prior leg**, **range contraction before the trigger**, **level cleanliness**, and the "**price acceptance**" veto (tight bars at the lows = buyers absent = no play). ⭐ [18:03] states the tightness-vs-fragility mechanism — a quality pattern places its own invalidation close by. ⭐ [19:41] the **next video maps grade → size**: the missing first link to the 6× lever. ⚠ He drew every chart *including the outcomes*, then claims "this isn't retrospective hindsight analysis whatsoever" — zero numbers, zero base rates, 3 cherry-picked winners, course pitch mid-video. ⭐ **Collides productively with `crash_leader_reversion_study.md`** — he says decline *shape* discriminates, that study says *regime* does; event set already on disk to test both. |
| [Anchored VWAP — trend context, not a level](principles/anchored-vwap.md) | regime / trend-context | 2/5 | EOD-testable | no | **Coherent mechanism, honestly presented — but NOT the entry-location tool this KB was opened to find.** He explicitly refuses to use (A)VWAP as a level: "I am not buying or selling simply because we get above or below that line." It is a directional veto (don't short above it unless capitulated) plus a swing trailing-exit structure. ⚠ Null hypothesis unaddressed: AVWAP is a volume-weighted MA with a hand-picked start, and nothing shows the weighting/anchor beats a fixed-lookback trend filter. ⭐ One fully mechanical rule extracts and is the cheapest open test in the repo. |

---

## Priority queue

**22 videos ingested · ALL written up** (2026-07-26/27, +`9SgNXrWTefY` 2026-08-02). Two co-equal
tracks — see [README.md](README.md). Nothing below is written up yet except AVWAP.

### ⚠ Next ingest — named by him, not yet in the manifest queue

- [ ] **The setup-grading → sizing video** that `9SgNXrWTefY`@[19:41] forward-references ("grade
      your setup A through D and directly influence your sizing"). This is the **most on-point
      unwatched video for the standing open question** — it is the join between setup quality and
      the 6× sizing lever. ⚠ **Not in `channel_videos.txt` — the manifest is stale.** `9SgNXrWTefY`
      is line 1 (newest) and is dated 2026-07-25, so the manifest predates the sequel. The only
      sizing titles in it (`eDdpTNB04ws`, `tIB72PAeZLU`) are both already written up and neither is
      the A–D grading video. **Regenerate the manifest via yt-dlp before hunting for it.**
- [ ] **Ariel Hernandez** — named at [19:19] alongside Kyle Williams as a practitioner of the same
      nuance. Possible cross-source check; not currently in any KB.

### Track A — SETUPS (testable on data already on disk)

- [ ] **The 2 Swing Trading Strategies That Made Me Millions** — `k-X0164r66U` ✅ WRITTEN UP
      Swing = the horizon the whole `risk_architecture/` harness already tests. Highest-value.
- [ ] **Right Side of the "V"** — `wtQIj6Apiq0` (2025-11-15). Named reversal setup.
- [ ] **I Only Trade Stocks That Meet This Criteria** — `7FbTZZNljSo` ✅ WRITTEN UP. His universe
      gate — compare directly to the repo's own GATES (ADR / dollar-volume / Stage 2).
- [ ] **The 4 IPO Trading Strategies** — `dGjqaXTeiTU` (2026-04-25) ⭐ Young stocks are
      *structurally excluded* from every backtest so far (SMA200 + 400-bar minimum). This is the
      known blind spot named in `HOW_THEY_DO_IT.md` §4.
- [ ] **How to Trade the SpaceX IPO (and every big IPO)** — `i8NgzZgc5L4` (2026-06-09). Same theme.
- [ ] **Bobblehead Method** — `fpwQd__kGSQ` (2025-10-15). Named proprietary concept.
- [ ] **The 3 Scalping Strategies** — `2DXQqwKSwJE` (2026-04-11). Intraday; park the evaluation.
- [ ] **ORB Trading Only Works If You Do These 3 Things** — `QmPUp9ISuDw` (2026-06-24).
- [ ] **Multi-Timeframe Analysis** — `k6I04ciE1KE` (2025-12-06).
- [ ] **How to Trade the News Like a Top Wall St Trader** — `-ZV_EpqmUDQ` (2025-11-01).
- [ ] **What Is a Trading Playbook?** — `bKvEfCGJS4g` (2025-07-22). How he specifies a setup
      precisely enough to size it — the bridge between the two tracks.

### Track B — EXECUTION / STOPS / SIZING (the open question; blocked on minute bars)

- [ ] **How to Stop Guessing with Your Stop Losses** — `WgRQWJq54OY` ✅ WRITTEN UP
      The most on-point title on the channel for the stop-fragility question.
- [ ] **The Trade Sizing Strategy that Made Me Millions** — `eDdpTNB04ws` ✅ WRITTEN UP
      The sizing lever itself (position = risk% ÷ stop%).
- [ ] **The Art of Betting Big** (w/ Kyle Williams) — `tIB72PAeZLU` (2025-10-22), 60k chars ⭐
      When to size up. Two elite traders, long form.
- [ ] **52-Minute Risk Management Masterclass** — `hC4g7qY6UcQ` (2026-07-15), 61k chars ⭐
- [ ] **Stop Trading in "No Man's Land"** — `fCp6CRu6E5Y` (2026-02-28). Entry location.
- [ ] **How to Read the Tape with Level 2** — `RKV1rncXSkg` (2026-05-30). ⚠ Check prop dependency.

### Track C — cross-source / skeptic checks

- [ ] **Reacting to Qullamaggie's Moving Average Strategy** — `H01JbbEY7ac` ✅ WRITTEN UP
      One of the three named traders, evaluated by another. The single best cross-source document
      available, and it bears directly on `HOW_THEY_DO_IT.md`.
- [ ] **Technical Analysis is a SCAM!? What the Research Actually Shows** — `QP5HohzDGww`
      (2026-02-07). His engagement with the academic evidence — a direct read on his epistemics.
- [ ] **The Bollinger Band Edge Most Traders Never Discover** — `ZZ-e9wxARSI` ✅ WRITTEN UP.
      ⚠ Same "…Edge Most Traders Never Discover" series as the AVWAP video. The repo already
      **killed the Squeeze** (BB inside Keltner) three ways — so this is a live test of whether
      he repeats a claim we have already falsified.
- [x] **Anchored VWAP** — `D2P-0xh6aEM` ✅ written up 2026-07-26.
      ⚠ **Hypothesis NOT supported.** He disclaims using AVWAP as a level, so it says nothing
      about entry precision or the sizing lever. Luk uses it as a stop level; Breitstein refuses
      to — same tool, opposite application, do not merge.

## ⭐ Extracted test — ready to run

From the AVWAP write-up, in fully mechanical form:

> Anchor to the highest-volume session of the trailing N days; stay long while price closes above
> the anchored VWAP; exit on the first close below it.

Slots straight into the `risk_architecture/` harness as a **seventh exit rule**, against data
already on disk. Baseline to beat: `close<50EMA`, the best of the six exits tested across 320
configurations. Null hypothesis to kill: that the volume weighting and the anchor add nothing
over a fixed-lookback trend filter.

## What to capture from each video

For this KB specifically, prioritize in this order:

1. **Entry location** — where exactly, relative to what reference (AVWAP, opening range, pivot,
   level), and how far the invalidation sits from it. This is the open question; everything else
   is secondary.
2. **Stop placement and resulting size** — the ratio is the whole lever.
3. **Exit** — especially anything resembling scale-out-into-strength.
4. **Regime / market-condition gating.**
5. **Process** — review, journaling, psychology. Record, but file as unfalsifiable.

## ⚠ Flag on every write-up

Whether the technique depends on **prop infrastructure** (locates, borrow, fees, routing,
capital, risk oversight). That is the most likely way to mistake his edge for a transferable
method, and it is the first thing to check before anything here graduates to `data/studies/`.
