# Volatility-Contraction Breakout (VCB)

**Status:** exploring · detector built (`vcb.py`) · **live-alert wired** in
`signal_monitor.py` (`--signals vcb`) · backtested on a **selection-biased** cache
(hand-picked movers, ~990 sessions May–Jun 2026) → all numbers are an **upper
bound** until a clean out-of-universe test.

## Idea
After the opening range, a strong name **coils on contracting volume while holding
above VWAP**, then **breaks the opening-range high on a volume expansion** and
trends for the rest of the session. Distinct from MFR (fades morning weakness) and
PHB (a time-boxed power-hour variant of this same DNA — VCB is time-agnostic).
Archetype: **AAOI 2026-06-04** — coiled 10:00–12:10, broke 181.30 @ ~12:24 on
3.4× volume, ran +20%, closed +16.9% on a day SPY closed +0.65% (idiosyncratic,
not beta).

## Anatomy (gate → trigger → invalidation)
- **Gate (the coil):** after the opening range (default first 30 min), the base
  (OR-end → now) is quiet — avg volume/min ≤ `CONTRACT`(0.70)× the opening-range
  volume/min — and price holds above VWAP. Contraction = stored energy.
- **Gate (selection — THIS is the edge):** the name is **outperforming the index
  by ≥ `RS_MIN` pts** (ret-from-open vs SPY) at the breakout bar. This, not the
  trigger, is what separates winners from beta floaters. Default **RS ≥ +3 vs SPY**.
- **Trigger:** first bar that **closes above the opening-range high** with **volume
  ≥ `VOL_MULT`(2.0)× the trailing-30-min baseline**, while **close > VWAP**,
  **EMA9 > EMA20**, and **RSI ≥ `RSI_MIN`(60)**. Entry = that bar's close.
- **Invalidation / exit:** intraday-flat (always out by the close). Stop options below.

## Granularity: 1-minute (tested, not assumed)
Swept 1/3/5/15-min holding momentum context constant (structure on N-min bars,
RSI/EMA/VWAP read from 1-min as-of each decision bar — avoids the `add_indicators`
bar-period warmup confound). **1-min wins on every metric**; win-rate is flat
(~44%) across timeframes, so coarser bars just discard trades. Part of 1m's edge is
faster stop reaction (legit — you'd use it live).

## Stop options — KEEP BOTH ON FILE
Tested on gate=baseline+RS≥+3 (249 trades, SPY/QQQ excluded). **Tighter = strictly
worse (monotonic); the signal wants room.** ADR-normalized trailing (K × the
symbol's own avg-daily-range%) beats fixed-% trailing decisively.

| stop | win% | total% | PF | worst | medCap | when to use |
|---|---|---|---|---|---|---|
| **none — hold to close** | 55 | +216 | **2.38** | −7.0 | +19% | max return; rule is "just hold, flat at EOD" |
| **adr:0.45** (≈0.45× ADR) | ~51 | ~+162 | **~2.0** | ~−5 | +4–8% | **practical default**: mechanical, volatility-scaled, tighter tail |
| vwap | 47 | +146 | 1.77 | −4.1 | −14% | (clips winners — not preferred) |
| trail:3.0 (best fixed%) | 49 | +111 | 1.59 | −3.0 | −4% | inferior to adr at same aggressiveness |

- **No-stop** = max edge, but eats the full intraday crater on the rare fader.
  Safe *only because* it's intraday-flat (worst trade bounded by EOD). Overnight
  would flip this.
- **adr:0.45** = ~95% of the no-stop edge with a smaller worst trade and a
  mechanical, per-name-adapting rule (mean ADR ≈6.3%/day → ~2.8% trail typical;
  AAOI 13.5% ADR → ~6% room; quiet name → ~1%). Best insurance for the fader
  regime where this selection-biased backtest is most likely wrong.
- Avoid: tight trails, ema9, level, and vwap+combos — all clip winners.

## Tools
```bash
# detector + granularity sweep + single-name trace
PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb.py
PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb.py --explain AAOI --rs-min 3 --stop adr:0.45
# experiments
PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_gate_sweep.py    # intraday gate (can't buy precision)
PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_rs_sweep.py      # RS is the discriminator
PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_stop_sweep.py    # exit comparison (table above)
# index data needed for RS:
PYTHONPATH=src .venv/bin/python3 ibkr_bot/fetch_intraday.py SPY QQQ --days 40
```

## Key findings (why the recipe is what it is)
1. **1-min optimal** (granularity sweep).
2. **The intraday gate CANNOT buy precision** — sweeping vol/contract/RSI/vwap-dist
   moves win% only 43→48% and *worsens* PF (1.74→1.12). Volume/RSI/etc. don't
   discriminate winners from losers.
3. **Relative strength IS the discriminator** — RS≥+3 lifts PF/avg/medCap where the
   intraday knobs degraded them (cuts losers faster than winners). Edge = selection.
4. **Wide, volatility-scaled stop (or none)** beats every tight stop.

## Open questions / next steps
- **Out-of-universe test (decisive):** rerun the full recipe on a neutral symbol
  set / fresh days. How much of PF ~2.0 survives off the movers-biased cache?
- QQQ as the RS benchmark for semis (many track QQQ, not SPY).
- Exclude SPY/QQQ from evaluated universe; try RS≥+3 *and* RSI≥70 together.
- **Out-of-universe test before trusting the live alerts as edge** (alerts are wired
  but the numbers are still selection-biased).

## Live alerting (wired)
`signal_monitor.py --signals vcb` fires the same alert plumbing as the other
patterns (bell + macOS dialog + `alerts.log` + UI store) via `detect_vcb`, which
delegates to `vcb.find_vcb` so a live fire == a backtest fire. It auto-subscribes
`--index` (default SPY) as a hidden relative-strength feed (`--vcb-rs-min`, default
+3 pts); **no index feed → no VCB fires** (the RS selection gate is the edge).
Validated by replay: AAOI 2026-06-04 fires live at 12:24, the same bar as the
backtest. ⚠️ alerts are a heads-up, not validated edge until the out-of-universe test.

## Examples
| Symbol | Date | OR-high | Breakout | vexp | RS vs SPY | Entry→exit (hold) | Day |
|---|---|---|---|---|---|---|---|
| AAOI | 2026-06-04 | 181.30 | 12:24 | 3.4× | +4.0 pts | 181.45→202.76 (+11.7%, captured 76%) | ran +15.6% / closed top 82% of range |

<details><summary>AAOI 2026-06-04 --explain trace (1-min)</summary>

```
=== AAOI 2026-06-04 — VCB trace (stop=vwap, index=SPY) ===
   1m  FIRE @ 12:24  entry 181.45  vexp 3.4x  rsi 78  RS +4.0pts
       -> exit 202.76@15:59 (close)  trade +11.74%  captured 76%
       | day ran +15.6% closePos 82%
```
</details>
