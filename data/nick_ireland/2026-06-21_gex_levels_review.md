# Review: "Why I stopped trading price action & only use gamma exposure ($1k/day strategy)" (Nick Ireland, 2026-06-21, bXVHsViQuyE) — 2/5

Reviewed 2026-09-21. 23:07, public. Sells a free checklist web app (ninjagex.com) and points to a paid gamma-map
platform ("IT Matrix HQ"). Transcript: `videos/education/2026-06-21_bXVHsViQuyE/`.

## The system

1. **Premise:** price action is random ("a scoreboard, not a signal"); patterns have no predictive power.
2. **Levels from dealer gamma (GEX):** each morning mark the SPY strikes with the largest gamma exposure; only trade
   at or near one ("no man's land between levels = no trade"). Large positive-gamma strikes act as magnets/pins.
3. **Regime:** positive gamma (dealers long gamma, hedge against the move) → suppressed volatility, cleaner trends,
   size normally, hold for 2R. Negative gamma (dealers short gamma, hedge with the move) → amplified moves, size down
   30–50%, take partials at 1R.
4. **Direction:** 9/21/50 EMA stack on the daily AND the 5-minute; calls only in a bullish stack, puts only bearish,
   sit out when the EMAs cluster.
5. **Trigger:** compression / flag at a gamma level, entry on the break with noticeably higher volume; no volume = skip.
6. **Risk:** 1–2% of the account per trade, stop below the EMAs, only 2:1 or better.

**Record shown:** Webull statements for three of his "better months" of 2025 (+$9,486 Feb, +$9,352 Jun, +$6,649 May),
a small account at $29,711 grown from $1,000, two winning SPY option trades (+$1,012, +$855; contracts +330% and +220%),
and a claim that every trade (red and green) is posted on X. A student "made over $16,000 in 2 months".

## Against our evidence

| Claim | Our evidence | Verdict |
|---|---|---|
| Price action alone has no predictive power | Every intraday trigger we've tested ≈ a random minute: Stage A (11,227 fires), 12 level triggers today, VWAP double-rejection, ICT sweep on QQQ | **Agrees** |
| His trigger (flag break on higher volume, EMA stack filter) | That IS a price-action trigger. Our intraday ORB / pivot breaks ≈ random minute; the "light vol" tag and intraday RVOL gates didn't rank R; the pivot break was the worst-timed of 13 arms today | **Contradicts his own premise**; no support in our data |
| Trade only at a large GEX strike; big positive-gamma strikes pin price | Untested by us. Pinning toward heavy open-interest strikes at expiry is documented in the literature for single stocks; intraday index "magnet" behaviour is a much stronger claim. Our level test found classic levels pick the DAY, not the minute | **Untested; plausible for expiry-day pinning only** |
| Positive gamma → lower realised vol; negative gamma → bigger, trending moves | Consistent with published work on dealer hedging and intraday momentum, and the mechanism behind the noise-band momentum we replicated on QQQ. We haven't measured it ourselves | **Plausible, testable** — already in our queue |
| Size down 30–50% in negative gamma | Our straddle/size studies: sizing is the lever; regime switches mostly fail to forecast. Size-by-regime untested | Neutral |
| $1k/day, statements | Three self-selected "better months" plus two winning trades; the full X log would be the real test | **Cherry-picked** as shown |

## Score: 2/5

Right about price action, sensible risk rules, and the gamma-regime idea has a real mechanism behind it. But the
entry he actually trades is the kind of price-action trigger he says is random, the level/magnet claim is asserted
from two examples, and the record shown is his best months. The one piece worth our time, gamma regime vs realised
volatility / intraday follow-through, is already queued from the IQCapital review; this adds the level-pin claim to it.
