# VIX Crash Hedge ("VIX hedging strategy" / double vertical spread) — AJ Brown

Source: `2026-02-08_UM_Q5xiYGNw` — "This VIX Trade Breaks Even Most of the Time — And Wins Big
in Crashes" ([watch](https://www.youtube.com/watch?v=UM_Q5xiYGNw)). Guest: **AJ Brown**, founder
of *Trading Trainer* (a paid options-education company, est. 2003; trading options since 1997),
self-described "end-of-day trader"; host: John. Unusually for this channel, this is **not** a
short-premium income trade — it's a **long-volatility / portfolio crash hedge**, so the skeptic
lens flips: the danger here is not a blowup but **slow carry/commission bleed**, a **capped crash
payoff sold as uncapped**, and an **under-acknowledged downside** when VIX collapses.

## Verdict

> **Conviction: 2 / 5 · Risk (carry/drag): 3 / 10 · Tested: NO (partially testable)**
> The *concept* is legitimate and genuinely complements an equity/income book: a cheap,
> defined-risk long-VIX position, **entered when VIX is low**, whose debit leg is **financed by a
> credit leg** so net carry is ~flat in calm times and pays off on a fear spike. That financed-hedge
> idea is sound and is the real diamond here. But the **specific structure undercuts its own pitch**:
> it is built from **$1-wide verticals, so the crash payoff is CAPPED at the spread widths** — a VIX
> move from 15→80 is monetized almost identically to 15→20. The advertised "5x / 10x / 20x" is a
> multiple on a **near-zero cost basis**, not on risk capital; the **absolute** dollars are small and
> capped, while the **max loss (VIX collapsing below the lower strike) is comparable in size** and can
> hit the full 20%-of-portfolio he allocates. No separable track record (10 yrs claimed, winners-only
> anecdotes). And the VIX-specific mechanics he glosses — options priced off **VIX futures, not spot**;
> European, cash-settled at the **VRO** open-auction; term-structure/backwardation muting a spike —
> can make the "grab almost all the profit on a spike" exit materially worse than the spot-VIX chart
> implies. A real tail hedge wants **uncapped** convexity; this caps itself. Sound idea, compromised
> instrument.

## Mechanics

- **Underlying: VIX options directly** (not SPX/equity options). He stresses VIX's quirks: weekly
  expirations land on **Wednesdays**, not Fridays; "often a lot of liquidity… you can do the
  weeklies." `@11:49`, `@12:14`
- **Structure — "double vertical spread" = a debit vertical offset by a credit vertical**, both on
  VIX, legged in: `@10:38`, `@10:51`
  - **Debit spread, placed BELOW current VIX (the "bottom trade"):** a **$1-wide call debit spread**
    (long lower call / short next call). His live example: **14.50 / 15.50** strikes, cost **70–90¢**
    (he paid **83¢**). Worth its full **$1** if VIX expires above the short strike. `@13:20`, `@13:38`
  - **Credit spread, placed ABOVE current VIX:** a **$1-wide put credit spread (bull put)** whose
    strikes sit above the current VIX, so it opens essentially at max loss (deep ITM puts) and **flips
    to its full credit if VIX rises above its strikes**. He collected **87¢**. Carries a **margin
    requirement** (width − credit ≈ small), which he says "the rest of the portfolio covers." `@14:08`,
    `@14:24`, `@14:38`, `@15:04`
  - **Net at open:** he targets the credit a **few pennies above** the debit, opening for a small **net
    credit** (in the example **+4¢**) so the position pays for its own commissions. `@14:24`, `@16:12`
- **Resulting payoff shape (combine the two $1-wide legs):**
  - **Wide middle plateau ≈ break-even** — debit spread at +$1, credit spread at −$1, net ≈ the small
    open credit. This is the most likely outcome. `@15:30`, `@15:59`
  - **VIX spikes up → max profit**, capped at roughly the sum of the spread widths (~$1–2). He closes
    **early** on the spike. `@16:39`, `@16:52`
  - **VIX collapses below the lower (debit) strike → max loss:** both legs go worthless / max-loss and
    the **allocated portfolio chunk is at risk**. `@28:39`, `@29:09`
- **DTE:** **2–4 weeks** (would say 3–5 weeks in a calmer 2024; shorter now because "events are
  coming"). `@12:26`, `@21:21`, `@21:36`
- **Entry timing (semi-mechanical):** enter when **VIX is at a low**. Signal = **MACD "fast" settings
  6-19-3** (he credits "the MACD organization," default 12-26-9 → he uses 6-19-3) printing a **light-blue
  bottom arrow** end-of-day, then **next-day follow-through** (VIX higher than the signal-day close,
  trading above the opening range). Bot-programmable as a next-day contingency order. `@12:39`, `@18:53`,
  `@19:10`, `@19:47`, `@20:20`
- **Strike placement (the real risk control):** push the **lower (debit) strike as low as possible** so
  the loss zone sits below VIX's historical floor (he notes VIX "really isn't trading below 14"); his
  14.50 is "a little aggressive," and conservative participants **pay a larger debit to get strikes lower**
  so the chance VIX dips into the loss zone is "almost nil." `@27:35`, `@27:49`, `@28:54`
- **Exit / profit-take:** **no fixed rule.** Either it runs to expiration as a break-even, or VIX pops
  above the strikes and he closes early to "grab almost all of the profit"; he also watches for a **MACD
  top signal ("pink arrow")**. Admits to being **greedy / holding for more**. `@16:52`, `@23:20`, `@24:36`
- **Stop / worst case:** stop-loss on the vertical plus reliance on time-to-expiration mean-reversion (VIX
  often re-spikes before expiry). If VIX falls below the lower strike, **the allocated portion is at risk**.
  `@27:08`, `@29:09`, `@29:48`
- **Sizing:** **~5% of portfolio per cycle in calmer 2024 → ~20% in 2026** ("sign of the times"), re-entered
  every 2–4 weeks on each signal. `@21:50`, `@22:19`, `@33:09`

## Claimed edge & returns

- **"Breaks even most of the time, wins big in crashes":** "most of the time this trade is going to do
  just a little bit better than break even… it's not a profit center… it's a hedge." `@10:24`, `@31:43`,
  `@32:07`
- **Spike payoff:** "you can usually grab almost all of the profit and it becomes **5x 10x your
  investment**… a very big payback." Elsewhere "**10x or 20x**." `@00:00`, `@16:52`, `@33:09`
- **Worked-dollar example:** $50k portfolio, $10k (20%) in the hedge → a spike "could easily be a **$20k–$25k
  profit**" that "bails out" the stressed other 80%. `@33:22`, `@33:53`
- **Track record (anecdotal only):** "I've been trading this trade for **almost 10 years**." Recent
  "**huge payout** in mid-October," "**again in November**," "**just got a nice payout**." On the recording
  day (Feb 5, VIX ~22) his open position is "**about 90% of max profit**." **No win rate, no P&L series, no
  losing cycle quantified.** `@23:20`, `@23:58`, `@34:52`
- **Self-rated risk: 3/10** — "without the big profits you're also not going to have the big risks."
  `@31:43`, `@32:18`

## Objective assessment (where the pitch breaks down)

1. **The crash payoff is CAPPED — which guts the "wins big in crashes" thesis.** Both legs are **$1-wide
   verticals**, so total profit is capped at ~the sum of the widths regardless of how far VIX runs. A VIX
   move to **80 pays essentially the same as a move to 18**. He even tells you to **close early "to grab
   almost all the profit"** `@16:52` — because there is no extra upside from holding. A genuine tail hedge
   wants **uncapped** convexity (long calls / far-wider or ratio structures); this one **caps the exact
   fat-tail it advertises**. This is the central objection.
2. **"5x / 10x / 20x" is a denominator trick.** Those multiples are measured against the **near-zero net
   premium** (he opens for a +4¢ credit) or the thin margin — not against risk capital. The **absolute**
   max profit per $1/$1 structure is ~$1–2/share and **capped**; the **max loss (VIX collapse) is of
   comparable magnitude** and applies to the **20% of portfolio** he allocates. Reframed on risk capital
   the asymmetry is roughly **symmetric with a wide flat middle**, not 20:1.
3. **Downside is under-acknowledged.** He waves off the loss case with folk-psychology ("confidence comes
   slowly, VIX never drops fast"). But **VIX mean-reverts DOWN fast after spikes** — a grind from 22→12
   over a few weeks is ordinary — and his **entry rule systematically buys at VIX lows on a MACD bottom**,
   i.e. closest to the loss zone, right after a spike has faded. The structural tension (good entry price
   ↔ proximity to the loss leg) is never resolved; the "almost nil" loss probability is asserted, not shown.
4. **No separable track record.** Ten years claimed; evidence is **winners-only anecdotes** ("huge payout
   in October… November") and a currently-open winner shown at "90% of max." No win rate, no per-cycle P&L,
   no carried loser. Same falsifiability gap as the channel's income pitches. `@23:58`
5. **VIX-specific mechanics are glossed (these matter a lot here).** VIX options are **European,
   cash-settled**, and **priced off the corresponding VIX FUTURE, not spot VIX** — so a spot-VIX spike to 40
   may move the relevant future only to ~25 if the market expects the spike to be transient (**backwardation**),
   and the spread will **not** reach the value the spot chart implies. Settlement is the **VRO special
   opening auction** (Wed AM), which can gap/print away from where options last traded. "Grab almost all the
   profit on a spike" is therefore **materially harder and less than the spot chart suggests**.
6. **Carry is flat-ish but not free.** The +4¢ open credit is trivial and a **four-leg VIX spread re-entered
   every 2–4 weeks** carries real **commission + bid/ask drag**; over a year of calm the structure is plausibly
   a **slow net bleed**, not a clean break-even ("take my significant other to dinner" `@16:27` ≈ noise).
7. **Conflict of interest / rapport-building.** He sells a paid education product (*Trading Trainer*); the
   extended **charity-kids story** `@04:09`–`@05:20` and the "27 patterns / Wyckoff / point-and-figure"
   pattern-mysticism `@37:40`, `@39:05` are persuasion filler, not strategy substance.
8. **Self-rated 3/10 is light** for a position that can lose the **full 20% allocation** in one adverse
   cycle and whose payoff is capped.

## What's genuinely sound (the diamond)

- **A cheap, defined-risk, financed long-vol hedge is a real and valuable idea** — and a genuine
  complement to the rest of this KB (which is short-premium). Owning convexity that is ~flat in calm
  markets and positive in a fear spike legitimately offsets a portfolio of short-vol/income trades, even
  at negative standalone expectancy, **provided the carry really is low**.
- **Financing the debit leg with a credit leg** (net cost ≈ 0) is the classic, sound way to cut a hedge's
  carry. The honest framing — "this is a hedge, not a profit center, it breaks even most of the time" —
  is **more candid than the channel norm** and is the one claim that is probably true.
- **Buying the hedge when VIX is low** (cheap vol, MACD bottom) is the correct time to add protection.
- **End-of-day, rules-light, bot-programmable**, defined-risk, cash-settled index — fits a busy trader and
  avoids assignment/blowup.
- The **MACD 6-19-3 bottom/top signal** and the strike-placement logic are concrete enough to reproduce.

## Backtestability

- **Hardest-to-backtest strategy in this KB so far — and a different data problem.** VIX options are **NOT**
  in `silver.options_daily_v3` (that table is **equity/index options, EOD**, e.g. SPX/XSP/QQQ). Pricing
  these spreads requires a **VIX OPTIONS chain priced off the VIX FUTURES term structure** — a separate
  dataset (e.g. CBOE DataShop / LiveVol historical VIX options + VIX futures curve). You cannot proxy VIX
  option payoffs from spot VIX, because the options track the **future**, not spot.
- **Closest existing proxy = the user's UVXY work.** UVXY tracks short-term VIX **futures** (1.5× / 2× the
  S&P short-term VIX futures index), so UVXY option backtests already capture much of the same
  term-structure/roll behavior. The user **trades UVXY call spreads + a put** (see UVXY playbook /
  notes) — that is the nearest in-house analogue and the practical place to test "long-vol-spike,
  defined-risk, entered at lows" before sourcing true VIX-options data.
- **Mechanically reproducible parts (given the data):** the **MACD 6-19-3** bottom-arrow entry + next-day
  follow-through on the VIX daily series; **$1-wide call debit spread just below spot VIX** + **$1-wide
  bull-put spread just above**, opened for ~flat-to-small-net-credit; **2–4 week (Wednesday) expiry**;
  exit on a vol spike / MACD top arrow vs. hold to VRO settlement.
- **Not faithfully testable:** the discretionary "be greedy / hold for more" exit, the early-close timing
  on a spike (path/intraday, and dependent on where the **future** is vs. spot), and the "the rest of my
  portfolio covers the margin" framing (portfolio-dependent).
- **Caveats:** EOD-only modeling can't capture the early-spike exit that the whole edge depends on;
  settlement must be modeled at the **VRO auction**, not the last option print; and any test must charge
  realistic **four-leg VIX commissions + bid/ask** every cycle, since the thin carry lives or dies on costs.

## Open questions / next step

- Is the standalone expectancy **break-even or a slow bleed** after realistic four-leg VIX commissions and
  bid/ask over a full calm year? (The hedge's value hinges on the carry truly being near-flat.)
- How much does the **$1-wide cap** cost in a real crash vs. an **uncapped** alternative (long VIX calls, or
  a wide/ratio call spread) on the same capital — i.e. is this a *good* tail hedge or a *mediocre* one?
- How badly does **VIX-futures backwardation** mute the spike payoff vs. the spot-VIX chart he shows
  (quantify the gap between "spot VIX +X" and what the priced-off-futures spread actually returns)?
- Does the **MACD-bottom entry** systematically place the trade too close to the loss zone (VIX still
  mean-reverting down)? Test the loss-cycle frequency the pitch claims is "almost nil."
- **Most efficient first test (on command):** evaluate the analogue on **UVXY** (defined-risk long-vol-spike,
  entered at VIX lows) before sourcing dedicated VIX-options + futures-curve data under
  `backtests/vix_crash_hedge/`.
