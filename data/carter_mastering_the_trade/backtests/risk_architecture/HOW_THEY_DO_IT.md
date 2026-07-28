# How Luk / Minervini / Qullamaggie get returns the backtests can't reach

**Date:** 2026-07-26 · inputs: `run_luk_alpha.py`, `lift_trades.parquet`, `REGIME.md`

## The size of the gap

Best simulated result in this entire study: **11.3% CAGR, MAR 0.52** (and that's best-of-320,
in-sample). Luk posted **+969% in a year**; Qullamaggie compounded a small account at roughly
triple digits for years. That is one to two **orders of magnitude**, not a margin.

A gap that size cannot come from a better entry signal. A signal improvement moves you from 11%
to 15%, not to 300%. So the question is which *mechanism* multiplies by 10x, and there turn out
to be only a few candidates that even could.

---

## 1. The sizing lever — and the number that explains everything

For a fixed fractional risk budget, **position size = risk% ÷ stop%**, so account return per
trade scales with **1 / stop_width**. Luk risks 0.3% with a 1–2.5% stop → a **20–30% position.**
Every simulation here used an ATR-scaled stop averaging 9.2% → a **3.3% position.**

Same risk per trade. **Six times the account impact per unit of price move.**

The catch is whether a tighter stop gets hit proportionally more often. Measured on the GATES
entry, 299-name panel, next-open entry (i.e. **no intraday precision**):

| stop | width | stop-out rate | mean %/trade | position | **account bp/trade** |
|---|---:|---:|---:|---:|---:|
| 1.0% | 1.0% | **94%** | +0.38 | 30.0% | +11.4 |
| 1.5% | 1.5% | **91%** | +0.52 | 20.0% | +10.3 |
| 3.0% | 3.0% | 81% | +1.42 | 10.0% | +14.2 |
| 1.0 ATR | 4.6% | 72% | +2.27 | 6.5% | +14.6 |
| 2.0 ATR | 9.2% | **39%** | +2.92 | 3.3% | +9.5 |
| 20d low | 17.0% | 5% | +2.53 | 1.8% | +4.5 |

**Account bp per trade is roughly FLAT across stop widths** (9–15 bp). The sizing lever almost
exactly cancels the higher stop-out rate. ⚠ This revises the "tight stops are ruinous" conclusion
in [RESULTS.md](RESULTS.md): on a *good* entry the arithmetic per-trade result is flat, not
ruinous. Tight stops lost there on the *portfolio* path — 94% stop-out at 30% positions produces
long loss strings, only ~3 concurrent positions, and brutal geometric drag — not on expectancy.

Now the decisive observation. **The only thing suppressing the tight-stop cells is the stop-out
rate: 91% at 1.5% versus 39% at 9.2%.** That rate is a property of *where you entered*, not of
the stop. Entering at the next day's open puts the stop at an arbitrary 1.5% below an arbitrary
price. Entering just above a pivot with the day's low 1.5% underneath puts it at a level the
market must actually violate.

**If intraday precision brought the 1.5% stop-out rate down to the 2.0 ATR cell's ~39%, that cell
would earn 20% × 2.92% ≈ 58 bp/trade instead of 9.5 — roughly 6×.** That is the only lever in
this entire study with a 6× on it, and 6× on an 11% CAGR is in the right territory for the gap.

> **The thesis, stated falsifiably:** their edge is not the signal and not the stop. It is that
> intraday entry location decouples stop *tightness* from stop *fragility*, which unlocks a 6×
> position for the same risk. Everything else — the screen, the trend template, the ADR gate — is
> the qualifying filter that makes a name worth applying that machinery to.

**This is exactly what daily bars cannot test**, and it is the boundary flagged at the start of
the architecture work. It has turned out to be the whole thing.

## 2. Discretionary selection alpha — measured, real-sized, not yet significant

`run_luk_alpha.py`: 386 observed trades from 64 livestreams, 273 usable, Nov 2025 – Jul 2026,
scored against the same-day universe from the Minervini cache. Median 500+ names passed the
screen on his trade days; he took a handful.

Excess return vs the **screen-matched** pool (the number that isolates the *choice*):

| horizon | his % | screen % | **excess** | t | beat screen % |
|---|---:|---:|---:|---:|---:|
| 1d | +1.02 | +0.08 | +0.94 | 1.62 | 51.4 |
| 5d | +1.41 | +0.51 | +0.89 | 0.70 | 51.1 |
| 10d | +2.65 | +0.71 | +1.94 | 1.14 | 50.0 |
| 20d | +6.91 | +2.08 | **+4.84** | 1.84 | 49.6 |

Two things matter here:

1. **The point estimates are large** — he roughly triples the screen's 20-day return.
2. **"Beat screen %" sits at 50%.** His median pick is a coin flip against the screen. The excess
   is *entirely* in the tail — same structure as the mechanical gates (flat win rate, doubled
   p99), but stronger. He is not more often right; he is bigger when right.

⚠ **Not statistically established.** t = 0.7–1.8 over 9 months, n = 130–180. Consistent with real
alpha of a few percent per swing; nowhere near proof. The cleanest subset (stated + long, n=172)
is weaker still: +2.32% at 20d, t=0.80.

## 3. My entire test suite is long-only. He isn't.

**71 of 273 observed trades (26%) are shorts** — and the short book showed the largest excess
(+19.1% at 20d, t=2.13, beat screen 71%), though at n=17 that is uninterpretable. The point
stands structurally regardless of that number: when the regime filter puts the simulated
long-only book in cash, he is trading the other side. That is a whole source of return the
simulations are blind to by construction.

(Note this is Luk-specific — Minervini and Qullamaggie are essentially long-only.)

## 4. Structural exclusions in my own filters

- **Young stocks are excluded outright.** Stage 2 needs SMA200 and the sim drops names with
  <400 bars. Recent IPOs are a staple of Qullamaggie's biggest winners, and they cannot appear
  in any result here.
- **The universe is too slow.** The ADR gate is ≥3.5%; their bread and butter is 6–15% ADR
  small/mid caps. The panel is skewed to names that qualify at the bottom of that range.
- **Sell-into-strength is untested** — his most-repeated exit rule; every exit tested is a
  weakness-based trail or a fixed target.
- **No theme/sector concentration.** His stated selection priority is hottest theme first; the
  sim treats every qualifying name as interchangeable.

## 5. What is honestly attributable to reporting

Minervini's headline figures (155% in 1997, 334.8% in 2021) are **contest years**, which reward
maximum risk-taking and are not a compounded track record. Qullamaggie's compounding ran from a
small base through 2011–2021, an exceptionally favourable momentum decade, and he says himself
that the edge shrinks with size. This does not make them lucky — but the number to beat is a
sustained CAGR, and the widely-quoted figures are peak years.

---

---

# ⚠ CORRECTIONS — 2026-07-26, after ingesting the Breitstein channel

Twenty-one videos from Lance Breitstein were transcribed into `data/lance_breitstein/`. Four
findings revise this document. Two of them cut against its central thesis.

## C1. ⚠ The 6× sizing lever is an INTRADAY phenomenon. §1 over-generalized it.

This document argued the gap is tight stops → large positions. Breitstein, who ran both styles,
says the opposite for the swing horizon — and names it as his own costliest early mistake:

> "One of the biggest mistakes I made early when transitioning into swing trading is that my
> entries and exits were still too intraday focused… a beautiful weekly breakout setup with a
> **logical stop 8% lower**… Old Intraday Lance would stop himself out because the stock dipped a
> percent and a half intraday. **If you're trading based on the daily chart, your risk management
> needs to align with the daily chart.** … **If your stop is three times wider, your size probably
> needs to be three times smaller.**" (`k-X0164r66U` @06:50)

**Every simulation in this repo is a swing simulation** (median hold 16–22 days). So
`RESULTS.md`'s conclusion — tight stops catastrophic, wide ATR stops best — is *correct for the
timeframe actually tested*, and is independently corroborated by a practitioner. The error was
importing Luk's intraday-precision entry into a swing context and concluding the lever applies
there. **It does not.** The lever is real but lives at Breitstein's old intraday horizon, where
stops are "$0.50 or $1 away" and there is no overnight gap between entry and invalidation.

Luk is the genuine anomaly here — intraday-precise entries on multi-day holds — and he and
Breitstein flatly disagree about whether that is wise.

## C2. Re-entry hypothesis — TESTED AND REFUTED

The natural reconciliation was that a tight stop is a cheap *probe*: you pay several small stops
to be positioned for one large win, and it only works if you go back in. Luk's trade log contains
explicit `action: reentry` rows. Every backtest here used `COOLDOWN = 10` days, which forbids that.

`run_reentry.py` re-ran the broad panel (regime-gated, GATES/BREAKOUT) at cooldown 10 / 3 / 0.
Portfolio CAGR, 50 slots, GATES:

| stop | cd=10 | cd=3 | cd=0 |
|---|---:|---:|---:|
| 1.5% | −9.00 | −8.28 | **−14.48** |
| bar low | −1.42 | −0.93 | −4.66 |
| 3.0% | −2.18 | −2.08 | −12.30 |
| 2.0 ATR | **+4.71** | +2.89 | +2.49 |

Re-entries genuinely occurred (24% more trades taken; signal pool up ~2.5×) and stop-out rates
barely moved (94.4% → 94.6% at 1.5%). **Allowing re-entry makes things worse, and worst for the
tight stops.** The probe thesis does not survive on daily bars. One candidate explanation
eliminated.

## C3. "Naturally tight setups are better setups" — tested, not confirmed, but not refuted

Breitstein states the mechanism this document could only hypothesize:

> "If that low of the bar was really tight up against resistance, we end up with a far tighter
> stop than if the bar had been much looser. **That often is what gives a setup far better
> expected value.**" (`WgRQWJq54OY` @06:12)

Tested by quintiling trades on *natural* stop width (stop = breakout bar low). Account bp/trade,
Q1 tightest − Q5 loosest: DUMB −0.9 (t=−0.26), GATES +2.8 (t=+0.30), BREAKOUT +4.1 (t=+0.40).
Directionally right for the screened tiers, non-monotonic, insignificant.

⚠ **Probably a measurement failure rather than a refutation.** The tightest quintile stops out
88–90% with a 1–2 day median hold — the overnight-gap signature. Entry here is the *next* day's
open with the stop at the *prior* bar's low, so gap noise fires it before the setup can work. Both
Breitstein and Qullamaggie enter **intraday on the breakout day**, so the stop goes live only once
that day's low exists. The claim remains untestable without minute bars.

## C4. The two traders contradict each other on sizing, not just stops

- **Breitstein:** exponential. A-grade trades (1–2/month) get ~$100k of risk; B-grade get ~$10k —
  **10×**. Premised on "80% of profits come from 5% of trades."
- **Luk:** near-constant ~0.3%, and explicitly "**never half- or double-size on conviction alone.**"

Both are successful. The plausible split is overnight gap risk: Breitstein's sized-up bets were
intraday and flat by the close; Luk carries positions where a 10×-sized name can gap through the
stop. **Either way, every simulation here sizes flat, so it captures none of the concentration
effect** — another multiplier the harness structurally cannot see, and a candidate for the
residual gap alongside intraday precision.

## C5. He says the swing edge is genuinely thinner

> "There is generally **less absolute edge in swing trading** compared to intraday trading.
> Intraday still has more inefficiencies because emotions, liquidity imbalances and panic happen so
> quickly… Swing trading, at the expense of scalability, is often more efficient. As a result your
> edge can feel thinner and variance much higher."

Taken seriously, this partly explains why every swing backtest here lands near or below SPY — not
because the implementation is wrong, but because the swing horizon is where the edge is smallest
and the capacity is largest. That is the trade both he and Qullamaggie describe making
deliberately.

## Net effect on the thesis

The §1 claim survives in narrowed form: **intraday entry precision unlocks a large sizing lever,
but only for intraday holds.** It does not explain swing returns, and the swing results in this
repo need no apology — they agree with what a practitioner of both styles says about swing.

What remains unexplained for swing: discretionary selection (§2, measured at +4.84% per 20d on
Luk, t=1.84), concentration/sizing (C4), the short book (§3), and the excluded young-stock
universe (§4). None of those is a 6×; together they may be enough.

---

## What to do about it, in priority order

1. **Buy minute bars and test the linchpin.** The claim in §1 is precise and falsifiable: *does
   entering at a structural intraday level cut the 1.5% stop-out rate from ~91% toward ~40%?*
   Nothing else in the study has a 6× attached to it. A few hundred names × 2–3 years of 1-minute
   data is enough. **This now outranks the survivorship fix** — survivorship refines a
   measurement; this tests the mechanism.
2. **Add the short book.** One-line change in principle, and it addresses 26% of his activity
   plus the periods the regime filter currently sits out.
3. **Drop the SMA200 / 400-bar requirement** and add a young-stock path (e.g. IPO base
   breakouts). Cheap, and it stops excluding the trades that make their year.
4. **Test sell-into-strength exits** against the trailing exits already measured.
5. **Extend the Luk trade log.** n=273 over 9 months gives t≈1.8. Another year roughly doubles
   the sample and would move the selection-alpha estimate toward or away from significance.
   The extraction pipeline already exists.
