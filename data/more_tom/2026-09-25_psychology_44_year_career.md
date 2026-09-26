# Lossdog: "The Psychology Behind Tom Sosnoff's 44-Year Trading Career" (gKl_sNJiTtU) -- review 2026-09-25

**Score 1.5/5.** Friendly interview by his own firm's chief strategist (the channel is Lossdog, his venture), ending in a
product plug (his trade feed on the platform). 3,116 words of auto-captions. Only two numbers are testable, and nothing
here is a strategy.

| # | claim | verdict |
|---|---|---|
| 1 | "Positive drift": the market is up 53/47 historically, "closer to 60/40" for the last ~two decades | **Partly right.** SPY 2009-2026: **55.3% of DAYS up** (the same since 2016), **68.9% of MONTHS up**. 60/40 is wrong for days and too low for months; he's blending timeframes. |
| 2 | "Selling premium has nothing to do with upside or downside -- it's an approach to time value" | **CONTRADICTED by today's tests.** On the same 13 underlyings, same deltas/DTE/costs: short 0.25/0.15 put spreads earn **+2.94%/trade**, short 0.25/0.15 call spreads **-4.70%/trade** (`add_on_put_spread`, `leg_in_call_spread`). The gap between the two sides IS the drift. Premium selling's P&L is directional, and his own "positive drift" is what pays the put side. |
| 3 | Contrarianism came from the pit: take the other side of the public | True of a market maker, but a market maker earns the **bid-ask spread**, which a retail trader pays. Taking the other side is not an edge off the floor (our fade/reversal tests: exhaustion fade retracted, bouncy-ball short fails). |
| 4 | Don't let one move wipe you out; trading too big always fails | **Agrees** (size-lever study: the lever is exclusion and size; every non-size tail variant INVERTED). Not new. |
| 5 | The market is "very fair": ~50% of traders beat mediocrity, ~16% do very well, a Gaussian | **Made up, and against the evidence.** Studies of retail day traders (Barber-Odean, Taiwan; Chague et al., Brazil: ~97% of persistent day traders lose) show a heavily left-skewed distribution. No data was offered. |
| 6 | Never had a losing year "if you looked at my total investment portfolio", which includes business investments | Unverifiable, and it mixes trading with ~$1.85B of business exits. Not evidence about trading. |
| 7 | 10,000+ trades/yr; the scarce resource is "ideas" | Promotional framing for the trade feed. More trades don't make the edge per trade positive; for Gabe, same-day churn is the largest measured leak. |

**For Gabe:** nothing to test. The one useful takeaway is what our data already says: premium selling works on the put
side because it's short a crash-protection premium and long the drift, so size it as a directional position.
