# Rolling Options to Avoid Losing Money - Trade Like a Pro

**Video:** `aOT1yP10_To` · **Presenter:** Brian Overby (not Tony Zhang) · **Watched:** 2026-09-26 · **Published:** 2025-02-02 · 70 min

> **2/5 · no new test.** Really "rolling covered calls". About 60% is basics, exercise/assignment and Q&A. The roll
> rule is stated clearly and the risk is described honestly, but there is no evidence, and both halves of the trade
> (the covered call, and a short call sold after a rally) already fail in the ledger. No rule for a losing short put
> or credit spread.

## The rule
- **Trigger:** roll pre-emptively as spot approaches the strike; "if it hits the strike… I want to roll", and "if it
  gets 1 to 2% in the money then you have to roll" [51:54–52:52]; "don't want the stock to get more than 2% in the
  money" [32:51].
- **Action:** roll UP and OUT for a NET CREDIT, to the nearest expiry that pays one: "go out as far or as little
  amount in time as feasible and still… get this done for a net credit" [45:32]. 30–45 DTE, 90 at most, avoid
  earnings [34:56].
- **Fallback:** if up-and-out can't pay a credit, roll out at the same strike [37:03–39:12]. At 5–7%+ in the money,
  "close everything and start over" [59:21]. No rule for when to stop rolling.

## Evidence
None. One constructed example (buy back the 90 call at $2.10, sell the 95 call 60 days out at $2.30, +$0.20 net)
and a JPM paper-trade demo priced at the mid; "easier to get near the mid at the close" [30:42] with no data. Free-trial
pitch twice.

## Concepts
- ✅ Honest on the key point: "you did book a loss… you still got all the risk of still owning the stock" [30:42]. A
  roll is a close plus a new trade; the credit doesn't erase the realised loss.
- ⚠ He frames the roll as doubling down at blackjack [28:35, 45:32]: martingale framing in his own words.
- "Pre-emptive rolling is way easier" means it's easier to collect a credit. A credit isn't profit.

## Against the ledger
- BCI covered calls / CSPs vs stock at the same delta: **FAIL** (stock minus costs).
- The rolled-to call is a short call sold after a rally. Leg-in call spread (2026-09-25): **INVERTED**, −7.26%/trade,
  t −4.31, 11/15 years negative.
- PMCC with rolled shorts: fails as specified (−20.55pp, t −4.93).
