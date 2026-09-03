# The VCP "Low-Risk Entry" — Minervini Private Access

> **Verdict:** The entry half is the framework this repo already runs, and the repo's own 20-year
> test independently supports its core (volume-confirmed breakouts work — at RVOL ≥1.8). The
> genuinely new material is the **exit framework**: sell ⅓–¼ into strength at ~+20% to "finance the
> risk," then trail with a manually-ratcheted "backstop." That is specific, testable, and addresses
> an open gap in this repo. Everything *differentiating* about the presentation — RPR, "FAB Five,"
> trend-stage, extension alerts — is proprietary and unavailable. Evidence is winners-only and the
> headline is oversell.
> **Type:** swing (primary) / short-term intraday (Weissman variant) · **Instrument:** US equities
> **Conviction:** 2.5/5 · **Risk:** 5/10 · **Tested?** **partial** — entry side covered by
> [`data/studies/industry_rotation_detection_study.md`](../../studies/industry_rotation_detection_study.md) Part II; exits untested.
> **Source:** [Trading $100K Into $20 Million With Only One Setup | The VCP Strategy](https://www.youtube.com/watch?v=uMJXA_I9HDw),
> TraderLion, 2026-07-29, 1:12:22 — [transcript](../videos/interviews/2026-07-29_uMJXA_I9HDw/transcript.txt)

---

## 1. Who, and what's being sold

- **Mark Ritchie II** and **Brandon Hedgepath** — portfolio managers, and directors of trading /
  education at **Minervini Private Access (MPA)**. Attended Minervini's first Master Trader Program
  in 2010; 10 years as paying subscribers before joining the team.
- **Bob Weissman** — director of ops at MPA, 22 years working with Minervini, 38 years trading;
  **2025 US Investing Championship winner, money-manager division, +115%**.
- Host: Richard (TraderLion), himself an MTP alum.

**Commercial context, stated plainly:** this is an MPA panel on a channel that runs a **mid-roll
sponsor read for the Deepvue platform** ([13:42], "DFW" in the captions) with a free-month offer.
Every mechanism cited runs through MPA/Deepvue proprietary tooling. The video is a funnel.

## 2. Mechanics

**Universe / screening — bottom-up, explicitly NOT theme-first** [07:24]:
> "We let the market tell us what to trade… we're bottoms up. We're going to find whatever stocks
> are meeting Mark's criteria, and from there it may turn out there's a bunch of them in the memory
> space."

Asked directly whether the data-storage theme mattered for STX, Ritchie: *"Not really."* [06:12]
He manages **correlation risk by cutting size in real time**, not by refusing correlated names —
"if they're both breaking on the same day, I'd buy them both."

**Filters (all proprietary):**
- **RPR** ("relative performance ranking") — every stock vs every *other stock*, not vs the index,
  scaled 1–100. Entries cited at **98–100** (top 2%).
- **"FAB Five"** behaviour analytics — never defined on camera.
- **Trend-stage indicator** — must be Stage 2; red = doesn't qualify [52:00].
- News-count overlay (18 news items on a day vs 2 = something real happened).

**Setup — the VCP:** 1-2-3 progressive contractions, volume drying up into the pivot, tight final
range (~5% cited for STX). The strongest single tell given: **"right before we bought was one of
the lowest volume days in that whole base"** [05:12].

**Entry variants — note the video's own title says "only one setup"; at least six appear:**

| Variant | When |
|---|---|
| Classic pivot buy | textbook VCP, buy through the pivot high |
| Pullback buy | after a failed/early breakout, 1-2-3 pullback on light volume + inside day |
| "Cheat" / low cheat | earlier entry inside the base; needs confirmation if riding the 50-day |
| "Pause pivot" | gap-up then sideways pause; not a classic pivot but valid |
| Early turn | **only** for a power play or big base, and only at very high RPR |
| Bottom-fishing pivot | after 3–4 lower lows on a high-RPR name |

**Execution:** buy **incrementally**, add through the level, and pay up rather than haggle —
> "I'd much rather pay up 1% to be sure that the stock is free and clear and on the move." [12:44]

**Sizing:** STX was **~7.5%** of the book [09:54]. Size is a function of *how the trader is
currently performing*: "If I have a tight entry and I'm running racks, I'm coming in big right off
the hop. If things aren't working… I'm going to start smaller, build up slower." [10:26]

## 3. Risk management

- **Stop:** a "violation" of the rules, or the stop level — "you hit a stop level, you just get out."
  ⚠ the violation list is proprietary (built into their charting as indicators).
- **Time stop:** *"all our losers look the same. It doesn't work within one to five days — max
  probably 5 to 10 — we're gone."* [35:53]
- **Expectancy target:** ~50% win rate, **2:1 average win to average loss** [39:47].
- **Earnings:** *"never hold an overweight position into an announcement like that, because you're
  guaranteed at some point to take a massive hit."* [25:40] No fixed cushion rule — sized to
  personal tolerance ("pillow factor").

## 4. The exit framework — the genuinely differentiated content

This is where the panel spends most of its time, and it is the part this repo does not have.

1. **First sale finances the risk.** Sell ⅓ (STX) or ¼ (ARM) into the first strong thrust, around
   **+17–20%**. *"That financed the risk. So now we had a free roll."* [15:49]
2. **Don't let a 15–20% gain round-trip.** Hold through the *first* natural reaction to see if you
   own **"a tennis ball or an egg"** — but if up 15–20%, sell a piece into it rather than give it
   all back [41:28].
3. **Sell into strength, in pieces, as extension grows.** They have historical extension levels
   coded (vs the 50-day) and leak out more as the stock gets statistically stretched [17:14].
4. **The "backstop"** — explicitly *not* a resting trailing stop. After a gap up, place a manual
   stop just under the gap day's low and ratchet it up, letting momentum take you out. Used only in
   "profit-protection mode" when already well extended [43:09].
5. **Final piece:** close below the 50-day.

The rationale is volatility-of-equity-curve, not price prediction [38:05]: a 20% give-back on the
last tranche is not worth the drawdown when the capital can be redeployed into a fresh low-risk
entry. Ritchie: *"performance is measured on return relative to risk."*

## 5. Claimed edge & returns

| Claim | Where | Status |
|---|---|---|
| $100K → **$20 million** over 15 years (Ritchie II + Hedgepath, pooled) | [30:47] | Unaudited, no CAGR/drawdown, two people, 15 yrs |
| Weissman **+115%** in 2025, USIC money-manager division | [01:50] | Real competition; small self-selected account |
| **~80% of that 115% came in Aug–Oct** (3 months) | [56:48] | Concentration admitted — argues against generalizing |
| "5 of the last 7" USIC winners were MPA members | [71:20] | Marketing; survivorship |
| STX ≈ $1M profit on a **7.5%** position | [05:03] | No account size → unverifiable |
| MU ≈ $1M, +70% in ~3 weeks | [48:38] | ditto |
| ARM: sold 25% at +17.75%, 25% next day, rest **+40% in days** | [53:33] | ditto |

Case studies: **STX, FLNC, MOD, VICR, MU, ARM, AVGO, IREN, NBIS**, plus a SpaceX IPO-day 5-minute
VCP. Weissman's 2025 work was **4–5 day holds**, not swing trading — a different strategy presented
under the same banner.

## 6. Objective assessment

- **The title is straightforward oversell.** "$100K Into $20 Million With Only One Setup" — it's
  two traders, fifteen years, no denominator, and by their own account **at least six** entry
  variants. The panel is more honest than the title.
- **Winners-only, and they say so:** *"obviously we're reviewing winners here."* [35:53] Nine
  case studies, zero losing trades walked through. AVGO is the closest and it's framed as a save
  (exited ~breakeven because they'd de-risked into the pre-earnings rally).
- **The differentiating mechanism is a black box.** RPR, FAB Five, trend-stage, violation
  indicators, extension levels — all MPA/Deepvue-only. What's left when you strip them out is
  generic VCP, which is public.
- **Circular stop rule.** "Get out on a violation of Mark's rules," where the rules are a
  proprietary indicator. Not falsifiable as stated.
- **Sizing rule is discretionary and reflexive** — size on how well *you* are trading. Defensible
  as risk management, impossible to backtest, and a route to over-sizing after a hot streak.
- **Caption quality is poor.** Verify every figure: "three-quarters of a billion" [00:00] is almost
  certainly three-quarters of a *million*; "DCP" = VCP; the platform is Deepvue, not "DFW."

## 7. What's genuinely sound

- **The core is independently supported by this repo's own data.** The 20-year, 299-name test
  (rotation study Part II) found breakouts *in aggregate* are negative (−0.51pp at 21d, t=−3.29)
  and only the **volume-confirmed** subset works (RVOL ≥1.8 → +0.86pp at 63d, t=3.64). Their
  insistence on volume dry-up into the pivot and a decisive move out of it is the right variable.
- **"Efficiency of capital" as the reason for a tight entry** [45:41] — wanting to know quickly
  whether you're wrong so capital can rotate — is the same logic behind the repo's trigger-bar stop.
- **The exit framework is coherent and specific.** Financing the risk out of the first thrust is a
  real mechanism, not a platitude, and the equity-curve argument for it is sound.
- **Honest moments:** ~50% win rate expected; "we don't always sell perfectly"; "everybody's a
  genius after the fact"; Weissman conceding his 2025 result was concentrated in three months and
  came from a *different* (short-term) style.

## 8. Testability

| Component | Class | Note |
|---|---|---|
| VCP contraction + volume dry-up + pivot breakout | **EOD-testable — partly done** | Entry side already covered; see below |
| Sell ⅓ at +20% vs hold-and-trail | **EOD-testable — NOT done** | The highest-value open test |
| Backstop-under-gap-low trailing | EOD-testable | Approximable on daily bars |
| Time stop (out in 5–10 days if it doesn't work) | **EOD-testable — NOT done** | Cheap and directly actionable |
| Never hold overweight into earnings | EOD-testable | Repo already has earnings dates + `options_daily_v3` |
| RPR / FAB Five / trend stage / extension alerts | **Proprietary — untestable** | Substitute: repo's own RS + Minervini template |
| Weissman's 4–5 day intraday variant | Needs intraday data | Not wired up |
| "Size by how you're trading" | Discretionary | Not testable |

**What the repo already knows about the entry side** (rotation study Part II, 299 names, 2006–2026)
— and where it refines the video's advice:
- Raise the RVOL gate to **~1.8**; 1.3–1.8 is still negative.
- **Veto** breakouts below the 200-day SMA or down >10% over six months (−3pp at 21d).
- **Don't require the 52-week high** — the 3–15%-off-high cohort beats the at-the-high cohort.

## 9. Overlap with the existing book

- **Entry: ~90% duplicate.** `run_minervini_scan.py` (Trend Template), the breakout scorecard, and
  the pivot/volume gates already implement this. See [[project-minervini-scan]],
  [[project-breakout-monitor]].
- **Exit: genuinely additive.** Exit levers are a known gap — flagged unbuilt in the Sleeping
  Giants work, and "exit = sell intraday strength" is the *second* alpha in the Tito playbook. This
  video supplies a concrete, testable exit policy from the same lineage.
- **Contradiction worth noting:** Ritchie explicitly dismisses top-down sector work ("not really,"
  "bottoms up"), whereas the daily report leads with sector/industry RS. The repo's own rotation
  study **supports Ritchie** — industry RS was found descriptive, not predictive
  ([[project-rotation-detection-study]]).

## 10. Next test (recommended)

**Exit-policy bake-off** on the existing 299-name / 2006–2026 panel, over volume-confirmed
breakouts (RVOL ≥1.8):

| Policy | |
|---|---|
| A | Hold to a 50-day-close stop (baseline) |
| B | **Sell ⅓ at +20%, remainder to the 50-day stop** (their rule) |
| C | Sell ⅓ at +20%, ⅓ at +40%, remainder to the 50-day |
| D | B + time stop: exit if not up X% within 10 days |
| E | Trailing-stop-only, no scale-out |

Report CAGR-equivalent, max drawdown, and **return per unit of risk** — the metric Ritchie says
matters. That directly tests whether "financing the risk" improves risk-adjusted return or merely
truncates winners, which is the real question and one the video cannot answer about itself.
