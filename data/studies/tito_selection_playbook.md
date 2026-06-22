# Tito Adhikary — Selection Playbook (Directional Swing, Options as Vehicle)

> **Status: DRAFT / accumulating.** This codifies Tito Adhikary's *stock selection* edge for
> directional swing trades. Source: a 20-trade spreadsheet with his own Setup_Type / Days_In_Trade /
> Entry_Price / Return columns. Vehicle mechanics (strike/DTE) now characterized from his data.
>
> ⚠⚠ **These 20 are a CURATED "best trades" list — survivorship-biased.** The 20/20 win rate and ~1900%
> average are a **highlight reel, not an expectancy.** Use them to learn *what his winners look like*,
> never to estimate hit rate or edge. (See the survivorship caveat in the exit-timing section.)
>
> Belongs to the long-side swing/breakout pipeline (see `premarket_watchlist.py`,
> `ibkr_bot/breakout_monitor.py`, `scratch_eval.py`, `theme_strength.py`), NOT options-selling research.

---

## Core Philosophy (extracted, will grow)

- **Trade stocks with a history of big moves.** Pre-filter the universe to high-volatility,
  large-range names. He wants vehicles that *can* move, because the whole thesis is a directional swing.
- **Buy breakouts from tight bases**, specifically VCP (Volatility Contraction Pattern):
  a completed downtrend → basing → contractions tightening (higher lows, lower highs) with
  **volume drying up** into a flat resistance line, then enter on the **high-volume break** of that line.
- **Require trend confirmation** before the breakout: the short/medium SMAs stacked in the correct
  (bullish) order.

---

## Four Archetypes (= Tito's own Setup_Types: Breakout / Earnings / Exhaustion / Catalyst)

These map 1:1 to Tito's own labels — **A=Breakout, B=Earnings, C=Exhaustion, D=Catalyst** (see the
ground-truth reconciliation below; his labels are canonical). **A & B are long breakouts** that share a
base and differ at the trigger. **C is the mirror trade** — a short-side (put) fade of climactic
*extension*. **D is the outlier** — a long entered *below* the (multi-month) pivot to position for a
macro event. All trade the **same universe** (history of big moves); direction and bar-signature flip.
⚠ Note Tito's **Breakout** bucket is broad — it absorbs most of "B" and any *local*-base breakout; his
**Earnings** and **Catalyst** are narrow specialist setups (n=1 and n=2). Detail below.

A & B both require: **history of big moves** + **prior deep base that contracts with volume drying
up** + **breakout through resistance**. They differ in the *trigger* and the *volume/trend signature*:

- **Archetype A — Technical VCP breakout** (TSLA 2025-09-11, RKLB 2025-06-23, GEV 2024-08-29, plus
  NVDA 1/8, GLD 3/1, BRKB 7/11, MSTR 10/11, IWM 7/11, BABA 9/19 — see roll-up):
  pre-established SMA stack + **modest** breakout volume (~1.1–1.2×) with the **real volume expansion
  the NEXT day**, decisive close through flat resistance. Two gates the 3rd case (GEV) loosened:
  - **Stack durability ≥ ~1–2 weeks, not 20d** — GEV's stack held only **9d** and worked; TSLA's "held
    ~20d" was that case's specifics, not a floor.
  - **Shakeout-under-pivot is common, NOT mandatory** — TSLA/RKLB had recent failed pokes; GEV was a
    **clean first break** of long-standing resistance with no failed poke in the prior 20d.
- **Archetype B — Earnings-catalyst breakout** (APP 2025-08-07, PLTR 2024-11-05, ARM 2024-02-08,
  SMCI 2024-01-19): contracting base with **higher lows + volume drying up**, then a **day-after-event
  thrust** closing **decisively above the pre-event pivot, near its high**, behind a **fundamental
  positive surprise**. That four-part signature is the **invariant**. Range across the 4 cases:
  - **Catalyst volume has NO ceiling:** APP 3.65× / PLTR 3.53× / SMCI 7.3× / **ARM 15.15×**. ~3.5× is a
    floor-ish typical, not a cap — gate **≥ ~2×**, don't bound it.
  - **The "earnings" can be a guidance pre-announcement:** SMCI entered on a **1/18 AMC preliminary
    guidance raise**, not the full print (which came later). The trigger is a *fundamental upside
    surprise + raised numbers*, whatever form it takes.
  Two features that vary (do NOT gate on them):
  - **Trend state is free:** APP still had the **50 overhead** (50>10>20); PLTR was already a **full
    10>20>50 stack**. The catalyst carries it either way — full stack is fine, 50-overhead is fine.
  - **Entry mechanic has two modes:** **dip-then-reclaim** of the pivot (APP: dipped 385 → reclaimed
    400) *or* **gap-and-hold** above it (PLTR: gapped over the 45.14 pivot, day's low never lost it).
    Either way, **don't chase the after-hours pop** — require the pivot to *hold* on the cash session.
  ⚠ Needs an **earnings calendar + a beat/guidance feed** to screen — heavier than A.
- **Archetype C — Climactic-exhaustion fade** (SMCI 2024-02-16, NVDA 2024-03-08): the **inverse** of
  A/B. A big-mover stretched **far above its rising 10/20/50 SMAs** after a steep multi-week parabola
  **gaps/pushes to a new high, then reverses hard intraday** — a wide-range bar closing **near its low**
  on **climactic volume (≥2.3–4.4× the 50-day avg)**. Vehicle = a **0DTE / very short-dated put**,
  entered intraday **once the new high fails** (price rejects the highs / loses the open), not shorted
  at the open. ⚠ Volume is the **tell** here (must be climactic), the opposite of A where volume can be
  modest. ⚠ Binary 0DTE — needs **intraday execution + extension data**, the riskiest archetype to time.
- **Archetype D — Catalyst** (= Tito's "Catalyst"; DJT 2024-10-22, TSLA 2024-11-05 — **both the
  election**): the **outlier — no breakout.** He buys a big-mover **BELOW its pivot** (DJT −4%, TSLA −8%)
  to **position for a macro/binary EVENT** (here, the US election), then **sells into the run-up.** The
  defining feature is *structural* (entered below the pivot, no decisive bar at a level), so there is
  **no technical trigger** — the edge is **conviction + event timing**. ⚠ Entry volume is **not** a
  signature (0.87×–2.98×). ⚠ **Exit-critical:** the pop is **sold into**, often *before* the event —
  DJT exited **~9 days in (≈Oct 31), into the pre-election run-up**, not held to expiry (which gave it
  all back). Sizing: **smaller, event-risk position.** ⚠ n=2; narrow specialist setup.
  - ⚠ **COIN 2024-02-09 was earlier filed here but Tito labels it "Breakout" (held 37d).** It broke a
    *local* base and was held as a trend trade — reclassified to Breakout (see reconciliation below).

---

## ⭐ Tito's own labels (GROUND TRUTH) — reconciliation

Tito's spreadsheet tags each trade with a **Setup_Type** and **Days_In_Trade**. His four setup types —
**Breakout / Earnings / Exhaustion / Catalyst** — were derived *independently* of the A/B/C/D archetypes
above and **match them**, which is strong validation. **15/20 agree** on the mapping
(Breakout↔A, Earnings↔B, Exhaustion↔C, Catalyst↔D); **his labels are canonical — where they differ, his win.**
Reconcile script: `scratch_adhikary_reconcile.py`.

**His "Breakout" is broader than my "A".** All 5 divergences collapse the same way — into **Breakout**.
He folds catalyst-*triggered* base-breakouts and local-base breakouts into one bucket. Revisions this forces:
- **"Earnings" is NARROW (n=1, ARM):** a violent earnings *pop* taken for a **quick exit (5 days)** — NOT
  every earnings-triggered trade. SMCI (guidance), AAPL (WWDC), **PLTR (earnings)** all → **Breakout**.
  My "B = catalyst-breakout" over-split this; most of it is just Breakout held as a trend trade.
- **"Catalyst" = macro/binary EVENT positioning (the election): DJT + TSLA only.** COIN is **not**
  Catalyst → he calls it Breakout (held 37d). D narrows to the two election trades.
- **His pivot is a LOCAL base, not the multi-month high.** COIN / MSTR 2/8 entered "below" my 3-month-high
  pivot but broke out of their *near-term* consolidations. ⚠ **Fix the pivot detector (recipe #5) to anchor
  on the most-recent base.**

**⚠ One internal inconsistency in Tito's own labels (confirmed copied correctly — likely his own slip):**
**PLTR (#17) = Breakout** but **ARM (#4) = Earnings**, though both are day-after-earnings gaps. Could be a
deliberate hold-based distinction (ARM = 5-day pop; **PLTR = 45-day trend hold**) or just a mislabel. Kept
as his label, flagged here — do not silently "correct" it.

**Days_In_Trade = the exit signature** (answers the previously-open "how does he exit?" question; ≈ calendar days):

| Setup (Tito) | n | Days held | Exit behavior |
|---|---|---|---|
| **Exhaustion** | 2 | 1, 1 | 0DTE, same session |
| **Earnings** | 1 | 5 | quick pop, booked well before expiry |
| **Catalyst** | 2 | 9, 17 | event-bracketed; **DJT sold ~Oct 31 INTO the pre-election run-up** (not held through) |
| **Breakout** | 15 | 1–48 (med 11) | trend trades — winners run to ~expiry (GLD 48 / PLTR 45 / COIN 37), **losers cut fast (COST 1)** |

**Net taxonomy (his counts):** **Breakout 15** (dominant, broad) · **Catalyst 2** · **Exhaustion 2** ·
**Earnings 1**. Breakout is the core engine; Earnings/Catalyst are narrow specialist setups; Exhaustion is
the lone short side. **Exit rule of thumb: let Breakout winners run to ~expiry, cut failed breakouts in ~1
day, book Earnings pops in days, and sell Catalyst trades INTO the event run-up.**

### ⭐⭐ Exit timing IS alpha — true option P&L (from Entry_Price + Days_In_Trade)

Tito's **Return** column is now ground truth (`scratch_adhikary_returns.py`). His **Entry_Price** lets us
infer the strike + **delta/DTE vehicle rule** (recipe #7); comparing his actual returns to my reconstructions
validates the method AND exposes how much his **exit execution** adds.

**Strike inference validated** — on the 13 held-to-expiry trades, my at-expiry intrinsic vs his actual has
**median error 16%** (PLTR his 4018 / mine 3929; NVDA 2500 / 2801; GLD 3233 / 2837). The reconstruction is sound.

**Exit execution is a massive, separate edge** — on the 6 early-exit trades he sells **intraday peaks**, so
his actuals dwarf both at-expiry intrinsic and my exit-*close* estimate. The progression is the whole story:

| Trade | At-expiry | my exit-close | **TITO actual** | what his exit did |
|---|---|---|---|---|
| **COST** | **−100%** | +117% | **+842%** | cut in ~1 day at the spike — the "lone loss" was a big WIN |
| **DJT** | **−100%** | +18% | **+217%** | sold the pre-election pop — gain, not a wipeout |
| ARM | +578% | +368% | **+1966%** | sold the 2/12 intraday peak |
| BABA | +829% | +1343% | **+2269%** | sold the China-stimulus top (beats holding) |
| GEV | +1237% | +672% | **+1332%** | |
| BRKB | +516% | +298% | **+858%** | |

**Conclusions:**
- ⚠ **COST is NOT a loss** (my original QA's "lone loss" was a hold-to-expiry artifact) — his ~1-day cut
  booked **+842%**. The universe-gate lesson still holds: COST's low ADR made it fade to a total loss by
  expiry, so his fast cut is exactly what *saved* it. **DJT** likewise: +217%, not −100%.
- **At-expiry AND daily-close both badly understate him.** COST: −100% → +117% → **+842%** across the three
  methods. **Any backtest MUST model his actual intraday exits** — expiry/close pricing is worthless here.
- His **sell-into-strength / cut-fast** discipline is alpha *on top of* selection.

### When to HANG TIGHT — daily-close trail (from the 12 held-to-expiry winners)

For a trader who bails too early on intraday wobble, the path analysis (`scratch_adhikary_holdpath.py`)
is the antidote: **the intraday swings were brutal, the daily closes were calm.**

| | median | worst |
|---|---|---|
| drawdown from entry, **daily-close** basis | **0.0%** | −9.0% (MSTR) |
| dip from entry, **intraday** basis | −5.9% | **−20.0% (SMCI)** |

The typical held winner **never closed below entry**, yet intraday you'd have watched SMCI −20%, MSTR
−12.6%, APP −10.7%. **Watch intraday → you bail. Watch only the close → nothing to react to.**

**Trailing-level test (daily CLOSE basis, across the 12 winners):**
- **20-EMA: never broken (0/12)** → the hang-tight line.
- breakout pivot: broken once (1/12). 10-EMA: broken 3/12 (too tight — would have cost COIN/AAPL/PLTR).
- **10 intraday pokes below the 10-EMA closed back above it** — pure head-fakes.

**Rules (these apply to GRIND-up trades — steady climbers; spike trades are different, see trail-test below):**
1. **Manage on the daily close; stop watching intraday.** A −5 to −10% intraday dip is normal noise here
   (even −20% recovered). Acting on it is the mistake.
2. **Hang tight while the daily *close* holds above the 20-EMA;** exit only on a daily *close* below it,
   never an intraday touch. This kept you in all 12 winners.
3. **Short-dated weeklies (≤~8 DTE): just hold to expiry** — too short to trail meaningfully.
4. **Pre-commit to the heat at entry** (~10% intraday tolerance); set ONE daily-close alert at the 20-EMA, walk away.

⚠ **Survivorship:** these are winners, so they held the 20-EMA by construction. This proves the rule
**won't prematurely shake you out of a winner** (your failure mode) — it does NOT establish the false-signal
rate on real failures (needs his losers). It's a "when to HOLD," not a full "when to FOLD."

### ⚠⚠ ...but the 20-EMA trail FAILS on SPIKE trades — sell the spike (`scratch_adhikary_trailtest.py`)

Pressure-test: on the **6 trades Tito exited early**, what would the 20-EMA-close trail have done instead?
**It lost on all 6 — badly — because he sold *strength* and the trail holds until the trend *breaks*:**

| Trade | Tito (sold spike) | 20-EMA trail | trail outcome |
|---|---|---|---|
| ARM | +1966% | +578% | held to expiry, gave back the 2/12 spike |
| BABA | +2269% | +658% | broke 10/15 — gave back ~70% |
| GEV | +1332% | +1237% | ran into expiry (OK) |
| BRKB | +858% | +206% | broke 8/2, gave back most |
| **DJT** | +217% | **−14%** | broke 11/1 → **win turned to loss** |
| **COST** | +842% | **−100%** | faded to expiry → **total wipeout** |

**Why:** a short-dated option that **spikes** gives back the spike *plus* theta long before a daily close
breaks the 20-EMA. The trend-trail is too slow for convex, decaying premium.

**→ The exit rule is TWO REGIMES:**
- **SPIKE** (option triples+ in a few days, then fades): **sell into strength — take it.** Do NOT trail.
  This is where Tito's biggest, fastest money is (and where the trail is catastrophic — DJT/COST).
- **GRIND** (steady climb, no burst — the held-to-expiry winners): **trail the 20-EMA daily close**, ignore intraday.

**Implementable bridge (no intraday-watching):** the proxy for "sell the spike" is a **GTC profit-target
order set at entry** — scale out 50–75% at a big multiple (~+200–300%), trail the rest on the 20-EMA close.
Captures most of the spike mechanically while you're not watching, which fits the "trouble with intraday" constraint.

This answers the open **stop-price** question with a fork: **grinds → 20-EMA-close trail; spikes → profit-target into strength.**

### ⚠⚠ SURVIVORSHIP CAVEAT — read before using any of these numbers

This is a **curated list of Tito's BEST trades** (per the source). The aggregate — **20/20 wins, median
+1856%, mean +1969%, range +217% to +4205%** — is a **highlight reel, NOT a strategy expectancy.** It is
silent on hit rate, average loss, and how often the setups fail. Use this dataset to characterize **what his
winners look like** (which setups, structure, vehicle, exits) — **never** to estimate win rate or edge.
Per-setup medians (tiny samples): Breakout 1747% (n=15) · Catalyst 2211% (n=2) · Exhaustion 2240% (n=2) ·
Earnings 1966% (n=1).

---

## Recurring primitive — the "shakeout under the pivot" (3 of 4 breakout cases)

Common but **not mandatory** (TSLA, APP, RKLB had it; GEV broke clean with no recent failed poke).
When present, he does **not** buy the first tag of the **B/O pivot** (breakout pivot = the buy-trigger
price at the top of the base). The repeating sequence:

> **Failed test(s) at the pivot → low-volume pullback / shakeout → reclaim → tightness under the
> pivot → entry.**

He wants the pivot rejected, supply flushed on a *quiet* (low-volume) pullback, and price coiling
tightly back under the line before committing.
- **TSLA:** two failed intraday pokes of 357 → decisive close through.
- **APP:** open dip under 400 → reclaim-and-run.
- **RKLB:** rejections at ~31 / 32.7 → low-vol pullback to ~25 (RVOL 0.7) → reclaim.

**Trigger = the high-volume thrust bar INTO the pivot** (resolved across TSLA + RKLB): a wide-range,
above-average-volume bar closing **near its high at/through the B/O pivot**, emerging out of the
low-volume shakeout. He buys the *power bar reaching the pivot* — whether it closes a hair above
(TSLA 9/11, +6%) or a hair below with next-day confirmation (RKLB 6/23 close 32.78 vs 33.34 pivot →
6/24 closed 33.46) is secondary. He is **not** anticipating from well below the pivot.

Volume *magnitude* varies (TSLA 1.22× vs RKLB 2.35×) — the constant is **above-average + rising,
wide range, close near the high.**

**Mirror primitive (Archetype C — the fade):** the same "failed test of a line" logic runs inverted.
On the long side he buys the **reclaim** of a pivot after a failed poke *above* it; on the fade he
sells the **failed new high** — price pokes to a fresh high (the final exhaustion tag, mirror of the
failed pivot poke), **fails to hold it, and reverses through the open** on climactic volume. Long
trigger = power bar closing **near its high** into the pivot; fade trigger = reversal bar closing
**near its low** off the failed high. Same skeleton (a rejected level + a decisive bar), opposite sign.

---

## The Selection Recipe (v1 — calibrated across 19 classified trades)

| # | Primitive | Signal to screen | Status |
|---|-----------|------------------|--------|
| 1 | **Universe: history of big moves** | **ADR%(20d) ≥ ~3%** (winners 3.6–6.9%; the 2 lowest-ADR names = the loss + the marginal) | **gating filter — resolved** |
| 2 | Prior context | Off the lows; downtrend → basing transition | qualitative |
| 3 | Base pattern: VCP | Contractions tightening (higher lows / lower highs) + declining volume | needs detector |
| 4 | Trend confirmation | 10/20/50 SMA stacked, **held ≥ ~1–2 weeks** (not 20d); B/D tolerate 50-overhead | screen-ready |
| 5 | Pivot | **Highest high of the prior ~10–15 trading days** (LOCAL consolidation, not the multi-month high); A/B/C buy a close *clearing* it, D buys below it | **resolved — N≈15** |
| 6 | Trigger | A: modest break ≥~1.1× + next-day expansion · B: day-after-catalyst ≥~2× · C: climactic ≥2.3× reversal · D: none (conviction) | per-archetype, loose |
| 7 | Vehicle | Long options (A/B/D = calls; C = 0DTE puts). **Delta scales inversely with DTE:** ≤~11 DTE → **near-ATM ~0.5–0.9Δ**; ≥~15 DTE → **OTM ~0.2–0.35Δ** (cheap leverage, time to work). Premium $0.5–6. | **resolved (from Entry_Price)** |

**Open questions (precision levers) — status after mining:**
- ✅ **ADR / "big move" cutoff** — resolved: **ADR%(20d) ≥ ~3%** is the dominant gate (COST/AAPL proof).
- ✅ **Volume threshold** — resolved as **per-archetype & loose**: A modest (~1.1×, next-day expansion);
  B ≥~2× (no ceiling — ARM 15×); C climactic ≥2.3×; D has no volume signature (0.87–2.98×).
- ✅ **Pivot reference** — resolved: **local high of the prior ~10–15 trading days** confirms **15/15**
  of Tito's Breakout trades (entry clears it), vs **12/15** for the 3-month high (which mis-flags COIN,
  MSTR 2/8, GLD). N=20 falls to 13/15. ⚠ Do **not** add a hard base-tightness gate — Tito breaks out of
  looser ~20–30% bases too (SMCI/COIN/MSTR), so a tightness filter would reject real trades.
  Validated by `scratch_local_pivot.py`.
- 🟢 **Exit** — resolved into **two regimes** (the key practical finding): **GRIND trades → trail the
  daily CLOSE above the 20-EMA** (never broke across the 12 held winners; 10-EMA too tight); **SPIKE trades
  → sell into strength / profit-target** (the 20-EMA trail LOST on all 6 early-exit trades, turning DJT/COST
  into losses). Implementable proxy: GTC profit-target (~+200–300%, scale out) + 20-EMA trail on the rest.
  ⚠ Still survivorship-limited (no losers → can't rate the trail's false-signal rate on real failures).
- ⏳ **Intraday entry trigger (C)** — blocked on IBKR intraday data; `scratch_fade_trigger.py` staged.

---

## Trade Log (reference cases)

### TSLA — 2025-09-11 — Breakout (long)
- **Why on the radar:** Tesla = classic "history of big moves" name.
- **Context:** Bottomed April 2025 (**low 214.25 / close 221.86, Apr 7–8**). Built a ~5-month base.
- **VCP — validated from Tradier daily data:**

  | Month | Range % | Monthly low (higher lows) | Avg vol |
  |---|---|---|---|
  | May | 35.7% | 271 | 105M |
  | Jun | 30.9% | 273 | 122M |
  | Jul | 17.0% | 289 | 98M |
  | Aug | 19.3% | 298 | 76M |
  | Sep (pre-BO) | **10.1%** | **326** | **74M** |

  - **Contraction:** range tightened 35.7% → ~10%. **Higher lows:** 271→273→289→298→326.
  - **Flat resistance ~357:** highs cluster (May 367, Jun 357.5, Aug 355, Sep 358 poke).
  - **Volume drying up:** ~141M (Apr) → ~74M into the pivot (roughly halved).
- **Trend — SMA stack (10>20>50):** flickered all summer, durable stack formed **Aug 14** and **held
  20 days** through the breakout. (Flickers: stacked May 6, broke Jun 9, re-stacked Jun 26, broke Jul 8,
  stacked-and-held Aug 14.) At breakout 9/11: sma10/20/50 = 344 / 340 / 327.
  - ⚠ **Screener lesson:** require the stack **held for N days** (~20), not "first day stacked" —
    else the May/Jun/Jul false stacks fire.
- **Pivot:** Clear flat resistance ~**$357**.
- **Trigger:** First **decisive close** above $357 → entered **Sept 11, 2025** with a long (options) strategy.
  - Prior **failed pokes** above 357 (intraday, closed back below): 9/5 (hi 355.87) and 9/8 (hi 358.44).
    The 9/11 bar was the first *close* through the line ($368.81, +6%, wide range, closed near high).
- **Archetype:** A (technical VCP breakout).
- **Invalidation:** _unknown — not important right now per Tito._
- **Volume detail (Tradier, pulled):**
  - Breakout day 9/11: **103.8M vs 50-day avg 84.7M = 1.22× RVOL** — only modestly above average.
  - Follow-through: 9/12 = **1.96×**, 9/15 = **1.87×** (the real volume expansion came *after* confirmation).
  - ⚠ **Precision lesson:** a "breakout volume ≥ 1.5×" gate would have **missed this entry**. What defined
    it was a **wide-range bar closing decisively above the pivot on above-average, rising volume** — not a
    single big spike. Encode the volume gate **loose** (≥1.0–1.2× day-of, with rising/expanding follow-through),
    not the textbook ≥1.5–2×.

### APP (AppLovin) — 2025-08-07 — Post-earnings breakout (long)
- **Why on the radar:** Extreme "history of big moves" name (Feb 2025 monthly range = **81.8%**).
- **Context:** Deep correction (Feb high ~525 → Apr low ~200, ~60% drawdown), then rebuilt a
  contracting base into earnings.
- **Base (Tradier, pulled) — contraction + volume dry-up:**

  | Month | Range % | Avg vol |
  |---|---|---|
  | Feb | 81.8% | 9.0M |
  | Mar | 53.4% | 11.1M |
  | Apr | 49.5% | 8.4M |
  | May | 45.6% | 7.1M |
  | Jun | 34.1% | 6.1M |
  | Jul | **22.2%** | **4.1M** |

- **Trend — "surfing the SMAs":** Through July, price rode **above the rising 10 & 20 SMA with
  higher lows** (daily lows 325 → 358), tight price action into earnings. But the full **10>20>50
  stack was false** — the **50 was still overhead** (order `50>10>20`, the lagging 50 weighed down by
  the Feb–Apr decline). The earnings move **reclaimed the 50 and completed the stack** on Aug 7.
  ⚠ Archetype-B trend condition is **"surfing rising 10/20 + higher lows, 50 being reclaimed,"** NOT
  a pre-established durable stack.
- **Pivot: 400 (psychological round number).** Hard ceiling for months: **0 closes ≥400 in May
  (high 402.90) or July (high 397.92)**. June briefly poked above (4 closes, to 429) then **failed
  back below — a failed breakout that turned 400 into firm resistance.** Aug 7 close 437 cleared it.
- **Earnings event (confirmed, Aug 6 AMC):** **beat EPS** (~$1.96 est), **revenue +77% YoY**, 81%
  EBITDA margin, **raised guidance**. Stock **dipped ~5% after hours, then recovered**.
- **Trigger / entry mechanics — dip-then-reclaim (not a gap-chase):** Aug 7 opened 397.25 (just
  *under* 400), **dipped to 385, then reclaimed 400 and ran** to close 437.34 (+11.97%, near high).
  He let the pivot reclaim confirm rather than chasing the after-hours pop.
- **Volume detail (Tradier, pulled):** Aug 7 = 20.7M = **3.65× RVOL** (Aug 6 run-in already 2.37×).
  Confirms volume tolerance is **situational**: modest is fine on a clean technical breakout (TSLA),
  but catalyst entries come with a genuine spike.
- **Invalidation:** _unknown._
- **Archetype:** B (earnings-catalyst breakout).
- **Sources (APP):** [AppLovin Q2'25 press release](https://s27.q4cdn.com/966411597/files/doc_financials/2025/q2/2Q25-AppLovin-Press-Release.pdf),
  [SEC 8-K](https://www.sec.gov/Archives/edgar/data/0001751008/000175100825000069/exhibit991-2q25earningspre.htm),
  [TradingKey earnings review](https://www.tradingkey.com/analysis/stocks/us-stocks/250965503-applovin-app-earnings-tradingkey)

### RKLB (Rocket Lab) — 2025-06-23 — Technical breakout (long)
- **Why on the radar:** High-volatility big-mover (small-cap space name).
- **Context / base:** **7-month base.** Base low **10.85 (Nov 1, 2024)** → high **33.34 (Jan 24, 2025)**
  → based ~7 months. April low **14.71 (Apr 7)** = higher low; surfed the rising SMAs off the April low.
- **Trend — SMA stack:** durable 10>20>50 stack formed **Apr 30** and held (first durable stack since
  the Jan flickers — stacked Jan 2→broke Jan 22→Jan 27→broke Feb 13→**Apr 30 held**). Archetype A.
- **B/O pivot = 33** (the January base high, 33.34).
- **Shakeout-under-pivot sequence (Tradier, pulled):**
  - **Failed approaches to 33:** 5/28 high **30.78** (closed weak); 6/9 high **32.70** on a **3.29× RVOL
    blowoff that reversed −8.3%** the next day (classic failed-breakout exhaustion).
  - **Low-volume pullback:** 6/12–6/13 down to **25.24 on RVOL 0.70 / 0.84** ("pulled back on low volume").
  - **Reclaim:** 6/16→6/20 rebuilt on building volume (6/20 +7.86%, RVOL 2.00).
- **Entry = the thrust bar, 6/23:** **+9.12%, RVOL 2.35,** wide range (28.44→32.93) closing **32.78
  right at the 33 pivot**, near the high. **6/24 confirmed: closed 33.46, decisively above 33.34.**
  Then ran (6/26 +11.72% to 36.14, 6/27 high 37.66). Same trigger as TSLA: a power bar driving into
  the pivot out of the shakeout — not anticipation from below.
- **Invalidation:** _unknown._
- **Archetype:** A (technical breakout).

### PLTR — 2024-11-05 — Earnings-catalyst breakout (long) — *2nd Archetype-B case*
- **Why on the radar:** big-mover momentum leader; tightening into a Q3 print.
- **Base (Tradier, pulled) — higher lows + volume dry-up into earnings:** monthly lows **rose**
  Jul 25.14 → Sep 29.31 → **Oct 36.05** while Oct range tightened to **25.2%** and **volume dried from
  ~80M (Sep) to ~46M (Oct)** — the contracting-base-into-earnings setup.
- **Trend — already a full stack:** at entry the SMAs were **10 > 20 > 50 (44.06 / 43.46 / 38.58)** —
  a durable stack. ⚠ Note vs APP: B does **not** require the 50 overhead; the catalyst carries a
  full-stack name just as well.
- **Pivot: 45.14** (the Aug–Oct pre-earnings high).
- **Earnings event (11/04 AMC):** Q3 blowout — large EPS/revenue beat, **raised full-year guidance**,
  US-commercial acceleration. Fundamental beat + raise = the B trigger condition. ✓
- **Trigger / entry — gap-and-hold (the other B mode):** 11/05 **gapped to 47.86, above the 45.14
  pivot, and the day's low (46.86) never lost it** — closed **51.13 (+23.5%), 91%ile of range** on
  **RVOL 3.53×** (matching APP's ~3.6×). No dip-reclaim needed; the gap held. Follow-through 11/06
  **+8.6%** (RVOL 1.93×), then ran to **+60% over the next ~34 sessions** (high 82.02).
- **Invalidation:** _unknown — loss of the pivot (45.14) / gap-fill would be the natural line._
- **Archetype:** B (earnings-catalyst breakout). **Confirms B; n=2.**

### GEV — 2024-08-29 — Technical VCP breakout (long) — *3rd Archetype-A case*
- **Why on the radar:** post-spinoff (Apr 2024) momentum leader, power/grid theme.
- **Base (Tradier, pulled) — contraction + volume dry-up:** monthly range **37.1% (Apr) → 22.3 →
  19.3 → 17.9% (Jul)** with **volume drying 7.0M → 2.6M**; lows held ~149–156 (flat-to-higher).
- **Trend — full stack, short durability:** 10 > 20 > 50 = **185.00 / 179.64 / 175.49**, but the stack
  **held only 9 days** at entry. ⚠ Worked anyway — durability floor is **~1–2 weeks, not 20d**.
- **Pivot: 190.80** (the prior ~3-month high).
- **Trigger — modest break, next-day expansion:** 8/29 **+4.0%, RVOL 1.13×**, closed **191.36 just
  above the 190.80 pivot** (mid-range close, 58%ile). The real expansion came **next day** —
  8/30 **+5.0%, RVOL 1.20×, 95%ile** — the same TSLA signature (modest day-of, rising follow-through).
- **No shakeout:** clean first break of long-standing resistance, **no failed poke in the prior 20d.**
  Confirms the shakeout-under-pivot is common but not required for A.
- **Invalidation:** _unknown — loss of the 190.80 pivot is the natural line._
- **Archetype:** A (technical VCP breakout). **Confirms A; n=3, and loosens the durability + shakeout gates.**

### COIN — 2024-02-09 — Breakout (per Tito; held 37d) — *I had mis-filed this as Archetype-D*
- **Why logged:** biggest non-BTC winner (**+91% MFE**); also the case that taught the **local-pivot** lesson.
- **Tito's label = Breakout, Days_In_Trade = 37.** He broke out of the **near-term** early-Feb base
  (2/8 +8.6%, 2/9 +7.1%, RVOL ~1.15×) and held it as a **trend trade** through the 2/15 earnings.
- **Why I mis-filed it as D:** against the **3-month-high** pivot (187.39) it looked "below pivot"
  (entered 141.99, −24%) with the **50 overhead** — so I read it as pre-catalyst anticipation. ⚠ Wrong
  reference: Tito's pivot is the **most-recent consolidation high**, which COIN *did* break. **Lesson
  → recipe #5 pivot detector must anchor on the local base, not the multi-month high.**
- **Archetype:** **Breakout** (Tito). The catalyst (2/15 earnings) was a tailwind he held through, not
  the setup — consistent with his treating earnings-adjacent base-breakouts as Breakouts, not "Earnings."

### DJT — 2024-10-22 — Catalyst (Tito's label) — *1st of 2 Catalyst/D cases*
- **Why on the radar:** the QA's "exit-dependent" trade (**+59% MFE, −10.5% to expiry**) — D's
  exit-critical risk in one chart.
- **No breakout:** stacked (10/20/50 = 28.34 / 22.36 / 20.33) but entered **34.39 — ~4% BELOW the
  35.77 pivot** on a **momentum surge** (10/21 +5.8%, **10/22 +9.9%, RVOL 2.98×**).
- **Catalyst held through:** the **US election (11/05)** was 2 weeks out; he positioned ahead and held.
  Ran +59% into the election, then **gave it all back by the 11/22 expiry** — the catalyst pop had to be
  **sold into.** ⚠ The cleanest illustration of D's exit-critical, binary nature.
- **Archetype:** D (catalyst anticipation).

### TSLA — 2024-11-05 — Catalyst (Tito's label) — *2nd of 2 Catalyst/D cases*
- **Why on the radar:** +40% MFE; entered **on election day** itself.
- **No breakout:** stacked (10/20/50 = 251.60 / 237.61 / 235.48) but entered **251.44 — ~8% BELOW the
  273.54 pivot**, on **low volume (RVOL 0.87×)** — *not* a momentum-surge entry (contrast COIN/DJT).
  Confirms D's entry has **no volume signature** — it's pure positioning.
- **Catalyst held through:** bought into the **election (same-day)** binary and held; post-election
  Tesla ripped (+40%).
- **Archetype:** D (catalyst anticipation). **Confirms D; n=3 (emerging).**

### BABA — 2024-09-19 — Technical breakout + catalyst tailwind (Archetype A, not D)
- **Why logged here:** looked like a D-candidate (catalyst held through) but **fails the D test** —
  it actually **broke out**: stacked (10/20/50 = 84.26 / 83.27 / 80.52) and entered **88.49 = +3%
  ABOVE the 85.79 pivot** on **RVOL 1.44×**, a legit A trigger.
- **Catalyst was a tailwind, not the thesis:** the **PBoC stimulus bazooka (9/24)** super-charged an
  already-valid breakout. ⚠ **Lesson:** "held through a catalyst" alone ≠ Archetype D — D requires
  entry **below the pivot**. A breakout that happens to precede a catalyst is still **A**.
- **Archetype:** A (technical breakout, catalyst-assisted).

### Roll-up — additional classified cases (Jan–Oct 2024 cluster)

Compact classifications (lessons already folded into the archetype bullets above; full prose reserved
for cases that *refined* an archetype). Metrics from Tradier daily, split-adjusted.

| Trade | Trend | Entry vs pivot | Day-of vol | Catalyst | Archetype | Note |
|---|---|---|---|---|---|---|
| **ARM** 2/8 | stack | +42% above | **15.15×** | earnings 2/7 AMC | **B** | catalyst vol has no ceiling |
| **SMCI** 1/19 | stack | +18% above | 7.26× | **guidance pre-announce** 1/18 | **B** | catalyst ≠ only the full print |
| **NVDA** 1/8 | stack | +3% above | 1.58× | none (earn far) | **A** | textbook modest-vol breakout |
| **APP** 9/11 | stack | +4% above | 2.36× | none (earn 8/7 far) | **A** | breakout, ADR 4.4%; ≠ the 2025-08-07 APP case |
| **GLD** 3/1 | flat/converged | ~at pivot | 2.28× | gold macro | **A** | breakout from converged-MA base |
| **BRKB** 7/11 | stack | ~at pivot | 1.16× | value rotation | **A** | clean modest-vol breakout |
| **MSTR** 10/11 | strong stack | +7% above | 2.55× | BTC momentum | **A** | above-pivot breakout |
| **IWM** 7/11 | 50-over | ~at pivot | 2.68× | cool-CPI rotation | **A** (marginal) | catalyst-assisted, like BABA |
| **MSTR** 2/8 | 50-over | **−19% below** 3mo-hi | 1.84× | BTC momentum | **Breakout** (Tito) | I called it ambiguous; Tito = Breakout of a *local* base (same lesson as COIN) |
| **AAPL** 6/11 | stack | +5% above | 2.95× | WWDC AI event 6/10 | **B** | catalyst = product event; **ADR 1.4% → only marginal** |
| **BTC**(IBIT) 11/6 | stack | +3% above | 3.22× | post-election momentum | **A** | day-after election; breakout, not anticipation |
| **COST** 11/8 | mixed | +2% above | 1.84× | none | **A-structure but LOST** | **ADR 1.3% → fails universe gate; only loss in the set** |

⚠ **Both MSTR trades are "Breakout" to Tito** — 10/11 broke the 3-month high; 2/8 broke a *local* base
while still −19% under the 3-month high. The lesson is the **pivot reference**: anchor on the most-recent
consolidation (Tito) rather than the multi-month high (which made 2/8 look like "no breakout" to me).

### ⭐ Universe gate validated — ADR% is the dominant selection filter

The **two worst outcomes in the entire 19-trade set are the two lowest-ADR names**, despite both having
*structurally valid breakouts*:

| | ADR%(20d) | Structure | Outcome |
|---|---|---|---|
| **COST** 11/8 | **1.3%** | valid A breakout (+2% over pivot) | **weakest setup** — faded to a total loss *by expiry*, but Tito **cut it in ~1 day for +117%** (see exit-timing section) |
| **AAPL** 6/11 | **1.4%** | valid B breakout (+5%, 2.95× vol) | marginal (+0.2% to exp) |
| — winners — | **3.6–6.9%** | (TSLA 3.6 / COIN 6.5 / SMCI 6.9) | big winners |

**Lesson (refined):** a clean structure on a low-ADR vehicle is the **weakest** trade — COST would have
been a total loss held to expiry, and AAPL was only marginal. The underlying can't travel far enough for a
long-option swing to pay, so these depend entirely on a fast exit. **ADR ≥ ~3% is the gating filter;
structure is secondary** — rule #1 earning its spot. (Note: with his actual 1-day cut COST was a *gain*,
so the set has **no realized losses** — but it remains the lowest-quality setup by ADR.)

### SMCI — 2024-02-16 — Climactic-exhaustion fade (0DTE put)
- **Why on the radar:** Extreme big-mover mid-parabola — **+253% in the prior 25 trading days**
  (25d low 30.57 → fade-day high 107.79, split-adjusted).
- **Extension (the setup):** at the open, price was **+35% / +64% / +140% above the 10 / 20 / 50 SMA** —
  stretched to a climactic degree (the inverse of a tight VCP base).
- **Reversal bar (Tradier, pulled):** gapped **up +4.1%** (prior close 100.40 → open 104.55), poked a
  **new high +3.1% past the open (107.79), then reversed −23.2%** to close **80.33 — at the 1st %ile of
  the day's range (dead on the low)**, a 26.5%-of-price range bar.
- **Volume:** **340M vs 50-day avg 77M = 4.40× — climactic blow-off.** Volume IS the tell on the fade.
- **Context:** monthly **opex** day; a parabolic AI/server name running into a known liquidity event.
- **Vehicle / entry:** **0DTE put**, entered intraday as the new high failed and price lost the open —
  not shorted at the open print. (Daily close-to-close shows ~0% — the trade is invisible to any
  daily-bar model; it lives entirely in the intraday reversal.)
- **Confirmation:** next session **2/20 closed 78.76 (−2.0%)** — fade followed through.
- **Invalidation (inferred):** a **reclaim of the high-of-day** (defined, tight) — the failed high is the line.
- **Archetype:** C (climactic-exhaustion fade).

### NVDA — 2024-03-08 — Climactic-exhaustion fade (0DTE put)
- **Why on the radar:** Classic big-mover, **+58% in the prior 25 trading days** (61.65 → 97.40,
  split-adjusted) — semis-leader parabola.
- **Extension (the setup):** at the open, **+14% / +21% / +44% above the 10 / 20 / 50 SMA.**
- **Reversal bar (Tradier, pulled):** the famous **bearish outside-reversal day** — gapped **up +2.7%**
  (92.67 → 95.14), made a **new high +2.4% past the open (97.40), then reversed −8.0%** to close
  **87.53 — 9th %ile of range (near the low)**, an 11.5%-of-price range bar.
- **Volume:** **1.14B vs 50-day avg 494M = 2.31× — climactic.**
- **Vehicle / entry:** **0DTE put**, entered intraday on the rejection of the highs / loss of the open.
- **Confirmation:** next session **3/11 closed 85.77 (−2.0%)** — fade followed through.
- **Invalidation (inferred):** reclaim of the high-of-day.
- **Archetype:** C (climactic-exhaustion fade).

> **Two-case fade signature (constants across SMCI + NVDA):** parabolic name **extended ≥+14% above
> the 10-SMA** → **gap up into a new high that fails intraday** → **wide-range reversal bar closing in
> the bottom ~10% of its range** → **climactic volume ≥2.3×** → **−2% next-day follow-through.** The
> run-up magnitude (+58% vs +253%) and extension depth vary; the **failed-new-high + close-near-low +
> climactic-volume** bar is the invariant. Open levers: minimum-extension gate, intraday entry trigger
> (lose-open vs lose-VWAP vs lose-opening-range), and the 0DTE-vs-short-dated vehicle choice.

**Out-of-sample daily-bar scan (`scratch_fade_detector.py`, 26 big-movers, 2024):** the gate set
[ext10≥+10%, new-high>10d, close in bottom ≤20% of range, range≥5%, vol≥2×, red bar] fires **17×/yr**
and **re-surfaces both known cases**, but **next-day follow-through is a coin flip — 9/17 (53%) down,
median −0.2%.** Several hits were *continuation* wicks inside an uptrend (MSTR 3/11 → +7.4% next day,
DJT 3/26 → +14.2%), not exhaustion tops. **Lesson: the EOD daily signal has no predictive edge** — the
fade's entire P&L is the **same-session open→low** move (SMCI −23.2% / NVDA −8.0% open→close), captured
by a 0DTE put **intraday**. So the daily detector is only a **candidate-narrower**; the edge is in
**selection + intraday execution**, consistent with the long-side thesis (see `project-ibkr-bot`:
intraday gates can't buy precision). The cleanest discriminators in-sample were **close in bottom ≤10%
of range + open→close ≤ −8%** — both only knowable mid-session, so they belong in the intraday trigger,
not the screen.

### Intraday trigger validation — RESOLVED (1-min bars, 2026-06-19)

Pulled IBKR 1-min RTH bars for all **17 daily-detector hits** (2024) via `fetch_intraday.py --end-date`
and tested the intraday entry/exit on real ticks (`scratch_fade_trigger.py`). Findings:

- **Entry trigger = `lose_vwap`** (first 1-min close below running VWAP) beats `lose_open` and `lose_or5`
  on both known Tito cases: it fires earliest (5 min SMCI / 9 min NVDA after the high), enters at the
  highest price (best put entry), and on a fade you want max entry price → it slightly *beats* the naive
  open→low benchmark. `lose_or5` is worst (waits for the opening-range break, enters low).
- **Naive "first VWAP loss" is too trigger-happy** — fired before the real session high on 5/17 and got
  run over, *including NVDA 3/8 (a known winner): stopped −0.7% because the famous outside-reversal high
  was at 10:30, not the open.* The other premature stops (DJT, MSTR 3/11, BABA, SMCI 12/3) were also
  before the top — yet **every one of those days still closed deep red.** Timing was wrong, direction right.
- **Fix = fade-the-failed-new-high + RE-ENTRY.** Rule: enter on a VWAP loss; **a new high above the
  high-at-entry is the stop** (the "failed" high wasn't the top); after a stop, re-arm and fade the next
  failed high (≤3 legs). This recovers all 5 — NVDA −0.7% → **+8.1%** (09:46✗ → 10:39✓), DJT → +6.5%.
  **Underlying capture: 17/17 profitable days, median +7.0% (mech, held to close) / +8.9% (MFE, sold into
  the intraday low). Only 5/17 needed a re-entry; the 2nd leg always held (never needed leg 3).**
- **0DTE option P&L (BS reprice, ATM put, TRADING-time T, central = IV 90% + 10% round-trip haircut):
  median +216% (mech) / +257% (MFE), 17/17 positive, worst day +34%.** Convexity *helps* — a stock down
  8–23% intraday makes the ATM 0DTE put a multibagger. Robust across IV 60–120% (most conservative cell
  still +206% median / +39% worst-day). **⚠ Two real constraints: (1) a STOP LEG loses ~99–100% of its
  premium — each leg's premium is full risk capital, size accordingly; (2) magnitude is model-fragile
  (tiny ATM denominator, single flat IV, no smile, 0DTE fills worse than mid±10%) — trust the SIGN, not
  the number.** MSTR 3/11's re-entry was 15:20 (degenerate, ~40 min of 0DTE life) — a marginal trade.

**Status of the edge:** daily detector = candidate-narrower with no next-day edge; the **realized edge is
selection (the screen) + intraday execution (`lose_vwap` entry, new-high stop, re-enter the next failed
high, sell into weakness).** ⚠ Still **n=17, selection-biased** (these are the days that already passed the
exhaustion screen, which re-surfaces both known cases). **Next:** true out-of-sample — run the detector on
2023 + 2025, pull those bars, re-test. Scripts: `scratch_fade_detector.py` (daily screen),
`scratch_fade_trigger.py` (intraday entry/exit + 0DTE repricing).
