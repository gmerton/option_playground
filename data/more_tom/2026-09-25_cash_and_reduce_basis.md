# More Tom: "What Nobody Tells You About the Cash in Your Portfolio" (FZfndYs_nXc, 2026-09-22, 4.5 min) -- review 2026-09-25

**Score 2/5.** A clip cut from a longer show, with no numbers and a product plug at the end. Transcript: auto-captions (810 words).

## Claims
| # | claim | verdict |
|---|---|---|
| 1 | Cash sleeve = T-bills / BIL / SGOV (best), money funds, stablecoins, dividend stocks | Housekeeping, not testable. Calling dividend stocks "cash" is wrong: they carry equity drawdowns. |
| 2 | "Non-correlated reduces risk ~30%; switching strategies another 10-30%" | No derivation. The figures are made up; the direction is textbook. "Bonds and stocks are not correlated" is regime-dependent (2022). |
| 3 | 30/30/40 (trading / long-term / cash) via "subjective market timing" | Not testable: the timing is discretionary. |
| 4 | Under-hedge (hedge 25-50 of 100 deltas); never over-hedge | Consistent with our tail-hedge work (WL-5f: 5-delta same-expiry hedges return -100% every trade). Not new. |
| 5 | **"Always reduce basis": a losing put spread + the stock is up today -> sell a call spread above it** | See below. One anecdote (NFLX), outcome not shown. |

## Claim 5 -- "sell a call spread to reduce basis"
**What it really is.** Adding a short call spread turns the bull put spread into an iron condor. The credit lowers the
put side's breakeven *on paper*, but "basis" is accounting: the new call spread is a **separate trade whose
expectancy is its own**, the EV of selling that call spread at that moment. It doesn't repair the put spread's loss.
It adds a second bet that the stock stays below the call strikes. If the rally that "rescues" the put spread continues
through the call strikes, you lose on the call side. The upside recovery you were hoping for is now capped.

**What it genuinely buys.** On margin, a condor needs only one side's width, so the extra credit uses no extra buying
power. That improves ROC if (and only if) the call spread has EV >= 0 after costs.

**What our ledger already says about that EV** (no re-test needed for the base case):
- Call side of the ETF put-spread exit rule: FAIL. The ETF condor earned +0.36%/trade, t 0.6 (`etf_condor_call_side_2026-09-16.md`).
- Single-name short premium after costs: 0/13 screener spreads certify, and costs eat the gross (TEST_INDEX 9/22 rows).
- Short 7-DTE straddle on single names: NULL as a strategy.
- The one certified short-premium cell is the SPY put side in stress. The call side has never shown an edge here.

**What is untested (the only NEW axis).** The *conditional* entry: sell the call spread on a name that is already
short a losing put spread, right after an up day. That fades short-term strength. The prior is low: every call-side
cell has been null, and the house data says strong names keep going (12-1 momentum, t 2.93). A cheap
v3 test is possible (paired: condor-conversion on up days vs holding the put spread alone, real fills, held to expiry).
It is **not queued**. Ask if you want it pre-registered.

**For the book today:** don't add call spreads to "fix" a losing put spread (e.g. the GLW roll). Judge the call
spread as a stand-alone trade. On current evidence it has no edge after costs.
