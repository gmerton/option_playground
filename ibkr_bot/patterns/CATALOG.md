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
| Morning Flush Reversal (MFR) | [morning_flush_reversal.md](morning_flush_reversal.md) | exploring | 1 | morning oversold reclaim |
| Power Hour Breakout (PHB) | [power_hour_breakout.md](power_hour_breakout.md) | exploring | 4 ex + 5 counter | late-day base breakout |

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
