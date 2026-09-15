# My Trading Journey -- "How My Double Calendar Spreads Earned $19,080 This Month" (2025-01-31)

https://www.youtube.com/watch?v=ehm4xgbKJU0 | 14 min | ~24k views | reviewed 2026-09-15 | Patreon trade log (free tier
shows trades), affiliate links (Market Chameleon, LuxAlgo). Captions via yt-dlp.

## His recipe (the live MSFT trade, spot 416)
- Idea source: Market Chameleon "calendar put spread" alerts; builds the graph in OptionStrat.
- Sell Mar 21 (49 DTE) 395P / 430C, buy Apr 17 (76 DTE) same strikes: **49 / 76 days, 27-day gap** -- far longer
  and wider than anything in our study (front 12-20 DTE, gap ~7).
- Strikes ~5% below / ~3.4% above spot, put at ~0.22Δ ("78% OTM"); skewed to the downside because his LuxAlgo
  daily signal says "sell". Debit ~$5.83, ~$10k per trade (18 contracts), Robinhood for zero commissions
  (100-lot trades = 800 fills at Schwab rates would matter).
- Management: **take profit 20-30%, stop 30%**, average hold 18 days; will hold winners over a weekend for the
  theta; "beginners take profits too quickly."
- Record: 76 closed trades, 77% win, avg win +22%, avg loss -11% (= +14% of debit per trade if true), on MSFT /
  GOOGL / AMD-type mega-caps. Patreon-logged, not independently verified.

## Against the calendar path study (real bid/ask, 2018-2026)
| his rule | our data | verdict |
|---|---|---|
| mega-cap stocks with tight markets | stock doubles work ONLY on the tight cut (BA <= 25% of debit, ex-earnings): +7%; NFLX/TSLA/NVDA/META/AAPL/GOOG/MSFT/AMD/AVGO +11-22% | agrees -- the names he trades are the ones that pass |
| 49 / 76 DTE, 27-day gap | **not tested** -- the chain cache stops at 40 DTE; would need a new Athena pull | open |
| ~0.22Δ short strikes, downside skew | sym25 weaker than sym35 on ETFs (+8/+6 vs +12/+19); asym 0.35/0.10 weak; no directional lean tested | leans against, not on his exact structure |
| take profit 20-30% | pt25 -4 to -8pp vs hold on ETFs, -7pp on the stock tight cut; monotone | rejected (buys the 77% win rate) |
| stop 30% | stop40 -1 to -2pp, rarely triggers | harmless |
| earnings just passed = "stable" | our stock cut excludes earnings INSIDE the window (-3pp); post-earnings entry not tested separately | plausible, untested |
| commissions matter at 8 fills | our cost model: $0.0065/sh/leg + 25% of each leg's bid-ask; slippage dominates commissions -- Robinhood removes the small part | agrees, but the big cost is the spread, not the ticket |
| IV down hurts | term-structure cut: flat/inverted entries best; no IV gate in the playbook | agrees on the greek |

## Reading
A generic long-dated double calendar on mega-caps with a 20-30% profit take. The name selection is the one thing our
data supports (tight-market mega-caps are where the stock version works); the management is the same
win-rate-for-expectancy trade every calendar video sells, and the 49/76-day structure is outside our tested range so
the +14%/trade claim can be neither confirmed nor refuted. Directional skew off an indicator adds an untested bet.
Evidence: self-logged Patreon record, affiliate-funded. Score 2/5. If we want to test his structure: pull 45-80 DTE
chains for the tight-cut mega-caps (Athena, a few hours) and run `run_dcal_path_sim.py` with a (49, 5, 76) structure.
