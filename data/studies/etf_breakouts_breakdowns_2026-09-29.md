# The house breakout (long) and its mirror breakdown (short) on sector / industry ETFs (2026-09-29)

## Pre-registration (written BEFORE any data pull or run; do not edit this section after the results)

**Why.** Gabe: shorts first; single-name breakdown shorts are 0 for 9 because names drift up and bounce off fresh
lows. ETFs don't delist or squeeze, and the sector-momentum spread already hedges. [BB-3] (Gabe 2026-09-23: "I'm OK
owning an ETF if the setup is good") asks the long mirror; the desk never shows ETFs (ADR ≥ 3 gate).
**Universe.** The 31 group ETFs of `group_move_study_2026-09-17.md` (ARKK CIBR GDX IGV IHI ITB IYT JETS KIE KRE KWEB OIH
SMH TAN URA XAR XBI XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY XME XOP XRT). yfinance adjusted daily OHLCV
2008 → 2026-09; signals 2010-01 → 2026-06. Every ETF-day with data is eligible (no ADR gate — that is the point).
**Harness.** `pattern_test.run_daily`, close entry, hold cap 60, harness costs, arm fixed = **ema20** (the house trail;
for the short, exit on a close above the 20 EMA). A setup refires in the same ETF only after 10 sessions.
Controls: **xname** (3 random other ETFs, same date, same stop %) = PRIMARY; **post** (same ETF, random later session
within 20) reported.

**LONG (BB-3).** Close > prior 20-session high while the prior close was not; RVOL (volume ÷ 50-day mean) ≥ 1.1; close
in the upper half of the day's range; SMA10 > SMA20 > SMA50. Stop = min(day low, close × 0.98), judged on the close.
**SHORT (mirror).** Close < prior 20-session low while the prior close was not; RVOL ≥ 1.1; close in the lower half of the
range; SMA10 < SMA20 < SMA50. Stop = max(day high, close × 1.02), judged on the close.

**PASS (each side, Šidák-2 → t ≥ 3.2):** paired edge vs xname > 0 with t ≥ 3.2, both halves (split 2018-01-01) > 0.
**The SHORT additionally needs mean R > 0 in absolute terms** (it must make money, not just lose less than other ETFs).
**Reported:** vs post; mean R and % return; per-ETF counts; the long side's absolute R.
**Prior.** Long low–moderate (house breakout ~0 on stocks; the group-move study found the ETF/SPY ratio a martingale
after a group-strength signal). Short low (our short record), but the ETF vehicle removes the delisting/squeeze
asymmetry that hurt single names. Local, ~1–1.5 h.
