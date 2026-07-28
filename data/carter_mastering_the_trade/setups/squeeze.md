# The Squeeze (TTM Squeeze)

> **Verdict:** The volatility-compression *observation* is real and survives 20 years — the trade
> built on it does not, in any of the three forms tested. Direction rule: negative excess return in
> all four eras. "Longer squeeze = bigger move": contradicted monotonically. Expansion: real, but
> belongs to the compression *state*, not the fire — and **fully priced**, with RV/IV
> indistinguishable from baseline (t=0.10), so there is no long-premium edge either. Three
> independent avenues, all closed.
> **Type:** swing (tested) / intraday (as presented) · **Instrument:** equities, indices, futures
> **Conviction:** 1/5 · **Risk:** 4/10 · **Tested?** **yes** — see
> [backtests/squeeze/RESULTS.md](../backtests/squeeze/RESULTS.md)
> **Source:** Carter's signature indicator, 3rd ed. (2019); later productized as the TTM Squeeze.

---

## 1. Mechanics

- **Universe / instrument:** any liquid instrument; Carter emphasizes index futures intraday.
- **Timeframe:** any; tested here on daily bars as a swing setup.
- **Setup condition:** Bollinger Bands contract *inside* the Keltner Channels = "squeeze is on"
  (volatility compression).
  - BB = SMA(close,20) ± 2.0 · stdev(close,20)
  - KC = SMA(close,20) ± 1.5 · SMA(TrueRange,20)
  - ON when `BB_upper < KC_upper AND BB_lower > KC_lower`
- **Trigger:** the squeeze "fires" — BB expand back outside the KC (ON at t−1, OFF at t).
- **Direction:** given by the momentum histogram — 20-bar linear-regression endpoint of
  `close − (donchian_mid(20) + SMA20)/2`. Positive → long, negative → short.
- **Entry:** on the fire, in the momentum direction.
- **Exit:** when the momentum histogram rolls over (commonly two bars against).
- **Stated amplifier:** the longer the squeeze has been on, the bigger the expected move.

## 2. Claimed edge & returns

No separable track record is attached to the indicator itself — it is presented as a mechanism
(compression precedes expansion) plus a directional read, illustrated with charts. That is the
core problem: there is no stated win rate or return to falsify, so the claim has to be
reconstructed and tested from the mechanics, which is what was done.

## 3. Market-structure dependencies ⚠

Baseline 2019. **This turned out to be the wrong lens.** The setup does not show decay — it shows
uniform absence of directional edge across 2006–2011, 2012–2018, 2019–2021 and 2022–2026. There
is no era in which the direction rule worked, so there is nothing for 0DTE or the 2020 vol shift
to have broken.

The one effect that *is* real (relative vol expansion) is **strongest in 2022–2026**, the 0DTE era —
the opposite of decay.

- **Hard-coded thresholds:** BB 2.0σ / KC 1.5·ATR / length 20. Sensitivity tested: KC multiplier
  1.0 / 1.5 / 2.0 / 2.5 moves the squeeze-ON rate from 2.4% to 68% of bars but leaves the edge
  negative-to-zero throughout (best −0.013% at kc=2.0). **The result is not a calibration artifact.**
- **Decay risk verdict:** n/a — no edge to decay.

## 4. Objective assessment

- **The direction rule is the weak joint.** The momentum histogram is a lagging linear-regression
  transform of price; as a cross-sectional predictor it is mildly *anti*-predictive (`mom<0` beat
  `mom>0` at every horizon). The compression observation and the direction rule are two different
  claims bolted together, and only the first has support.
- **The stated amplifier is backwards.** Longer squeezes are followed by *smaller* moves,
  monotonically across four duration buckets (ratio 1.003 → 0.906, t=−4.2 at 20+ bars).
- **The trigger adds nothing over the state.** Bars still inside the squeeze predict expansion more
  strongly (t=+67) than fired bars (t=+12). If the mechanism were "release unleashes the move,"
  the fire should dominate. It doesn't.
- **What the effect really is:** volatility mean-reversion. Low realized vol is followed by higher
  realized vol. That is a well-documented property of volatility, not something the indicator
  discovers. The Squeeze is a serviceable low-vol detector wearing a trigger it doesn't need.
- **Absolute vs relative confusion is the trap.** Post-fire names expand *relative to themselves*
  but remain **below-average-volatility names in absolute terms** (0.98× universe vol). A trader
  reading "big move coming" will size for a big move in a stock that is, in absolute terms, quiet.
- **Unfalsifiable as presented:** no track record, chart illustrations, and discretionary market
  context. The mechanical core is testable and was tested; the discretion around it is not.

## 5. What's genuinely sound

- **Compression precedes expansion is true and durable** — 20 years, every era, strengthening
  recently. The mechanism is not fake, only the trade built on it.
- **BB-inside-KC is a clean, cheap, non-repainting compression detector.** As a *state variable* —
  "is this name coiled?" — it is fine, and cheaper than most alternatives.
- **It is honest about being a volatility tool.** Carter's own framing is that the squeeze tells
  you a move is coming, not which way. The data supports exactly that framing and rejects the
  momentum-histogram patch applied on top of it.

## 6. Testability

- **Class:** EOD-testable — **done.** 5,302-name cross-section (14 mo) + 299-name × 20-year
  era split + direction-free vol tests.
- **Skeleton tested:** mechanical fire + momentum sign, excess return vs same-universe baseline,
  date-level t-stats, KC-multiplier sensitivity, duration buckets, forward |return| / realized vol
  / expansion ratio.
- **Realized vs implied — tested, and it fails too.** 9,143 fires with ATM 30d IV
  (Athena `options_daily_v3`, 2010–2026). Options on coiled names are genuinely cheaper
  (IV −0.91 vol pts, t=−3.6) but realized vol comes in even lower (−1.03), so **RV/IV is 0.980 vs
  0.982 baseline, t=0.10** — the compression is fully priced. Bars inside the squeeze are
  significantly *expensive* (VRP −0.59 vs baseline, t=−2.64). No long-premium edge.
- **What the skeleton can't capture:** intraday application, discretionary market context, use as
  a filter on top of another setup, earnings contamination inside the 30-day window, and actual
  straddle P&L (path/gamma/spreads — which would be *worse* than the RV-vs-IV comparison).

## 7. Overlap / conflicts with the existing book

- **Duplicates existing machinery.** `src/lib/commons/vol_compression.py` already screens
  compression, and the breakout pipeline's VCP/tightness layer covers the same ground with a
  volume-dry-up condition the Squeeze lacks. The Squeeze adds no information the current stack
  doesn't have.
- **Consistent with the house finding on arrival signals.** Same shape as the pullback-short
  result: *arrival at a state is not the trade*. There, the rejection was hypothesized to carry
  the edge; here, the compression state carries what little there is and the release does not.
- **Consistent with precision-over-recall.** A signal that fires on 17–22% of all bars and
  produces ~30k events over 20 years with negative excess return is a recall machine. It belongs
  nowhere near an entry trigger.
- **The cheap-premium hypothesis is now closed.** The obvious remaining use — buy the coil in a
  leader via options rather than shares — was the reason to keep the setup alive after Results 1–3.
  Result 4 kills it: the compression discount is fully in the IV. What's left is only the
  *unconditional* observation that low vol mean-reverts, which you can read off realized vol
  directly without the indicator.
