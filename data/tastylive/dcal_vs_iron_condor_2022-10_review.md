# tastylive -- "Double Calendar vs Iron Condor: 3 Keys to Neutral Trades" (2022-10-28)

https://www.youtube.com/watch?v=-TsOWo9XFEo | 11 min | ~36k views | reviewed 2026-09-15 | educational segment, no
product pitch beyond the platform. Captions via yt-dlp.

## What they say
1. Both are range trades, but for EARNINGS the double calendar exploits the near-term IV inflation more efficiently:
   the short leg sits in the inflated weekly, the long in the calmer back cycle (META example: 95P / 105C, sell 7-day,
   buy 21-day, front IV 58% vs back 55%, debit $3.25).
2. Same-strike longs net intrinsic risk to zero: a double calendar is ALL extrinsic-value risk; the condor's risk is the
   strike width. Always a debit; selling the back would be a synthetic short strangle.
3. The IV number on the near expiry "spikes" into earnings because time value is decaying while extrinsic value is held
   up by the event -- not because extrinsic value is rising. (Correct and well put.)
4. Profit peaks AT the strikes (W shape) for the calendar, at the centre for the condor.
5. The calendar's short-vega window is brief: "if you don't get the vol crush right away you'd be better off with the
   iron condor"; over 2-3 weeks the condor has more profit potential; the calendar is "really a short-term trade."

## Against the calendar path study (real bid/ask, 2018-2026, sym 0.35Δ doubles, tight-market stock cut BA ≤ 25%)
Cut added tonight (`calendar_path_study.md`, "earnings position"): where the earnings date falls relative to the two
expiries, 90 stocks, hold to short expiry.

| earnings falls... | 12/19d n | ROC | win | halves | 20/27d n | ROC | win | halves |
|---|---|---|---|---|---|---|---|---|
| before the SHORT expiry (their play: short leg absorbs the crush) | 311 | **+1.4%** | 50% | +1.2 / +1.7 | 178 | +10.4% | 60% | +12.5 / +9.5 |
| BETWEEN the expiries (short expires first, long carries the event) | 851 | **+10.4%** | 66% | +8.4 / +13.0 | 540 | **+15.1%** | 66% | +9.6 / +19.1 |
| none in the window | 4,839 | +7.2% | 58% | +6.1 / +8.7 | 2,262 | +7.4% | 56% | +6.8 / +7.8 |

- **Their earnings play is the weakest cell on the 12/19 structure** (+1.4%, coin-flip win rate, 2018 −9, 2025 −3): the
  crush hits the long leg too, and the front's extra premium is what the bid-ask eats. On 20/27 it works (+10%), but no
  better than the event-free trade in the first half.
- **The best cell is the one they do not describe:** short expiry BEFORE earnings, long expiry after it. The short
  decays into a still-rising IV, the long is sold at the pre-event IV peak. +10-15%, 66% win, both halves, positive
  in every year 2018-2026, and a 3-4 day gap between the short expiry and the event beats 5-7 (+15.1 vs +10.9).
  Names: PLTR +43 (n=32), MSFT +30, HD +23, AMAT +23, GS +19, META +17, AAPL +16, NVDA +15.
- "Short-term trade / decay turns against you if you hold": not what the paths show. Hold beat every early exit in
  every earnings cell (before: hold +4.7 vs pt25 +0.3; between: +12.3 vs +6.8; none: +7.3 vs +1.5).
- Mechanics (points 2-4) are correct textbook statements and match how the sim prices the structure.
- Iron condor vs double calendar on the same entries is NOT tested head-to-head here (our SPX condor evidence is a
  separate engine). Cheap to add on the chain cache; queued as an idea, not started.

## Reading
Good mechanics explainer, wrong trade recommendation on the data: the pre-earnings double calendar is the one earnings
placement that does NOT pay on tight-market stocks at 12/19 days, while the placement where the long leg carries the
event is the best stock cell in the whole study. Score 3/5 as education, 1.5/5 as a trade idea.

**Proposal (not applied):** replace the playbook's "no earnings inside (entry, long expiry]" stock rule with:
earnings allowed, PREFERRED, when it falls between the short and the long expiry (ideally 3-4 days after the short);
avoid it only when it falls before the short expiry on the 12/19 structure. The old blanket rule came from the pooled
90-name table where wide-market names dominated.
