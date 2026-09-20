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
| [Capitulation quantified + writeup template](principles/capitulation-and-trade-writeups.md) | setup (blowoff short) + review-process | 3/5 (hypothesis) | EOD ⭐ | no | ⭐ **Testable now:** blowoff = bar range ≥ 2× prior day AND volume ≥ 2× prior day after an accelerating run; both timeframes capitulating = strongest. Third source for the **no-news veto** on fades. Template adds two fields the journal lacks: the **analog ticker** and the **prior-gap cause**. `TexislSXpjs` (2023). |
| [$MULN layup anatomy](principles/muln-layup-anatomy.md) | setup (catalyst long → overnight → day-2 failed drive) | 3/5 template · 1/5 evidence | overnight piece EOD ⭐ | no | ⭐ **Cross-source match for the repo's FBO short detector**: drive above the level, fail to hold, lower high, break below VWAP → short, stop at the highs (adds a *lower-high* gate worth testing). Holder psychology (99% out of the money = no supply) + **share turnover** (volume > float resets the cost basis) + skew = the overnight thesis. Timeframe weights 70/25/5. Pod-dependent. `-x1nbxasFcE` (2023). |
| [15 risk-management lessons](principles/risk-management-15-lessons.md) | sizing + process | 3/5 | two rules testable on our journal | no | Numbers: broker-enforced **daily loss limit**; **overnight size = ½–⅓ of intraday**; 3× wider stop → ⅓ size; **80% of profits from 1–5% of trades, best trades 100× normal**. ⚠ **Contradicts Luk twice**: overnight (Luk: no stops, it evens out) and risk skew (Luk: constant 0.3%). Testable: exit quality vs position size; worst-day distribution → a loss limit. `gb7nNveNBjg` (2025-11). |
| [Specialist-knowledge edges](principles/specialist-knowledge-edges.md) | edge-sourcing | 2/5 | index-rebalance EOD; rest need domain data | no | Preferreds (STRC put sale), biotech clinical literacy, M&A headlines, index rebalancing, **ADR premium — names SK Hynix's US line trading rich to Korea** (⚠ user held SKHY overnight the day this was written). Charts execute, knowledge finds. Course pitch mid-video. `e4m5smJxiVY` (2026-08). |
| [Four constraints + the AI trap](notes/four-constraints-and-the-ai-trap.md) | review-process | process | unfalsifiable; the diagnosis is checkable | — | ⭐ **Best diagnostic frame in the KB:** edge → execution → opportunity → risk, strict hierarchy, fix the current bottleneck only. ⚠ **Lands on this repo**: the Sept-2026 journal reads execution-constrained while the week's tooling was opportunity work. AI earns its keep on trade-database diagnosis and guardrails, not idea generation. `3sug7e1AYk8`, `Z9THivbJ2mI` (2026). |
| [Trade grading (A/B/C/D -> size) + the daily report card](principles/trade-grading-and-report-card.md) | review-process | 3/5 | process (2 rubric variables are EOD) | partial (sizing half tested; **boring-stock/violent-move tested 2026-09-19: INVERTED, normalising by own ADR shrinks the reversion, weak-tape regime is the whole effect**) | ⭐ **Firsthand source for the repo's own process grade — and it is TWO systems, not one.** Per-TRADE grade, assigned BEFORE entry, output = size (= our `alerts/grading.py`); per-DAY report card, post-close, output = tomorrow's focus (= our `run_journal_grades.py`). The secondhand note fused them; the code was always right. ⭐ Ours is MISSING: the rotating single goal *as* the grade, time-block grading (09:30-11/11-12/12-14/14-16), the state->risk dial, the easiest-LAYUP field (the only one scoring trades not taken), and it cannot grade a zero-trade day at all. ⚠ Do NOT import: the C-grade feeler trade (vs precision-over-recall), "compare your grades to your results" (vs gabes-trades-are-not-evidence; and he has no universe control — the error our v1->v2 revision caught), and "size up on A" (size study: exclusion +0.29R vs 10x spread +0.08R). `vKy6Q9hwon4`, `ubofAZwgd4w` (+`M-rpkVekvOQ` cadence). |
| [Hot-streak protocol](notes/hot-streak-protocol.md) | psychology / risk process | process | one claim checkable on `journal_nav` | no | Six proactive steps; the rule underneath: aggression matches the **EV of the opportunity, not the emotional state**. Checkable: day-after-a-top-decile-day P&L (needs a quarter of data). `AVoMjAebyB4` (2026-06). |
| [Macro regimes + playbook rotation](notes/macro-regimes-and-playbook-rotation.md) | regime | framing | untested | no | Rates / inflation / elections / strong vs weak economy → which playbook pays. Slower regimes than the repo's 30-day state (which showed no persistence); defined by opportunity type, not trailing returns — a different object, untested. `9EEUa618xQw` (2026-01). |
| [Anchored VWAP — trend context, not a level](principles/anchored-vwap.md) | regime / trend-context | 2/5 | EOD-testable | no | **Coherent mechanism, honestly presented — but NOT the entry-location tool this KB was opened to find.** He explicitly refuses to use (A)VWAP as a level: "I am not buying or selling simply because we get above or below that line." It is a directional veto (don't short above it unless capitulated) plus a swing trailing-exit structure. ⚠ Null hypothesis unaddressed: AVWAP is a volume-weighted MA with a hand-picked start, and nothing shows the weighting/anchor beats a fixed-lookback trend filter. ⭐ One fully mechanical rule extracts and is the cheapest open test in the repo. |
| [Trend definition + the counter-trend entry](principles/trend-definition-and-counter-trend-entry.md) | entry-location / trend definition / veto | 2/5 | EOD ⭐ (entry) · intraday (VWAP veto) | **yes** (2026-09-19: FAILS — A −0.15R every arm, bare trigger −0.08R ≈ control, deeper/volume-flush worse; VWAP veto arm parked) | Six trend definitions, five of which are "price crossed a line" — the family Stage A already failed (11,227 fires, every arm −0.10 to −0.13R, beaten by a random entry same name-day). Value = the two rules stated **with their invalidation**: no counter-trend until the **break of prior bar highs**, no long below VWAP **unless it capitulates**. ⚠ His counter-trend long is the **mirror image of the bouncy-ball short**, which the harness killed (−0.34R daily vs control +0.34/+0.48) — the long side is untested and is now specced. ⭐ He never says how far above the trend is too far; our 1–2 ADR leak / 0.3–1 ADR winning cell is the measurement he lacks. `vGqaqTUxMG4`@[03:28] supplies the missing extension precondition. ⚠ Evidence = his own trade log + 8 hand-picked winners, asserted as "not hindsight". `ZOHG-OnQuos` (2025-12). |
| [High-volatility playbook](principles/high-volatility-playbook.md) | regime + sizing | 2/5 | EOD ⭐ (the gate) · rest process | **yes** (2026-09-19: NO switch — `t1R` worst arm in BOTH vol halves, H−L ±0.02R, 12/12 cells) | ⭐ **Size ∝ 1/stop, and dollar risk need not fall** — correct, and the third statement of that arithmetic in this KB. ⚠⚠ But its central instruction, **shorten the horizon / cut overnight exposure, is our losing bucket**: same-day exits are the negative bucket in BOTH books (scalp −0.13R vs trail +0.89R; Gabe 278 same-day cycles −$8.3k) and the daily CLOSE entry beats every intraday entry. Scope, not verdict — he is intraday prop with a firm loss limit. ⭐ His regime switch **survives our regime nulls on a real technicality**: it conditions on contemporaneous volatility, not trailing returns, and changes horizon/size, not direction (precedent: VIX<20 is negative for SPY short-dated selling). Gate now specced as an A/B on the breakout book. Vehicle point = capital efficiency, complementary to "no vehicle fixes entries". `mjfONTBf6M0` (2025-04). |

| [0DTE only into expansion events](principles/zero-dte-expansion-events.md) | setup + universe gate (options) | 2/5 | partly EOD ⭐ | partial | Correct on the base rate ("used too frequently, they will drain your account"), correct on frequency (**"a few times per year"**, "entire weeks where conditions do not justify"), pointed at the wrong instrument. Gate = **expansion events only** (breakout / breaking news / exhaustion gap), invalidation pre-stated (breakout reclaims the range → out). ⚠ The adjacent trade is measured: the 1-DTE long ATM straddle is **−30% of premium on 153k trades however you exit it**, and **the bid/ask is the entire P&L** (−1.7% at <5% spread vs −45.0% at >20%) — a variable he never mentions. ⚠ 0DTE forces a **same-day round trip**, the negative bucket in both books, expressing a trigger family Stage A measured at −0.10 to −0.13R. ⭐ His gate (forward catalyst) is genuinely untested; the repo's own event-convexity result (+30.7% vs −3.6%) says buy that convexity with **5 days**, not 5 hours. "Paid two ways by IV expansion" is false at 0DTE (vega ≈ 0). `U9UZ2U6bozQ` (2026-04). |
| [The 4 golden rules for selling options](principles/selling-options-four-rules.md) | regime gate + sizing + tenor (short premium) | 3/5 (rule 1: 4/5; rule 4: 1/5) | EOD ⭐⭐ | partial | ⭐ **Rule 1 lands on a finished repo statistic**: "never, ever sell options during times of complacency" = paid-to-wait ungated **−3.3%** → own-IV ≥60th pct **+5.7% net, 78% win**, and SPY 10-DTE **VIX<20 is NEGATIVE**. ⚠ But he states it as universal and it **inverts on QQQ** (≥80th pct = veto). Rule 2 (only sell where you'd be *happy* assigned; annotate the net-of-premium breakeven) = the BCI finding from the other end (short puts = stock at the same delta minus costs). Rule 3 tolerance ("premium could double and double again" ≈ 3× credit) **calibrates to within ~3× of our measured tail on liquid names** (loss>2×prem on 2.0–2.5%) and is off by 6× on illiquid ones (12.7%). ⚠⚠ **Rule 4 is the conflict** — his "same week, a few days left" is where 10-DTE single-name selling is **net negative, costs = 136% of gross**. ⭐ Finds a real gap: **margin expansion** (CME gold/silver 2026) is unmodelled here. All four are **vetoes, not selection rules**. `eWeGAYvjxh4` (2026-05). |
| [Ross Cameron's system, as relayed](principles/ross-cameron-system-relayed.md) | setup (intraday momentum) + risk process + epistemics | 3/5 (as record) · **1/5 as edge** | universe gates EOD ⭐; trigger = don't buy the data | partial | ⭐ **Best-reasoned skeptic document in the KB.** Splits "is he really trading?" (yes — statements, accountant, FTC deterrent) from "is that record evidence about the method?" (no — livestreaming to thousands in <100M-float names is a reflexivity engine: *"he lights the spark, the chat room is the gasoline, the rest of the world is the rocket fuel"*). ⭐⭐ **Independently derives this repo's own evidence standard**: "the statements close one debate and open another." ⚠ But 13 of 22 minutes endorse **intraday continuation entries Stage A measured at −0.10 to −0.13R with a random entry beating the trigger**, plus same-day exits (the negative bucket in both books) and "press the gas when it's hot" (the breakout-regime study found the paying periods unforecastable). ✅ Agrees: in-play gate, high RVOL (our bar is **≥1.8**; 1.3–1.8 is negative), continuation over shorts, don't cap green days, hard-coded loss limits. ⚠ Asterisk rests on **4 anonymous competitors**. ⭐ One clean test: Cameron's **"80% chance of doubling my loss after I go below max loss"** — run the conditional on our own journal. `sxjsqauWE9E` (2026-04). |

---

## Priority queue

**30 videos ingested · ALL written up** (2026-07-26/27, +`9SgNXrWTefY` 2026-08-02, +8 on 2026-09-09). Two co-equal
tracks — see [README.md](README.md). Nothing below is written up yet except AVWAP.

### ⚠ Next ingest — found, blocked on YouTube rate limits (2026-09-09)

- [x] **`ubofAZwgd4w` "My Trade Grading System that Made Me $100M (A,B,C,D)"** — ✅ INGESTED +
      WRITTEN UP 2026-09-19. The setup-grading → sizing sequel `9SgNXrWTefY`@[19:41] forward-references.
      It delivers the mapping (D fold / C feeler / B standard / A size up) — and the mapping is the half
      `project_size_lever_study` has already partly refuted. See Track B.
- [ ] `jZ5-j7Q4GzY` "ICT is a Fraud, But Do His Trading Concepts Actually Work?" — same cross-source
      format as the Qullamaggie reaction. 429 on 2026-09-09.
- [x] `mjfONTBf6M0` "Best Practices to Navigate High-Volatility Markets" — ✅ ingested + written up 2026-09-19 (Track B).
- [ ] Also unwatched and relevant: ~~`ZOHG-OnQuos` (trend — ✅ written up 2026-09-19)~~, `ABzXM-9LonM` (3-step losing-trade
      review), `_jWWfY_pesY` (daily routine). ~~`sxjsqauWE9E` (Ross Cameron)~~, ~~`eWeGAYvjxh4`
      (selling options, 4 rules)~~, ~~`U9UZ2U6bozQ` (0DTE warning)~~ — ✅ all three written up 2026-09-19.
- [ ] **Ariel Hernandez** — named at [19:19] alongside Kyle Williams as a practitioner of the same
      nuance. Possible cross-source check; not currently in any KB.

### Track A — SETUPS (testable on data already on disk)

- [x] **Watch Before Trading 0DTE Options** — `U9UZ2U6bozQ` ✅ WRITTEN UP 2026-09-19.
      Gate = expansion events only, "a few times per year", invalidation pre-stated. ⚠ Conflicts
      with the 153k-trade 1-DTE study (−30% of premium, and **the bid/ask IS the P&L**) and forces
      the same-day round trip both books measure as negative. ⭐ Untested: the *catalyst* gate.
- [x] **How to Sell Options Like a Wall Street Trader (4 Golden Rules)** — `eWeGAYvjxh4` ✅ WRITTEN
      UP 2026-09-19. ⭐ Rule 1 (sell only after vol blows out) = the paid-to-wait IV gate,
      corroborated (−3.3% → +5.7%); ⚠ rule 4 (same-week expiries) is the tenor where costs are
      **136% of gross** on single names. Also flags margin expansion, which we don't model.
- [x] **99% of Traders Don't Know How to Trade with the Trend** — `ZOHG-OnQuos` (2025-12-20) ✅ WRITTEN UP
      Six trend definitions + the counter-trend entry (break of prior bar highs after a flush) and
      the VWAP veto, both stated with their invalidation. Harness spec written; the long-side prior
      is poor — the mirror-image bouncy-ball short failed at −0.34R vs a +0.34/+0.48 control.
- [x] **Can YOU Spot the 4 KEY Days!?** — `vGqaqTUxMG4` (2025-05-31) ✅ WRITTEN UP (notes only)
      Four pivot-day types on the Apr–May 2025 NQ chart: level break, capitulation bottom,
      trend-break gap + higher low, continuation gap. No entry/stop/size anywhere, outcome known,
      he disclaims it as subjective → no principles file. ⭐ Its one contribution is the capitulation
      precondition (~20% from the MA, "unheard of for the NASDAQ"), folded into the trend spec.

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

- [x] **Best Practices to Navigate High-Volatility Markets** — `mjfONTBf6M0` (2025-04-10) ✅ WRITTEN UP
      Size down as the stop widens while dollar risk stays free; reduce (don't eliminate) overnight
      exposure; spend the daily loss limit late. ⚠ The horizon half conflicts head-on with our
      exit-timing and entry studies; the volatility **gate** underneath it is specced as an A/B.

- [ ] **How to Stop Guessing with Your Stop Losses** — `WgRQWJq54OY` ✅ WRITTEN UP
      The most on-point title on the channel for the stop-fragility question.
- [ ] **The Trade Sizing Strategy that Made Me Millions** — `eDdpTNB04ws` ✅ WRITTEN UP
      The sizing lever itself (position = risk% ÷ stop%).
- [ ] **The Art of Betting Big** (w/ Kyle Williams) — `tIB72PAeZLU` (2025-10-22), 60k chars ⭐
      When to size up. Two elite traders, long form.
- [ ] **52-Minute Risk Management Masterclass** — `hC4g7qY6UcQ` (2026-07-15), 61k chars ⭐
- [ ] **Stop Trading in "No Man's Land"** — `fCp6CRu6E5Y` (2026-02-28). Entry location.
- [ ] **How to Read the Tape with Level 2** — `RKV1rncXSkg` (2026-05-30). ⚠ Check prop dependency.
- [x] **Copy My Trading Report Card That Made Me $100 Million** — `vKy6Q9hwon4` (2025-08-08) ✅ WRITTEN UP
      ⭐ The firsthand source for `run_journal_grades.py`. His card = ONE rotating process goal *is* the grade,
      + time blocks, a sleep/state→risk dial, and "easiest 50k" (the day's easiest LAYUP, not the biggest trade).
      Per DAY. Ours has 5 frozen components and can't score a zero-trade day. **3.5/5**, zero evidence, course module.
- [x] **My Trade Grading System that Made Me $100M (A,B,C,D)** — `ubofAZwgd4w` (2026-08-15) ✅ WRITTEN UP
      Per TRADE, graded BEFORE entry, output = size; one rubric PER SETUP (capitulation vs breakout variables are
      "almost the opposite"). ⚠ His validation loop has no universe control — exactly the error our v1→v2
      rubric revision caught. ⭐ Testable: "boring stock, violent move" = drop% ÷ own ADR. **3/5**.
- [x] **The 60-Day Trading Routine to Becoming Profitable** — `M-rpkVekvOQ` (2026-09-12) ✅ WRITTEN UP
      Restates the report card + the four constraints as a 75-Hard-style challenge; adds only a time budget
      (30 min prep / 2 h post-close / 3 h weekend / 20 chart studies a week). One keeper: judge the day on process
      because "your P&L is often noisy over short periods, but your process is not" [01:36]. **1.5/5**, promotional.

### Track C — cross-source / skeptic checks

- [x] **Reacting to Ross Cameron's Momentum Trading Strategy (Is He Legit?)** — `sxjsqauWE9E`
      ✅ WRITTEN UP 2026-09-19. Second "one trader evaluates another" relay after Qullamaggie.
      ⭐ Independently derives our own evidence standard ("the statements close one debate and open
      another"); ⚠ but endorses the exact intraday trigger family Stage A killed. One clean test:
      Cameron's "80% chance of doubling my loss after I go below max loss", on our own journal.
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
