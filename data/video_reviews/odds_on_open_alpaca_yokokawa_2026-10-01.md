# Odds on Open: "Ex-Lehman Trader: AI Won't Give You Edge" (Yoshi Yokokawa, Alpaca CEO)

- Video: https://www.youtube.com/watch?v=E-kC8n9Q1_E (channel `@oddsonopen`, ~56 min podcast; sponsor read for Onyx Flux @08:00)
- Reviewed 2026-10-01 from auto-captions (9.8k words).
- **Score: 1/5 for trading content. No test possible.** This is a founder interview: the second half is Alpaca's
  business (API brokerage, entity accounts, tokenized-equity custody, YC hedge funds) and career philosophy.
  No strategy, no rule, no number about returns. The guest is a broker CEO; every user anecdote is
  survivorship from his own customer base ("some people do find edges").

## Claim ledger

| time | Claim | Our evidence | Verdict |
|---|---|---|---|
| 00:03-00:04 | AI/LLMs don't give edge; they shorten trial-and-error so you can "do more trials and get better edges" | First half AGREES with this book's experience (fast iteration, almost everything still fails). Second half is backwards without a multiple-testing charge: more trials manufacture more false edges (ledger-wide BH/Holm correction 9/22; p_search / p_opt harness 9/23; "a clean result is a bug" rule) | MIXED: speed yes, "more trials = better edges" CONTRADICTED |
| 00:04-00:05, 00:18-00:20 | Having an edge is step one; executing it with discipline is a separate, harder skill | AGREES. Our largest measured leak is execution, not selection: same-day round trips (278 cycles, -$8.3k, 19% win); intraday stop execution hurts (entry study 9/17) | AGREES (already in hand) |
| 00:05-00:06 | Successful users stop when "market dynamics change", retune, and come back | CONTRADICTED: strategy good stretches are unpredictable (WL-2b: persistence rho -0.01, regime sweep p 0.36); breakout regime feedback can't forecast paying months; self-regime holdout NULL 2010-19. Retuning on recent results is the curve-fit path | CONTRADICTED |
| 00:13-00:16 | Number of (YC) "AI hedge funds" and entity accounts is rising | Not a trading claim | n/a |
| 00:44-00:47 | Markets are a fair "street fight"; same tools for everyone | Not testable; costs and fills are not equal (our cost model exists because retail pays the spread) | n/a |

## What it adds
Nothing to test. The one operational idea (pause and retune a system when the regime changes) is the
specific thing our localisation tests reject.
