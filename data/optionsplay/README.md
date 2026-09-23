# OptionsPlay — knowledge base

Retail options education + platform (Tony Zhang, chief strategist). Webinars are teaching sessions that double as
demos of the OptionsPlay screener/strategy picker. Captions come down cleanly with yt-dlp (no interceptor needed).

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
