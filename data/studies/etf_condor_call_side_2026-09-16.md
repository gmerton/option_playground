# Does the 50%-take / no-stop rule generalise to the call side? (2026-09-16)

> **Answer: no, twice over.** (1) The exit rule that earns on the bull put spread earns **nothing on the
> bear call spread**, and the two sides are year-by-year mirror images — the put result is substantially
> directional beta, not premium harvesting. (2) The iron condor, which nets that direction out, has
> **no edge at all: +0.36%/trade, monthly t 0.60** once contaminated marks are removed.
>
> ⚠ **A first pass of this study reported the condor at +2.95%/trade, monthly t 2.19. That was wrong.**
> 2.4% of wings carried returns that are mathematically impossible for a credit spread, and they
> supplied ~87% of the apparent edge. Corrected below.

Script: `scratchpad/condor_test.py` -> `data/cache/etf_condor_recon.parquet`; scorer `scratchpad/condor_score.py`.

**Setup.** Identical to `etf_put_spread_exit_rule_2026-09-16.md` so the two are comparable: 20 ETFs from
`options_cache`, every Friday, 45 DTE (tol 5), 0.35Δ short / 0.25Δ long, take at 50% of the side's own
credit, **no stop**, each wing managed independently. ROC on margin = |short−long| − credit. Filters:
credit/width ≤ 0.50, margin ≥ 0.10, exit mark present, expiry ≤ 2026-03 (bid/ask cliff). 13,780 wings scored.

## 0. ⚠ The contaminated-mark filter this study needed

A credit spread's best possible outcome is keeping the **full** credit, so
`ROC_max = credit / margin = cw / (1 − cw)` where `cw = credit/width`. Anything above that implies a
**negative exit value**, i.e. the long leg marked richer than the short leg — impossible for a vertical
(the short strike is always the more valuable one), so it is a crossed or stale quote, not a trade.

| | Wings | Share |
|---|---|---|
| Exceeding the theoretical ceiling | 325 of 13,780 | **2.4%** |
| Their mean recorded ROC | +71% | vs ceiling median 35.1% |

Concentrated exactly where you would expect — thin names and small margins:

| Ticker | % bad | | Margin | % bad |
|---|---|---|---|---|
| INDA | 9.3 | | < 0.50 | 5.2 |
| ASHR | 6.1 | | 0.50–1 | 2.7 |
| XLU | 5.5 | | 1–2 | 2.3 |
| XLP | 5.0 | | 2–5 | 1.3 |
| USO | 3.8 | | > 5 | 0.4 |

**The existing `credit/width ≤ 0.50` and `margin ≥ 0.10` filters do NOT catch this.** These wings pass
both. The ceiling test is the one that works, and it belongs in every credit-spread engine.

## 1. The rule is put-specific (contaminated wings removed)

| Side | n | ROC/trade | Weekly t | Monthly t |
|---|---|---|---|---|
| **Put** | 6,744 | **+5.70%** | 4.87 | 3.13 |
| **Call** | 6,711 | **−2.66%** | −2.09 | −1.21 |

Gap rates in exit marks are symmetric (call 7.1% missing, put 7.7%), so excluding those does not bias
the comparison. That was the pre-registered check; it passes.

## 2. The two sides are mirror images -> the put result is largely beta

Pre-correction yearly means, which show the pattern most clearly: the put side earns +11.3 / +11.6 /
+13.6 / +19.5 in 2019 / 2020 / 2024 / 2025 and loses in 2018 and 2022; the call side earns +7.8 and
+4.7 in those two down years and loses 13.9 and 10.0 in 2019 and 2020. **The bull put spread is a
bullish vehicle, not a premium harvest.** The 50% take contributes; direction does the heavy lifting.
This weakens the two-sleeve pair story — that sleeve carries equity beta rather than diversifying it.

## 3. The condor has no edge

Both wings on the same ticker-Friday, each taken at 50% of its own credit; margin = the larger wing.

| Version | n | ROC | Weekly t | Monthly t | Yrs + |
|---|---|---|---|---|---|
| As first reported (contaminated) | 6,207 | +2.95% | 3.38 | 2.19 | 6/9 |
| **Corrected** | 5,983 | **+0.36%** | **1.19** | **0.60** | 5/9 |

By year (corrected): 2018 +1.0, 2019 −4.3, 2020 −2.4, 2021 +2.8, 2022 −5.8, 2023 −1.9, 2024 +5.5,
2025 +9.0, 2026 +38.0 (n=38, ignore). Excluding the 38-trade 2026 stub the mean is ≈ +0.5%.

**Removing the direction removes the edge.** That is the whole finding.

## 4. The chop conditioning does not survive either

The pre-correction chop cut looked strong (condor +10.59% in chop vs +1.97% elsewhere). It rests on the
same contaminated wings, and separately **2022 contains ZERO chop days**, so the best-looking cell
excluded the one grinding bear market in the sample. Not rehabilitated; not pursued.

## Reading

**Closed. Do not pursue the condor.** The direction-neutral structure earns +0.36%/trade at monthly
t 0.60. The honest surviving fact is a negative one about a strategy we already hold: the ETF bull put
spread's headline is substantially long-beta, and its corrected mean on this run is +5.70% rather than
the +6.92% in `etf_put_spread_exit_rule_2026-09-16.md`, which used the insufficient filters.

**Action items this creates:**
1. Re-score `etf_put_spread_exit_rule_2026-09-16.md` with the ROC-ceiling filter (§0).
2. Add the ceiling test to `put_spread_study.py` / `call_spread_study.py` so it cannot recur.
3. Re-examine any prior credit-spread result that leaned on thin names (INDA, ASHR, XLU, XLP, USO).
