# Mechanical "very extended name, first failure" short (2026-10-01)

**Verdict: NULL, tightly bounded. Over 17 years the mechanical version of Ariel's short spot (and Qullamaggie's
parabolic short, daily proxy) earns nothing against same-date names: -0.03pp, t 0.00, on 1,166 events / 652 dates.
In absolute terms it loses money (-0.76% per trade).** Script `run_extended_first_failure_short.py` (pre-registered
dd68ec2 before scoring), log `logs/extended_first_failure_short.log`, events `..._events.csv`. Panel
`liquid_panel_2009` (1,728 names, 2010-2026), eligible at $5 / $50M ADDV.

Spec: extended = max over the prior 5 days of (close - SMA50) / ATR14 >= K; trigger = the first daily close below the
prior day's low (none in the prior 20 sessions); short at that close, hold h sessions, 10 bp per side.

| cell | n / dates | vs C1 (same-date ADR tercile) | t | halves | years + | absolute short |
|---|---|---|---|---|---|---|
| **PRIMARY K=8, h=10** | 1,166 / 652 | **-0.03pp** | **+0.00** | -0.34 / +0.18 | 8/18 | **-0.76%** |
| S1 K=10 (his 10-13x) | 129 / 107 | +0.59pp | +0.85 | +0.62 / +0.43 | 9/17 | +0.05% |
| S2 K=6 | 8,041 / 2,135 | -0.10pp | -0.63 | -0.00 / -0.14 | 10/18 | -0.68% |
| S3 K=8, h=20 | 1,159 / 647 | -0.17pp | -0.43 | -0.19 / -0.18 | 11/18 | -1.22% |
| S4 trigger vs extension without trigger | -- | **INVALID** (see below) | | | | |

- The primary MDE is 0.96pp, so any edge above about 1pp per trade is ruled out. Only 4 of 18 years see the
  mechanical short make money outright.
- **S4 is RETRACTED as designed.** Its control (C2) shorts the same name on extended days in the 10 sessions *before*
  the trigger, and those days are selected because a failure followed. That is outcome conditioning. Its
  -1.63pp / t -10.2 says nothing about the trigger. (The "clean result is a bug" rule caught it before it was read
  as a finding.)
- Reported, not a test: in Ariel's own window (2025-10 -> 2026-03) the mechanical K=8 short earns +2.98pp vs C1
  (t 2.23, n 40) and +1.79% outright. The spot paid in that regime, but not across 17 years.

## Reading
- Ariel's short edge (+7.66pp, t 3.39) is not the mechanical property "very extended + first failure". Across the
  full history that property is a coin flip that loses its drift. What his record shows sits in his window and in his
  discretion: which extended names, which failure, and when.
- This is consistent with every prior single-name fade here (capitulation scorecard, Tito exhaustion fade, bouncy ball:
  now **0 for 5**) and with the short-universe null. Qullamaggie's parabolic short is not tested in its real
  universe (small-cap pumps and delisted names) and this panel cannot test it. The daily large-liquid proxy is NULL.
- Ariel's short cell stays a CANDIDATE, but now explained as "regime x discretion", not as a codable setup. The only
  way left to test it is FORWARD: log his new short slides as they publish and score them out of sample.
