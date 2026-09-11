# Oil-spike short playbook: USO / BWET / CVI (written 2026-09-10, evening)

Idea: fade the Iran-war oil and tanker spike with Qullamaggie's parabolic short, expressed with
defined-risk options. Data is from the 9/10 close. Everything here is analysis, not tested edge. Our
own evidence on fading exhaustion is negative, and nothing we have covers war-driven commodity moves.

## 1. Setup at the 9/10 close

| Name | What it is | Last | Up days | 10-day | 20-day | Over 21 EMA | ADR | 9/10 candle |
|---|---|---|---|---|---|---|---|---|
| BWET | Breakwave tanker freight-futures ETF | 650.00 | 7 | +82% | +91% | +6.7 ADR | 6.4% | closed at the high, 0.8× vol |
| USO | front-month WTI futures ETF | 158.38 | 3 | +24% | +24% | +6.2 ADR | 2.5% | closed near the high, 2.1× vol |
| BNO | front-month Brent futures ETF | 63.13 | 8 | +25% | +25% | +6.8 ADR | 2.4% | closed near the high, 2.3× vol |
| CVI | CVR Energy, a refiner stock (not an ETF) | 48.60 | 9 | +21% | +39% | +3.5 ADR | 5.1% | upper wick: high 50.27, closed at 19% of range, 1.7× vol |

XLE closed red on 9/10 (−0.6%, near the low of a wide range) while crude ripped, so the energy
stocks lagged the commodity.

**Why it's moving (news, 9/7-9/10):** US-Iran strikes intensified around the Strait of Hormuz. On
9/10 Iran said it targeted two US vessels near Hormuz and Houthi rebels seized a key Yemeni port.
Brent touched ~$105 and US crude $100, the first time since May. Tanker earnings are at records
(VLCC near $800k/day), shipping stocks are at decade highs, and freight is expected to stay elevated
into next year. OPEC+ kept October output unchanged on 9/6, citing the Hormuz disruption. Bond
yields jumped with oil, which ties this to CPI (Fri 9/11, 08:30 ET) and FOMC (9/15-16).
**This is a live supply shock, not a sentiment blow-off.** That's the environment where parabolic
shorts fail most: the next headline can restart the move, and the real crack is likely a
de-escalation headline that gaps oil down overnight.

## 2. The trigger: Qullamaggie's parabolic short

- **Setup:** a vertical multi-day run (3-5+ up days) far above the 10/20-day averages.
- **Trigger:** never the first day up, never ahead of a crack. Either a failed gap-up that breaks the
  opening-range low, a close back under VWAP after a new high, or the first red day.
- **Stop:** the high of the day. Size to it, small.
- **Exit:** cover into the 10-day average, then the 20-day. Take some off on the first flush.

**As built in the alert monitor (untested):**
- **Daily state "parabolic" (SHORT):** at least 3 up days and at least 4 ADR over the 21 EMA, or at
  least 5 up days and at least 3 ADR. No resistance needed.
- **PARA detector:** after 09:45, on a completed 5-min bar, it fires on the first close under the
  15-min opening-range low and VWAP, or the first close back under VWAP after a post-opening-range
  new high. The stop is the high of day plus 0.1 ADR, and the alert lists the 10/20-day cover targets.
- **Red-day rule:** any short on a name at least 2 ADR over its 21 EMA only shows once the name is
  under the prior close. Otherwise it's saved as out of play.
- **Replay 9/8-9/10** on BNO, USO, BWET, CVI and FRO: without the red-day rule, 9 shorts fired inside
  green days and all 9 lost. With it, only CVI 9/9 remained (PARA at 45.60 plus a BIR at 45.04), and
  both still lost when CVI closed 47.73.

**Friday 9/11: every short needs a trade below the prior close**

| Name | Day state | Must trade below | Cover 1, 10-day SMA | Cover 2, 20-day SMA |
|---|---|---|---|---|
| BWET | SHORT parabolic | 650.00 | 495.78 | 455.14 |
| USO | SHORT parabolic | 158.38 | 141.40 | 135.62 |
| CVI | SHORT parabolic | 48.60 | 43.97 | 40.58 |
| BNO | SHORT parabolic | 63.13 | 55.95 | 53.86 |

## 3. Read by name

- **USO:** the textbook setup: vertical, 6 ADR stretched, climactic volume, no crack yet. It's the
  purest expression of the war. Its options are liquid, so it's the main vehicle.
- **CVI:** the only one already showing a crack (the 9/10 upper wick). Trigger: a break of 48.20, the
  9/10 low, or of Friday's opening-range low, with a stop at 50.27. Two cautions: part of the run is
  real refining margin (diesel cracks are spiking), and a CVI short against a DINO long is partly a
  refiner pair trade.
- **BWET:** the most parabolic, but freight futures carry structural support from rerouting, the
  daily range is ~6%, and borrow may be hard. It trades ~$130M/day, which is the most liquid in its
  group. Five option expiries are listed; open interest and spreads are unchecked.

**BWET alternatives: none moves like it**

| Name | $ volume/day | 10-day | Over 21 EMA | 60-day corr with BWET | Option expiries |
|---|---|---|---|---|---|
| BWET | $130M | +82% | 6.7 ADR | n/a | 5 |
| FRO | $110M | +18% | 3.1 ADR | 0.60 | 6 |
| DHT | $67M | +17% | 2.5 ADR | 0.52 | 7 |
| STNG | $56M | +13% | 2.3 ADR | 0.41 | 5 |
| TNK | $47M | +18% | 2.8 ADR | 0.51 | 5 |

The tanker stocks have priced in mean reversion of spot rates, so shorting them means shorting
laggards. BDRY is dry bulk (0.05 correlation), and BOAT and SEA trade under $3M/day. **FRO is the
follow-on short once BWET itself cracks**, not a substitute beforehand.

## 4. Vehicle: bear put spread over bear call spread

USO implied vol is 58-62%, about double normal, and the 25-delta calls trade 10-13 vol points above
the 25-delta puts (upside-panic skew).

| 9/25 expiry, 15 days | Bear put spread: buy 158P / sell 141P | Bear call spread: sell 171C / buy 181C |
|---|---|---|
| Price, mid / natural | 5.99 debit / 6.48 | 1.55 credit / 1.03 |
| Max gain / max loss | 11.01 / 5.99 | 1.55 / 8.45 |
| Reward:risk | 1.8 : 1 | 0.18 : 1 |
| Breakeven | 152.00 (−4.0%) | 172.55 (+8.9%) |

Why the put spread wins here:
1. **It pays on the thesis.** A crack to 141/136 pays up to 11; the call spread earns 1.55 even in a crash.
2. **It survives a war tape.** One escalation gap blows through 171 and the call spread loses 8.45 to
   make 1.55, which needs an 85%+ win rate to break even.
3. **The far call strikes had zero open interest**, so the gap between mid and natural eats a third
   to two-thirds of the credit.
4. **Put skew is cheap**, so the long put costs less than usual.

The call spread wins only if the view is "oil stalls," not "oil falls."

## 5. Expiry: about 36 days

Same 158/141 bear put spread, per spread, P&L vs the mid debit (Black-Scholes at each strike's IV):

| Expiry | Days | Debit | Reward:risk | Decay/day | Crack to 141 in 5 days | Flat for 20 days |
|---|---|---|---|---|---|---|
| 9/25 | 15 | $599 | 1.8 | −$12 | +$637 | −$599 |
| **10/16** | **36** | **$718** | **1.4** | **−$5** | **+$423** | **−$135** |
| 11/20 | 71 | $778 | 1.2 | −$2 | +$310 | −$57 |
| 12/18 | 99 | $837 | 1.0 | −$1.5 | +$264 | −$42 |
| 3/19/27 | 190 | $857 | 1.0 | −$0.6 | +$187 | −$40 |

- **Short-dated is a timing bet;** long-dated survives the wait but captures a third of a quick move
  at even-money payoff.
- **The war premium sits in the front months.** On 9/10, USO (front month) rose 5.6% vs USL (a
  12-month strip) 2.5%, so a de-escalation hits USO hardest and fastest.
- **In a steeply backwardated curve USO drifts up from the roll** even with spot flat, which works
  against multi-month shorts.
- **Choice: 10/16** (a month for the crack, survives the Monday off and weekend headlines, about $5 a
  day to wait). **11/20** if you expect a slow de-escalation. **9/25** only when entering on the
  red-day trigger itself. Work orders at mid; natural runs 6-14% above.

## 6. oquants volatility dashboard (USO, 9/10)

| Measure | Now | Mean | What it means |
|---|---|---|---|
| Implied vs trailing realized (30-day) | 60.6 | 18.6 | implied ~2.5σ rich; near-term realized ~31% vs implied ~62% |
| Volatility cone | above the 75th pct, all tenors | n/a | expensive, far below the 2020 max |
| Call skew | −11.8 | −2.4 | OTM calls unusually rich, all tenors to 90 days |
| Term structure slope (30/60) | −0.21 | 0.01 | backwardation, −1.5σ |
| Forward factor 30-60 / 90-180 | 0.15 / ~0.24 | 0.01 | only 90-180 clears their 0.20 threshold |
| 30-day short straddle backtest | avg +14.2%, win 67.7% | n/a | worst trade −455% |

IV rises with spot in USO (the reverse of stocks), so a crack down would likely come with falling
vol. That's a mild headwind for long puts, and another reason to use a spread. **oquants' own
frameworks lean the other way:** momentum plus rich call skew is their setup for a bullish call
vertical, and the forward factor flags a long calendar. This short is a contrarian fade.

## 7. The 90-180 day long calendar (forward factor)

Our chain reproduces the signal: Dec-18 vs Mar-19-2027 ATM IV 52.0% vs 47.7% implies a forward vol
of 42.6%, **FF +0.22**. Jan vs Mar is +0.20.

| Dec-18 / Mar-19 | Call calendar, K = 158 (neutral) | Put calendar, K = 141 (on the cover target) |
|---|---|---|
| Debit, mid / natural | $545 / $675 | $375 / $455 |
| oquants max debit (FF ≥ 0.20) | $593: passes at mid, fails at natural | $366: fails even at mid |
| OI front / back | 93 / 17 | 233 / 58 |

P&L per calendar at December expiry. "Market fwd" = the March leg ends at today's implied forward
vol; "de-escalation" = vol ×0.75. War persisting (vol ×1.2) improves every cell.

| USO in December | 135 | 141 | 158 | 170 | 185 |
|---|---|---|---|---|---|
| Call 158, market fwd | −$83 | +$109 | +$889 | +$442 | +$72 |
| Call 158, de-escalation | −$235 | −$71 | +$672 | +$235 | −$92 |
| Put 141, market fwd | +$414 | +$726 | +$155 | −$76 | −$237 |
| Put 141, de-escalation | +$236 | +$542 | −$4 | −$196 | −$309 |

- **The call 158 is a range bet** (USO ~140-180 in December with later vol holding). It's the only
  version that passes the debit rule, and only near mid.
- **The put 141 fits the bearish view** (a slow drift to ~141 while vol stays elevated), but it's too
  rich by their rule at mid.
- **It complements the bear put spread:** the spread wins on a fast crack, the put calendar on a
  slow grind. Both lose on a continued rally.
- **Cautions:** outside what oquants tested (their guide keeps the back leg under 100 days; their
  backtests stop at 60/90, and USO's 60-90 FF is only ~0.08). Our own FF replication isn't done, and
  our only calendar backtest (not FF-gated) was net-negative after costs. The back month is thin, so
  natural runs 20-25% over mid, and it's a 99-day hold through FOMC and the headlines.
- **If traded:** the 158 call calendar, filled at or near mid (≤ $5.93), sized small.

## 8. Checklist

1. **Before 08:30 ET Friday (CPI):** pull the IBKR report; `./start_alerts.sh` by 09:25.
2. **Only act on a red day.** A PARA alert confirms, but a genuine de-escalation headline is the real trigger.
3. **Preferred expression:** a USO 158/141 bear put spread, 10/16 expiry, entered at mid after the
   trigger, sized small. CVI shares or puts only on a break of 48.20 with a 50.27 stop. BWET small or
   skip; FRO as the follow-on.
4. **Weekend and the Monday off:** no share shorts over the weekend. A debit spread's max loss is known.
5. **Optional, separate:** the Dec/Mar 158 call calendar, only at ≤ $5.93.

## 9. Open items

- An event study on the liquid panel since 2019: after the first red day following ≥3 up days and
  ≥4 ADR over the 21 EMA, does the 10-day SMA come before the day's high? Until then PARA is untested.
- Replicate oquants' forward-factor calendar on options_daily_v3 with the house cost model (first in
  the oquants queue).
- Check BWET option open interest and spreads before relying on them.

## Sources
- [CNN: Global oil hits $105 per barrel and bond yields surge](https://www.cnn.com/2026/09/10/investing/oil-iran-war-diesel)
- [Bloomberg: Oil extends rally above $100 as Middle East hostilities escalate](https://www.bloomberg.com/news/articles/2026-09-10/latest-oil-market-news-and-analysis-for-sept-11)
- [Washington Times: Oil prices rise as Iran targets vessels in Strait of Hormuz; Houthis seize critical Yemeni port](https://www.washingtontimes.com/news/2026/sep/10/oil-prices-rise-iran-targets-vessels-strait-hormuz-houthis-seize/)
- [Al Jazeera: Oil prices surge as US-Iran strikes intensify in Strait of Hormuz](https://www.aljazeera.com/economy/2026/9/7/oil-prices-surge-as-us-iran-strikes-intensify-in-strait-of-hormuz)
- [CNBC: Shipping stocks hit decade highs as Hormuz disruption grinds on](https://www.cnbc.com/2026/09/03/shipping-hormuz-tankers-earnings-freight-rates-iran-trump-crude-china-stocks.html)
- [TT News: Surging tanker rates signal a deepening global energy crisis](https://www.ttnews.com/articles/surging-tanker-rates-energy)
- [Energy Connects: OPEC+ keeps output policy unchanged for October](https://www.energyconnects.com/news/oil/2026/september/opecplus-keeps-output-policy-unchanged-for-october)
- Market data: Tradier quotes/chains/history (9/10 close). Vendor dashboard: oquants.com/dashboard/volatility/USO (vendor data, not ours).
