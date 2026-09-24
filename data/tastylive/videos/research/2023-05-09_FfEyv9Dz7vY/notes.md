# tastylive / Dr. Jim: "How I Would Manage a Short Strangle Moving Against Me" (2023-05-09 upload, 17:06)

_Reviewed 2026-09-24. Dr. Jim Schultz, solo with a producer, one slide of "patient vs aggressive" management columns,
then his live JPMorgan earnings strangle on the platform. The upload is 2023-05-09 but the content was recorded on a
Friday before Netflix/Tesla report "next week", which fits JPM's Q1 report on 2023-04-14 (not checked against a price
panel). Transcript (`en-orig` auto-captions) is in this folder; the captions garble "Tom Sosnoff" as "Bob Noznoff /
Obama" and "Tony Battista" as "Pony Babista". **There is no study here: it is a decision framework plus one open
trade, and the "tested" half uses prices he says are not the real ones (14:17–14:36).**_

## Verdict: 1.5 / 5

The most honest thing in the video is its conclusion: **"I actually don't know that there's an optimal point here"**
and "I don't think that in this situation there's a clear-cut winner" (08:17–09:30). That's correct, and it's also an
admission that nothing in the segment is evidence. Every claim is a trade-off stated in words.

His own default (**untested → do nothing**) is the one that lines up with our ledger: the only management rule we've
measured on this structure (the 21-DTE close) earns less than holding, and every P&L-conditioned exit we've tested on
short premium is a cost. The rest is untested by us:

- **"Roll out in time when tested, everybody agrees"** (05:02–05:31) is stated as consensus with no data. It adds
  duration exactly where our premium is weakest and pays a fresh spread crossing on a single name.
- **Baby vs full inversion** is framed purely as temperament. No numbers.
- **The trade is an earnings strangle.** The entry itself sits in a cell our ledger closed: earnings premium is real
  at mid and dies at the bid on the full universe (−0.428%), PARKED only on the most liquid names. JPM would plausibly
  be in that bucket, but it's the entry that matters there, not the management.

## Data audit

| item | what the video gives |
|---|---|
| underlying | JPM, one open earnings strangle (120P / 140C), stock ~138 on the day |
| period | one day (~2023-04-14); the trade's outcome isn't shown |
| n | **0 completed trades**; the only data is one live position's greeks and a chain |
| entry rule | earnings short strangle; delta, DTE and credit **not stated** |
| management | a 2×2 of untested/tested × patient/aggressive: untested → do nothing (patient) or roll the untested side in at 20 net Δ (aggressive); tested → roll out in time (both); ITM → baby inversion (patient) or full inversion to ATM (aggressive) |
| fills | live mid-ish chain prices for the untested roll; the ITM example uses prices he says don't represent a 150 stock |
| control | none |
| win rate / avg / tail | none |
| significance | none. He explicitly declines to name a best choice |
| selection | n/a (hypothetical) |

## Numbers as spoken

| @ | number |
|---|---|
| 00:28–00:48 | earnings calendar context: "Netflix and Tesla… next week", then the mega-caps |
| 03:24–03:38 | aggressive, untested: **roll the untested side in once the position reaches ~20 net deltas** |
| 06:30–06:35 | "I have not been in an inverted strangle in at least several weeks… **100% luck**" |
| 08:31–08:36 | the systematised reference points: **45 DTE entry**, portfolio theta and delta/theta ratios, "largely just reference points" |
| 10:25–10:31 | stock "breathing on that **140 call strike**" |
| 11:13–11:25 | position **−40 delta**: short put ~0Δ, short call ~−50Δ |
| 11:59–12:04 | roll the **120 put (~5Δ)** up to **135** for a 135/140 strangle |
| 12:21–12:29 | put roll from **$0.25 to $2.00 → +$1.75** credit |
| 13:35–13:37 | stock at **138** |
| 13:39–14:36 | hypothetical: JPM at **150**, 140 call ITM; "these prices… are not going to be indicative" |
| 14:47–15:06 | full inversion: roll the 120 put to the **150** (ATM) strike |
| 15:33–16:37 | baby inversion: roll to the **145** put, "sandbagging" 5 points below spot |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 02:39–03:05 | **Untested → do nothing**; "the strategy is actually working" even when near a short strike | ✅ **Consistent** with our ledger, not a direct test of it. On our 45-DTE/20Δ strangle panel the unmanaged hold is **+$0.23/share, 74% win** vs **−$0.29** for the 21-DTE close (paired **−$0.52, month-clustered t −2.42**; FIX-1, `exit_21dte_2026-09-23_fixed.csv`, TEST_INDEX §1). Every loser-conditioned exit we've measured on short premium is a cost (straddle −50% stop, credit-spread 2× stop −4.3%/trade t −5.4 vs +0.6% held; `sosnoff_doctrine.md` rule 23). We haven't tested "do nothing near the strike" vs a pre-breach roll specifically |
| 03:21–04:51 | Aggressive: roll the untested side in at ~20 net Δ; gimme = more extrinsic, gotcha = whipsaw | **UNTESTED.** We've never tested a roll on a short strangle. The whipsaw cost he names is the right one to worry about, and it's the one a mid-priced backtest hides: each roll crosses two single-name spreads (our straddle entry spread is a **median 6.5% of mid**, TEST_INDEX §9 "Long straddle entry slippage"). tastylive's own 17-year SPY roll-to-straddle arm (−$5 vs −$55 on the breached subset, no n/t, probably mid) is the only data point for it; see `2023-01-23_W9KBp_3BpVM/notes.md` |
| 05:02–05:31 | **Tested → roll out in time; "everybody agrees"**; "duration over direction"; softens greeks, more credit, wider breakevens | **UNTESTED on strangles · negative prior.** (1) The added credit comes from tenor, and tenor is where our premium is weakest: VRP **10d t 8.93 vs 30d t 2.08 vs 90d t 1.30** (TEST_INDEX §9 "More Tom… 26 clips"). (2) On credit spreads, Sosnoff's own "never roll a loser out and wider" is the doctrine and our credit-spread exit evidence agrees with it (`sosnoff_doctrine.md` rule 23; 2×-stop −4.3%/trade t −5.4 vs held +0.6%). A same-strike roll out isn't wider, so that's adjacent, not a match. (3) It's a close plus a new 45-DTE entry, and our new-entry evidence on single names is NULL (hold +$0.23/share) and fails on costs at short tenor (10-DTE single-name selling, costs = **136% of gross**, TEST_INDEX §1) |
| 05:53–07:40 | ITM → go inverted to neutralise direction; he prefers a **baby inversion** (5 points below spot) to a **full** (ATM) | **UNTESTED.** Pure trade-off framing. A full inversion locks in the whole ITM amount as intrinsic in exchange for peak extrinsic; the baby one keeps a directional lean. Without a path distribution there's no way to rank them, which he concedes (08:17) |
| 06:30–06:35 | Not being inverted for weeks is "100% luck" | ✅ Honest, and matches our reading of management outcomes as path luck at n = 1 |
| 08:17–09:30 | "I don't know that there's an optimal point… it's always trade-offs"; even 45 DTE and portfolio ratios are "reference points" | ✅ **AGREES** as a statement of evidence. It's also the video's own admission that it has none. Our only measured tastylive "reference point" on this structure, the 21-DTE close, came out NULL on return, leaning INVERTED, and a risk reducer only (TEST_INDEX §1, FIX-1) |
| 12:33–13:00 | Rolling up to a 135/140 strangle is "a huge gimme" (+$1.75), but you surrender the "real estate" between the strikes | ✅ Correct as a trade-off. ⚠ The extra credit is paid for in short gamma at the money, the same point as `2023-01-23_W9KBp_3BpVM/notes.md` makes about "outlier risk" |
| 00:00–01:20 | Context: the trade is an **earnings** short strangle | ⚠ **The entry cell is closed on our ledger.** Earnings vol premium: **+0.601% at mid, −0.428% at the bid**, crossing costs **171% of gross**; PARKED only on the top ~40% by volume (+0.284% at the bid, t 1.1) (TEST_INDEX §9 "Earnings vol premium"). JPM is liquid enough to plausibly sit in the PARKED bucket; that cell is below the t bar |

## What I would take

1. **His default: untested → do nothing.** It's the one line that agrees with what we've measured, and he says it
   without a sales pitch.
2. **"There's no clear-cut winner"** is the right label for everything else in the segment, from the presenter.
3. **Nothing to adopt, nothing new to test beyond the existing spec.** Roll-in, roll-out and inversion are the same
   harness as the two sibling reviews.

## Not tested, could be

These fold into the roll / delta-band harness specced in `2023-01-23_W9KBp_3BpVM/notes.md` and
`2023-07-01_kPco6uly26E/notes.md`; they're extra arms, not a separate study (specs only; not queued):
- **Roll-out-when-tested arm.** On the 21-DTE panel entries (`exit_21dte_2026-09-23_fixed.csv`), at the first EOD
  close beyond a short strike: buy the whole strangle at the ask and sell the next monthly (~+28 days) at the same
  strikes at the bid; hold to that expiry. Compare to hold, paired per entry, month-clustered t ≥ 3, both halves
  same sign; report worst trade and CVaR, and P&L per day of capital at risk (the roll lengthens the trade, so a
  per-trade mean flatters it).
- **Inversion arms.** At the first close with the tested short ITM by ≥ 1× the entry expected move: (full) roll the
  untested short to the ATM strike; (baby) roll it to one strike-increment short of spot on the untested side. Hold
  to expiry; same paired statistics.
- **Pre-breach roll-in arm** (his "aggressive, untested"): when net position delta reaches ±0.20 per 1-lot, roll
  the untested short to 30Δ. This is the delta-band arm of the ROKU spec with a tighter trigger.
- **Prior:** all three ≈ zero at mid and negative after costs on single names; roll-out additionally dilutes into
  the 30–90d tenor where our VRP doesn't clear. Worth running only as arms of the one study.
