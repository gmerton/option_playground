# tastylive / Options Jive: "Probability of Touch: What 21-Day Management Changes" (2026-02-10, 13:10)

_Reviewed 2026-09-23 for the Sosnoff-doctrine batch (Tier 1). Two hosts discussing research slides. Transcript
(`en-orig` auto-captions) in this folder. Slides aren't in the transcript; every number below was spoken._

## Verdict: 2 / 5

This is a real empirical measurement, and its direction is consistent with ours: **realized touch rates sit below
the 2×delta rule of thumb** because implied vol over-states realized. The put/call asymmetry they find (calls
touched more, attributed to upward drift) is also sensible.

Three problems cap it:

- **Touch isn't P&L.** They say so twice: "probability of touch doesn't dictate good or bad trade" (01:52),
  "having your strike tested doesn't necessarily imply that you're going to lose money" (02:19). The video then
  concludes "21 days is going to significantly compress your P&L volatility" (12:13) without showing any P&L.
- **"Managing cuts touch by more than half" is mostly mechanical.** A 45→21 DTE exit observes the path for 24 of
  45 days. Fewer days of observation means fewer touches, whatever the edge.
- **The spoken numbers don't agree with each other.** Managed touch is "approximately 0.8× the delta" (05:36).
  For a 20Δ option that's ~16%, yet the next example is "on a 20 delta option, you're looking at a **10%**
  probability of touch" (06:15). A "30 delta put" is given "a 67 / 60% plus chance of touching" (04:07). The
  2×delta rule says 60%, and 67% matches nothing.

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY only (explicitly: "this might be different on a single stock name", 11:56) |
| period | **not stated** |
| n | **not stated** |
| entry rule | each OTM put and call at deltas **10 to 45**, opened at **45 DTE** |
| management | managed = exit at **21 DTE**; comparison = the same option held to expiry, and the theoretical 2×delta |
| fills | none; touch is a price event, not P&L. Channel disclaimer: "not presented net of all commissions" |
| control | theoretical POT (2×delta) and the held-to-expiry realized POT, the right comparisons **for a touch statistic** |
| win rate / avg / tail | none |
| significance | none |
| selection | SPY in a sample they describe as "upside drift… for quite some time" (08:45). Period unstated, so the drift effect can't be sized |

## Numbers as spoken

| @ | number |
|---|---|
| 00:30 | rule of thumb: theoretical probability of touch ≈ **2× delta** |
| 03:06–03:56 | sell a **20Δ call → expect ~35Δ** at some point; sell a **20Δ put → expect ~25Δ** at some point, "even if you're managing at 21 days" |
| 04:07 | "selling a 30 delta put, there's a 67… 60% plus chance of touching it" |
| 04:38 | with 21-DTE management, "the 60% probability of touch goes down significantly to **40, 30**, something like that" |
| 05:22–05:36 | realized POT at expiration is below 2×delta for **all deltas**; managed at 21 DTE, average POT ≈ **0.8× the delta** |
| 05:53–06:02 | 30Δ: theoretical 60%, realized "**55, 50%**" |
| 06:15 | "on a 20 delta option, you're looking at a **10%** probability of touch" (managed) |
| 06:29 | managing cuts POT "by a factor of about half, a little bit greater than half" |
| 07:30 | gap between theoretical and realized **narrows as delta rises**; a 40Δ (80% theoretical POT) "does realize that probability" |
| 11:13–11:31 | calls: managing cuts POT "by **50% plus**" across 10Δ–45Δ |
| 12:16–12:24 | realized POT for **puts slightly below their delta**; **calls ≈ their delta** (managed) |
| 12:39–12:46 | when managed, the put/call difference "becomes minimal" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 05:22 | Realized POT is below 2×delta at every delta because IV is over-stated | ✅ **Agrees in direction.** VRP panel: implied > realized, **10d +1.75 vp, t_NW 8.93, 17/17 years**; but **30d +0.78 (t 2.08) and 90d +0.84 (t 1.30) don't clear.** Their 45-DTE window sits where our premium is weakest, so the size of the gap they show isn't something we'd expect to replicate one-for-one. |
| 07:30 | The overstatement shrinks toward ATM | **Consistent** with the put-skew shape. Untested here as a touch statistic. Adjacent: the short 7-DTE ATM straddle is **NULL** on single names (−1.83% at mid before costs, TEST_INDEX §9 row "Short 7-DTE ATM straddle"). ATM carries no over-statement you can harvest. |
| 06:29 / 11:31 | 21-DTE management cuts POT by >50% | ⚠ **Mostly mechanical** (24 of 45 days observed). The P&L version is ours: ~~21-DTE management PASS, paired +$1.53/share, t +4.26; both arms lose~~ (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners). Fixed (`data/studies/exit_21dte_2026-09-23_fixed.csv`): **21-DTE close − hold −$0.52/share, month-clustered t −2.42** (NULL on return, leaning INVERTED; risk reducer only: sd $9.33 vs $17.09, worst −$291 vs −$617); held +$0.23, managed −$0.29/share. Their claim and ours agree on the shape (less path risk), and the path-risk cut costs return. Neither video shows the managed trade's absolute P&L. |
| 08:37–08:49 | Calls get touched more than puts in SPY because of upward drift and put skew | ✅ **Consistent with our book.** The call side of short premium has repeatedly been the weak side: ETF condor call side **+0.36%/trade, t 0.6**; UVXY bear call **−7.4% net**. Same-delta calls sit closer to spot. |
| 12:13 | "21 days going to significantly compress your P&L volatility" | ✅ **True, and measured by us, not by them.** sd $11.86 vs $23.58/share; worst −$259 vs −$617/share (panel). |
| 03:06 | A 20Δ short call should be expected to trade at ~35Δ at some point | Reasonable risk-budgeting advice ("have some wiggle room"). Untested; no P&L claim. |

## What I would take

1. **The sizing heuristic in their words:** expect a 20Δ short leg to spend time at 25–35Δ even when managed.
   That's a delta-budget rule, not an edge claim, and it's compatible with "size to the max loss".
2. **The put/call asymmetry as a caution:** at equal delta on SPY, the call side is the one that gets tested. It
   agrees with our call-side nulls.

## Not tested, could be

- **Realized POT by delta, held vs 21-DTE exit, on SPY.** Measurable on `data/cache/SPY_puts_v3_2018_2026.parquet`
  (puts only; calls need a v3 pull like `run_spy_puts_v3_pull.py` with `cp='C'`) plus the adjusted SPY panel. Recover
  spot from the chain, since v3 strikes are RAW. ~2 hours. **Not worth queuing:** a touch rate is descriptive, and
  the P&L question it stands in for is already answered (the 21-DTE row).
