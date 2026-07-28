# Double-Calendar Skeleton vs. User's SPY dcal — Backtest Results

**Run 2026-06-25.** Mechanical EOD backtest on `data/cache/SPY_options.parquet` (SPY, 7.9M rows,
2018-01-02 → 2026-02-20). Engine: `src/lib/studies/double_calendar_study.py` (the same engine that
backs `run_spy_double_calendar.py`). Script: `run_backtest.py`. Entry = Friday for **all** configs so
the only thing varying is *structure*. Marks at **mid**, plus an after-cost view:
**cost = $0.052/share commission (8 legs) + 25% of each leg's quoted bid-ask, paid on entry *and* exit.**

> **What is NOT tested:** Bernich's *intraday transform* of a winning double calendar into an
> all-front-month "risk-free" credit iron condor. It is triggered by a 1-minute IV tool and is
> **unreplayable on daily data**. This backtest is therefore the **floor** — the double-calendar
> skeleton *without* the transform — i.e. exactly the part both Bernich (pre-transform) and Ravish
> (no transform at all) actually hold. Ravish's discretionary VIX-timing is likewise not modeled.

## The three structural differences tested (vs. the user's SPY dcal)

| axis | User SPY dcal | Theta-Profits skeleton |
|---|---|---|
| gap short→long | **+7 days** (Fri/Fri) | **+3 days** (Fri-short / Mon-long) — Bernich & Ravish |
| short strikes | 0.25Δ (0.25P/0.10C in BHI) | Bernich **~0.35–0.40Δ** (closer in); Ravish ≈ expected-move |
| profit target | 50% (BuLO) / hold (BHI) | Ravish **15–30%**; out before expiry |

## Headline — capital-weighted ROC per trade (sum PnL / sum debit), AFTER costs

Capital-weighted (not mean-of-ratios) because the tight-gap debit is tiny (~$0.80) and per-trade ROC%
is outlier-unstable. `sumPnL` is per-share dollars summed over all trades (robust).

**Full sample 2018–2026:**

| config | gap | Δ | PT | n | win% | rocCW **mid** | rocCW **net** | sumPnL net |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **USER BuLO** (0.25/0.25, 50%PT) | 7 | .25 | 50% | 385 | 49 | +6.87 | **+2.05** | **+17.3** |
| **USER sym** (0.25/0.25, hold) | 7 | .25 | hold | 385 | 48 | +7.03 | **+2.22** | **+18.7** |
| **USER BHI** (0.25P/0.10C, hold) | 7 | .25/.10 | hold | 374 | 45 | +7.56 | **+1.93** | **+12.4** |
| TP-Ravish (0.25/0.25, **g3**, 25%PT) | 3 | .25 | 25% | 387 | 55 | +8.37 | **−5.07** | **−14.6** |
| TP-Bernich (0.35/0.35, **g3**, 25%PT) | 3 | .35 | 25% | 392 | 63 | +10.94 | **−2.05** | **−6.8** |
| TP-Bernich (0.35/0.35, **g3**, hold) | 3 | .35 | hold | 392 | 46 | +8.87 | **−4.12** | **−13.7** |
| **CTRL** tight-strike **g7** (0.35, 25%PT) | 7 | .35 | 25% | 383 | 65 | +8.31 | **+3.58** | **+33.6** |
| CTRL low-PT g7 (0.25/0.25, 25%PT) | 7 | .25 | 25% | 385 | 56 | +5.66 | +0.84 | +7.1 |

**2022+ only** (clean window — Fri/Mon tight-gap expiries genuinely exist post-2022; pre-2022 the engine
matches odd EOM long legs):

| config | n | win% | rocCW **mid** | rocCW **net** | sumPnL net |
|---|:--:|:--:|:--:|:--:|:--:|
| **USER BuLO** (0.25/0.25, 50%PT) | 198 | 56 | +7.66 | **+4.49** | **+28.1** |
| USER sym (0.25/0.25, hold) | 198 | 56 | +6.84 | +3.67 | +23.0 |
| TP-Ravish (0.25/0.25, g3, 25%PT) | 194 | 59 | +11.82 | **−0.43** | −0.7 |
| TP-Bernich (0.35/0.35, g3, 25%PT) | 201 | 68 | +19.25 | **+7.33** | +13.2 |
| TP-Bernich (0.35/0.35, g3, hold) | 201 | 46 | +8.01 | −3.90 | −7.0 |
| **CTRL** tight-strike **g7** (0.35, 25%PT) | 198 | 68 | +10.45 | **+7.37** | **+51.6** |
| CTRL low-PT g7 (0.25/0.25, 25%PT) | 198 | 60 | +5.76 | +2.59 | +16.2 |

## What the data says

1. **At mid prices the TP skeleton looks exactly as good as it's pitched** — higher win rates (59–68%)
   and higher mid-ROC than the user's dcal (TP-Bernich +19% vs user +7.7% in 2022+). This is the
   seductive surface that sells the videos. **It does not survive realistic fills.**

2. **The tight +3 gap is the killer, and it's the killer *because* it shrinks the debit.** A Fri/Mon
   calendar costs **~$0.80** vs the user's **~$3.16** (2022+). The same per-leg commission + slippage is
   then a far larger share of both the debit and the thin 15–30% target. Cost destruction mid→net:
   **TP-Bernich −11.9 pts, TP-Ravish −12.3 pts, vs the user's −3.2 pts.** The tight-gap structures bleed
   ~12 points of ROC to fills; the user's wide-gap structure bleeds ~3.

3. **Full-sample, every tight-gap (+3) config is net-negative after costs** (−2% to −5% CW; −$6 to −$15
   sumPnL), while **all three user configs are net-positive** (+1.9% to +2.2%; +$12 to +$19). The user's
   structure also works through 2018–2021 and 2020's crash; the TP skeleton's only good stretch is the
   post-2022 vol regime.

4. **The one genuinely useful borrow is tighter STRIKES at the user's WIDE gap — not the tight gap.**
   `CTRL tight-strike g7` (0.35Δ both sides, **+7 gap**, 25% PT) is the **best config tested**: full
   sample **+3.58% CW net / +$33.6**, and 2022+ **+7.37% net / +$51.6 at 68% win** — beating both the
   user's current 0.25Δ and every tight-gap TP variant. Moving the short strikes from 0.25Δ → 0.35Δ
   (closer to the money) on the user's existing structure is the real, testable improvement.

5. **TP-Bernich g3 IS positive in 2022+ (+7.33%)** — so don't overstate. But it earns the *same* ROC%
   as the wide-gap control while producing **¼ the dollars** (+$13 vs +$52), because the debit is ¼ the
   size; to match the control's capital you'd run ~4× the contracts and ~4× the multi-leg SPX fills.
   And it's negative full-sample. The control dominates it on every practical axis.

6. **Bernich's actual edge, if real, lives entirely in the untested intraday transform.** The EOD floor
   (hold/PT, no transform) does **not** beat the user's dcal. His pitched 63% win / high profit-factor
   comes from converting winners into no-loss condors intraday — which this data cannot reach. So the
   verdict is not "his strategy fails," it's "**the part that beats the user's dcal is the part that
   can't be verified**," and the part that *can* be verified underperforms after costs.

## Verdict for the user's question

**The double-calendar skeleton does NOT beat your SPY dcal.** Your wider +7 gap is, after costs, the
better structure — the tight Fri/Mon gap that defines the Theta-Profits version is a net-negative once
you pay realistic fills, because the ~$0.80 debit can't absorb 8-leg commissions + slippage against a
thin target. The transform that's *supposed* to redeem it is intraday-only and unverifiable here.

**The single actionable takeaway:** test moving your short strikes from **0.25Δ → ~0.35Δ** at your
existing +7 gap with a 25% profit-take. That borrowed one idea (closer strikes) was the best config in
this sweep (+7.4% CW net, 68% win, 2022+) — better than your current 0.25Δ and better than the full TP
skeleton. Worth a regime-gated confirmation run before adopting.

## Regime-gated confirmation (2026-06-25, `run_gated_confirm.py`)

Does the "0.25Δ → 0.35Δ closer strikes" borrow survive *inside the regimes you actually trade*
(BHI / BuLO), gated by your real classifier (SPY vs 50-MA; VIX≥20), or was it an ungated artifact?
Same +7 gap, same cost model, capital-weighted ROC after costs. **It survives — and refines per regime.**

Harness check: my incumbent **BuLO rocCW_mid +10.46%** ≈ the playbook's documented **+10.4%** → the
engine reproduces your existing edge, so the relative comparison is trustworthy. (My capital-weighted
basis runs cooler than the playbook's mean-of-ratios on the asymmetric BHI; relative deltas are robust
to that choice.)

**Bullish_LowIV** (your high-frequency regime, n≈212):

| variant | n | win% | rocCW net | median net | sumPnL net |
|---|:--:|:--:|:--:|:--:|:--:|
| INCUMBENT 0.25/0.25 50%PT | 212 | 53 | +6.14 | +6.05 | +28.1 |
| **CHALLENGER 0.35/0.35 50%PT** | 209 | 58 | **+9.65** | +15.08 | **+48.9** |
| CHALLENGER 0.35/0.35 25%PT | 209 | **67** | +8.47 | **+20.38** | +43.0 |

→ Tighter strikes lift CW net ROC **+6.1% → +9.7%** (~+57%) and nearly double the dollars. The 25%-PT
variant trades CW-ROC for a higher win rate (67%) and median.

**Bearish_HighIV** (smaller, n≈66 — playbook already treats it half-size):

| variant | n | win% | rocCW net | median net | sumPnL net |
|---|:--:|:--:|:--:|:--:|:--:|
| INCUMBENT 0.25P/0.10C hold | 66 | 47 | +7.92 | −6.63 | +10.9 |
| **CHALLENGER 0.35P/0.10C hold** | 67 | 54 | **+13.11** | +2.37 | **+19.2** |
| CHALLENGER 0.35/0.35 hold (symmetric) | 66 | 53 | +5.40 | +3.51 | +10.4 |
| CHALLENGER 0.35/0.35 25%PT | 66 | 68 | +9.80 | +22.47 | +18.8 |

→ In BHI the winner is **bump only the PUT to 0.35Δ and keep the call far-OTM at 0.10Δ** (+7.9% →
+13.1%). Pulling the *call* in to 0.35Δ (symmetric) **hurts** (+5.4%) — it adds upside risk in a
bearish/high-vol regime. So apply "closer strikes" to the tested put side and **keep the BHI skew.**

**Recommendation (confirmed):**
- **BuLO:** move short strikes 0.25Δ → **0.35Δ** both sides. Keep 50% PT for max CW-ROC (+9.7%), or
  switch to 25% PT for a 67% win rate / faster turnover (+8.5%).
- **BHI:** move the short **put** 0.25Δ → **0.35Δ**, keep the **call at 0.10Δ** (preserve skew); hold
  to expiry. +13.1% CW net vs +7.9%.
- **Honest limits:** the gains concentrate in 2021/2024/2025; early benign years (2018–20) are ~flat
  to slightly worse, though never a blow-up (defined-risk holds). BHI is small-sample (some years
  n≤4) — treat as provisional, half-size, and re-confirm as the sample grows. This refines your
  existing strategy; it does **not** vindicate the Theta-Profits tight-gap version.

## Caveats

- **Ungated.** The user's real dcal is **regime-gated** (BHI/BuLO only; playbook shows BHI → +23.7% mid
  gated). This test ran the user's *parameters on all Fridays*, which dilutes them — so the user's
  deployed edge is **understated** here, strengthening the conclusion. The TP skeleton has no comparable
  gating tested (Ravish's VIX<20 timing is unmodeled).
- **Cost model.** 25% of quoted spread per leg per side + $0.65/leg. Robust check: even **halving**
  slippage leaves the tight-gap configs below the user's and the wide-gap control (they lose ~12 pts
  mid→net; half is still ~6 pts into negative territory full-sample).
- **Entry day fixed to Friday** for a controlled comparison; Ravish/Bernich actually enter Tue/Wed.
- **Transform & VIX-timing not modeled** (intraday / discretionary) — this is the floor, not the ceiling.
- SPY proxy for SPX (the TP traders use SPX); SPY ends 2026-02-20.
