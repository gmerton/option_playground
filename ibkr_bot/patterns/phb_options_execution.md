# PHB via near-dated CALL options (execution research)

Implementing the intraday-flat Power Hour Breakout ([[power_hour_breakout.md]]) by
buying a **call (3–9 DTE)** at the trigger and selling at the close, instead of
the stock. Goal: pick an optimal delta. Today (2026-05-29) → "next Friday" expiry
= **2026-06-05 (7 DTE)**.

## Persisted data (2026-05-29) — reproducible offline
IBKR intraday option history is perishable, so it's saved to `ibkr_bot/data/options/`:
- `phb_option_bars_2026-05-29.csv` — 4,860 rows: full afternoon 1-min BID_ASK path
  for 27 option series (CIEN/IBM/DDOG/PANW/CSCO/KLAR/NVDA × ~4 strikes, Δ 0.32–0.82).
  Reconstruct any option's price at any minute → replay any delta / exit rule offline.
- `phb_option_meta_2026-05-29.csv` — per strike: greeks (delta/IV/gamma/theta) +
  trigger entry/exit times, exit reason, stock entry/exit px. NVDA tagged
  `filtered_out` (retained as the bull-trap stress case).
Stock 1-min bars for all examples live in `ibkr_bot/data/*_1min.csv`. (Nothing
committed to git yet — on disk only.)

## Option-data methodology (what works on this account)
- **Live intraday quotes:** not after-hours; would also need an OPRA subscription.
- **Frozen EOD greeks** (`reqMktData` + `reqMarketDataType(2)`): deltas reliable,
  but **after-hours spreads are blown out (CIEN ~20%) — do NOT use for cost**.
- **Historical intraday option bars** (`reqHistoricalData` on the Option contract):
  ✅ available — TRADES and **BID_ASK** 1-min bars for the session. This is the
  right source. ⚠️ Full-day 1-min BID_ASK for many strikes **trips IBKR pacing**
  (timeouts). **Pull only at the entry + exit timestamps** (`option_entry_exit.py`)
  — 2 small requests/name. For BID_ASK bars use **high=max ask, low=min bid** (the
  open/close come back equal on thin minutes → false 0% spread).

## ATM-call replay of the 6 winners (entry=trigger min, exit=close, buy ask/sell bid)
| Sym | strike | stock move | opt $ in→out | entry spread | opt round-trip | leverage |
|---|---|---|---|---|---|---|
| DDOG | 242.5 | +1.70% | 8.20→13.00 | 0.6% | +58.5% | 34.4× |
| IBM | 292.5 | +2.03% | 8.13→11.90 | 0.4% | +46.4% | 22.8× |
| PANW | 280.0 | +0.95% | 14.20→16.20 | 0.0% | +14.1% | 14.8× |
| CIEN | 557.5 | +4.12% | 41.00→55.00 | 0.0% | +34.1% | 8.3× |
| SNOW | 252.5 | +1.21% | no hist data | — | — | — |
| APP | 612.5 | +0.01% | no hist data | — | — | — |

## Findings
- **Intraday spreads at the trade times are tight (0–0.6%)** — the 20% was an
  after-hours artifact. These calls are tradeable in the power hour.
- **Earnings IV is the dominant vehicle-selection factor, not delta.** CIEN had
  the biggest *stock* move but the *worst* leverage (8.3×) because ~150%
  earnings-inflated IV makes its ATM call cost $41. DDOG (+1.70% stock) gave the
  best leverage (34.4×) on a cheap $8.20 call. **Prefer cheap-premium / low-IV
  names; screen out names with earnings inside the DTE window.**
- **Liquidity verdict:** IBM/DDOG/PANW clean & cheap; CIEN liquid but
  earnings-expensive; SNOW/APP no historical option data (thin or missing).

## Delta ladder (winners only; `option_delta_ladder.py`, exp 2026-06-05)
| Name | stock | 0.65Δ | 0.50Δ | 0.35Δ |
|---|---|---|---|---|
| IBM | +2.0% | $9.80 +35% (17×) | $5.81 +45% (22×) | $3.45 **+59% (29×)** |
| DDOG | +1.7% | $8.20 +32% (19×) | (same strike) | $2.48 **+73% (43×)** |
| PANW | +0.9% | $19.14 +8% (8×) | $12.26 **+12% (12×)** | $7.50 +10% (10×) |

- **Lower delta = more leverage — but only if the move is big enough to carry the
  OTM call up its gamma curve.** Big moves (IBM/DDOG ~2%) → 0.35Δ dominates (29×,
  43×). Small move (PANW +0.9%) → 0.35Δ *underperforms* ATM (10× vs 12×): the move
  didn't travel far enough. **Delta should scale to expected move size; ~0.35–0.50
  is the sweet spot for typical 1–2% PHB moves.**
- ⚠️ **WINNERS ONLY — not yet a recommendation.** Leverage cuts both ways: on a
  VWAP stop-out the cheap 0.35Δ OTM call bleeds a far higher % of premium than a
  0.65Δ ITM call. **Optimal delta requires replaying the LOSERS (NVDA bull-trap +
  mid faders) at each delta and computing expectancy across the full trade set.**
  That is the decisive next step (and fits the precision/loss-control preference).
- Tooling note: DDOG's near-ATM strikes were too sparse (0.65 & 0.50 both mapped to
  the 242.5 strike) — widen the greek band or interpolate.

## SNOW / APP — option data resolution
Options ARE available (full **weekly** chains 6/5, 6/12, 6/18, 6/26… across 20
exchanges, single class) — **not monthly-only.** But this account returns **0
historical intraday BID_ASK bars** for SNOW & APP at *every* expiry, while
CIEN/IBM/DDOG/PANW return data fine → **name-specific historical-data gap**, not an
expiry/class issue. Can't replay them from history; fallback = live frozen quotes
during RTH. (Chain's near-monthly is listed as 6/18, not the standard 3rd-Fri 6/19.)

## Expectancy by delta (winners + losers; `option_expectancy.py`, exp 2026-06-05)
Filtered trade set (1.0% VWAP gate on) with option data: winners CIEN/IBM/DDOG/PANW
+ losers CSCO/KLAR. NVDA correctly FILTERED OUT (no fire at the gate — the bull-trap
is rejected). FLEX fires but its 6/5 calls returned no data.

| delta | win% | avg | total | profit factor |
|---|---|---|---|---|
| 0.70 ITM | 83% | +18.1% | +108% | **12.9** |
| 0.50 ATM | 83% | +18.2% | +109% | 4.0 |
| 0.35 OTM | 67% | **+24.0%** | **+144%** | 4.9 |

Per-trade: KLAR loss was −9% (0.70) vs −36% (0.50) vs −33% (0.35); DDOG win was
+29% (0.70) vs +73% (0.35). **0.35Δ maximizes raw return but has the worst win-rate
and fattest tail; 0.70Δ ITM amplifies wins solidly (IBM +44%, CIEN +30%) while
containing losses to single digits → far higher profit factor.**

**RECOMMENDATION (provisional): ~0.65–0.70Δ (ITM).** Best fit for the
precision/loss-control preference ([[feedback-precision-over-recall]]) — strong win
amplification, tight downside. Use 0.35Δ only to maximize raw return and tolerate
deeper drawdowns. ⚠️ **6 trades, ONE up-day, ~1 real loser (KLAR) — PF 12.9 is
inflated by the thin loss sample. The ITM advantage IS loss-containment, which is
exactly what's under-sampled. A DOWN-DAY (frequent stop-outs) will prove or break
this.** Not settled.

## Trailing stop (fixes the KLAR-style give-back) — stop × delta interact
`power_hour_trigger.py` exit modes now include **ema9** (exit on close < 9 EMA) and
**trail:X** (exit X% off the running peak). Stock-level: `ema9` too tight (chops
winners, WIN-day avg +1.67%→−0.06%); `trail:0.5` best consistency (78% win, PF 12)
but clips winners (total +7.99%→+5.05%).

Option-level (via `option_expectancy.py --stop`):
- **The trail FIXES KLAR:** option P&L −9%/−36% (0.70/0.50Δ, vwap) → **+9%/+9%**
  (trail:0.5). Exits near the 15:42 peak instead of riding it back.
- **But at ITM it costs more than it saves** — 0.70Δ total +108% (vwap) → +57%
  (trail:0.5) / +87% (trail:0.75): the trail clips winners (CIEN +30→+18, IBM
  +44→+27). **The ITM call already self-protects** (KLAR only −9% at 0.70Δ on the
  plain vwap stop), so a tight trail mostly sacrifices upside.
- **The trail pays off at lower delta** where give-back is catastrophic: at 0.50Δ,
  `trail:0.75` BEAT vwap (+129% vs +109% total).

**Two coherent packages:** (a) **ITM 0.65–0.70Δ + plain vwap stop** — high delta IS
the give-back protection; don't clip winners. (b) **ATM/OTM 0.35–0.50Δ + ~0.75%
trail** — more leverage, trail tames the give-back. ⚠️ KLAR's reversal was MILD
(0.7% give-back) so the trail's value is **understated**; a sharp down-day reversal
would favor it more. Still 6 trades / one up-day / ~1 loser.

## Open / next
- **Down-day replay** — decisive for the PHB edge, the ITM delta pick, AND the
  trailing stop (sharp reversals are where the trail proves itself).
- Add an **earnings-date filter** (skip names reporting before expiry; CIEN proved why).
- KLAR has option data (unlike SNOW/APP/FLEX); revisit those via live RTH quotes.
