# Review: "Time spread in SPX options remaining attractive in low volatility" (The Options Mentor, 2026-09-20, UAgX48eqZ9k) — 2/5

Reviewed 2026-09-21. 10:37, public. Transcript: `videos/education/2026-09-20_UAgX48eqZ9k/`.

## The claims

1. **"If the VIX is below 15, I just don't think there's a better trade than the calendar."** (03:29; VIX 14.81.)
2. **Structure:** ATM SPX calendar, short the 10/9 expiry (~18–19 DTE), long "4 days wide" (~22 DTE); ~$7.50 debit,
   theta 27, vega 68. 5 days wide = $12.30 for theta 26 / vega 84 → "not a good value proposition", stay at 4.
3. **Calls vs puts:** compare the two on the risk graph; calls now give wider break-evens (7750–7775 region vs puts
   contracting), so calls this week; if they're configured the same, treat them as interchangeable (puts cheaper).
4. **Avoid a short leg on non-farm-payrolls Friday** (10/2): the short's IV stays elevated and won't decay into
   expiry week.
5. Place it midday Monday around the money; a little above or below is fine.

No P&L history, win rate or backtest is shown. The last third of the video sells a Slack, courses and mentoring.

## Against our evidence

**Claim 1, tested directly.** The clean calendar re-run (2026-09-16, `data/cache/calendar_path_clean/results_single.parquet`:
ATM put calendars on SPY/QQQ/IWM, Friday entries 2018–2026, real daily bid/ask, mid ± 25% of the spread + commissions,
held to the short expiry) stores the VIX at entry, so the claim splits cleanly. ROC % of the debit:

| structure | VIX | trades | entry dates | mean | median | win | t (dates) | halves |
|---|---|---|---|---|---|---|---|---|
| **short ~21 DTE, long +7 days (closest to his)** | **< 15** | 267 | 89 | **−9.8%** | **−34.9%** | 38% | −1.1 | −21.4 / −3.9 |
| | 15–20 | 409 | 137 | +3.5% | −25.3% | 44% | 0.3 | −23.1 / +28.7 |
| | ≥ 20 | 422 | 141 | −17.4% | −43.3% | 33% | −2.1 | −10.8 / −28.0 |
| short ~12 DTE, long +7 days | < 15 | 266 | 89 | +5.6% | +3.0% | 50% | 0.7 | −3.9 / +10.4 |

In his own regime and tenor the calendar LOSES: negative in both halves, median trade −35%, and on SPY specifically
−14.0% (IWM +0.9%, QQQ −16.4%). By year it swings −42% to +123% (2019 −42, 2023 −40, 2026 +123 on few trades). Low VIX
is not a regime where the calendar works; no VIX bucket clears t 2 on either structure. The whole family showed no
edge on index ETFs after costs (calendar_path_study.md, clean re-run).

⚠ Differences from his trade: SPX not SPY (same index; SPX spreads are proportionally tighter, cash-settled,
European), calls not puts, a 4-day gap not 7 (a narrower gap is even more of a pin bet: less vega, the same short
gamma). None of these is a known reason for the sign to flip, but none is tested.

**Claim 3 (calls vs puts by break-even width).** The risk graph's break-evens assume IV stays put; a wider break-even
is bought with a bigger debit, not found free. Neutral: a presentation choice, not an edge.

**Claim 4 (avoid NFP in the short leg).** Untested here. Adjacent evidence: FOMC proximity is noise for our books
(catalyst study), and single-name calendars with the EVENT in the short leg lose at every back-leg distance
(earnings_calendar_backleg_2026-09-20.md). Reasonable risk hygiene; no evidence either way for NFP.

**Claim 2 (4 vs 5 days wide).** Theta per dollar is higher on the narrower one, as he says; we didn't test gap width.

## Score: 2/5

Concrete and honest about mechanics (tenor, width, theta/vega, the call-vs-put check, event avoidance), and he says
VIX "can go right back up". But the headline claim is contradicted by our clean data in his own regime and tenor, he
shows no results, and the video ends as a course pitch. Don't trade the calendar on the VIX < 15 rule.

## Follow-up (not queued)

If ever revisited: SPX (or SPY as the proxy) CALL calendars with a 4-day gap at ~18 DTE, VIX < 15, from the v3 chain
through Feb 2026 — the only untested corner of his exact trade. Low prior given the table above.
