# 0DTE SPX Pin Butterfly ("1200% Average Win") — Shamoun Bari ("Jamal")

Source: `2026-04-05_D5Kg5SkPwRo` — "This 0DTE SPX Strategy Targets 1200% Average Wins"
([watch](https://www.youtube.com/watch?v=D5Kg5SkPwRo)). Guest introduced on air as **Shamoun Bari**
`@00:24` but addressed as **"Jamal"** throughout (`@24:39`, `@40:32`, `@40:42`) — name uncertain
(auto-captions, see notes.md). Claims ~7 yrs trading, an internship/role at Raymond James and
"working with hedge funds." Host: John.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 5 / 10 (defined-risk per trade) · Tested: NO**
> A **convex / lottery-style** 0DTE SPX long butterfly: buy a very narrow (5–15 pt, usually 10)
> ATM call fly mid-afternoon, predict the closing "pin" from dealer-gamma + RSI/VWAP confluence,
> and scale out into the close. Unlike the channel's income trades, the skew is reversed — frequent
> small/total losses paid for by rare 4–5,000% jackpots. The headline "1,200% average win" is the
> trap: an average win is meaningless without the **win rate AND the average loss**, and here the
> claimed inputs (52% win, ~−100% capped loss, +1,200% avg win) imply a per-trade EV near **+520%
> of risk** — so wildly positive it strains belief, and is **internally inconsistent** with the
> modest 52%/yr return he also quotes (the reconciliation is tiny 0.5% sizing + low frequency). The
> 1,200% figure almost certainly conflates **OptionStrat theoretical peak P&L** with realized,
> scaled-out fills. **No separable track record**, the win-making step is admitted **discretionary
> "feel" in the last 30 minutes**, the setup fires only **once every 2–4 weeks** (tiny sample), and
> the pitch leans on "go backtest it yourself" / "find a mentor." Defined risk (can't lose more than
> the debit) is the one solid virtue. Slightly above Burrito Butterfly because he at least states a
> win rate and the math ties; below Time Flies because there is **zero verifiable evidence**.

## Mechanics

- **Underlying:** SPX 0DTE — chosen for European/cash settlement (no early assignment), liquidity,
  tight strikes. `@00:38`, `@00:48`
- **Structure:** long **call butterfly** — sell 2 calls at the predicted pin strike, buy 1 above and
  1 below, usually equidistant (sometimes skewed to a broken-wing). Net **debit**; max loss = debit.
  `@03:39`, `@04:05`
- **Wing width:** **very narrow, 5–15 pts, "10 is the sweet spot."** `@04:59`, `@17:27`
- **Cost / max loss:** ~**$0.40–0.55 per contract ($40–55)** entering mid-afternoon; max loss = 100%
  of debit, capped. `@06:18`, `@18:33`, `@19:50`, `@28:16`
- **Entry time:** midday **12:00–2:00 pm ET**, **sweet spot 2:15 pm ET**, claimed Greeks "inflection
  point" (theta/vega/delta shift); ±15 min window. `@07:35`, `@07:46`
- **Setup filter (wants):** a **slow drift / contained chop**, small candles, no violent moves, no
  news; the 2:15 window is played as a **reversal**. `@08:38`, `@09:56`
- **Pin selection (the "golden ticket"):** confluence of (1) **RSI divergence** on the 5-min,
  (2) **DSS Bressert** indicator curling up from below its 20 band, (3) a **dealer-gamma profile**
  (proprietary model, or SpotGamma / OptionsDepth / "VS 3D") showing **positive-gamma nodes
  sandwiched by negative-gamma nodes** = compression toward a pin, and (4) **VWAP**, which he claims
  "nine times out of 10" coincides with the pin. `@11:15`–`@17:14`
- **Entries / sizing:** **1–3 entries, all on the same pin strike**, scaled in with limit orders
  (one market order first to gauge the spread). Position sizing **≤1% of portfolio max, typically
  ~0.5%**. `@09:06`, `@10:12`, `@29:42`
- **Exit / management:** start scaling out **~3:00–3:30 pm** at the break of a technical structure,
  when up "**3–500%**"; **close at least half** (locks a net win), then take a chunk **every 5 min**;
  leave only **~10% (max 20%) to expiration**. Explicitly active, discretionary, uses 2nd-order
  Greeks (gamma/vanna/charm) by feel. `@20:41`–`@22:32`, `@23:15`
- **Frequency:** only **one qualifying setup every 2–4 weeks** (more in low-vol stretches). Pairs it
  with a separate high-frequency 0DTE iron condor "backup" to stay busy. `@31:31`, `@33:30`

## Claimed edge & returns

- **Win rate: ~52%.** `@02:55`, `@30:31`
- **Average winner: 1,200%** of risk, "skewed by the max winners… close to 4–5,000%"; **median
  winner ~750%.** `@00:00`, `@30:45`
- "**Very hard to lose money with this strategy if you're keeping that 52% win rate.**" `@00:00`,
  `@30:55`
- **Annual return: 52%/yr using only this strategy.** `@31:19`, `@32:14`
- **Max loss: 100% of debit** (defined risk, "never blow up by 1,000%"). `@28:16`
- **Self-rated risk: 7–7.5** (says it's a 9–10 "for the average trader," talked down via the
  "risk is the absence of knowledge" line attributed to Buffett/Howard Marks). `@28:54`, `@29:13`
- Evidence basis: a single OptionStrat walk-through of a *winning* example day (Wed Mar 11, pinned
  6775) and "go back and backtest this." **No statement, no trade log, no separable track record
  shown.** `@16:28`, `@34:48`

## Objective assessment (where to be skeptical)

1. **"1,200% average win" is the headline trap — and the inputs are almost certainly inflated.**
   The convex-trade skeptic rule: an average win means nothing without the win rate *and* the
   average loss. He does supply both (52% win; loss capped at −100% of debit), so do the math.
   **Breakeven win rate** at +1,200% win / −100% loss ≈ **100 / 1,300 ≈ 7.7%.** He claims **52%** —
   ~6.7× breakeven, implying a per-trade EV of **0.52·1200 + 0.48·(−100) ≈ +520% of risk.** A real,
   repeatable +520%/risk edge is extraordinary; the only reason it nets a mild 52%/yr is **0.5%
   sizing × ~15–25 trades/yr.** Nobody who genuinely had +520%/risk would size at half a percent.
   The likeliest resolution: the **1,200% is OptionStrat theoretical peak P&L** (the curve only
   spikes in the final 30 min at a perfect pin — he admits "very rare you get the entire thing"
   `@01:21`), while realized, scaled-out wins are a fraction of that. Mixing theoretical peaks into
   an "average win" is the classic convex oversell.
2. **The win rate is suspiciously generous and self-defined.** "Closing half at +3–500%… you are
   now guaranteed to win on that trade" `@21:05` means a "win" is booked off a partial scale-out, so
   52% is not a clean hit-the-pin rate. Getting a **10-wide 0DTE SPX fly to any profit on 52% of
   discretionary pin predictions** is itself a strong claim with no audit trail.
3. **No separable, verifiable track record — at all.** Every number is self-reported; the only
   shown trade is a *winner* on OptionStrat (model prices, not fills). The repeated deflection is
   "**go backtest it yourself**" `@34:48` and "**find a mentor / ask AI**" `@38:40`. This is weaker
   evidence than Time Flies (weekly-published multi-year record) and on par with Burrito Butterfly's
   "I can't untangle the results."
4. **The alpha is admitted discretion.** "Anyone can enter it… the actual thing that takes practice
   is **managing it** in the final 30 minutes" `@23:15`; "it does take discretion." So the
   win-determining step (last-30-min scale-out by feel, "gauging the strength of the push") is
   **unfalsifiable and un-backtestable** — a mechanical version is not the strategy that produced the
   numbers.
5. **Extreme path dependence + 0DTE gamma/timing risk.** A narrow 0DTE fly is worthless until the
   last hour and only pays at a near-exact pin; a small late move out of the tent = total loss. The
   "edge" rests on **dealer-gamma pinning**, which fails precisely on the violent/negative-gamma days
   he says to avoid — i.e. the strategy works when the market is calm and quietly dies when it isn't.
   He cannot reliably forecast which day he'll get.
6. **Tiny sample.** One setup every 2–4 weeks ≈ **13–26 trades/yr.** A 52% win rate and a fat-tailed
   1,200% average over that few convex trades is **statistically noise** — a couple of jackpots
   (or their absence) swing the whole record. No way to tell skill from variance.
7. **Costs hand-waved.** Multi-leg SPX commissions + wide 0DTE bid/ask (he admits "the bid and ask
   spread… are fairly large" `@18:46`) on a ~$0.44 debit, plus scaling out in chunks every 5 minutes,
   meaningfully tax a thin-priced structure. Not modeled.
8. **Authority/marketing tells.** Raymond James / "hedge funds" credentials, "proprietary model,"
   2nd/3rd/4th-derivative Greeks name-dropping, the Buffett/Marks risk quote to talk a self-described
   9–10 down to 7–7.5, and a vendor discount plug (Mentor Q) at the end `@40:22`.

## What's genuinely sound (the diamond)

- **Defined risk, no blow-up:** max loss = debit, SPX cash-settled, no assignment, sized ≤1%
  (typically 0.5%) of portfolio — you cannot get destroyed on one trade. Real and valuable.
- **Honest about the skew:** he openly calls these "lottery tickets," states a *below*-even 52% win
  and that "the win rate isn't anything extraordinary" `@33:20` — less oversell than "risk-free"
  pitches; the convex framing itself is correct in spirit.
- **Dealer-gamma pinning is a real, documented phenomenon** (positive-gamma compression on OPEX-style
  days). Buying a *cheap, defined-risk* structure positioned for a pin is a legitimate idea — the
  question is only whether his discretionary edge beats the cost and the coin-flip.
- **Discipline:** scale out, lock a win by closing half, never hold more than ~10–20% into the
  final print, tiny sizing. Sensible risk management *if* the entry edge is real.

## Backtestability

- **More testable than a discretionary intraday strategy — but only crudely.** Because this is a
  *convex buy-cheap-defined-risk* trade, an EOD test of the **raw lottery EV** is partially
  informative: buy an ATM (or VWAP-anchored) narrow 0DTE SPX call fly at the prior close and **hold
  to settlement**, measure the realized distribution (win rate, median/mean win, % full losses, EV
  after modeled spread+commissions). That answers the core question — **does the cheap 0DTE pin fly
  pay for itself without his hand-management?** If even the raw structure is ~breakeven-or-better, his
  management could plausibly add; if it bleeds, the 1,200%/52% story needs the discretion to be doing
  *all* the work (unverifiable).
- **Not faithfully testable:** the 2:15 pm entry, the dealer-gamma/RSI/VWAP confluence filter, the
  scale-in on limit fills, and the last-30-min discretionary scale-out — the alpha-bearing steps.
  EOD data has **no intraday**, so entry timing, the partial scale-outs, and "leave 10% to expiry"
  cannot be replayed; an EOD test materially *understates or mis-states* his realized P&L by
  construction.
- **Data:** ✅ SPX confirmed in Athena `silver.options_daily_v3` (2010 → 2026-02-20, greeks +
  bid/ask, **0-DTE present daily**) — the structure is constructible. ⚠ **EOD-only** is the binding
  limitation for an intraday 0DTE trade; treat any backtest as a crude prior-close→settle proxy, not
  the strategy.
- **Honest null comparison:** raw 0DTE ATM fly held to settle, and the same fly *with* a no-cost
  mechanical pin proxy (e.g. anchored at prior VWAP/close), to see whether confluence-based strike
  selection beats naïve ATM. If it doesn't beat ATM at the EOD level, the discretionary entry claim
  has no support in testable data.

## Open questions / next step

- What is the **realized** average win (post-scale-out fills), vs the OptionStrat peak? The whole
  pitch hinges on this number and it was never shown.
- Is the 52% a per-entry win rate or a per-setup rate, and does it count partial scale-outs as wins?
- Does the **raw EOD 0DTE ATM fly** (no management) have positive EV after spread+commissions on
  SPX 2018–2026? That bounds the lottery's intrinsic edge.
- How does the record hold up out-of-sample given only ~13–26 trades/yr — is 52% distinguishable
  from luck?
- **Next step (on command only):** EOD proxy backtest of the raw cheap-0DTE-fly lottery under
  `backtests/zerodte_convex_butterfly/`, framed explicitly as a crude lower-bound on the convex EV.
