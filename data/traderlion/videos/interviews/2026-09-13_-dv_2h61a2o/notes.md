# TraderLion: "The 7 Steps to a Profitable Trading System" (Ariel Hernandez with Richard, published 2026-09-13, 2 h 18 min)

_Reviewed 2026-09-30. Recorded 2026-06-17 (FOMC day, "recording June 17th" [0:07]), published three months later.
It is a slide deck, "Puzzle Pieces to Profitability", with ~21 "non-negotiables" in five parts: foundation,
selection, execution, management, survival. Richard (Deepvue) chimes in throughout, and there is a Deepvue
sponsor read at [0:17]. The title's "7 steps" are the seven foundation pieces. Transcript (`en-orig` auto-captions)
is in this folder. Timestamps are `[h:mm]`, from the transcript._

⚠ The video id starts with `-`, so pass it to yt-dlp after `--`. The folder name keeps the real id (ASCII).

## Verdict: 2.5 / 5

**What's good.** This is the most complete statement of his process on record, and most of it is numeric:
- **Risk per trade 0.25–0.30%** of equity ("more than 1% is gambling"), stop at the low of the day, at most
  1–1.5 ATR and never more than 7–8% [1:32–1:42]. Open heat is capped at ~2%, and correlated names count as
  one bucket [1:59].
- **Universe rules** with thresholds, below.
- He discloses his losses: an 11-trade losing streak in October 2025 (−1.5%), a 35–40% win rate, and the
  SanDisk breakout he passed on [1:34, 2:08, 1:22].

**What isn't.**
- There is no track record and no base rates, and the examples are all winners: PLTR, CLS, HOOD, DELL,
  SNDK, gold.
- The parts presented as the edge are the ones our data contradicts or inverts:
  - groups first;
  - names that held up in the correction;
  - the market filter;
  - trimming into momentum bursts;
  - trimming harder as extension grows;
  - progressive exposure.
- His selection half does have support (below), and his risk hygiene is sound but not an edge.

## His criteria, pinned down (this video)

| piece | stated rule | @ |
|---|---|---|
| Market filter (no new longs) | index **below its 50-day AND 10 < 20, both sloping down**; exception: a follow-through day | [1:27] |
| Risk on | index > 50-day > 200-day, breadth expanding, tech/QQQ leading | [0:15] |
| Groups | trade only names in the **top 40** industry groups; "worst stock in the strongest group > best stock in the weakest group"; "half of any stock's move is its sector" | [0:24–0:28] |
| RS | IBD RS ≥ 70, prefers 80–90; names within 10–20% of their high while the market falls | [0:22, 0:35] |
| **Momentum scan** | **≥ 70% above the 52-week low · price > $10 · > 2M shares/day · price above the 50 SMA (or up to 5% below)** | [0:52] |
| CAN SLIM scan | accelerating EPS **and** sales, ≥ 25% QoQ or TTM; near 20-day highs; **market cap > $1B** | [0:51] |
| Event scans | episodic pivots / power earnings gaps; HVC; buys gap days on day 2–5, not day 1 | [0:53, 1:12] |
| Liquidity | "just north of $100M a day" for his size; "you're not missing any of the best stocks if you set a filter at **$60M**" | [0:57–0:59] |
| Volatility | **"don't trade stocks with less than 3% ADR"** (Richard: 5–8% sweet spot) | [0:59–1:00] |
| Universe size | 100–150 names; ≤ 50 worth attention on any day; 8–12 with alerts | [0:50] |
| Extension veto | no new buys **> 4× ATR above the 50 SMA** (bending to 5× lately); earnings gaps exempt; never buy after the stock has already moved its full ADR that day | [1:28, 1:38, 1:40] |
| Trims | ⅓–½ into a 3–5-day momentum burst of 8–20%; then 10% of what is left for every ATR beyond 7× ATR above the 50 SMA | [1:50–1:52] |
| Adds | only on a fresh setup, smaller than the original, treated as a new position | [1:53] |
| Trail | price structure (higher lows) over the 10/20/50; the 200 is "the line in the sand" | [1:43–1:45] |
| Sizing feedback | progressive exposure: add as trades work; shrink 10% → 7 → 5 → 3% position size through a losing streak | [1:34, 1:55, 2:08] |
| Shorts | names below the 200 SMA shorted into a declining 20/50; parabolic shorts covered on day 2; 0.25% risk | [2:02–2:07] |

## AH encoding vs what he says here (`lib/minervini/scan.py` AH_*, `run_universe_test.py`, `run_ariel_ablation.py`)

| criterion | ours (AH, from his 2026-01-11 universe video) | this video | matters? |
|---|---|---|---|
| a1 ≥ 70% above the 252d low | ✓ same | same | leans ADDS inside INT (t −2.74) |
| a2 close > 50 SMA | strict | **"or up to 5% below"** (to catch Kell wedge pops) | inside INT it is subsumed by TT c5/c6 regardless; only AH-alone changes |
| a3 ≥ 2M sh/day | ✓ same | same | **certified ADDS** (t −4.24) |
| a4 price | **> $7** | **> $10** | a4 is inert (+0.02pp, t 0.81); immaterial |
| a5 ADDV | ≥ $100M | $100M for his size, **$60M** "enough" | inside INT the TT floor ($200M) binds, so INT is stricter than either |
| ADR floor | **none** | **≥ 3%, a hard rule** | not encoded. INT's median ADR is 3.5%, so it cuts maybe a third of names; nearest evidence HYB-B (TT@$100M + ADR ≥ 4) PARKED t 2.6; HYB-A's raw lead was ADR |
| market cap | none (not in the panel) | **> $1B** (Jan video: > $300M or > $1B) | ADDV ≥ $100M does most of it on the liquid panel |
| second scan (CAN SLIM C+A, near 20d high) | not in AH | part of his universe | EPS-C as a filter: **NULL 2026-09-30** ([BB-2], `canslim_c_filter_2026-09-30.md`, INT∧C − INT −0.43pp t −0.85) |
| discretionary admission (theme, linear prior move, "personality") | none | the final cut | not encodable |

**Read.** AH is a faithful encoding of his *momentum scan* only. His *universe* adds an ADR ≥ 3% floor and a
$1B market cap, and it is the union of three scans plus a discretionary cut. The criterion ablation
(`ariel_ablation_2026-09-28.md`) has already run on the AH encoding. The two criteria that bind (a1, a3) are
identical in both videos, so the ablation's verdict stands. The one encoded difference that could matter is the
**ADR ≥ 3% floor** (spec below, low priority).

## Claims against our ledger

| @ | claim | our evidence |
|---|---|---|
| [0:12, 1:27] | Market filter: no new longs when the index is below its 50 and 10 < 20, both falling | ❌ **NULL.** QQQ 10/20 index filter on 55k house breakouts: RED −0.86pp, t −1.68, halves flip; SPY < 200d is *better* (+1.18pp). "Market state doesn't sort breakout outcomes" (`index_filter`, TEST_INDEX §7, WL-5e). FTD as a regime switch fails |
| [0:24–0:28] | Top-40 groups; worst stock in the best group beats best stock in the worst | ❌ **INVERTED at the sector level:** bottom-3 sector breakouts beat top-3 by +5.60pp at 63d, t 2.61, and the gap survives net of the sector ETF (rotation study §12–13). Same-morning theme co-breakouts NULL (+1.61pp, t 1.80) |
| [0:22, 0:35, 0:40] | Names holding up while the market falls are the next leaders | ❌ **NULL leaning INVERTED:** weak-tape leaders −0.69pp at 40d, t −1.50, worst in V-recoveries ("the recovery is led by what fell"); down-day RS **INVERTED** −3.51pp, t −3.33; TT c9 RS ≥ 70 UNDERPOWERED |
| [0:42] | Post-FTD, leaders keep giving secondary setups | ⚠ UNDERPOWERED: post-FTD *controls* beat other periods, but the breakout entry is worse (8 episodes; `ftd_names`) |
| [0:52–1:00] | Momentum scan + liquidity + ADR ≥ 3 select | ✅ **Partly agrees.** AH beats TT on selection (+0.87 vs +0.56pp ADR-matched, not significant); a3 certified, a1 leans; INT is the production universe. ADR ≥ 3 itself: see the spec |
| [0:50–0:51] | Accelerating EPS + sales keep a winner from round-tripping | ❌ EPS-growth filter NULL (BB-2, 2026-09-30); sales untested |
| [1:28, 1:38] | Don't buy > 4× ATR above the 50 SMA; don't buy once the day's full ADR is used | ⚠ **Direction agrees, rule untested as stated.** The leak is the *entry location* (breakout pays +0.52 ADR above the 20d high vs −2.09 for a random later same-name entry, `entry_vs_stop`). But extension is a **timing** variable, not a **selection** one: ranking candidates by extension within a date is negative (t −2.06…−0.95), and the best extension gate (distance to the 21 EMA) is +0.057R, t ≈ 2 (`breakout_hold_predictors`). The house breakout already vetoes days up ≥ 8% |
| [1:50–1:52] | Trim ⅓–½ into a 3–5-day burst; trim 10% per ATR past 7× | ❌ **INVERTED.** Qullamaggie partial-then-trail (day-3/5 and +2-ADR-burst partials at 20/33/50%) −1.87pp, t −4.39; trims −0.25…−0.33R; "extended → tighten" −0.19R, t −2.8 (`profit_lock`) |
| [1:53] | Add only on a fresh setup | ❌ NULL: add-to-winner re-fire −0.77pp, t −0.55; O'Neil pyramid NULL |
| [1:43–1:45] | Trail on structure (higher lows), not MAs | **Untested as stated.** The nearest are the 20-EMA trail (kept; trail cost ≈ ¾ beta, `trail_cost_exposure`) and trail_bar (prior-bar low), which never beats the 20 EMA. A swing-low trail has not been run (spec below, low prior) |
| [1:32–1:42] | Stop at low of day, ≤ 1–1.5 ATR, 0.25–0.3% risk | ✅ risk hygiene agrees (Brandt's fixed 60–70 bp agrees too). ⚠ Our tight stop (the session low) is judged **on the close**, while resting it intraday is rejected (`stop_definitions.md`). His "never buy after the full ADR" is the same instinct as our close-entry finding |
| [1:34, 1:55, 2:08] | Progressive exposure; shrink size through losing streaks | ❌ **NULL as a return lever:** simulated adaptive trader — no feedback rule beats trading flat; anti-martingale rules *lose* (−0.31 log wealth); DD-cut halves max DD at about half the growth = risk reshaping. Strategy persistence ρ −0.01 (WL-2b) |
| [0:48] | When a group laggard breaks below its 50, the leaders follow in 1–3 weeks ("my own observation") | **Untested; the one new axis** (spec below). Low prior |
| [0:40] | (Richard, from Eve Boboch) after a correction low, rank names by % change since the key low (5d) and over 1 month | **Untested as a ranking.** The weak-tape study found recoveries led by what fell, which this ranking would catch (spec below) |
| [2:02–2:07] | Short names below the 200 into declining MAs | ⚠ mixed: the pullback-short arrival screen FAILS; the gap-up fade below a declining 50 SMA in falling breadth is PARKED (+0.54%, t 3.87, cost-fragile, paper-forward) |
| [0:59] | "Half of a stock's move is its sector" | descriptive; the nearest number is median liquid-name ρ with QQQ 0.33 (R² 0.11). Not a strategy |

## Specs (NOT RUN; pre-registerable)

### 1. Laggard-breakdown contagion (the one new axis)

- **Event:** a "former leader" breaks. The name was in the top RS quintile of its GICS industry (126d) 20
  sessions ago, has its first close below the 50 SMA after ≥ 40 sessions above, and the industry has ≥ 4 panel
  names.
- **Arms:** the industry's *other* names still above their 50 SMA on the event date. Forward 5/10/15-session
  ADR-matched excess vs same-date names in industries with no such event.
- **Primary:** 15d. Two-sided: he says the leaders follow, but the rotation and weak-tape results lean to
  mean reversion. Date-clustered t; halves split 2018-01-01; per-year table. Bar |t| ≥ 3, Šidák over 3 horizons.
- **Confound:** a common industry shock (the laggard broke because the industry fell). Also report the excess
  net of the industry's equal-weight return on day 0.
- **Panel:** `liquid_panel_2009` + `data/ticker_industry_map.csv`. ~½ day, local. Prior: low. Group-level RS
  has been descriptive, not predictive, every time.

### 2. Strongest bounce since the correction's key low

- **Episodes:** reuse the 60 breadth-washout episodes from `run_weak_tape_leaders.py`.
- **Day 0** is point-in-time: the first close with breadth back above 35%. Rank each eligible name by its return
  from the episode's lowest-breadth close to day 0.
- **Cells:** top quintile vs the ADR-matched field at 20/40d; one observation per episode.
- **Power ceiling:** 60 episodes, so this cannot certify a rule (|t| ≥ 3 at n 60 needs a large effect).
- **Prior:** moderate in direction (the weak-tape study saw V-recoveries led by what fell), low on size.
  Watch the 1-month short-term reversal confound.

### 3. Swing-low structural trail vs the 20-EMA trail

- **Rule:** exit on a close below the most recent *confirmed* swing low (pivot low with 3 bars either side,
  usable only once confirmed).
- **Setup:** precision pool, paired % per trade, same frame as `run_rs_loss_exit.py`.
- **Controls:** a random exit drawn from the trail's own holding-time distribution, and the beta-matched SPY
  fill from `run_trail_cost_exposure.py`. A looser exit wins on exposure alone; the RS-loss "pass" on 2026-09-30
  was exactly that.
- **Prior:** low.

### 4. (low priority) ADR ≥ 3% on INT, his stated hard floor

- **Test:** add one criterion, INT ∧ ADR20 ≥ 3% vs INT, paired, 20d, `run_trend_template_ablation`
  frame.
- **Report raw AND ADR-matched.** ADR-matching removes most of what an ADR filter does by construction, so the
  matched cell asks only whether the low-ADR names INT keeps are *worse than their own ADR peers*.
- **Prior:** low. HYB-A's raw lead was ADR. Cheap (minutes) if wanted, but probably not a new answer.
