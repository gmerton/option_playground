# Options With Ravish -- "My $545K Options Strategy Generates Weekly Income in Any Market (Double Calendars)"

https://www.youtube.com/watch?v=2w8XI0jnQzM | uploaded 2026-07-02 | 16 min | ~95k views | reviewed 2026-09-15
Transcript: auto-captions via yt-dlp (`--js-runtimes node`). Sponsored segment (Moomoo); sells an "elite coaching program" + Discord.

## His recipe
- Sell a put ~10 pts below and a call ~10 pts above spot, 2 weeks out; buy the same strikes 1 week later (14/21 DTE, 7-day gap).
  On a ~745 underlying with VIX 15-20 that is ~0.3-0.35 delta -- i.e. our **sym35, 12/19-day** cell.
- Take profit 20-40% of max risk, scaling out (80% of size gone by +40%, a few runners). Mental stop -30% ("never a resting stop").
- If price drifts out: hold for mean reversion, or re-center the whole trade at new strikes.
- Enter in LOW IV (VIX at the bottom of its 15-20 range), skip when VIX is spiking; prefer a range-bound tape.
- SPX / SPY / QQQ only (bid-ask on stocks kills the edge). Measure P&L on max risk, not on the debit.
- Double diagonal (longs one strike further out) when you expect IV to fall -- less vega. (Not tested by us.)
- Claims: 82% win rate, $100k -> $535k in 16 months (Kinfo-verified, but Kinfo shows 52% by leg; $10M "deferred loss" = enormous turnover).

## Against our calendar path study (real bid/ask paths, 2018-11 .. 2026-02, IWM/QQQ/SPY sym35)

| his rule | our result (12/19d, n=1,018 / 20/27d, n=1,000) | verdict |
|---|---|---|
| structure: sym ~0.35 delta, 7-day gap, 2 weeks out | hold +12.4% (60% win) / +19.1% (59% win), both halves + | **agrees** -- this is exactly our best cell |
| take profit at +20-40%, scale out | pt25 +7.5 (68% win) / +10.7 (73% win): −4.9 / −8.5pp vs hold; pt50 −2.0 / −4.2 | **rejected** -- buys win rate, sells expectancy |
| mental stop −30% | stop40 −1.6 / −1.6pp, stop60 −0.9 / −1.1pp vs hold | mildly negative; harmless at most |
| re-center when price leaves the range | recenter2s −3.2 / −4.0pp | **rejected** |
| hold for mean reversion when price leaves the range | = hold | **agrees** (his other option) |
| enter in low VIX, skip spikes | Bear_HiVIX +25.6 / +31.5% (69-75% win, both halves +); Bull_LoVIX +8.1 / +12.7% and NEGATIVE before mid-2022; front/back IV ratio ≥1.03 +26% vs ≤0.90 +4% | **inverted** -- his vega reasoning is right about the greek, wrong about the outcome |
| range-bound tape | regime cut: trend direction matters little, VIX level matters a lot | not supported, not harmful |
| SPX/SPY/QQQ only, bid-ask matters | bid-ask ≤10% +10.2 / +8.6, 10-25% +6.6 / +7.5, >25% −12 / −15 | **agrees** -- the gate that decides everything |
| P&L on max risk | our ROC = P&L / (debit + slippage + commissions) = max risk for a calendar | same convention |
| double diagonal when IV may fall | untested | open question; cheaper vega but the long-leg bleed the study measures gets worse |
| 82% win rate | 60% held; 68-73% with pt25 at −5 to −8pp expectancy | consistent with his exits, not with an edge |

## Reading
The structure he trades is the one our study rates best, and his liquidity rule is our gate. Everything he layers on top
(early profit-taking, re-centering, low-VIX entry) is what our data says NOT to do -- the first two convert expectancy into
win rate, the third picks the weakest regime and the weakest term structure. His account claims cannot be checked
(Kinfo counts legs; the wash-sale figure implies turnover far beyond the weekly strategy shown). Nothing here changes
`double_calendar_playbook.md`. Score 2.5/5 as a source: right vehicle, wrong management, sales funnel.

Worth one test if we care: the double diagonal (longs 1 strike wider) on the same entries -- his claim is lower vega
sensitivity; our question is whether the wider long strike costs more in bleed than it saves.

## Follow-up 2026-09-15: the double diagonal tested (`run_ddiag_path_sim.py`, study step 7)
His one untested idea is the best thing in the video: longs 1% of spot wider beats the double calendar on the same
IWM/QQQ/SPY entries (+15.6% vs +12.1% on max risk 12/19d, +22.5% vs +19.1% 20/27d, 67–72% win vs 60%, paired
t ≈ 20, 8 of 9 years), and the gain is largest when VIX falls, exactly as he argues. Score raised to 3/5 for that;
management rules still rejected.
