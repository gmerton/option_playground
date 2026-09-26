# IBD: "Trade Small, Trade Often: Tom Sosnoff on Managing Risk" (00P-Gurxe6k) -- review 2026-09-25

**Score 2.5/5.** The risk-hygiene half is sound and matches our data. The rest is the usual: no numbers for the
strategy, and a pitch for tastytrade's research, which our replications have repeatedly marked down (mid pricing, no t).
2,249 words, auto-captions.

| # | claim | verdict |
|---|---|---|
| 1 | Blow-ups are always size: too big, or doubling down on a loser. **Don't add to losers.** | **AGREES, and we tested it today.** Averaging down a bull put at 45 delta was no better than selling the same spread on any day, and it doubled the tail: p5 -200% vs -100% of one spread's risk (`add_on_put_spread`). Size-lever study: the lever is exclusion and size. |
| 2 | "The key to risk management is NOT stop orders or taking losses; losses are random" | **Broadly agrees.** No stop variant beats buying the close (entry study), intraday stop execution hurts, and the 1-ADR disaster stop is ~+0.03R and doesn't beat its control. ⚠ It isn't a licence for no stop: the disaster stop exists for the crash, not for edge. |
| 3 | Per-underlying cap ~10% of net liq (up to 15%); ~$5k max per stock position on a $50k account; less for options | Hygiene rule, not testable as edge. **Directly relevant to today's CIBR/cyber concentration** (FTNT, CRWD, PANW, RBRK + CIBR = one bet). Use it as the cap per THEME, not per ticker. |
| 4 | Allocate more when volatility is higher (more opportunity) | **Agrees for index put selling**: the certified SPY cell requires VIX >= 20, and vix_pct predicts put-spread ROC (t +6.54). Not a general rule: for long straddles the gate is the inverse (IV pct <= 30). |
| 5 | "I'm a contrarian, I take the other side" | As before: a floor market maker earns the spread, which retail pays. Our fade tests are null or inverted. |
| 6 | Correlations scatter in bull markets and go to one in selloffs; "no correlation between bonds and stocks anymore" | First half is textbook and right. Second half is roughly right day to day (daily SPY-TLT correlation -0.49 in 2019 -> ~0 to +0.13 in 2022-25, from parity spot, which is noisy and biases toward 0). **But that's why bonds stopped HEDGING**: in 2022 both fell. Zero correlation != protection. |
| 7 | Tasty's think tank gives "optimal DTE, deltas, strategies" backed by data | Our replications of tastylive studies: 1.5-2.5/5, mostly mid-priced, no n or t; the 21-DTE management claim failed here (manage-at-21 earns LESS than hold, t -2.42). |

**For Gabe:** adopt #1 and #3 as hygiene (no adding to losing option positions; cap each THEME at ~10-15% of net liq).
Nothing to test.
