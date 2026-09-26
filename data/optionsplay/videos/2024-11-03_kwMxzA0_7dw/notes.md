# How to Fix a Losing Trade | Step by Step (2024)

**Video:** `kwMxzA0_7dw` · **Presenter:** Brian Overby · **Watched:** 2026-09-26 · **Published:** 2024-11-03 · 67 min

> **1.5/5 · no new test (one optional low-priority cell noted).** Converts a losing SPX bull call debit spread into a
> butterfly by selling the adjacent call spread. By put-call parity that is the same position as the ledger's
> put-spread iron-fly repair, which is INVERTED (−16.68%/trade, t −7.28). A hypothetical priced at the mid, with
> slide-math errors [21:14–27:31] and no live demo (the platform lacks SPX [37:02]).

## The rule
- **Entry:** Monday, 5 DTE, in-the-money SPX bull call spread: long 5820 / short 5835 (ATM), paid $8.75.
- **Trigger:** SPX down ~0.5% (20–40 points), usually by Wednesday's close, and the adjacent 5835/5850 call spread has
  fallen to about half its entry value ($5.35).
- **Action:** "if I ever see this credit spread trading for $2.50 or around $2.25, I'm going to roll into that
  spread" [28:34]: sell 5835/5850 → long 5820/5835/5850 call butterfly, net cost ~$6.50–6.75. Minimum $2; skip at
  $1.50 [49:55].
- **Exit:** close the fly if spot returns to 5835, "no other adjustment" [44:35, 48:51]. Profit exit: sell the
  original spread at $13–14 on a 1–1.5% rally [41:21].
- **Scope:** only "within the last 10 days" [54:09]; not for out-of-the-money debit spreads [45:39]. Stated
  alternative: a 50%-of-debit stop [42:26], rejected because retail won't execute it.

## Evidence and concepts
- None; mid-priced ("go midpoint"). Pitches: free trial, platform spread alerts, daily plays.
- "Adds no additional risk… reduces the overall risk" [58:19] is correct: max loss falls by the credit. The hidden
  cost is that it sells the rebound above 5835. He says "it's not a perfect hedge" [07:25], calls it "a chip and a
  chair", and correctly notes most real hedges add risk [57:15].

## Against the ledger
- **Parity:** bull call spread (long K−w, short K) + short K/K+w call spread ≡ bull put spread + the same call spread.
  **Put-spread iron-fly repair: INVERTED**, −16.68%/trade on risk net, t −7.28, 14/15 years negative, "stocks bounce
  after the drop" (vs matched control −0.46pp, t −3.15).
- 50% stop ≈ the straddle −50% stop (a cost); the 50% take / 2× stop exit on credit spreads −4.3%/trade, t −5.4.
- Only new axis: ≤ 5 DTE on the index vs 20 DTE on SPY/QQQ/IWM + mega-caps. Prior negative (index rebounds are, if
  anything, stronger). Optional spec, not queued: SPY Monday-close ATM bull call spread (long ~0.25% below), Friday
  expiry 2016→2026-03; trigger at Wednesday's close = K/K+w call spread ≤ 50% of its Monday value and sellable for
  ≥ 23% of the debit; arms hold / close at trigger / sell the call spread, paired; primary = fly − hold in % of the
  debit, house costs, halves + per year, p5 tail and the rebound given up.
