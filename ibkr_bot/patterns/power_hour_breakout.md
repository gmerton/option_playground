# Power Hour Breakout (PHB)

**Status:** exploring (N=3 — CIEN, CRDO, AVGO, all 2026-05-29)

## Idea
After a tight midday consolidation that coils around VWAP, the stock ignites in
the **power hour (~15:00–16:00 ET)** on a surge of volume and closes in the top of
the day's range. We want to buy the late-day expansion as it starts — riding
strength into the close, the mirror image of MFR (which fades morning weakness).

Shares the catalog theme with MFR: both end the day **closing at/near the high**.
They differ by *where the buyable entry is* — MFR = morning oversold reclaim;
PHB = late-day base breakout.

## Anatomy (gate → trigger → invalidation)
*Thresholds PROVISIONAL from N=3.*

- **Gate (the midday coil):** roughly 12:00–14:30 ET, a **tight range hugging
  VWAP** (examples were 1.4–2.5% wide; coil sat within ~±1% of VWAP — above or
  below both occur). Low volume / drifting.
- **Trigger (the power-hour ignition):** during 15:00+, price expands up out of
  the coil on a **volume surge — power-hour per-minute volume ≥ ~2.5× the midday
  average** (examples 2.6–5.0×). Close clears the midday base high. ⚠️ see open
  questions — the plain "break of base high" entry is laggy.
- **Invalidation:** loss of the breakout / fall back into the midday range, or a
  fade off the highs into the close.

## What the 3 examples agree on
- Midday coil glued to VWAP (CIEN +0.2%, CRDO −1.0%, AVGO −0.4%) — **position vs
  VWAP doesn't matter; tightness does.**
- **Volume explosion in the final 30 min** is the signature: 4–9× the midday
  30-min volume on every one. Most reliable, most consistent tell.
- **Strong close:** 71–96% up the day's range, within ~2% of HOD.
- **A new HOD close is NOT required** — CRDO closed −1.9% off its *morning* high
  and still qualifies. The outcome is "power-hour expansion + strong close," not
  "fresh HOD."

## Directional trigger v1 (`power_hour_trigger.py`, backtested on the 45-name set 2026-05-29)
Conjunction at a power-hour bar (ALL required): **close > VWAP · 9 EMA > 20 EMA &
close > 9 EMA · new afternoon high (since 12:00) · RSI ≥ 60 and rising · bar
volume > 1.5× trailing-20.** Entry = first bar meeting all; outcome label from
where the day closed in its range (WIN ≥85%, FADE ≤40%).

| Scan window | Winner recall | Winners avg fwd→close | Fader false-pos | Faders avg fwd→close |
|---|---|---|---|---|
| 14:30–15:30 (intraday exit) | 46% (6/13) | +1.67% | 16% (3/19) | −1.90% |
| 14:30–15:45 | 54% (7/13) | +1.74% | 26% (5/19) | −1.12% |
| 14:30–15:59 (buy-the-close) | 100% (13/13) | +1.14% | 32% (6/19) | −0.93% |

**Validated:** the directional filter silences the high-volume faders that beat a
volume-only gate — TXN (8.9×), M (4.0×), SLB (5.0×), MCHP (4.1×) never fire.
True fires are net positive, false fires net negative in every window (~2.5–3.5pp
separation). Widening 15:45→15:59 added all 6 remaining winners but only 1 fader
(faders don't make new afternoon highs late — the window extension is nearly free).

**Two regimes:** early fires (≤15:30) = more runway, fewer false positives,
intraday-tradeable; late fires (15:50+) = catch the rest but only as buy-the-close
/ overnight holds. Faders that fire barely run before rolling (fwd→high +0.1–0.2%),
so a **stop under the entry bar** would cap most false-positive losses near
breakeven (NVDA −2.95% was the one real bull-trap).

### Intraday-flat backtest (chosen direction; scan 14:30–15:30, flat by close)
Round-trip P&L with a stop, exit at session close if not stopped (`power_hour_trigger.py --scan-end 15:30 --stop <mode>`). 14 fires on 2026-05-29:

| Stop | Win-rate | Avg/trade | Total | Profit factor |
|---|---|---|---|---|
| bar_low (1-min low) | 14% | +0.32% | +4.45% | 3.62 |
| **vwap (close<VWAP)** | 43% | +0.29% | +4.00% | 1.66 |
| pct:0.5% | 36% | +0.33% | +4.56% | 2.07 |
| pct:1.0% | 50% | +0.46% | +6.41% | 2.24 |

Net positive under every stop. **`bar_low` is too tight** (nicked by noise — chops
winners, avg win falls to +0.96%). **VWAP stop is the interpretable default**
(thesis: long while price holds VWAP; exit on close back below) — and it produced
the ideal signature: **all 6 WIN-day fires exited at the close green (CIEN +4.12%,
IBM +2.03%, DDOG +1.70%, SNOW +1.21%, PANW +0.95%, APP +0.01%); every loser
exited at VWAP for a small loss (worst NVDA −1.69%).** Winners run, losers self-cut.

⚠️ **IN-SAMPLE, ONE up-day, 14 trades — not yet an edge.** The mechanism behaves
correctly and the numbers are encouraging, but a single up-day is no validation.
Must replay on more days (esp. a down-day) before trusting any stop number or the
profit factor. Stop choice is mildly fit to this day — don't over-optimize it.

### Precision filter: distance above VWAP at the trigger (the winner/fader discriminator)
Comparing the 14 fired trades' trigger-bar features, **volume did NOT separate
winners from faders** (both ~2.2× trailing-20); nor did RSI, EMA spread, breakout
size, or 3-bar follow-through. The one clean discriminator was **how far above
VWAP price was at the trigger**:

| group | dist above VWAP at trigger |
|---|---|
| winners (6) | 1.88% avg (1.21–2.79%) |
| faders (3) | 0.87% avg — MNST 0.93, QCOM 0.93, **NVDA 0.76** |

Faders fire while *hugging* VWAP (weak, flips back below easily); real PHBs fire
only once price is decisively extended above VWAP. Adding **close ≥ 1.0% above
VWAP** to the trigger (now the default `MIN_VWAP_DIST` in `power_hour_trigger.py`):

| filter | trades | win-rate | avg | total | profit factor | faders let in |
|---|---|---|---|---|---|---|
| none | 14 | 43% | +0.29% | +4.00% | 1.66 | 3/19 |
| **≥1.0% above VWAP** | 9 | 67% | +0.89% | +7.99% | **4.94** | **0/19** |

Kept all 6 winners, removed all 3 false positives (NVDA/MNST/QCOM) + 2 weak mids.
Chosen per the user's precision-over-recall preference ([[feedback-precision-over-recall]]).
1.0% sits in the gap (fader max 0.93 / winner min 1.21) with buffer — not fit to the edge.

## Open questions
- **Volume must be paired with direction.** (Resolved-ish by the 45-name batch:
  volume surge alone has a high false-positive rate — faders surge too.) Next
  trigger to prototype: power-hour bar where price is **above VWAP and above the
  9 EMA, making a new afternoon high, RSI rising (>~60), AND volume expanding** —
  the conjunction, tested on this batch's winners vs faders to see if it separates.
- **The "break of base high" entry is laggy** (AVGO fired 15:50, 26% of move
  left). The directional trigger above should fire earlier than the base-high clear.
- **Single breakout-bar volume is unreliable** (CRDO's was 1.0× trailing-20);
  prefer the **power-hour aggregate** ratio.
- **Early-afternoon variant:** PANW/DDOG/IBM broke out 14:31–14:40 and still
  closed strong. Widen the breakout window to ~14:00, or split a sub-pattern?
- **What separates a strong PHB from a weak one** (CIEN/AVGO new HOD vs CRDO no
  new HOD)? Base width? Broader-market tailwind (all examples were the same up-day
  — need a down-day sample to control for it)?

## ⚠️ Batch finding (2026-05-29, 45-symbol scan via scan_phb.py) — volume surge is NOT the signal
Scanning 45 names broke the "4–9× final-30min volume is the signature" hypothesis
from the first 3 examples (which were all winners). Across the batch the biggest
power-hour volume surges were **faders, not breakouts**:

| Sym | power-hr vol | close % up range | result |
|---|---|---|---|
| TXN | 8.9× | 11% | faded to lows |
| MNST | 6.8× | 38% | faded |
| SLB | 5.0× | 26% | faded |
| MCHP | 4.1× | 17% | faded |
| M | 4.0× | 6% | faded to lows |

The volume range of faders (1.6–8.9×) fully overlaps the winners (SNOW 2.6×, AVGO
5.0×, MSFT 4.6×). **A late-day volume explosion happens just as much on power-hour
*selling*.** Volume is necessary, not sufficient. The real discriminator is the
**direction** of the power-hour move — winners hold above VWAP and make higher
highs into the close; faders surge then roll over. → see open questions (trigger
needs a directional/RSI filter, not just volume).

## Examples (PHB card)
| Symbol | Base 12:00–14:30 | Coil vs VWAP | Breakout | Power-hr vol | Close (% up range, off HOD) |
|---|---|---|---|---|---|
| CIEN | 543.22–556.74 (2.5%) | +0.2% | 15:09 @ 557.63 | 4.3× | 580.60 (96%, −0.3%) STRONG |
| SNOW | (2.6% wide) | +0.4% | 15:02 | 2.6× | (95%, −0.3%) STRONG |
| MSFT | (0.7% wide, very tight) | +0.4% | 15:50 | 4.6× | (93%, −0.3%) STRONG |
| AVGO | 434.11–441.34 (1.7%) | −0.4% | 15:50 @ 445.11 | 5.0× | 447.21 (90%, −0.4%) STRONG |
| CRDO | 227.19–230.41 (1.4%) | −1.0% | 15:33 @ 230.67 | 2.6× | 236.15 (71%, −1.9%) ok |

**Early-afternoon variant (broke base high 14:31–14:40, before the 15:00 power hour, still closed strong):** PANW (2.5×, 93%), DDOG (4.2×, 89%), IBM (3.7×, 89%). Possible separate sub-pattern or wider window — TBD.

## Counter-examples (coiled but no clean late breakout / faded into close)
| Symbol | Base | Coil vs VWAP | Power-hr vol | Close % up range | Why it's a counter |
|---|---|---|---|---|---|
| TXN | 1.3% | −1.1% | 8.9× | 11% | huge volume surge, faded to lows — the perfect foil to "volume = signal" |
| M | 0.7% | −0.4% | 4.0× | 6% | big volume, faded to lows |
| SLB | 0.5% | +0.1% | 5.0× | 26% | big volume, faded |
| TSLA | 1.5% | +0.6% | 1.1× | 57% | tight coil but never ignited (no-trade) |
| ON | 1.3% | −1.0% | 1.6× | 23% | tight coil, drifted lower |

<details><summary>Full PHB cards</summary>

```
===== PHB  CIEN  2026-05-29 =====
  BASE 12:00-14:30: 543.22-556.74 (2.5% wide), coils above VWAP (550.70, +0.2%)
  BREAKOUT of base high @ 15:09 (557.63), 63% ahead to late-high 582.47
  VOLUME surge: power-hour 4.3x midday/min; breakout bar 2.6x trailing-20
  CLOSE 580.60 = 96% up day range, -0.3% off HOD (HOD 582.47@15:59)  -> STRONG close

===== PHB  CRDO  2026-05-29 =====
  BASE 12:00-14:30: 227.19-230.41 (1.4% wide), coils below VWAP (231.05, -1.0%)
  BREAKOUT of base high @ 15:33 (230.67), 64% ahead to late-high 236.82
  VOLUME surge: power-hour 2.6x midday/min; breakout bar 1.0x trailing-20
  CLOSE 236.15 = 71% up day range, -1.9% off HOD (HOD 240.81@10:00)  -> ok close

===== PHB  AVGO  2026-05-29 =====
  BASE 12:00-14:30: 434.11-441.34 (1.7% wide), coils below VWAP (440.01, -0.4%)
  BREAKOUT of base high @ 15:50 (445.11), 26% ahead to late-high 448.90
  VOLUME surge: power-hour 5.0x midday/min; breakout bar 10.6x trailing-20
  CLOSE 447.21 = 90% up day range, -0.4% off HOD (HOD 448.90@15:55)  -> STRONG close
```
</details>
