# KINFO -- "$10,000,000 Verified Day Trader: His Core Patterns, Process & Live Trades" (David Veprek, 2026-07-25, 70 min)

_Reviewed 2026-09-23. Host Stephen Johnson ("Transparent Traders"); guest David Veprek, CFA, #2 on Kinfo's all-time
leaderboard. Three worked trades (MOBX long, SIDU short, SpaceX-IPO basket long/short) plus his morning process.
Transcript (`en-orig` auto-captions) and `meta.json` in this folder. The chapter list in the description matches the
content (unlike OneOption's SEO blurbs)._

Two funnels run through it: a Kinfo subscription ad at 15:00 ("50% off for life, $12 a month"), and TraderPods,
the guest's wife's free community, which is where he says his live ideas now go. Neither sells a course or signals.

## Verdict: 2.5 / 5

**The provenance is the best of any trader reviewed here and the method is the least transferable.** He is the
most credible person in these KBs. He's broker-linked, shows a ~$200k loss in detail, admits a four-year drawdown,
and says the CFA "probably" didn't help. But everything that makes money in his account happens in a universe we
don't have: sub-$1 to low-single-digit small caps gapping 40%+ pre-market, traded on float, dilution and
underwriter research. The one mechanisable piece that overlaps our data (buy the catalyst day, then enter on a
pullback) is already NULL/negative on the liquid panel. His real edge, reading the press release, is catalyst
**classification**. That's our open queue item #1, and we have no historical news text to test it with.

Score split, in the style of the Mari Trades review: **provenance 4/5, process 3/5, testable claims 1.5/5.**

## Provenance: what exactly is "verified"?

| question | what the video establishes | what it does not |
|---|---|---|
| Mechanism | Kinfo links broker accounts; trades are shown "verified on Kinfo" (the MOBX fill is shown with prices 0.44 to 1.15, +$184k, 22:39). Same mechanism as the Malik review: the dollars are very likely real money actually made | Kinfo books **realised P&L on closed positions** (Malik's own correction, `data/video_reviews/kinfo_malik_tqqq_2025-09-11.md`). The "$10M" is **cumulative dollars, not a return**. The profit curve is on screen at 8:54 but never read out, so the transcript gives no start date, CAGR or max drawdown |
| Period | Trading since 1999; hedge-fund job 2003; own merger-arb book 2006; penny-stock and cannabis promotions ~2009-2014; "a really good stretch" early 2021; **a four-year drawdown from mid-2021 to 2025**; a run in 2025-26 | We can't tell which years the $10M comes from. By his own account the curve is lumpy: two good stretches bracketing four flat-to-down years. **That is regime-dependence, the pattern our breakout book shows (the edge lives in the busy months), not a steady edge** |
| Account size | "I trade with a big account, so the risk… was small relative to the account size" (31:52). The stock "could have gone to zero and I would have been fine" | **No account size or return on capital is ever stated.** A $10M P&L on a $50M book and on a $2M book are different claims. ⚠ Since 2025 he also runs **a fund seeded by three partners** ("Helium Master Trading", 9:00). Is the Kinfo account personal, or the partnership's, or both? The video never says, so we can't tell whose capital the profits were earned on |
| Survivorship | He is **#2 on the all-time leaderboard**, and the channel interviews leaderboard toppers | **The denominator is every Kinfo-linked account**, and neither the size of that population nor its P&L distribution is ever shown. The #2 of N accounts is the maximum of a distribution, and a maximum proves only that the tail exists. Kinfo also only sees accounts people *chose* to link, which adds a self-selection layer on top. The channel's business is the leaderboard, so it has every reason to show the top and none to show the median |
| Shown trades | One best long (MOBX), one worst short (SIDU), one best thesis (SpaceX basket) | All three are picked **because of their outcomes**. That's more honest than showing winners only, but it is still three hand-picked tails, not a sample. No win rate, no expectancy, no trade count |

**Net:** the dollars are real and the trader is genuinely skilled at *something*. The record can't tell us whether
that something is a repeatable mechanical edge or twenty years of discretionary pattern-matching in a niche
(small-cap promotions, dilution games) that he himself says keeps dying and needs reinventing (merger arb, then 2008
arb, then penny promotions, then cannabis, then small caps). **His own biography is the strongest argument that the
edge is non-stationary.**

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 15:54 | Scanner = biggest pre-market % gainers; **ignore anything under +40%** (small caps) | **Outside our universe.** The liquid panel ($100M ADDV floor for shorts; DR-EP catalyst = gap >=3% & RVOL >=1.8 & ADR >=3) almost never contains a +40% gapper. The same block as Mari Trades (§10: "PARKED, blocked on data -- do not queue until a small-cap low-float universe exists") |
| 16:05 | Float first (dilutiontracker.com); **under 1M float: won't short**, or only small | **Untestable here** (no float or dilution data in the repo). As a *risk veto* it's sensible and costs nothing: it's the squeeze tail, the same "size by the tail" logic as our max-loss rule |
| 16:30-18:17 | Research dilution: underwriters, warrants, converts, ATMs, SPAs, institutional ownership, **when the company usually raises** (pre-market / intraday / after hours) | **Untestable here, but the most concrete testable hypothesis in the video**, given data: SEC EDGAR S-3 / 424B filings are free and point-in-time. See "Not tested, could be" |
| 17:00 | Paste the PR into Claude: is it repeat news? already known? any forward catalyst? China ties? | This is **catalyst CLASSIFICATION**, the live residual in `project_catalyst_queue` after DR-EP closed the timing half. We can't backtest it: `run_news_pull.py` only merges live TradingView MCP pulls, so there is no historical point-in-time PR archive. It **can be run forward**, as a logged classification scored later (thesis-log style) |
| 19:40 | **H.C. Wainwright** deals are "typically the best at manipulating the stock", so they're harder to short | **Anecdote, n unknown.** Codable only with offering-participant data. Plausible mechanism (the underwriter wants price and volume before pricing), not evidence |
| 20:17-29:24 | MOBX: US Navy Tomahawk PR on day 4 of the Iran war. Bought the **shallow pullback** ~35 min after a +200% spike, sat through 3 h of sideways, sold 3/5 into the 11:10 breakout, held 2/5 overnight, sold pre-market. **+$184k, "best long of the year"** | **n = 1, selected as his best.** The mechanisable skeleton (buy a catalyst day) is **DR-EP arm A: -0.173R, t -4.70, both halves negative, loses to both controls** (6,815 events, `drep_catalyst_retrace_2026-09-22.md`). Deferring entry helps only from bad to less bad (arm B -0.067R, t 0.21), and **the catalyst gate adds nothing** (B is worse than the ungated retrace D at -0.057). ⚠ That's the liquid panel with a daily close entry and a multi-day trail. His trade is intraday on a sub-$1 name, so this is **not a refutation** (creator patterns have no fixed timeframe). He himself says the technicals didn't matter: "it was more about the news being the right news in the right environment". The edge he claims is the classification, which DR-EP didn't have |
| 25:00 | Shallow pullbacks = the long entry, and also the signal to stay out of the short | **Closest intraday analogue: the ORB retest (2026-09-23).** Conditional on firing, the retest beats a random minute by **+0.324pp (t +4.45)**, the only intraday arm here ever to clear that control. **But it fails as a strategy**: on days that never come back the break earned +1.264%, so waiting for a pullback misses the best days. His "shallow pullback" on a +200% spike is that trade-off in its most extreme form |
| 29:30 | Scale out with a "D-WAP" (time + price schedule) | Execution tooling, not a claim. Consistent with our stance that the intraday machinery is execution insurance |
| 31:52 | Start small, add as it works, "add to winners, not losers" | **O'Neil pyramid NULL** (2026-09-22): adds earn the same edge as the base, and no add condition beats the unconditional add. Scaling **scales** an edge, it doesn't create one. Fine as risk control |
| 32:00-44:00 | SIDU: shorted a +50% "first green day" in a serial diluter (5 raises in 2025, with the Dec-22 and Dec-26 gap-then-offering precedent), expecting an after-hours offering. None came; no stop; fought it and **added** on day 3 (including a "red-to-green" re-short). **Lost ~$200k** where a day-2 exit cost ~$25k. The offering did come 17 days later | ⭐ **His own best illustration of the queued Cameron/Breitstein test** ("80% chance of doubling the loss after breaching max loss", §7, Breitstein queue test 1). A **thesis-invalidation exit** (the expected event didn't happen by the close, so get out) would have capped it at ~$25k. That's an **8x** loss multiplier from fighting it, one instance. The short side is also consistent with our **short-universe NULL** (2026-09-23): 0 of 10 cells, and 10/10 weak-name universes still had a *positive absolute* return. "Right thesis, wrong timing" is exactly why a short must beat drift, not just a benchmark |
| 34:00 / 43:00 | The mistake: **ignored that space was the hottest sector**. Only size up when fundamentals *and* technicals align | **Partly contradicted on the long side of the same variable**: industry-rotation study, breakouts in **bottom-3** sectors earned **+14.55%** vs **+7.11%** in top-3 (t 2.6, INVERTED), and down-day RS as a selection filter INVERTED (-3.51pp, t -3.33). For a **short veto** ("don't short the leader of a hot group") we have no test. The "confluence" rule is untestable without his fundamental tag |
| 38:00 | "Red-to-green" short: gaps down, crosses back above the prior close, short it | **Untested as a short.** The level-trigger family (PDH/PDL/21EMA/AVWAP/ORH, 20,148 name-days) is **NULL 0/12**, and "the level picks the DAY, not the minute". Descriptive: a gap-down >=0.5 ADR closes back above the prior close only **15.8%** of the time (per-name affinity study), which is the base rate the short is betting on. Prior-close crossing is the one level not in that test |
| 44:04-52:00 | **Buy the rumour, sell the news**, "made me millions": the SpaceX IPO (June 2026). Long DXYZ (closed-end fund, ~15% SpaceX) from 3/11, added on the 3/24 valuation news, sold into strength and bought the dip when it traded **above NAV**, all out by 5/22, **3 weeks before the IPO**. First buy 29, last exit 64 | **n = 1 thesis.** Nearest ledger rows: **index-add run-up reversal FAIL** (173 adds, T+5 -1.00%, t -1.17, bar 3) and **FOMC pre-drift FAIL**, i.e. scheduled-event run-ups don't reverse reliably in our tests. The **pre-event OTM calls +1.9pp at real fills** (earnings) is the one positive "own it into the event" cell. The IPO class is a known **structural blind spot** (§10 IPO-lockup row: SMA200 + 400-bar minimums exclude every IPO). ⚠ The population of *mega*-IPOs with a listed proxy is maybe 5-15 events ever, so this is **UNDERPOWERED by construction** |
| 47:00 | Next: **Anthropic IPO "around October-ish"**; DXYZ holds ~18%; already long DXYZ, same plan | **A tip, not evidence.** It is also a live, checkable, pre-registered forecast: long DXYZ into the IPO, flat before, short weak sympathy names after. Log it; don't act on it (see "What I would take") |
| 50:50 / 52:00 | DXYZ trading above NAV means sell; estimate NAV by marking the private holdings with Claude | **Closed-end-fund premium/discount reversion** is a real, well-documented literature effect. Untested here. With one fund and marks he builds himself, it's a judgement call, not a rule |
| 56:08-1:04:00 | Short a basket of **low-quality** space names (ASTI, SPCE, MNTS) on the SpaceX IPO day, cover 2-3 days later. Reduced size because the group had already faded into the event. "Weaker ones roll over first, then the leader" | The short leg is small (~$31k on MNTS, shown) and admits the setup was degraded. The "weak roll first / leaders break out first" sequencing is untested here. Our rotation work says we **can't front-run** group moves (leading-group filter INVERTED) |
| 1:05:07 | Risk management: big stubborn losses cost the loss **plus the next good trades** (opportunity cost); size way down in drawdowns; the edge needs reinventing | ✅ Agrees with the book: fixed small size, the **size lever is exclusion** (+0.29R OOS) not a 10x spread, and "the paying months can't be forecast". His "size down in a drawdown" is a trailing-own-P&L rule, and **every trailing-30d rule from August failed 2019-26**, as did the Stage-A own-P&L feedback (NULL). So: agreed as survival, not as a return lever |

## His core patterns as codable specs

All normalised to ADR / the spike's own range, so they're not tied to a timeframe. "Covered?" means the ledger
has run something that would catch it.

| # | Pattern | Codable spec | Covered? |
|---|---|---|---|
| P1 | **Day-one news long** | Universe: pre-market gap >= max(40%, 8 ADR20), with a PR in the last 12 h. Gate: catalyst class in {new, material, forward-looking, in-theme with a live macro story}. Veto: repeat or already-known news, China ties. Entry: first pullback after the initial spike that retraces <= 0.382 of (prior close to spike high) and holds for >= 15 min. Stop: below the pullback low (quote stop/ADR). Exit: scale 60% into a break of the spike high, carry 40% overnight, sell pre-market | **Skeleton: YES, negative** (DR-EP A -0.173R t -4.70; Stage A intraday triggers ~= random minute; ORB retest wins conditional on firing but loses as a strategy). **Differentiator: NO.** The universe (+40% small caps) and the news-class gate are both outside our data. **It is a SELECTION rule, not a trigger**, so Stage A doesn't refute it |
| P2 | **Day-one dilution fade (short)** | Universe: gap/day gain >= +50% (or >= 5 ADR20) with no material news, float >= 1M. Gate: serial diluter (>= 2 offerings or an active ATM/S-3 in the last 12 months; the historical raise-timing pattern matches). Entry: short into the last hour on day 1. **Thesis stop: cover if no offering by the next open** (his SIDU lesson). Veto: the name leads a hot sector | **NO.** Needs EDGAR filings plus a small-cap price panel. The liquid-panel short universe is NULL 0/10; exhaustion fade FAIL; bouncy ball FAIL. **Selection rule (fundamental), not a trigger** |
| P3 | **Red-to-green short** | Open <= prior close - 0.3 ADR; first 1-min close above the prior close means short; stop = session high so far (floor 0.6 ADR); exit at the close | **Partly.** The level family is NULL 0/12 and the per-name gap-down reclaim base rate is 15.8%, but the prior close as a short trigger isn't in the level test. A Stage-A-style trigger, so the prior is that it will ~= a random minute |
| P4 | **Buy the rumour, sell the news (scheduled mega-event)** | Event E with a known date >= 60 sessions ahead. Long the listed proxy / quality sympathy basket from E-60, add on news-driven volume days (RVOL >= 2), **flat by E-15**. On E, short the weakest (dilution-prone) sympathy names at the close, cover at E+3 | **Partly and UNDERPOWERED.** Index-add run-up reversal FAIL, FOMC pre-drift FAIL, pre-event OTM calls +1.9pp. IPO events are a blind spot. Mega-IPO n is too small for a t-test |
| P5 | **Thesis-invalidation exit** | Any trade whose thesis names an event and a deadline ("offering after the close"): exit at the deadline if the event hasn't happened, whatever the P&L | **Queued** as the Cameron/Breitstein max-loss doubling test (Breitstein queue test 1), which can run on the journal for *conformance* only |

## What I would take

1. **P5, the thesis-invalidation exit, as a desk rule of conduct.** It's the same as our "never add to a loser past
   max loss", with an event deadline added. His SIDU loss is the cleanest public example: ~$25k becomes ~$200k.
   It's a conduct rule, not an edge claim, and it's consistent with the queued Breitstein test 1.
2. **The low-float short veto** (no short under ~1M float) whenever we're near small caps. It's a free tail-risk rule.
3. **Log the Anthropic-IPO call as a forward, pre-registered observation** (DXYZ long into the IPO, flat before it,
   weak-sympathy shorts after). Score it when it resolves. **Do not trade it on his say-so**: n = 1 thesis, and he
   has the position already.
4. **A method note:** "paste the PR into an LLM with a fixed question list" is a cheap, codable classifier. It's
   the only concrete proposal we have for the catalyst-classification residual.

⛔ **Not taking:** the leaderboard as evidence of a method (survivorship, above), the hot-sector-respect rule for
longs (our data inverts it), or add-to-winners as an edge (O'Neil pyramid NULL).

## Not tested, could be

- ⭐ **Catalyst classification by LLM, forward.** Every day, take the liquid-panel names that gap >= 3 ADR on
  RVOL >= 1.8 (the DR-EP catalyst definition, ~5/day). Pull the headline and story via the TradingView MCP
  (`run_news_pull.py`). Have Claude label each one with his five questions (new? already known? repeat? forward
  catalyst? in a live macro theme?) **before the close**. Score each class forward vs DR-EP arm A's -0.173R
  baseline and the same-day unclassified gappers. **No backtest is possible** (no point-in-time news archive), so
  this is a lockbox. Power: ~100 events/month gives a t-test on class spread in ~6 months. **~1 day of plumbing**
  (a classifier prompt plus a log table) and then passive. It's the test that directly addresses queue item #1.
- **Dilution-state day-one fade (P2)**: EDGAR S-3/424B/ATM filings, point-in-time, free. Blocked on the same
  small-cap price panel as Mari Trades. **When that panel exists, run P2 alongside Mari's first-green-day test.**
  ~2-3 days including EDGAR parsing. Prior: the thesis stop matters more than the entry.
- **Red-to-green short (P3)**: ~20 lines in `pattern_test` on the Stage-A 1-min caches, same-name-day
  random-minute control. Cheap (~2 h) but low prior (level family 0/12). Run only if batching intraday nulls.
- **Closed-end-fund premium/discount reversion**: literature effect, untested here. Out of scope for the desk
  unless we start trading CEFs.

## Links

- Prior KINFO review (Malik, TQQQ/SQQQ, 1.5/5; how the "verified" claim was treated): `data/video_reviews/kinfo_malik_tqqq_2025-09-11.md`
- `data/studies/drep_catalyst_retrace_2026-09-22.md`, `short_universe_test_2026-09-23.md`,
  `orb_retest_vs_break_2026-09-23.md`, `index_add_study_2026-09-20.md`, `industry_rotation_detection_study.md`
- `data/studies/TEST_INDEX.md` §5 (Stage A, level triggers), §7 (catalysts), §10 (Mari first-green-day PARKED,
  IPO-lockup blind spot, catalyst-as-selection)
