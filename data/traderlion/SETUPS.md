# TraderLion — Setup Index

Skeptic-default leaderboard of setups from the TraderLion channel.
Conviction 0–5 (independently-earned confidence, LOW until tested) · Risk 1–10 · Tested? no/partial/yes.
Convention and the channel-specific skeptic mandate: [README.md](README.md).

| Setup | Trader(s) | Instrument | Conviction | Risk | Tested? | One-line verdict |
|-------|-----------|-----------|:---------:|:----:|:------:|------------------|
| [VCP "Low-Risk Entry"](setups/minervini_vcp_low_risk_entry.md) | Mark Ritchie II · Brandon Hedgepath · Bob Weissman (Minervini Private Access) | US equities | 2.5/5 | 5/10 | **partial** | **Entry side ≈ what the repo already runs, and independently supported by our own 20y test** (volume-confirmed breakouts +0.86pp/63d at RVOL≥1.8; all breakouts pooled are NEGATIVE). Title is oversell — "$20M from $100K with **only one setup**" is 2 traders / 15 yrs / no denominator, and they describe **six** entry variants. Winners-only (9 case studies, 0 losers — they admit it), and every differentiator (RPR, "FAB Five", trend-stage, extension alerts) is **proprietary/untestable**. ⭐ The real value is the **exit framework** — sell ⅓ into strength at ~+20% to "finance the risk," ratcheted "backstop" under a gap low, final piece on a 50-day close — which fills a known gap in this repo and is directly backtestable. |
| [Covered Calls & Cash-Secured Puts (BCI)](setups/bci_covered_calls_cash_secured_puts.md) | Alan Ellman (Blue Collar Investor) | US stocks + options (short premium) | 1/5 | 6/10 | **yes** | **Tested 2026-09-17 on 326 names / 8 yrs of real bid/ask: the put ≈ holding the stock at the same delta, minus costs** (weekly +0.03%/trade vs +0.07%, excess t −1.7; ~0 even at perfect mid fills). **His public filters add nothing** (weekly book −1.4%/yr with them vs +1.2% without vs SPY +10.5%). Selling *through* earnings earned more, so the no-earnings rule shapes risk, not return. ITM covered call = short put (parity); 4 winners / 0 losers on camera, 2 contradicted by prices. Untested: paywalled stock list and exits. |

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
