# Dale Brethauer: "2 DTE Credit Spread Strategy" (Options Infinity)

- Video: https://www.youtube.com/watch?v=V5H2jHiKIUM (channel `@dalebrethauer7796`, ~13 min, September 2026 monthly update)
- Reviewed 2026-10-02 from auto-captions. **Score: 1.5/5. No new test.** About 40% of the runtime is the membership pitch
  (workshop, alerts, lifetime tier, a free "powerful indicator") plus three first-name testimonials.

## The strategy as stated
SPX bull put (or bear call) 10 points wide, opened 2 days before expiry, short strike chosen so that "~90% expire out of
the money"; credit about $0.90-1.10 (9-11% of width); entries timed by his own overbought/oversold indicator (not
disclosed); a loss-cutting exit (not specified).

## His numbers, checked
- "59 wins and 6 losses. That's 91% return." **91% is the win rate, not a return** (59/65 = 90.8%).
- Year to date at 20 contracts: +$100,650 won, -$21,200 lost, net **+$79,450** "on $20,000 margin = 397%".
  Average win $1,706 (~$85 per contract, about the full credit). Average loss $3,533 (~$177 per contract). Break-even
  win rate = 3,533 / (3,533 + 1,706) = **67%**. At 91% the record is positive expectancy *if real*.
- ⚠ The return-on-margin framing understates the risk: one full max loss on 20 x 10-wide is about -$18k, which is 23% of the
  year's net in one trade. His losers average 1/5 of max, so the record rests on the undisclosed exit. A gap through the
  short strike (2 DTE, no time to cut) is the risk the 65-trade sample has not shown.
- Self-reported spreadsheet, not a broker statement. Membership revenue depends on the record; survivorship of what is
  shown is unknown. "~4 years" claimed, without the 2022 months shown.

## Against our data
| claim | our evidence | verdict |
|---|---|---|
| Short-dated OTM index puts carry premium | AGREES. Calm weekly SPY put (7 DTE, 5-10 delta) beats its own beta, t 5.3-7.1, every year; SPY 1-day 16/5-delta put spread on positive-gamma days +1.9% on risk, t 3.5, 94% win (9/21) | AGREES |
| ...and that is the trade to take | The same 9/21 test: OTM spreads "win more often but collect little", and the edge is AT the money (2x iron fly +5.8% vs the put spread +1.9%) | PARTLY CONTRADICTED |
| Overbought/oversold timing is "an edge right off the bat" | Untestable (proprietary). Our closest: RSI on put spreads = a VIX proxy (no independent edge); intraday triggers ~ a random minute (Stage A) | UNSUPPORTED |
| "~90% expire OTM" is an edge | A ~10-delta short strike expires OTM ~90% by construction; win rate is the price of the credit, not edge (premium-to-width study, 9/22) | CONTRADICTED as stated |
| Works on "anything with a price chart" | Single-name short-dated selling is NET NEGATIVE after costs here (10 DTE); liquidity is the gate | CONTRADICTED |

## What it adds
Nothing new to test. The index short-dated put premium it relies on is already in the book in a better-measured form
(the calm weekly SPY put, gated on regime and dealer gamma). His timing indicator is the only differentiator, and it is
for sale, not disclosed.
