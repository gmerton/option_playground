# tastylive: "I Abandoned Neutral Strangles After This Research" (2025-07-25, 13 min)

_Reviewed 2026-09-23. Two hosts (not Sosnoff) read a research-desk deck. The transcript (`en-orig` auto) is in this
folder. ⚠ **The same study is re-presented 10 months later** as "The Bullish Strangle Nobody Talks About Almost Doubles
Your Return" (`2026-05-26__PhzgL9OpPI`, different host). Its notes carry the "almost twice the ROC" number, which
this cut never reads out. Treat the two as ONE study: effective n = 1 deck._

## Verdict: 2 / 5

**The title is false.** Nobody in the video abandons neutral strangles. The closing verdict is "both of these are
sustainable strategies… **one's not better than the other**" (07:59–08:05), and the host says he'd put neutral
strangles on "now [that] the VIX is in the teens" (12:00).

What the data showed them:
- Over 20 years of SPY, tilting the strangle bullish (30Δ put / 16Δ call) earned more than the 16Δ/16Δ neutral one, with a
  similar success rate but more volatility and a bigger worst loss.
- A plain 30Δ naked put earned more still.
- The bearish tilt earned least.

That's a clean read of **equity drift through the call leg**. Every structure ranks by how much long delta it carries.
The study has **no delta-matched stock control**, and on our data that control is exactly where a short put stops
looking like an edge.

## Data audit

| item | what the video gives |
|---|---|
| Underlying | SPY only |
| Period | "past two decades" (~2005–2025) |
| Arms | (1) 16Δ put / 16Δ call neutral strangle; (2) **30Δ put / 16Δ call** "bullish strangle"; (3) 30Δ naked put; (4) 16Δ put / 30Δ call "bearish strangle" |
| DTE / management | 45 DTE, **all closed at 21 DTE** (03:15) |
| n | not stated. Entry cadence not stated |
| Metrics on the slide | average premium, success rate, annualised return on capital, ROC volatility, largest loss. **Only the premiums are read out** |
| Fills / costs | not stated (tastylive convention: mid, no commissions) |
| Compared to | each other. **No stock, no delta-matched benchmark, no buy-and-hold SPY** |
| Win vs mean vs tail | success "about the same" (bullish vs neutral); bullish has a bigger largest loss; values not read |
| Significance | none |
| Selection | one index, one bull-dominated 20-year path. The host flags that dollar P&L is skewed to recent years because SPY's price quadrupled (01:57–02:36), so fixed-lot dollar results overweight 2020–2025 |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 01:03–01:13 | 30Δ puts "typically generate higher premiums" than 16Δ strangles |
| 01:49–01:57 | Average premium: **30Δ put $3.80 vs 16Δ strangle $3.10** ("$311 or $310" in the captions = $3.10/share) |
| 03:22–03:55 | Bullish strangle: better returns, more volatile, bigger losses on drops; ROC better than neutral |
| 04:00–04:02 | Success rates bullish vs neutral "just about the same" |
| 04:40–04:46 | Neutral: lower ROC volatility, **lower largest loss** |
| 04:57–05:14 | Bullish strangle vs 30Δ naked put: **the strangle made less and had a lower win rate**, but was less volatile with smaller max losses |
| 06:02–06:12 | Naked put: similar success, higher in a bull market; **largest loss "slightly lower" with the strangle** |
| 08:44–09:18 | Bearish strangle (16Δ put / 30Δ call): lowest return, lowest success rate, **lowest ROC volatility and lowest largest loss** |
| 09:37–09:43 | Bearish tilt still made "a little bit" of annualised ROC |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| title | "I abandoned neutral strangles" | ❌ **Contradicted by the video itself** (07:59–08:05, 12:00). Clickbait packaging on a research desk segment |
| 01:03–01:57 | Move the put up to 30Δ and drop the call: same or more premium, no upside risk | ✅ The premium arithmetic is right: put skew makes the 30Δ put richer than a 16Δ pair. But **premium isn't return.** Our BCI study (326 names, 8 years) finds the short put ≈ **stock at the same delta minus costs**. The CSP-vs-stopped-stock test (2026-09-23, 201,849 trades) finds the **unstopped delta-matched stock beats the put** (+0.49 vs +0.36 %/trade, worst 1% −16.9 vs −41.0) |
| 03:22–04:24 | The bullish strangle has better ROC than the neutral one at the same success rate | **Expected from delta alone, and not evidence of premium.** Our vehicle benchmark (4,742 paired entries, real fills): the **30Δ/20Δ put credit spread has NO edge over its own delta, +$7/contract, t 0.26**, and it's significantly worse at low IV rank (−$62, t −2.14). The cross-sectional cw play loses to delta-matched stock by −2.43pp even on the richest spreads. The bullish tilt adds ~+0.14 net delta per strangle to a sample that rose ~4× (≈ +7%/yr); the extra ROC is what that delta earns. Their table can't separate the two because it has no stock arm |
| 04:40–04:47 | The neutral strangle has lower ROC volatility and a smaller largest loss | ✅ Consistent with delta: less exposure, less variance. Nothing to test |
| 04:57–06:12 | The naked 30Δ put beats the bullish strangle on return; the strangle has lower variance and a smaller max loss | ✅ Same ranking by delta. The co-host of the 2026 re-cut says the same about the call leg ("not getting paid"), and our VRP panel agrees: SPY 30d premium +0.69vp, t 1.57, doesn't clear |
| 08:44–09:18 | The bearish strangle underperforms, with the lowest volatility and largest loss, because of "stair step up, elevator down" | ✅ The ranking is the delta ranking again. "Lowest largest loss" makes sense: the put is 16Δ, and the crash side is the one that gaps |
| 09:48–10:11 | A strangle wants time to pass, vol to collapse and the market in range, and that happens most "in low IV environments… drifting higher slowly" | ⚠ **Contradicted on the vol half.** Our VRP panel: the 90d premium by VIX is **−0.51vp at VIX < 15**, +2.53 (t 4.10) at 20–25, +3.45 (t 4.85) at > 25. The SPX strangle playbook: "LowIV regimes (VIX < 20) have near-zero or negative ROC across all delta combos." Low-IV grind-up is where *win rate* is highest and *premium* is thinnest. The one certified short-premium bucket is the opposite regime: **VIX ≥ 20 after a selloff** (SPY bull put t 6.07, SPX condor t 5.21, one bet) |
| 11:40–11:48 | "In the heat of the moment in April [2025]… I was throwing on bullish trades only" | **Agrees with our certified cell, anecdotally.** Selling index put premium after a selloff at high VIX *is* the bearish-high-IV bucket. n = 1 |
| 07:50–08:23 | Trade small; all of these are "decent trades over time as long as you are trading small" | **Sizing: agrees.** "Decent trades over time" for the neutral SPY strangle: **consistent with our corrected number** (+$1.13/share held, real fills, 2018–2026; see below). At the 21-DTE exit it does worse, not better: **21-DTE close − hold −$0.52/share, month-clustered t −2.42** (NULL on return, leaning INVERTED; risk reducer only: sd $9.33 vs $17.09, worst −$291 vs −$617) (re-run 2026-09-24, FIX-1) |

### What their researchers' data showed vs our strangle finding

- **Them:** every SPY 45-DTE strangle variant makes money (mid, 21-DTE close), and the bullish tilt makes the most. Nothing
  was abandoned.
- **Our ledger said:** the 45-DTE 20Δ strangle, 44 names, 2018–2026, sold at the bid and bought back at the ask, **loses in
  both arms**: hold −$2.55, 21-DTE close −$1.02 (paired +$1.53, t 4.26). SPY: hold −$1.77, 21-DTE −$0.46 per share.
- **⛔ That was an artefact (verified here, caveat below).** The study discards every trade whose two legs both expire
  worthless. **Restored, SPY held to expiry at real fills is +$1.13/share, median +$3.72, 75% win (n 402, 2018–2026).**
- ⟹ **On SPY our corrected data AGREES with theirs on sign.** The neutral 45-DTE strangle is positive at real fills even
  through 2020 and 2022. What's left of the disagreement is magnitude, the 21-DTE exit (not yet re-run on the full sample)
  and t (not computed). Answer to Gabe's question (1): **they didn't abandon neutral strangles, and our "it loses at real
  fills" finding doesn't stand.** It needs a clean re-run before either side of the claim is cited.
- ✅ **Re-run 2026-09-24 (FIX-1, 44 names, n 14,367):** hold **+$0.23/share, 74% win**; 21-DTE close **−$0.29, 64% win**;
  21-DTE − hold **−$0.52, t −2.42**. So "loses at real fills" is retracted (≈ flat held), and their 21-DTE close is the
  *weaker* arm on return; it only cuts risk.

### Settlement caveat on our strangle panel

⛔ **VERIFIED 2026-09-23 while writing these notes: the hold-to-expiry arm of `run_21dte_exit_test.py` drops the
winners.**

- **The mechanism:** line 83 applies `df[(bid > 0) & (ask > 0)]` to the **whole** frame, expiry day included. A leg that
  expires worthless has a zero bid on expiry day, so it's filtered out. When **both** legs expire worthless, `fin` is
  empty, and the `continue` at the settlement step **discards the trade**.
- **The effect:** the sample is selected on the expiry outcome, and the discarded trades are exactly the full-credit
  winners.
- **The check** was a targeted SQL re-pull of SPY (entries at 40–50 DTE, plus all expiry-day rows, same `pick()` and
  settlement as the study). Script: `data/tastylive/videos/research/check_21dte_settlement_spy.py`.
  - It reproduces the study exactly: **242 kept, mean −$1.77, 58.3% win.**
  - Out of **408** SPY entries, **166 were dropped. 160 of those have expiry-day rows**, all zero-bid, i.e. both legs
    worthless. The dropped trades average **+$5.51** (≈ the full credit).
  - **With them restored, SPY hold-to-expiry is +$1.13/share mean, median +$3.72, 75% win (n 402).**
    **The sign flips.**
- ⟹ The "45-DTE strangle loses at real fills" headline (hold −$2.55 / 21-DTE −$1.02 on the 44-name panel) is **not
  reliable as stated.** The **21-DTE PASS (+$1.53, t 4.26)** is computed on the same winner-depleted sample, so it's biased
  toward the early exit: on a full-credit winner, holding beats closing at 21 DTE.
- **The PASS needs a re-run** with settlement at intrinsic from chain-recovered spot (no bid filter on expiry day) before
  anything cites it. **The TEST_INDEX row isn't edited here (per instructions). Flagged to the caller.**
  ✅ **Done 2026-09-24 (FIX-1): PASS RETRACTED.** n 14,367: 21-DTE close − hold **−$0.52/share, month-clustered
  t −2.42**, halves −0.63/−0.40 → NULL on return, leaning INVERTED; risk reducer only (TEST_INDEX §1).
- Same failure family as the `run_iv_condor_study.py` INVALID row, pointing the other way: that one booked missing marks
  as wins; this one deletes the wins.

### The skew question: bullish strangle vs "the put spread has no edge over its own delta"

The two findings are **the same fact seen from two sides.** Tilting a short strangle bullish raises return because it adds
long delta in a rising market. Our benchmark says that delta is all a short put carries (+$7/contract over delta-matched
stock, t 0.26). So "the bullish strangle almost doubles your return" should be restated as "**the bullish strangle is a
neutral strangle plus about 0.14 SPY delta**", and should be judged against simply holding that delta.

⚠ One nuance in their favour. **Our own certified SPX cell is a bullish-skewed 45-DTE condor: 0.30Δ put / 0.20Δ call**
(bearish-high-IV, net t 5.21). The skew was picked by a 49-cell sweep, and the SPX bullish-high-IV cell's best put was even
fatter, 0.40Δ. So our data *also* prefers the fat put. But it pays only after a selloff at VIX ≥ 20, where elevated IV and
mean reversion both favour the put seller. That is premium plus a rebound, not a permanent tilt.

## What I would take

1. **Don't read "bullish strangle > neutral" as a premium finding.** It's delta. Any skew test here needs a
   delta-matched SPY arm.
2. **Their bearish-tilt row is a useful negative:** the only structure with less long delta did worst in a bull sample.
   Same mechanism.
3. **Nothing to adopt.** The skewed structure we trade (0.30p/0.20c) is already the certified cell, and only in its regime.

## Not tested, could be

**Neutral vs bullish vs bearish SPY strangle with a delta-matched stock arm, at real fills.**
- **Data:** v3 SPY 2010–2026. The puts come from `data/cache/SPY_puts_v3_2018_2026.parquet` plus a pull for 2010–2017 and
  for the calls.
- **Arms:** 16/16, 30p/16c, 16p/30c and a naked 30Δ put, every Friday, 45 DTE, sell the bid, close at the first session
  ≤ 21 DTE at the ask.
- **Control:** for each arm, SPY shares = entry net delta, held over the same window.
- **Primary:** (bullish − neutral) minus (their delta-matched stock difference), month-clustered t, both halves, per year.
- **Secondary:** the same cut on bearish-high-IV dates vs all other dates. Does the skew pay only inside the certified
  regime?
- **Effort:** ~1 day (v3 call pull ~2 h Athena; engine = the 21-DTE harness plus a delta-matched stock leg from
  `run_vehicle_benchmark.py`). Local.
- **Prior:** the skew premium ≈ 0 after the delta control outside the certified regime.
