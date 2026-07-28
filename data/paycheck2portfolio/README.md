# Paycheck To Portfolio — Knowledge Base

An archive + objective review of the **Paycheck To Portfolio** YouTube channel
(`@Paycheck2Portfolio`, channel `UCqweTiFXT0z9FcURR55RcRg`). Sibling to
`data/theta_profits/` and `data/martin_luk/`.

**How this channel differs from Theta Profits:** it is **one creator** documenting **one
coherent system**, not many traders each pitching a distinct options strategy. The system, as
presented across ~97 videos, is a **leveraged income-investing / FIRE approach**: invest the
whole paycheck into high-distribution *income ETFs*, use **margin** as leverage, and "live out
of the brokerage account" so that "the portfolio pays the bills" instead of the paycheck. A
weekly **"Spark to FIRE"** series journals the real-money portfolio.

So the unit of value here is **the claims/mechanics of that system**, not per-trade setups. The
deliverable is an **objective** assessment of whether the approach does what it says, and where
the risks the creator downplays actually live.

## Prime directive: skepticism (same mandate, different domain)

> **Creators oversell — income/FIRE creators especially.** The pitch here is emotional
> ("freedom," "my portfolio pays my bills," "fire your job") and the numbers are shown in a
> benign, recent, mostly-bull tape. The job is NOT to relay the pitch — it's to **separate the
> mechanics from the marketing**, name the real risks glossed over, and flag claims that are
> unverifiable or regime-dependent. Default conviction LOW until independently checked. Stay
> open — a disciplined leveraged-income plan *can* work for the right person — but demand the
> total-return math, not the yield headline.

### Red-flag checklist (domain-specific — call these out explicitly)
- **Yield ≠ total return.** High-distribution ETFs (YieldMax single-stock, covered-call funds,
  return-of-capital funds) often pay distributions that are partly **return of your own
  capital** → NAV erodes. "Income" can be principal handed back to you. Always convert to
  **total return** (price change + distributions), and check **NAV trend** and the fund's
  **ROC %** in the 19a-1 notices.
- **Distribution sustainability.** A 30–100% "yield" is not free money — covered-call/option-
  income ETFs **cap upside** and can **bleed NAV** in choppy or down markets; the distribution
  can be cut.
- **Margin / leverage amplifies BOTH directions.** "I don't fear margin" ignores **margin
  calls / forced liquidation at the bottom** and **sequence-of-returns risk**. Borrowing to buy
  high-volatility income ETFs is a **leveraged carry trade** — it only works while asset total
  return reliably exceeds the borrow rate, and it blows up in a sustained drawdown.
- **"Debt builds cash flow" / "borrowed money pays my bills."** True only if the spread
  (asset return − margin interest) stays positive through a full cycle; presented as a free
  lunch, it is a **positive-carry bet that is short volatility**.
- **"Living off the brokerage account."** Sustainable only if total return ≥ withdrawals +
  borrow cost across regimes. In a bull tape anything works → **survivorship / regime bias**.
  The real test is a sustained bear (2022, 2000–02, 2008) — usually absent from the sample.
- **No emergency fund.** Relies on margin/portfolio liquidity being available **exactly when
  markets are down** — i.e. when it is least available and most expensive.
- **Short / benign track record.** "Spark to FIRE — Week N" = N weeks of a recent, mostly-up
  market. Not a cycle.
- **Tax drag ignored.** Large distributions are often **ordinary income**; margin interest and
  turnover erode the net.
- **Sales / affiliate motive.** Income-ETF affiliate links, Patreon/Discord, course, brokerage
  referral — note it.

## Layout
```
README.md                 This file — convention + skeptic mandate.
REVIEWS.md                Index / leaderboard of reviews (format TBD — see "Open decision").
reviews/<slug>.md         One objective write-up per review unit (the deliverable).
videos/<date>_<id>/        transcript.txt · meta.json · notes.md  (ingested per video).
channel_videos.txt        Full 97-video list, [x]=reviewed / [ ]=not.
backtests/<slug>/          (created on demand) test scripts + results (e.g. income-ETF total-return / margin-survival sims).
```

## Open decision (review unit) — pending
This channel is single-creator and thematically repetitive (many videos restate the same
system), so per-video reviews like Theta Profits would be low-value and duplicative. Candidate
units: **(a) per-theme/claim** (margin, income-ETF selection, "live off brokerage," no-emergency-
fund, etc.) with videos as evidence; **(b) per-video** for the substantive ones only; **(c)
hybrid** — one "system overview" review + a handful of per-claim deep-dives. To be confirmed
before writing reviews.

## Workflow
1. Ingest a video: `.venv/bin/python3 add_luk_video.py <url> --kb data/paycheck2portfolio`
2. Write the objective review into `reviews/<slug>.md`; add a row to `REVIEWS.md`.
3. **On Gabe's command only**, evaluate (e.g. total-return vs the yield claim, a margin
   survival-through-2022 sim) under `backtests/<slug>/`, and update the verdict with evidence.
