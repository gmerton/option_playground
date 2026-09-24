# Intraday reversion to the largest-GEX strike, SPY [WL-5b] — 2026-09-23

**Verdict: NULL.** After price overshoots the largest-|GEX| strike, it drifts back to it no more than it drifts back
to a strike the same distance away on the other side of the open. That's true on all days, on positive-gamma days
(where a magnet should be strongest) and on negative-gamma days. This is the intraday complement to the daily pin
NULL (+0.6 bps, t 0.3). The "gamma strike as magnet" half of GEX is now null at both horizons. The half that passed,
negative gamma → more realised vol, is untouched. Per the spec the option leg was not tested: the underlying failed,
and there are no intraday SPY option quotes.

Script: `run_gex_strike_revert.py` (pre-registration in the docstring, from the Option Alpha review).
Log: `data/studies/logs/gex_strike_revert.log`. Events: `logs/gex_strike_revert_events.csv`. Local, ~minutes.
3,690 SPY sessions, 2010-01 → 2026-02 (the GEX strike cache's span).

## Spec

- **Per-strike GEX:** (cg − pg)·100·S²·0.01 from the prior day's chain, identical to `run_gex_regime_pin.py`.
- **K\*:** the largest-|GEX| strike within ±1% of the open.
- **Mirror:** the listed strike nearest 2·open − K\* (distance-matched).
- **Event:** the first 1-min close in 09:45–14:30 on the far side of the level from the open, ≥ 0.15 × ATR14 beyond it.
- **Outcome:** signed return toward the level at +30 / +60 min, and a touch within 60 min.

## Results

| level | events | toward +30 (bps) | toward +60 (bps) | touch ≤ 60 min |
|---|---|---|---|---|
| **K\*** | 1,055 | +0.46 (t 0.56) | −0.90 (t −0.76) | 42.7% |
| **mirror** | 1,024 | +1.18 (t 1.01) | +1.09 (t 0.85) | 41.6% |
| random minute (toward K\*, no event) | 3,680 | −0.29 | −0.75 | 18.0% |

- **PRIMARY (K\* − mirror, +60 min):** **−1.99 bps, Welch t −1.14**, halves −2.10 / −1.93 (split 2018).
- **+30 min:** −0.72 (t −0.50). **Touch-60 difference:** +1.1pp (t +0.49).
- **Positive-GEX days:** K\* −1.55 vs mirror +1.46 → −3.01 (t −1.64). Touch 37.7% vs 42.0%: *less* likely to come back
  when dealers are long gamma, the opposite of the magnet story.
- **Negative-GEX days:** −1.30 (t −0.50).
- **Per year:** no run of the diff's sign (2023 +12.6, 2025 −14.9, 2020 −11.3; the rest small).

## Reading

The ~42% touch rate within an hour is the same for the gamma strike and for its mirror. It's what any level just
overshot by 0.15 ATR does, not a property of dealer positioning. Option Alpha's main trade (fade the move back to the
big-gamma strike) and the GEX-levels creators' "magnet" framing get no support from 16 years of SPY minute data.
