# TraderLion — Setup Index

Skeptic-default leaderboard of setups from the TraderLion channel.
Conviction 0–5 (independently-earned confidence, LOW until tested) · Risk 1–10 · Tested? no/partial/yes.
Convention and the channel-specific skeptic mandate: [README.md](README.md).

| Setup | Trader(s) | Instrument | Conviction | Risk | Tested? | One-line verdict |
|-------|-----------|-----------|:---------:|:----:|:------:|------------------|
| [VCP "Low-Risk Entry"](setups/minervini_vcp_low_risk_entry.md) | Mark Ritchie II · Brandon Hedgepath · Bob Weissman (Minervini Private Access) | US equities | 2.5/5 | 5/10 | **partial** | **Entry side ≈ what the repo already runs, and independently supported by our own 20y test** (volume-confirmed breakouts +0.86pp/63d at RVOL≥1.8; all breakouts pooled are NEGATIVE). Title is oversell — "$20M from $100K with **only one setup**" is 2 traders / 15 yrs / no denominator, and they describe **six** entry variants. Winners-only (9 case studies, 0 losers — they admit it), and every differentiator (RPR, "FAB Five", trend-stage, extension alerts) is **proprietary/untestable**. ⭐ The real value is the **exit framework** — sell ⅓ into strength at ~+20% to "finance the risk," ratcheted "backstop" under a gap low, final piece on a 50-day close — which fills a known gap in this repo and is directly backtestable. |
| [Covered Calls & Cash-Secured Puts (BCI)](setups/bci_covered_calls_cash_secured_puts.md) | Alan Ellman (Blue Collar Investor) | US stocks + options (short premium) | 1/5 | 6/10 | **yes** | **Tested 2026-09-17 on 326 names / 8 yrs of real bid/ask: the put ≈ holding the stock at the same delta, minus costs** (weekly +0.03%/trade vs +0.07%, excess t −1.7; ~0 even at perfect mid fills). **His public filters add nothing** (weekly book −1.4%/yr with them vs +1.2% without vs SPY +10.5%). Selling *through* earnings earned more, so the no-earnings rule shapes risk, not return. ITM covered call = short put (parity); 4 winners / 0 losers on camera, 2 contradicted by prices. Untested: paywalled stock list and exits. |
| [Wedge Pop (cycle of price action)](setups/kell_wedge_pop.md) | Oliver Kell (2020 USIC) | US equities | 2/5 | 6/10 | no | **Most objective setup in this KB, zero evidence.** 10/20 EMA state + weekly filter; trigger = close above a tight mini-base's swing high after a higher low, **explicitly not the MA cross** [01:01]. That claim has a built-in same-date control (reclaim with vs without the structure). Loose cousin = reclaim arm, t 1.84-2.69, below the bar. EMA crossback = pullback-entry FAIL; RS during the correction = down-day RS INVERTED; selling exhaustion extensions = tighten INVERTED. Codable spec + pattern_test design written (NOT RUN). ⚠ he sizes 30-35% in one name |
| [High Tight Flag](setups/soreide_high_tight_flag.md) | Leif Soreide (2019 USIC) | US equities | 1.5/5 | 7/10 | no | **Clean definition, no evidence, headline numbers not in the videos** ("90%+ winners" = the 90% pole; "+222% in 27 days" never said). Pole >= 90% in <= 8 wks, flag 3-5 wks, depth <= ~25%, volume dry-up, volume pivot. Management (scale 1-3R, sell 100%, pyramid) contradicted/NULL. ⭐ His early low-volume inside-day entry buys *below* the flag high. Rare -> count first; UNDERPOWERED likely on the 2019 liquid panel. Spec + design written (NOT RUN) |
| [CAN SLIM Leader Screen](setups/haber_canslim_screen.md) | Ross Haber (ex-O'Neil) | US equities (universe) | 2/5 | 4/10 | **partial** | **Screen, not an entry.** RS12-sorted broad screens, then by eye for tight/orderly (ADR 2-4%), then CAN SLIM fundamentals (EPS YoY >=25% x3 quarters, accelerating, sales confirm). Technical half already answered here: RS12 = TT c9 UNDERPOWERED; low ADR contradicted (HYB-B ADR>=4 best); group confirmation NULL; "outperform in corrections" ~ down-day RS INVERTED. ⭐ EPS growth never tested here, codable on cached yfinance EPS. INT ^ C vs INT spec written (NOT RUN, ~1/2 day) |

---

## Highest-value open test

**Exit-policy bake-off** (spec in §10 of the write-up): hold-to-50-day vs sell-⅓-at-+20% vs
laddered scale-out vs +time-stop, over RVOL≥1.8 breakouts on the 299-name / 2006–2026 panel,
scored on **return per unit of risk**. Tests whether "financing the risk" improves risk-adjusted
return or just truncates winners.

## Channel notes

- Guests are usually **educators selling a service**, not anonymous traders. The methodology is
  typically sound; the *evidence* and the *differentiation* are where the problems live.
- ⚠ Auto-captions mangle tickers and figures. Seen here: "DCP"→VCP, "three-quarters of a
  billion"→million, "DFW"→Deepvue, "Mervini/Menervini/Manini"→Minervini.
