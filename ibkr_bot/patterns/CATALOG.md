# Intraday Pattern Catalog

Working catalog of intraday setups we're developing into automated **buy signals**.
Each pattern has its own file with a definition (context gate + entry trigger +
invalidation) and a table of real examples characterized the same way.

## Workflow for adding an example
1. `.venv/bin/python3 ibkr_bot/fetch_intraday.py <SYMBOL>` — pull & save 1-min bars to `data/`.
2. `.venv/bin/python3 ibkr_bot/characterize.py <SYMBOL> <YYYY-MM-DD>` — print the standard card.
3. Paste the card into the matching pattern file's examples table.

The standard card reports, for the session: open→low→high→close, the **context at
the low** (% vs VWAP, RSI-14, volume vs 20-bar avg), the session shape, and where
each candidate trigger (RSI>40, higher-highs, 9>20 EMA, VWAP reclaim) first fired
after the low — entry price, % off the low, and % of the move still ahead.

## Patterns
| Name | File | Status | Examples | Entry |
|---|---|---|---|---|
| Volatility-Contraction Breakout (VCB) | [volatility_contraction_breakout.md](volatility_contraction_breakout.md) | exploring · backtested (`vcb.py`) · **live-alert wired** | 1 (AAOI) | coil → OR-high break on volume, RS-gated |
| Morning Flush Reversal (MFR) | [morning_flush_reversal.md](morning_flush_reversal.md) | exploring · live-alert wired | 1 | morning oversold reclaim |
| Power Hour Breakout (PHB) | [power_hour_breakout.md](power_hour_breakout.md) | **retired** — dead out-of-sample (PF 0.66) | 4 ex + 5 counter | late-day base breakout |
| EMA 9/20 cross | (see `ema_monitor.py` / `signal_monitor.py`) | live-alert (v1, whippy) | — | EMA crossover |

## Live alerting
`signal_monitor.py` watches live 1-min bars and fires an alert (terminal bell +
macOS dialog + `alerts.log`) the moment any pattern triggers. Alert-only — no
orders. It reuses the *same* detection code as the backtests: indicators from
`characterize.add_indicators`, and PHB delegates to
`power_hour_trigger.find_trigger` (1.0% above-VWAP precision filter on,
intraday-flat window 14:30–15:30), so a live fire means what a backtest fire meant.

```bash
.venv/bin/python3 ibkr_bot/signal_monitor.py PL CIEN AAOI         # default ema,mfr,vcb
.venv/bin/python3 ibkr_bot/signal_monitor.py --signals vcb AAOI CIEN
.venv/bin/python3 ibkr_bot/signal_monitor.py --signals vcb --vcb-rs-min 5 --index QQQ MRVL
.venv/bin/python3 ibkr_bot/signal_monitor.py --mfr-trigger rsi40 PL
```

**VCB** (`detect_vcb`) reuses `vcb.find_vcb` (same gate/trigger as the backtest) and
needs a relative-strength benchmark: the monitor auto-subscribes `--index` (default
SPY) as a hidden feed and shares its ret-from-open, so the live RS gate (`--vcb-rs-min`,
default +3 pts) matches the backtest. No index feed → VCB never fires (by design — a
breakout without the selection gate is just noise). Validated by bar-by-bar replay:
AAOI 2026-06-04 fires live at 12:24, the same bar as the backtest. The intraday stop
(none / adr:0.45) is an *execution* choice, not part of the alert.

Validated offline by replaying cached sessions bar-by-bar: PHB fires on the four
winners (CIEN/IBM/DDOG/PANW) and stays silent on NVDA/TXN; MFR fires on PL and
stays silent on non-flush names. ⚠️ Still in-sample (one up-day) — alerts are a
heads-up, not a validated edge. MFR is N=1 and experimental; its gate is anchored
on % down from open (≤−5%) + oversold RSI (≤30 at the low), with below-VWAP as
context, not required (an open-gap flush drags session-VWAP down with price).

Batch-scan a watchlist through the PHB lens with `scan_phb.py SYM SYM ...` — sorts
into STRONG / weak / COUNTER. Counter-examples are first-class: a 45-symbol scan
disproved "volume surge = the signal" (faders surge too). See the pattern file.

**PHB via call options** (3–9 DTE intraday-flat): [phb_options_execution.md](phb_options_execution.md)
— option-data methodology + ATM-call replay (`option_entry_exit.py`). Key finding:
earnings IV, not delta, is the dominant vehicle-selection factor.

Shared theme: both end the day **closing at/near the high**; they differ by *where
the buyable entry is*. MFR fades morning weakness; PHB buys late-day strength.

`characterize.py` cards: default = MFR (anchored on the session low); `--phb` =
Power Hour Breakout (midday coil → power-hour breakout + volume surge).

## Anatomy of a buy signal (shared model)
Every pattern is built as **gate → trigger → invalidation**:
- **Gate** — the context that makes the setup worth taking (e.g. flushed below VWAP + oversold). Keeps us from acting on every indicator cross.
- **Trigger** — the bar event that times entry once the gate is open (e.g. RSI back > 40, 9>20 EMA reclaim).
- **Invalidation** — where the idea is wrong and we're out (e.g. close undercuts the flush low).
