# Options With Davis — Knowledge Base

Archive of the **Options With Davis** YouTube channel (`UC8V7hO071gTZezX_YqF_YCw`).
Single creator ("Davis"), index-options income focus, aimed explicitly at **small accounts**.

Same deliverable pattern as `data/options_with_ryan/` and `data/theta_profits/`: an
**objective, skeptic-default write-up per strategy**, not per video.

## What the channel sells

Every video routes to a funnel: two free PDFs ("Options Income Blueprint", "Credit Spreads
Blueprint") and a **12-month paid mentorship program**. The framing is consistent income from
"one to two hours a day."

## Prime directive: skepticism (the index-income edition)

> **A high probability of profit is not an edge.** This channel's signature construct is a
> defined-risk index structure with a quoted POP in the 90s. POP is a *statement about the
> option chain*, not about expectancy — a structure that collects $5 on 94% of occasions and
> loses $880 on the other 6% is roughly break-even before costs, and the platform's POP number
> will still read 94%. For every claim, ask:
> - **What is the payoff at each outcome, weighted?** Not the win rate. "Win" often means
>   keeping a token net credit, not reaching the advertised max profit.
> - **Where is the DTE?** POP, max profit and theta are all meaningless without it, and it is
>   frequently unstated.
> - **Is there a backtest, a trade log, or any out-of-sample evidence?** So far: no. Content is
>   platform walkthroughs (strike selection in a broker's analyzer), not track records.
> - **Does the structure embed a negative-expectancy leg?** Long index puts carry the variance
>   risk premium against the buyer. Financing them with a credit spread does not make them free.
> - **Tail correlation.** Per-trade risk is defined, but the loss scenario is a market decline,
>   which hits every open position at once. "Defined risk" ≠ diversified risk.

Default conviction LOW until independently tested. Stay open — the mechanics are competently
explained and the vehicle choice (XSP) is genuinely well-argued for small accounts.

## Layout

```
README.md                    This file.
STRATEGIES.md                Index: strategy · conviction (0–5) · risk (1–10) · tested? · verdict.
strategies/<slug>.md         One objective write-up per SYSTEM.
videos/<type>/<date>_<id>/   transcript.txt · meta.json · notes.md
backtests/<slug>/            (on demand) scripts + results.
```

## Ingest

```bash
.venv/bin/python3 add_luk_video.py <url> --kb data/options_with_davis --type strategies
```

`--type` categories in use: `strategies`.

Transcripts are yt-dlp auto-captions. Davis speaks clearly and the captions are far cleaner
than the Luk livestreams — but **numbers and strike prices are unreliable** (decimal points
drift: "5:1" for 561, "$1.7" for $1.07, "$4.89" for $489). Verify any figure against the
on-screen option chain before using it. Ticker garbling is not an issue here; there are
almost no single-stock tickers.
