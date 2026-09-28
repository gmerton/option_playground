# Gap Up Day Trading Strategy Crash Course (Humbled Trader)

**Video:** `9BVf72n8p8Y` · 65 min · published 2023-08-10 · reviewed 2026-09-28 · auto-captions

> **2/5 · one NEW axis (single-name gap-down buy after a strong prior day), not queued.** Five gap setups on large caps,
> each shown as one hindsight chart plus one recorded live trade, all five closed green: winners only, no n, no win
> rate. Credit where due: she restricts to large caps (inside our panel), writes the criteria down, and admits the PANW
> mismanagement. But the setups that make a mechanical return claim are the ones the ledger has already measured, and
> they fail: catalyst-gap buys, pre-market-high breaks, VWAP-rejection shorts. The one that agrees, shorting a gap-up in
> a downtrending "bag holder" chart, is our PARKED gap-fade result: cost-fragile and not yet certified.

## Setups as stated

| # | @ | setup | criteria / entry / stop / target |
|---|---|---|---|
| 1 | 04:12 | **Gap-up long** | large cap [03:10]; gap "over the key daily resistance", ideally a 52-wk high (SHOP) [05:15, 10:28]; positive catalyst, earnings beat [06:17]; don't buy pre-market, "wait for the open" [06:17]; enter on a dip to the level ("50 cents risk") or over the pre-market high [08:22]; stop = a break of the 5-min VWAP [11:31]; targets = the next daily resistance, can be played "for multiple days after" [10:28] |
| 2 | 18:55 | **Gap-down short** | mirror of #1: bad earnings, a break of daily support / 52-wk low (PYPL) [20:01]; short "little bounces towards VWAP", VWAP is the risk [21:06] |
| 3 | 27:30 | **Gap-up short ("bag holder")** | three criteria [30:40]: a "long-term downtrending chart", a pre-market gap up, and "gapping up on air, basically gapping up on nothing" (no news); trigger = break of the pre-market support, stop = the pre-market high, targets = daily supports, 1:1 minimum [29:36]; add on "confirmation of weakness", not strength [33:50] |
| 4 | 39:06 | **Gap-down long scalp** | four criteria [40:09–41:12]: large cap only ("does not work for small caps or micro floats"); a "really strong breakout the previous day"; a pre-market gap down; high pre-market volume (">1M shares", not "20,000") [41:12]; buy a daily support zone at the open, ~$0.40–1 risk, target the pre-market high, 1:2 to 1:4, hold "15–30 minutes", "hit it and leave it" [41:12–44:19] |
| 5 | 49:33 | **Pre-market gap-up short** (bonus) | as #3 but traded pre-market; "really risky"; size down to 1/10 on low volume and wide spreads; beware positive news [63:17] |

Exit rule she repeats: scale out into daily resistance [14:40] and "don't outstay your welcome" [64:21].

## Evidence offered

Five live trades, all winners: PANW long +$300 (was +$5k unrealised, "I didn't sell into those resistance areas")
[16:49]; MRNA short +$800 [25:23]; CVNA short +$1,100 [38:02]; TSLA long +$1,400 [48:29]; FCNCA pre-market short
+$9,400 [62:14]. SHOP and PYPL are hindsight charts. No sample, no losers, no costs; sponsor read (Moomoo) [16:49].
FCNCA breaks her own #3 rule (big positive news), as she admits. Evidence class = single-trade post-mortem
(`data/mari_trades/README.md`): execution realism only, never selection.

## Claims vs ledger

| claim | verdict | ledger |
|---|---|---|
| Earnings-gap long over a 52-wk high / key resistance (#1) | **CONTRADICTED** | EP base-break [WL-5d] NULL: "the long-base condition adds nothing", neither arm beats its timing control; DR-EP arm A buy-the-catalyst-day −0.173R t −4.70; PEAD NULL |
| Enter over the pre-market high / opening level | **CONTRADICTED** | ORB9 INVERTED −0.425pp vs a random minute, t −8.50; index ORB [WL-5a] NULL; Stage A: a random later minute ≈ trigger; level triggers NULL 0/12 |
| Short the VWAP bounce / VWAP as the stop (#2, #3) | **CONTRADICTED** | VWAP double-rejection short FAIL, 2nd touch −0.26R t −6.2, worse than a random minute; FBO INVERTED, retired |
| Gap-down short after earnings through a 52-wk low (#2) | **CONTRADICTED (partial)** | short-selectable universe NULL 0/10 (weak names still drift up); failed-retest breakdown short NULL; PEAD NULL. The 52-wk-low × earnings-gap cell itself is untested, low prior |
| Gap-up short in a downtrending chart (#3) | **AGREES, not certified** | Weak-market gap-up fade: PRIMARY PASS, cost-fragile, PARKED; +0.54% t 3.87, but "breadth NOT shown to matter: it's the stock's own down-cycle"; +20 bp/side → gone. Forward breadth-free holdout runs from 2026-09-28 |
| "Gapping on nothing" (no-news gate) | **UNTESTED** | No-news veto on fades, §10: needs a news field; [WL-5j] forward LLM catalyst classification queued |
| Gap-down long after a strong prior day (#4) | **UNTESTED on single names** | Index only: Carter opening-gap fade after a ≥1 ATR move +11.9 bp t 6.5 (SPY/QQQ/IWM/DIA, `carter_mastering_the_trade/SETUPS.md`); unconditional fade ≈ flat. Per-name gap-down reclaim affinity NULL (a rate, not a P&L) |
| Scale out into resistance | **CONTRADICTED** | Qullamaggie partial INVERTED −1.87pp t −4.39; trims −0.25…−0.33R (profit-lock study) |
| Large caps only, not small caps / floats | **UNTESTED (blind spot)** | Our panels need ADDV ≥ $50M; float as a universe variable queued (Cameron) |

## New test? Yes, one axis the ledger has not covered

**Single-name gap-down buy after a strong prior day.** The index version was positive and the veto ran backwards
(Carter), but we never carried it to single names. *Pre-register:* liquid_panel_2009, 2010-26. Day −1 = close ≥ 1.5
ADR above its open *and* a 20-session closing high. Day 0 = open ≤ prior close − 1.0 ADR. PRIMARY = buy the open, sell
the close, net 10 bp/side, % return. **Control holding the gap fixed:** same-date gap-downs of matched size (ADR bucket)
in names *without* the strong day −1, paired by date, date-clustered t; the difference is the claim. Secondary (1-min
Polygon backfill, ~1,700 names, 2024-10 → 2026-09 only): exit at 10:00 vs the same name-day's random later minute.
Charge 2 cells (Šidák). Bar: |t| ≥ 3, both halves same sign, per-year check, and still positive at +20 bp/side (the
gap-up fade died there). *Data:* the daily cell is supportable. Her pre-market-volume gate is not (no pre-market volume;
full-day RVOL leaks the future), so it is dropped, stated. 1-min power ≈ 2 years. Priority low-to-medium: costs are
the likely killer.
