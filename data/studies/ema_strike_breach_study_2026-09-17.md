# "More like CF + XLE": does the profile carry an edge? (stage one, 2026-09-17)

**Question.** Gabe called the CF 123/125 and XLE 61/62 bull put spreads (both expiring 9/18) successes and asked for more like them. Before pulling chains: is there anything in the *profile* of those entries, or were they ordinary wins?

**The profile (measured at the fill, per tranche; `journal_trades.trade_datetime` + Tradier 1-min underlying).**

| entry | spot | short put | IV | delta | cushion | spot vs 21 EMA | strike vs 21 EMA | credit/width |
|---|---|---|---|---|---|---|---|---|
| CF 9/1 12:27 x5 | 132.59 | 125P | 40.1% | -0.23 | 5.7% = 1.5 ADR | +1.9 ADR | +1.2% | 20% |
| XLE 8/31 14:37 x10 | 63.62 | 62P | 23.8% | -0.29 | 2.5% = 1.4 ADR | +2.0 ADR | +1.0% | 23% |
| XLE 9/3 11:11 x15 | 65.39 | 62P | 25.0% | -0.135 | 5.2% = 3.1 ADR | +3.0 ADR | -0.3% | 9% |

Common thread: a leader above its 50/200-day, within 7% of the 52-week high, extended 2-3 ADR over the 21 EMA, **short strike at the 21 EMA**, 15-18 DTE, held to expiry. IV was mid-range for both names (IBKR IV30: CF 62nd percentile of its year, XLE 47th; IV/RV 0.96 and 0.91) -- not a rich-vol sale.

**Test (`run_ema_strike_breach.py`, liquid panel 2019-01 -> 2026-09, 46,069 events, one per ticker per 12 sessions).** Breach = close 12 sessions later below the entry-day 21 EMA. Compared with (a) the name's own lognormal odds from RV20 and (b) a CONTROL: same names, any day, a strike the same distance below spot in ADR units. SEs from weekly means (348 weeks).

| cell | n | breach | model | edge (model - breach) | t |
|---|---|---|---|---|---|
| EVENT ext >= 1.5 ADR (cushion 2.0 ADR) | 46,069 | 18.3% | 21.2% | +2.2pp | 2.4 |
| CONTROL same cushion | 207,823 | 19.3% | 23.1% | **+3.7pp** | 4.1 |
| EVENT ext >= 2.5 (2.8 ADR) | 22,709 | 11.8% | 14.4% | +2.5pp | 3.3 |
| CONTROL | 214,233 | 12.4% | 14.5% | +2.0pp | 2.7 |
| EVENT ext >= 3.0 (3.3 ADR) | 13,890 | 9.3% | 12.3% | +3.2pp | 4.3 |
| CONTROL | 215,496 | 9.7% | 11.2% | +1.2pp | 1.8 |

Event by year (ext >= 1.5): every year +2.4 to +8.3pp **except 2022: breach 27.7% vs model 21.6%, -6.2pp** (also -5.0 / -1.5pp in the tighter buckets).

**Reading.**
1. The profile is not a selector. At the cushion the first CF and XLE entries actually used (~2 ADR) the extended-leader state breaches *no less* than any random day at the same cushion (edge +2.2 vs +3.7pp). Only at >= 3 ADR does the event beat its control, by ~2pp, untested for significance and tiny in credit (the XLE 9/3 tranche took 9% of width).
2. The "+2 to +4pp vs model" that shows up everywhere is the generic equity drift / short-put premium, not this setup. It is the same number the pooled studies already price: breach ~18% against a 20%-of-width credit is break-even before costs (median breach depth -3.2% is through a 1.5%-wide spread, so a breach is ~max loss). That reproduces the earlier results: unconditional ETF put spreads +0.6%/trade, paid-to-wait -3.3% net.
3. It fails 2022, like every unconditional put-selling rule in the book.
4. Touch rate is 2x the breach rate (39% vs 18%): any stop at the strike gets hit twice as often as the trade loses. Hold to expiry, as before.

**Verdict.** Three wins at an ~80% base rate are what the base rate predicts (0.8^3 = 51%). No chain pull is warranted for this profile. The put-spread conditions with evidence stay what they were: single names with own-IV >= 60th percentile and state != up/B+ (`paid_to_wait_study.md`), equity ETFs with VIX >= 25 above the 50-day (`etf_put_spread_study.md`). Neither was true of CF or XLE at entry.

**Caveats.** Panel universe = liquid as of 2026 (survivorship lifts both event and control equally). Model uses RV20, zero drift; real option-implied odds sit above it by the VRP, equally for event and control, so the *comparison* is unaffected. Stock-only: no fills, no costs.

**Open.** The profile above was reverse-engineered from the fills. If Gabe's actual reason for the trades was something else (energy/commodity theme in early September, the oil spike), that thesis is the thing to test, not this one.
