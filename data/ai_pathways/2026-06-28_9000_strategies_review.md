# Review: "Claude Tested Over 9,000 Trading Strategies (Here's What Works)" (AI Pathways, Brendan, 2026-06-28, nLQhKkjkuWI) — 2/5

Reviewed 2026-09-22. 19:54, 377k views. Funnels to a paid Skool community; the last ~3 minutes are the pitch
plus screenshots of the four prompts. Transcript: `videos/education/2026-06-28_nLQhKkjkuWI/`.

⚠ **Read the date first.** This is the **earlier** of the two AI Pathways videos in this KB (June; the ICT
25k video is August). It is therefore the *earlier build* of the same testing rig, and it is missing the three
guardrails that earned the ICT video a 3: a **coin-flip null**, an explicit **luck-correction step inside the
funnel**, and a **sealed holdout run once**. Their method got better over the summer. The 2/5 here is a verdict
on this artefact, not a downgrade of the channel's trajectory.

## What was done

Daily bars, 30 liquid assets (SPY/QQQ, all sector ETFs, gold, oil, bonds, BTC, ETH, AAPL, NVDA), 15 years
(~2010–2025). Classic strategy families — trend, mean reversion, momentum, volume, volatility, pattern — each
in "bare stripped-down form", each swept over a range of settings. That product is the 9,000 backtests.
Walk-forward: build/tune on an older chunk, evaluate on a newer one. Then a six-filter funnel:

> 9,000+ → **1,218** (out-of-sample Sharpe > 0.5) → drawdown ≤ 35% → in-sample-vs-out-of-sample degradation →
> minimum trade count → **524** → **478** (assets with ≥10 years of history only)

Finally a bootstrap: each survivor's trades reshuffled 500 times.

## What they claim

1. **Mean reversion is the only family positive on average.** Trend, volume, composite, volatility and pattern
   are all negative on average. Mean reversion is **64% of the 478 survivors**, and survives across breadth —
   RSI reversion on 20 tickers, Keltner reversion on 18.
2. **Trend is situational, not dead.** The single top survivor by "score" is *Turtle on Apple* at 1.18; other
   trend strategies rank high, "on specific strong trending names like Apple and Nvidia".
3. **Overfitting kills most of it.** Only 44% of strategies that looked strong in-sample stayed strong
   out-of-sample. TradingView-style single backtests are worthless because they have none of this validation.
4. **The bootstrap separates real from lucky.** Dual momentum on NVDA shows −61% / −51% drawdowns once
   reshuffled; the RSI reverter keeps a "solid verdict".
5. **Cross-sectional momentum rescues momentum.** Ranking a basket and going long the strongest / short the
   weakest "scored way better" than single-asset momentum's ~0.
6. **The build framework** (the part being sold): base signal → risk management and sizing → uncorrelated
   signals → **regimes via a hidden Markov model**, running momentum in trending regimes and mean reversion in
   chop.

## The arithmetic they don't do

**Their own headline filter produces exactly the noise count.** A Sharpe estimated over T years has standard
error ≈ 1/√T. A 1/3 out-of-sample split of 15 years is ≈5 years, SE ≈ 0.45. Under a pure-noise null, the share
of strategies clearing Sharpe > 0.5 is 1 − Φ(0.5·√5) = **13.2%**. They observed 1,218/9,000 = **13.5%**. The
"almost 8,000 strategies wiped out" that the video sells as rigour is, to within a rounding error, what you get
from feeding 9,000 coin flips into that filter. They never state the null pass rate, so this comparison — the
single most important number in the video — is absent.

**Their best result sits inside the noise envelope.** If the "score 1.18" on Turtle/Apple is an out-of-sample
Sharpe (it is never defined, and it is quoted immediately after a Sharpe > 0.5 filter), then at SE 0.45:

| effective independent tests | expected max Sharpe from pure noise |
|---|---|
| 9,000 (their nominal count) | **≈ 1.65** |
| 500 (30 correlated assets × families of neighbouring parameters) | ≈ 1.29 |
| 100 | ≈ 1.04 |

The best of 9,000 draws is ~3.7 SD above zero by construction. **Their top finding, 1.18, is below what noise
delivers unless the effective number of independent tests is under ~200** — and with 30 assets that co-move
(SPY/QQQ/XLK are ~0.9 correlated) and parameter grids whose neighbours are near-identical strategies, the
effective count is far *below* 9,000, but there is no reason to think it's below 200. This is the one piece of
arithmetic that would have settled the video, and it is the one they skip.

**The 44% number is ambiguous in a way that matters.** If "stayed strong" means positive out-of-sample, the
coin-flip rate is 50% and **44% is below the null**. If it means clearing a bar, we can't evaluate it without
the bar. Either reading is reported as evidence of rigour; on the first reading it is evidence there was
nothing there.

## Against our rules

**1. The out-of-sample was used for selection, so it isn't out-of-sample.** Every filter in the funnel is
applied to walk-forward OOS results, then the survivors' OOS performance is reported as the finding. There is
no third untouched slice. This is precisely the house rule "**out-of-sample must be SEALED, not peeked**" —
and their *own next video* got it right with a locked 2-year holdout run once. Here nothing is locked. The 524
are the 524 that looked best on the only fresh data in the experiment.

**2. Multiple-testing correction is claimed and never shown.** At [17:36] the layer-3 prompt is described as
adding "multiple test corrections". No correction appears as a step in the funnel, no corrected survivor count
is given, no p-value, no deflated Sharpe, no BH-FDR. Contrast the ICT video, where the luck correction was an
explicit funnel row (1,614 of 2,191). We ran our own ledger-wide correction on 2026-09-22 (BH-FDR 5/10% + Holm
+ |t| ≥ 3 over M = 125 questions, best-of-k charged with Šidák) and it moved 11 of our own acted-on claims to
NOT CERTIFIED — including the straddle/bull-put pair. A video whose premise is 9,000 tests and whose output is
a survivor list is the exact case that correction exists for.

**3. No costs, quantified.** "Realistic transaction costs" is named as a prompt feature; no spread assumption,
no slippage, no fill model, no borrow for the short legs of the cross-sectional momentum book appears anywhere.
Our own hardest-won rule is **price at real fills, not mid** — a mid-priced cost sweep on 2026-09-22 killed
nine strategies here outright (UVIX went +11%/93% win at mid → −8.8%/46% at real fills). Daily-bar ETF
strategies are more forgiving than 1-min futures, but RSI/Keltner reversion is high-turnover by construction
and buys into the widest spreads of the month. An unquantified cost model on a high-turnover family is not a
cost model.

**4. The bootstrap is misapplied.** Reshuffling the *order* of a fixed set of trades cannot change the total
or mean return — only path statistics like max drawdown. So "if we reshuffle this 500 times it still would have
produced a winning trade" is a tautology for the return, and the honest content of the exercise is the NVDA
drawdown finding, which is real and useful. What a bootstrap *could* have done — resample with replacement to
get a distribution of the mean, or block-bootstrap to respect serial correlation — is not what is described. It
also addresses sequence luck, not selection luck, which is the failure mode this experiment actually has.

**5. No benchmark.** Not once in 20 minutes is buy-and-hold mentioned. Over 2010–2025, SPY's own Sharpe is
roughly 0.8–0.9 — comfortably above the 0.5 bar that defined a "survivor". A long-biased daily mean-reversion
rule on SPY and sector ETFs in the best 15-year equity run on record with famous V-shaped recoveries (2011,
2015, 2018, 2020, 2022, 2023) is **long beta with a duty cycle**. He concedes the returns are "pretty modest"
and never says modest *relative to what*. Without that line, "mean reversion survives" cannot be distinguished
from "the market went up and dip-buying participated".

**6. Share of survivors is the wrong statistic.** "64% of survivors are mean reversion" is a function of how
many mean-reversion configs went *into* the 9,000. The dashboard tile is labelled "survival rate by category"
[02:08] and the rate is the right number — but the narration reports the share, and no base rate per family is
ever spoken.

**7. "Trend works on Apple and Nvidia" is hindsight, and they know better.** AAPL and NVDA are the two best
large-cap performers of the sample window, hand-placed in the asset list in 2026. Any long-biased trend rule on
a stock that 30×'d will score. The prescription — apply trend to "specific strong trending names" — requires
knowing in advance which names will trend, which is **the identical error their ICT video correctly demolished**
("a look-ahead perfect bias would win, i.e. the bias is only useful if you can forecast the day"). Two months
earlier, they fell for it.

**8. The tested half is negative; the sold half is untested.** Everything with a number behind it (mean
reversion modest, trend negative, momentum ~0, overfitting kills most) is deflationary. Everything actionable —
layering, uncorrelated signal stacking, HMM regime switching, cross-sectional momentum — arrives *after* the
data section with no test attached, and is what the Skool community teaches. That is the shape of a lead magnet:
the rigour establishes credibility, the product occupies the untested space.

## Against our evidence, claim by claim

| their claim | our evidence | verdict |
|---|---|---|
| Mean reversion is the only family with a standalone edge | ⭐ **Half-agrees, and the half it agrees with is our only certified bucket.** Our single BH-FDR-surviving positive family is index mean reversion expressed in options: bearish-high-IV SPY bull put **t 6.07**, SPX condor **t 5.21**, SPY 1-day short straddle on positive-gamma days **t 5.6**, 10d VRP **+1.75vp t 8.93, 17/17 years**. Selling into index stress *is* buying the dip with a premium cushion | **SUPPORTED at the index level** — by a mechanism he never mentions |
| …and it works across 20 single names | **CONTRADICTED on single names.** Our reversion section is 0-for-5: capitulation scorecard FAIL both sides; counter-trend long FAIL (every arm −0.15…−0.33R); bouncy-ball short FAIL daily *and* intraday; "boring stock violent move" INVERTED; pullback-short arrival signal −1.5%/10d. Crash-leader: buying deep selloffs is a **regime bet, not selection**, with a standing veto against it in a healthy tape | **CONTRADICTED** where we have data |
| Trend / MA crossovers don't broadly work; "one line crossing another shouldn't predict anything" | **AGREES.** `sma_stacked` fails to sort on 43,970 house breakouts (unstacked +0.022 vs stacked +0.009 = noise). Trend smoothness (share of closes above the 21 EMA, EMA slopes) is **NULL** against 20/60d forward returns, universe and leaders. Our own trend book (precision-tier breakout) is **WEAK** post-correction: t 3.3, k 10, month-weighted −0.04R | **AGREES** |
| Momentum ≈ 0 single-asset; cross-sectional momentum is much better | **Directionally consistent, untested here.** Our universe test found **the universe carries the return, not the trigger** (HYB-B +1.79 t 2.6, parked) — i.e. cross-sectional selection is where such edge as exists lives. But he gives no numbers, no costs, no short borrow, and 30 co-moving assets is a thin cross-section | **PLAUSIBLE, unevidenced** |
| Regime switching: HMM labels → momentum in trend, mean reversion in chop | ⛔ **The single most-falsified idea in our ledger.** Trailing-30d regime rules FAIL 2019–26 (weak breadth is a mild *buy*); O'Neil Follow-Through Day as a regime switch **NULL** (IWM negative in 10 of 12 cells); breakout regime feedback — **the paying months cannot be forecast** (47% positive, top decile = 68% of R); Breitstein high-vol regime gate **FAIL, no switch**; Stage A regime-conditioned alerts **NULL**. The one regime signal that passes is dealer gamma → **realised volatility** (+8.1% beyond VIX, t 7.7) — a volatility input with **no direction**, i.e. not a strategy switch | **CONTRADICTED, 5 independent times** |
| Overfitting kills more than half of good-looking backtests | **AGREES emphatically**, and our numbers are harsher: the pattern ledger went **0 for 19** once controls were honest, and the honest control itself was worth +0.14…+0.21R of the original "edge" | **AGREES** |
| Single-backtest platforms are misleading | Agrees, and correctly stated. The best 90 seconds of the video is the in-sample/out-of-sample scatter explanation at [04:38] | **AGREES** |
| Diversify across uncorrelated signals | Our own book is one line of this: the straddle + bull-put **pair** (corr −0.25) clears t 2.5 where neither leg clears alone. But it did **not** survive the ledger correction (NOT CERTIFIED), and "many spreads = diversification" was contradicted for SMB (3,377 bull puts = 53 independent dates) | **HALF-TRUE, and the half that's true is weaker than it sounds** |

## Funnel and disclosure

Paid Skool community, pitched twice, described as "the largest AI-focused trading community". No testimonials,
which is to his credit — but also **no disclosed strategy**. Not one parameter value, CAGR, Sharpe, trade count
or equity curve for any of the 524 survivors is given. The video is not reproducible from its own content; the
four prompt screenshots are the deliverable and the community is where the rest lives. Compare the ICT video,
which at least put dollar P&L and a funnel with counts on screen. **Disclosure went backwards between these two
videos even as method went forwards.**

## Score: 2/5

**Method: ~2.5.** The framework described — walk-forward, in-sample/out-of-sample scatter, degradation filter,
minimum trades, per-family aggregation, a history-length correction (XLC excluded, a real and unprompted piece
of care) — is above the retail norm, and the overfitting pedagogy at [04:38]–[05:47] is genuinely good and
correctly stated. But the funnel as shown has no null, no correction, no sealed slice, no benchmark and no cost
number, its headline filter reproduces the pure-noise pass rate to within 0.3pp, and its bootstrap is applied to
the statistic it cannot move.

**Strategy claim: ~1.5.** Unfalsifiable as delivered — no parameters, no returns, no benchmark. The one broad
finding (mean reversion) is right at the index level for reasons he never gives and wrong on single names
against five of our own tests; the trend finding is hindsight on the period's two best stocks; the actionable
recommendation (HMM regime switching) is the idea our ledger has killed five separate ways.

**The split from the previous review does not hold: their method is the weaker half here, not the stronger.**
The ICT video is the same rig two months later with a null, a luck correction and a lockbox bolted on — and
even that one's positive result died in our replication (−0.109R paper, −0.205R queue-aware, negative in all 20
years). Risk to a retail follower: **4/10** — nothing here is directly tradeable, so the damage is mostly
misplaced confidence in a validation stack that omits the correction its own premise demands.

## Testable here? — one candidate, low priority

**Not worth queueing (3 of 4):**
- *HMM regime switching.* Five independent failures already on file. Do not spend a sixth.
- *"Trend works on strong trending names."* Requires forward knowledge of which names trend; it is the perfect-bias
  error and not a testable rule.
- *Cross-sectional momentum on 30 assets.* Subsumed by our universe test (the universe carries the return); a
  30-asset cross-section is too thin to add anything, and the short leg needs a borrow model we don't have.

**Worth queueing (1):**

> **H — Daily RSI/Keltner mean reversion on liquid ETFs, benchmarked and costed.** His only falsifiable claim is
> that a bare daily reversion rule on ETFs has a standalone edge. The test that settles it is not "is it
> positive" but **"does it beat buy-and-hold on the same asset over the same window, after real fills"**.
>
> *Design:* liquid ETF panel 2010–2026 (SPY, QQQ, IWM, the sector XLs, GLD, TLT, USO), `lib.studies.pattern_test`
> harness. Entry = close on RSI(2) or RSI(14) below a pre-registered threshold; exit = close above the N-day
> mean or a fixed horizon. **Three arms, all pre-registered before the pull:** (A) the rule; (B) buy-and-hold the
> same asset, same total days-in-market scaled; (C) `post` — a random later entry in the same asset, which prices
> the timing rather than the beta. Costs from the house cost model (commission + 25% of bid/ask), never mid.
> Parameter grid ≤ 8 cells, Šidák-charged.
>
> *Bar (house):* beats **both** controls, both halves positive, |t| ≥ 3 after the best-of-k charge, and a
> positive **exposure-adjusted** return vs arm B — otherwise it is long beta wearing a signal.
>
> *Prior: 25% it clears B, ~10% it clears C.* We already know two things that bracket it: index mean reversion
> pays in **options** (bearish-high-IV bull put, t 6.07 — the premium, not the bounce, is the payment), and the
> equity-leg version on single names is 0-for-5. The most likely outcome is that the ETF equity version is
> positive but below buy-and-hold, which would be a clean **NULL with a MECHANISM yield**: the reversion is real
> and the way to get paid for it is the short-premium structure we already trade, not the underlying. ~30 lines
> on the existing harness; do it only after the current queue clears.

Related: [[project_ai_pathways_kb]], [[project_crash_leader_study]], [[project_tierab_significance]],
[[project_breakout_regime_feedback]], [[project_ftd_study]], [[feedback_price_at_real_fills]],
[[reference_test_index]].
