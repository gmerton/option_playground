# Long-call strategy — research plan and step 1 results (opened 2026-09-16)

**Origin.** The straddle leg-decomposition (`straddle_directional_legs_2026-09-16.md`) found the call is the best leg
in every trend bucket, and that *always buying the call* on the gated straddle signals earned +9.47%/trade against the
straddle's +4.34%. Gabe proposed building a call strategy in two steps: (1) adapt the straddle's gate to the new
vehicle, (2) optimise expiry and strike.

## ⚠ The governing risk, stated once

2019–2026 contains one bear year. **Any long-call strategy is long delta, so it will look good on this sample by
construction.** The benchmark for every result in this project is therefore **always-call (+9.47%/trade)**, never the
straddle, and **2022 is a separate must-pass** (always-call: −24.6%). A rule that beats the straddle but not
always-call has discovered leverage, not edge — the same trap as the ungated 52Δ/17Δ vertical in
`momentum_skew_vertical_study.md`. Report weekly/monthly t (not per-trade), the mean excluding the top 1% of trades,
and the 2022 number, on every cut.

## Step 1 — does the straddle's gate transfer to the call? **No.**

13,417 FVR-passing trades, call leg only, house cost model, intrinsic settlement (`leg_decomp.parquet`).

| gate | n | call | win | weekly t | mean ex-top-1% | 2022 |
|---|---|---|---|---|---|---|
| all FVR-passing | 13,417 | +6.41% | 36% | 2.01 | −0.72% | −4.2% |
| **+ IV pct ≤ 30** (the straddle's workhorse gate) | 5,886 | +7.62% | 36% | **0.60** | +0.23% | **−25.3%** |
| IV pct > 30 (the side the straddle rejects) | 7,531 | +5.46% | 36% | **1.99** | −1.28% | **+1.9%** |

The IV-percentile gate raises the headline mean and **destroys** everything else: weekly t falls from 2.01 to 0.60 and
2022 goes from −4% to −25%. It is the straddle's most important gate and it is actively harmful to a call.

That is economically coherent. Low own-IV means the market prices little movement. A straddle wants cheap vol because
it needs movement in *either* direction and pays for both. A call has given up the put, so a quiet stock that drifts
down is a total loss — cheap vol is now a warning, not a discount.

**By IV percentile, the call prefers the opposite end:**

| own-IV percentile | n | call | weekly t | ex-top-1% | 2022 |
|---|---|---|---|---|---|
| 0–10 | 2,453 | +6.57% | 1.63 | −1.09% | −18.3% |
| 10–20 | 1,765 | +11.91% | −0.10 | +4.61% | −31.3% |
| 20–30 | 1,668 | +4.63% | 0.91 | −1.98% | −24.5% |
| 30–50 | 2,813 | +4.24% | 2.27 | −2.70% | −25.6% |
| 50–75 | 2,985 | +6.37% | 1.82 | +0.39% | −2.8% |
| **75–100** | 1,733 | +5.87% | 1.87 | −1.52% | **+43.7%** |

The 10–20 bucket has the best mean and ex-top-1% but a weekly t of −0.10 — a few weeks carry it. The robust cells are
50–75 and 75–100, and the top bucket is the only one that survives 2022, by a wide margin. **FVR still helps** (>1.35:
weekly t 2.26, 2022 +0.4, versus 1.2–1.35: t 1.57, 2022 −7.0), so the forward-vol gate transfers even though the
IV-percentile gate does not.

**Trend, on the fully gated set** (4,795 trades with panel coverage):

| trend (ext. from 21 EMA, ADR) | n | call | ex-top-1% | 2022 |
|---|---|---|---|---|
| down (≤ −0.3) | 1,255 | +5.57% | −1.36% | −40.4% |
| flat | 671 | +5.27% | −1.30% | +7.4% |
| **up 0.3–1** | 895 | **+16.45%** | **+8.27%** | −10.1% |
| up 1–2 | 1,112 | +10.57% | +3.31% | −36.6% |
| up > 2 | 862 | +9.77% | +3.42% | −30.6% |

Mild uptrend is the standout and **the only cell whose edge is not purely tail-driven** (+8.27% excluding the top 1%,
against roughly zero everywhere else). Note it decays as extension grows, which matches the ORB9 extension finding.

## Plan

**Step 1b — DONE 2026-09-16. A gate that clears every kill criterion.**

Benchmark is always-call on this set: **+6.41%/trade**, weekly t 2.01, mean ex-top-1% −0.72%, 2022 −4.2%.

| rule | n | call | weekly t | ex-top-1% | 2022 | years + |
|---|---|---|---|---|---|---|
| always call (benchmark) | 13,417 | +6.41% | 2.01 | −0.72% | −4.2% | 7/9 |
| IV pct ≤ 30 (straddle gate) | 5,882 | +7.67% | 0.60 | +0.27% | −25.3% | 7/9 |
| uptrend 0.3–1 ADR | 1,935 | +10.83% | 1.99 | +3.68% | −13.3% | 7/8 |
| **uptrend 0.3–1 ADR + 21 EMA rising** | **1,620** | **+13.37%** | **2.28** | **+5.95%** | **+7.7%** | **8/8** |
| + IV pct ≥ 50 on top | 529 | +12.23% | 2.30 | +6.68% | +26.5% | 6/8 |

The winning rule beats always-call by 7pp, has a higher weekly t, is positive in **every** year, survives 2022, and —
the part that matters most — earns **+5.95% excluding the top 1% of trades** against the benchmark's −0.72%. This is
the first cell in any of this month's work whose edge is not tail-driven.

**It survives a split-half test.** Train (2019 → 2022H1): rule +12.28% vs base +4.82%, edge +7.5pp. Test (2022H2 →
2026): rule +14.27% vs base +9.62%, edge +4.7pp. Both halves positive, edge in both.

**Band sensitivity says the sweet spot is nearer the EMA than first tested**: 0–0.8 ADR gives +18.44% (weekly t 3.45,
ex-top-1% +11.85%, 2022 +27.7%) and 0.2–0.8 gives +20.21%; it decays to +7.11% at 0.5–1.5 and ex-top-1% goes negative.
That matches the ORB9 extension result and the August finding that entries 1–2 ADR over the 21 EMA are a leak.

⚠ **The honest caveat.** Neither component works alone in the expected direction: 'rising' on its own is +6.17%
(worse than 'not rising' at +10.18%), and the band alone is +10.83%. Only the combination is strong. That is either a
real setup — a pullback to a rising 21 EMA, which is precisely this book's core discretionary entry — or a mined
interaction. The band was also chosen in-sample and keeps improving as it is re-tuned, which is a fitting signature.
**The step-2 pull is the real test**: it covers every Friday for 331 names rather than only FVR-gated straddle
signals, so the gate can be re-validated on roughly ten times the entries, unfiltered.

### Correction (same day, Gabe queried the sample): the step-1b edge is inflated ~2x by the FVR filter

The step-1b sample was the **FVR ≥ 1.20 third** of the straddle file — 13,459 of 41,757 ticker-Fridays. The other
68% had no path data, but the file carries an entry mid and an expiry-day last print for **every** row, so the rule
can be tested outside the gate on a consistent (optimistic, no-slippage) basis where only rule-minus-base is
meaningful:

| sample | n | always-call | rule | rule weekly t | rule ex-top-1% | rule 2022 | years + | **edge** |
|---|---|---|---|---|---|---|---|---|
| all rows, no FVR filter | 32,592 | +11.22% | +14.68% | 2.88 | +7.65% | +22.9% | 8/8 | **+3.45pp** |
| FVR ≥ 1.20 (the step-1b sample) | 10,942 | +11.70% | +17.56% | 2.80 | +9.94% | +12.8% | 8/8 | **+5.86pp** |
| FVR < 1.20 (never tested before) | 21,650 | +10.99% | +13.01% | 1.90 | +6.34% | +26.8% | 8/8 | **+2.03pp** |

**The rule survives outside the gate** — positive, 8 of 8 years, 2022 strongly positive, ex-top-1% still healthy — so
it is not an artefact of the FVR filter. But **the FVR gate roughly triples the edge** (+5.86pp inside against
+2.03pp outside), so the two are complementary and FVR should stay in the strategy. The step-1b headline of +7pp over
benchmark is therefore the *gated* figure; applied broadly the rule is worth about +3.5pp.

Note the benchmark itself moves from +6.41% (proper cost model, slippage, parity settlement) to +11.22% on this
optimistic basis. That ~5pp gap is slippage plus last-print settlement bias — a reminder that **only the
rule-minus-base differences in this table are meaningful, never the levels.**

**Revised gate going into step 2:** keep FVR ≥ 1.20, drop IV pct ≤ 30, add extension 0–1 ADR over a rising 21 EMA.

**Step 1b (superseded — original plan).** Build the call's own gate from `leg_decomp.parquet`: FVR, own-IV percentile (testing
the *high* end), mild-uptrend, and their interactions — scored against always-call, with 2022 and ex-top-1% as
must-passes. Cheap, and it decides whether step 2 is worth the pull.

**Step 2 (needs an Athena pull).** Expiry and strike grid: DTE {7, 14, 21, 30, 45} × delta {0.65, 0.50, 0.40, 0.30,
0.20} for the 331-name pool, 2018 → **Feb 2026** (v3 loses bid/ask in March 2026). Roughly the shape of the
skew-vertical pull, which took minutes. Erratum rules apply: wide strike window, no delta filter on anything feeding a
path, settle at intrinsic from the underlying.

**Step 3 (only if 1b and 2 clear).** Management — hold to expiry versus a profit take or trailing stop. Every study so
far says hold wins, except the ETF put spread where the take *was* the edge, so it must be tested, not assumed.

**Kill criteria, set now.** Drop the project if the best gated rule fails to beat always-call on weekly t, or if 2022
is worse than −15%, or if the mean excluding the top 1% of trades is not clearly positive.


## FVR threshold sweep (2026-09-16): **do not tune it — the relationship is bimodal**

Gabe asked whether 1.20, chosen for the straddle, is the right floor for a call. Swept on top of the trend rule
(extension 0–1 ADR over a rising 21 EMA), same optimistic basis, 5,907 trades before the FVR gate.

**Floor sweep** — looks like a clean optimum at 1.30:

| FVR floor | n | call | weekly t | ex-top-1% | 2022 | train | test |
|---|---|---|---|---|---|---|---|
| none | 5,907 | +15.58% | 3.01 | +8.43% | +21.0 | +13.88 | +16.85 |
| ≥ 1.00 | 3,773 | +15.78% | 2.97 | +8.40% | +18.3 | +12.78 | +18.26 |
| ≥ 1.20 | 2,129 | +17.53% | 3.29 | +10.00% | +18.7 | +16.67 | +18.23 |
| **≥ 1.30** | 1,418 | **+21.99%** | **3.79** | +13.78% | +25.9 | +18.22 | +25.05 |
| ≥ 1.50 | 514 | +19.30% | 2.05 | +9.58% | +20.3 | +20.50 | +18.36 |

**But the band decomposition shows why that optimum is not real:**

| FVR band | n | call | weekly t | ex-top-1% | years + |
|---|---|---|---|---|---|
| 0.0–0.9 | 1,388 | +10.87% | 1.84 | +4.86% | 7/8 |
| **0.9–1.0** | 746 | **+23.27%** | 2.69 | +16.86% | 8/8 |
| 1.0–1.1 | 843 | +14.79% | 1.28 | +8.30% | 8/8 |
| 1.1–1.2 | 801 | +12.20% | 1.39 | +4.33% | 6/8 |
| **1.2–1.3** | 711 | **+8.62%** | 0.98 | +2.74% | **5/8** |
| **1.3–1.5** | 904 | **+23.52%** | 3.23 | +16.23% | 8/8 |
| ≥ 1.5 | 514 | +19.30% | 2.05 | +9.58% | 7/8 |

The response is **bimodal**: two strong buckets (0.9–1.0 and 1.3–1.5) with the *worst* bucket (1.2–1.3) sitting
between them. A genuine economic relationship would be monotone or single-peaked. The apparent "1.30 floor is best"
result is simply the floor that happens to exclude the weak 1.2–1.3 bucket — a threshold fitted to one noisy cell,
not a discovered level.

**Conclusion: the FVR floor is not optimisable on this evidence and should not be tuned.** Note also that the trend
rule *alone* is +15.58% with weekly t 3.01, 8 of 8 years, ex-top-1% +8.43%, train +13.88 / test +16.85 — the robust
part of the strategy is the trend gate, and FVR adds roughly 2pp on top of it, which is inside the noise implied by
the band structure. (The earlier claim that FVR "triples the edge" used the narrower 0.3–1 trend band; widening the
band to 0–1 strengthens the trend rule and shrinks FVR's marginal contribution.)

**Carry into step 2:** trend gate = extension 0–1 ADR over a rising 21 EMA. FVR ≥ 1.20 retained as a mild preference
only, at its original value, never re-tuned. The call-grid data with a proper cost model decides both.

## Step 2 (2026-09-16): expiry × strike grid on the full unfiltered universe

`run_call_grid_pull.py` + `run_call_grid_sim.py`, cache `data/cache/call_grid/` (60M option rows, 794 MB, gitignored).
**2.4M call entries**: every Friday 2018 → Feb 2026, 331 tickers, five DTE targets × five delta targets, entry at
mid + 25% of the leg's bid-ask + commission, held to expiry, settled at intrinsic against a put-call-parity spot.
1.66M carry a trend signal. ⚠ The pull was delta-filtered, which left too few expiry-day rows to settle from — parity
on any near-ATM pair sidesteps that, and no re-pull was needed, but it is the erratum trap in a new costume.

### The gate does not survive pooled — it is horizon-specific

| set | n | ROC | weekly t | ex-top-1% | 2022 |
|---|---|---|---|---|---|
| all entries (benchmark) | 1,661,440 | +15.99% | 4.71 | +0.90% | −9.8% |
| gate: ext 0–1 ADR + rising 21 EMA | 300,725 | +15.42% | 3.83 | +0.22% | −7.8% |

Pooled edge **−0.57pp**; train −1.68, test +0.80. But per cell the gate's edge is cleanly ordered by horizon:

| gate edge (pp) | 0.20Δ | 0.30Δ | 0.40Δ | 0.50Δ | 0.65Δ |
|---|---|---|---|---|---|
| 7 DTE | +2.7 | +4.8 | +4.0 | +2.5 | +2.1 |
| 14 DTE | +6.2 | +4.7 | +5.1 | +1.5 | +1.4 |
| 21 DTE | +2.1 | −0.4 | +1.5 | −1.8 | −0.5 |
| 30 DTE | −5.8 | −5.7 | −4.1 | −4.6 | −2.2 |
| 45 DTE | −5.7 | −6.8 | −4.8 | −5.7 | −3.6 |

A pullback to a rising 21 EMA is a short-horizon setup. Over 7–14 days it is informative; by 30–45 days it has
resolved and the label is stale. That is coherent, and it is why it looked strong on the 7-DTE straddle data.

### The raw grid says "longer is better" — that is beta, and it inverts on capital

Ungated mean ROC rises monotonically with DTE (7d ≈ 9%, 45d ≈ 26%) and so does the weekly t (2.0 → 6.3). **Per day of
capital it reverses completely:**

| ROC per day, gated | 0.20Δ | 0.30Δ | 0.40Δ | 0.50Δ | 0.65Δ |
|---|---|---|---|---|---|
| 7 DTE | 1.956 | **2.069** | 1.944 | 1.621 | 1.132 |
| 14 DTE | 1.230 | 1.335 | 1.231 | 0.890 | 0.706 |
| 45 DTE | 0.487 | 0.510 | 0.491 | 0.392 | 0.317 |

Longer holds simply capture more drift. Regressing each cell's ROC on the underlying's move, **the move alone explains
17–70% of the variance**, and the intercept is negative almost everywhere (45 DTE / 0.20Δ: −27.3) — the long-dated
low-delta cells are pure theta bleed dressed as return. **Every ungated cell loses in 2022.**

### Candidates

| configuration | n | ROC | per day | weekly t | ex-top-1% | 2022 | years + |
|---|---|---|---|---|---|---|---|
| 45 DTE / 0.40Δ, ungated | 68,501 | +25.89% | 0.610 | 6.26 | +11.83% | −7.98% | 7/8 |
| **14 DTE / 0.40Δ, gated** | 12,195 | +17.21% | 1.231 | 2.90 | +4.94% | −0.00% | 7/8 |
| **7 DTE / 0.40Δ, gated** | 11,537 | +13.41% | 1.944 | 2.31 | +3.49% | **+2.43%** | **8/8** |

### Verdict against the kill criteria set at project open

1. *Beat always-call on weekly t* — **marginal fail**. At 7 DTE the gate gives t 2.31 against 2.18 ungated; at 14 DTE
   2.90 against 3.09; pooled 3.83 against 4.71. The gate's value shows up in 2022 survival and capital efficiency,
   **not** in the t-statistic.
2. *2022 better than −15%* — passes comfortably, and the short-dated gated cells are the only ones that are positive.
3. *Mean ex-top-1% clearly positive* — passes for the gated short-dated cells (+3.5 to +4.9).

**Reading.** There is no selection edge here worth the name; what the grid mostly measures is how much bull-market
drift a long-delta position captures, which is why it grades better the longer you hold. The one genuinely useful
finding is the horizon structure of the trend gate, and the one defensible configuration is a **7–14 day, ~0.40-delta
call on a name pulling back to a rising 21 EMA**, which is the only cell that is positive in every year, positive in
2022, not tail-driven, and three times more capital-efficient than the headline-grabbing 45-day cell.

**Not promoted to the book.** It fails its own primary criterion, and a strategy whose return is 17–70% explained by
the underlying's move is a directional bet that should be sized and judged as one, not as an options edge.
