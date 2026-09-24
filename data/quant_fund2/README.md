# Ney Torres H / "Quant Fund 2 Research" (Substack) — reviews

Skeptic-default reviews of pasted articles (2026-09-24). Author sells a quant "clinic"; every post carries
"Hypothetical examples for illustration", so quoted figures are not verifiable results.

## 1. "How Quants Know a Momentum Trade Is About to Crash" (Jun 29) — 2.5/5, no test
Summary of Lou & Polk, *Comomentum* (RFS 2022, genuine): residual correlation among momentum winners/losers after
stripping market/industry/factors = arbitrage crowding; high readings precede weak momentum over 1–2 years. The
article's own figures are "illustrative" (12.7% / 8.4% vs 22.5% not verifiable here). **Fit:** a 1–2-year factor-regime
signal vs our days-to-weeks breakouts; our ledger says regime forecasting fails (breakout regime feedback, activity
gate PARKED); 2010–26 holds ~3–4 independent crowded episodes → underpowered; survivor panel drops the crash names.
**Only new adaptation (not queued, low prior):** 60-day residual correlation among current breakout names as a
20–60-day crowding gauge for the precision tier.

## 2. "The Screener That Wasn't Redundant" (Jun 4) — 2.5/5 (method 3, evidence 2), no test
Removing a top-150-by-2-year-return pre-filter let "wreckage bounces" into a Novy-Marx top-20 momentum book (MaxDD
−65% → −96%). **Right lesson:** a filter that looks redundant can be doing a different job — measure before deleting
(what we did for the 52wk-range gate: 11 of 671,700 name-days). **Weak evidence:** one backtest per config, Sharpe
0.74 / 0.81 / 0.68 all inside ±0.2 SE over 22 years; drawdown hinges on 2008–09; mechanism description muddled;
no costs shown. **Already answered here:** crash-leader veto; gate ablation (52wk-high gate kept, excluded set
−1.20%/trade); beaten-down rules NULL; the precision tier's stack + near-high gates are our "quality gate".

## 3. "How Big Is Your Tradable Universe?" (Jun 1) — 3/5, no test
Correct engineering: filter on DOLLAR volume, not shares (we do: ADDV ≥ $50M); size positions to ≤ 0.5–1% of ADV;
rank wide, hold narrow; cache data, hit the broker only to execute. **Unsupported:** "top 20 of 3,000 = sharper,
free signal" — his OWN follow-up (#2) shows the wider pool brings junk; our Trend Template ablation found the $200M
ADDV criterion the largest ADDER (dropping it −0.26pp), i.e. more liquidity helped, not less. **For Gabe:** at his
position sizes the $50M floor is far stricter than a 0.5%-of-ADV rule needs (a $10k position needs ~$2M ADDV), so a
lower floor is operationally fine — but whether $5–50M names help the breakout book is untested and DATA-BLOCKED
(the liquid panel is built at the $50M floor; same small-cap blocker as the dilution fade / Mari). **Data lead:** he
uses a survivorship-free 24-year US database from Financial Modeling Prep (~11,700 symbols) — a candidate source for
the blocked value + quality test (#3); check price and point-in-time fundamentals before choosing it over Polygon/Sharadar.
