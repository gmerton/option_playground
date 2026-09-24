# OptionsPlay — knowledge base

Retail options education + platform (Tony Zhang, chief strategist). Webinars are teaching sessions that double as
demos of the OptionsPlay screener/strategy picker. Captions come down cleanly with yt-dlp (no interceptor needed).

**Channel index:** `index/` (827 videos, tiered for review, 2026-09-24). See `index/README.md`.

`videos/<date>_<id>/` holds `transcript.txt`, `meta.json`, `notes.md` (the scored review).

⚠ **Caption trap (found 2026-09-22 on `pQlGgcyrUoQ`):** some videos here default to an `en` auto-caption track that
is a machine *translation* round-tripped through a dub — it renders thinkorswim as "Thinker Swim" and "gamma
explosions" as "gamma-ray bursts". **Check `--list-subs` for `en-orig` and pull that** before quoting anything.

| video | date | verdict |
|---|---|---|
| [The ONLY #1 Options Strategy You May Need with Tom Sosnoff](2024-10-14_sosnoff_interview_review.md) | 2024-10-14 | **3/5** — the full-context answer to the More Tom clips: specification improves hugely (a complete, executable 45-DTE/20Δ strangle rule + a live auditable trade), **evidence does not improve at all** (not one test statistic in 60 min; the flagship 21-DTE rule is offered as "theoretical"). ⭐ He denies cross-sectional edge outright — true *within* a name (our ARM B null), false *across* names, where this channel's own credit/width ranker beats him (+8.57pp, t 3.74), unchallenged by the host |
| [The Three Filters That Make a Credit Spread Worth Trading](videos/2026-07-25_YfrZT_kTo_4/notes.md) | 2026-07-25 | **3.5/5** — best creator score to date: his liquidity filter and his warning against 90%-win spreads match our cost work, and **ranking by premium-to-width PASSES on our quotes** (+7.6pp within-date, t 4.15) — though dialling it with your own wing buys nothing |
| [Why You're Selling Winning Stocks Too Early](videos/2026-09-05_iXOULnIGEKk/notes.md) | 2026-09-05 | **2.5/5** — diagnosis matches our exit findings exactly; the cure (add to winners) is our NULL pyramid test, and his "30–40% of breakouts fail" is 76% on our pool |
| [What Volatility Is Actually Telling You](videos/2026-09-11_lV8Jkl37h4M/notes.md) | 2026-09-11 | **2.5/5** — the volatility facts are right and match our own measurements; every actionable rule is mid-price reasoning with no costs and no test statistic, and one (debit spread beats the outright) is contradicted by our own test |
| [Finding the Optimal Credit Spreads](videos/2020-10-08_bk9Co7V6AI4/notes.md) | 2020-10-08 | **3/5** — the ranker's origin, but his rule is a **0.33 hard floor at 50Δ/25Δ, 45 DTE, managed**, not the 30Δ/20Δ quintile sort we tested (only 0.07% of our real-fill spreads reach 0.33). IV rank >50 and the 2×-credit stop both CONTRADICTED |
| [How to Trade Credit Spreads for An EDGE (Dan Passarelli)](videos/2022-02-10_gUOWa-i4R70/notes.md) | 2022-02-10 | **2/5** — short strike at support, narrowest width, exit on the strike cross: narrowest wing −0.04% vs +2.7–3.1% wider; stop family CONTRADICTED |
| [Credit Spread Income Strategy w/ NDX Weekly Index Options](videos/2018-09-16_2VzqGw2_ZFs/notes.md) | 2018-09-16 | **2.5/5** — oversold index put sale agrees in direction with the certified cell, but VIX does the work, not the stochastic; overbought bear call CONTRADICTED (−2.66%) |
| [How to Choose the BEST Stocks for Covered Calls Trading](videos/2025-02-17_n1T3PUyS4uQ/notes.md) | 2025-02-17 | **2.5/5** — "don't avoid earnings" AGREES (BCI t +3.6); trend + RS + high-IVR stock selection CONTRADICTED / unsupported |
| [How to Manage Losing Credit Spread](videos/2025-05-04_m2-bo0kxMu0/notes.md) | 2025-05-04 | **2.5/5** — settlement mechanics right (the $625k Biogen after-hours exercise); 2×-credit stop CONTRADICTED (−4.3%/trade, t −5.4); fills at mid CONTRADICTED |
| [Lose MORE than your Max Loss on a Credit Spread](videos/2021-03-19_p477UMpfVxI/notes.md) | 2021-03-19 | **2.5/5** — accurate pin/assignment mechanics, no edge claim |
| [How to Screen Both Legs of the Wheel Before You Trade](videos/2026-08-01_VSLc-kHxFlw/notes.md) | 2026-08-01 | **2/5** — CSP = "a paid limit order": CONTRADICTED (BCI: vs delta-matched stock −0.06%, t −1.8; book +1.2% CAGR vs SPY +10.5%) |
| [How to Trade Credit Spreads After Earnings (Brian Overby)](videos/2026-02-15_Uvk_no85Yj4/notes.md) | 2026-02-15 | **2/5** — sell after the print CONTRADICTED; it also collides with his own 33% floor, since post-print IV crush makes credit/width low |
| [Generating Income with Index Options using Iron Condors](videos/2022-10-07_5IvhBIQVujs/notes.md) | 2022-10-07 | **2/5** — VRP AGREES; "high IV makes condors work" PARTIAL (only SPX bearish-high-IV certifies) |
| [Stop Buying Options. Get Paid to Wait Instead.](videos/2026-04-11_jLUPi1Im9cw/notes.md) | 2026-04-11 | **1.5/5** — macro commentary plus five live trades; QQQ/TLT call spreads CONTRADICTED |
| [Why the Options Market Is Always Wrong About Volatility](videos/2026-09-19_wG0yvxmDuXI/notes.md) | 2026-09-19 | **2.5/5** — ⚠ a re-edit of lV8Jkl37h4M; "always over-estimates" holds at 10 d, only t 2.08 at his 30-d tenor with 3 of 17 negative years |
