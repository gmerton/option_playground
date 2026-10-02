# Ariel's broker-logged trades: selection vs management (2026-10-01)

**Verdict: the PRIMARY (all picks) is UNDERPOWERED. His SHORT selection is a CANDIDATE: +7.66pp vs same-date
controls, t 3.39. His LONG selection leans INVERTED (t -2.15).** Script `run_ariel_broker_picks.py` (pre-registered
0433a62 before scoring), log `logs/ariel_broker_picks.log`. Data: his six monthly "all trades" tables (Oct 2025 -
Mar 2026, `ariel_broker_log_2026-10-01.md`), 181 trades with a date and direction, merged to **146 picks (91 long,
55 short) on 83 dates**. Entry at the close of his open date, signed, 10 bp per side.

## Selection: 10 sessions, picks minus same-date ADR-tercile names (C1)
| cell | n / dates | mean | t | halves | months + |
|---|---|---|---|---|---|
| **PRIMARY: all** | 146 / 83 | +1.50pp | +0.98 | +3.64 / -0.64 | 4/6 |
| S1 longs | 91 / 62 | **-2.23pp** | **-2.15** | -1.63 / -2.81 | 1/6 |
| **S2 shorts** | 55 / 44 | **+7.66pp** | **+3.39** | **+11.77 / +3.70** | **5/6** |
| S3 all, 20 sessions | 146 / 83 | +1.26pp | +0.52 | +2.20 / +0.32 | 3/6 |
| S4 all vs same name later | 146 / 83 | +1.38pp | +0.22 | +4.35 / -1.60 | 5/6 |

- PRIMARY: +1.50pp is below the 3.4pp MDE, so by rule it is UNDERPOWERED, not NULL. The two sides pull in opposite
  directions, and that is the finding.
- **S2 shorts clear Sidak (2.57) and the discovery bar (3), with both halves positive and 5 of 6 months positive.**
  The ADR-matched same-date names went nowhere (-0.10%), while his shorts fell 7.6% in 10 sessions.
  Exploratory robustness, run after the result and labelled as such: median excess +5.2pp; excluding precious
  metals and miners +8.72pp (t 3.91, n 40); metals alone +4.84pp (t 0.90); dropping the 3 largest +5.84pp (t 2.94).
  It is not one trade and not the silver crash.
- His longs underperform comparable names (33% beat C1, 1/6 months positive). Below the bar, but consistently negative.

## Management (descriptive)
- M1: of his 10 largest dollar winners, 5 are top-decile on selection excess (their mean +21pp). The tail is partly
  the names moving and partly what he does with them; Spearman($ P&L, excess) is only +0.10.
- **M2: his implied traded notional is larger on winners (median $1.45M vs $1.05M, p 0.013).** He adds into what works.
  ⚠ The notional is |$| / |%|, and his % is cumulative over adds, so this is a proxy.
- M3: winners realise +4.90% against +4.87% for a fixed 10-session hold, so the same. Losers realise -1.99% against
  -0.54% if held: cutting fast costs about 1.5pp per loser on these names (indicative; % is cumulative over adds).

## Reading against the goal
- First creator result in this ledger to clear the discovery bar on a pre-registered cell: **his short selection.**
  The shorts are parabolic speculative names (RGTI, UAMY, CIFR, IREN, OKLO, QUBT, AXTI, APA, LITE...) at his "first red
  day", "rejection of the 20/50sma" and "10-13x ATR from the 50sma" spots.
- ⚠ What C1 does not hold fixed is EXTENSION. Same-date names of the same volatility are not names 10x ATR above
  their 50-day. The open question is whether the edge is his discretion or the mechanical property "very extended
  name, first sign of failure". That can be tested mechanically on the full panel and is the obvious next step.
- His dollars come from the shorts and from sizing up into winners. His long selection is a drag.
- ⚠ Six months, one regime (a speculative top and unwind, Oct 2025 - Mar 2026), 44 short dates. A secondary cell,
  not the primary: CANDIDATE, not adopted.
