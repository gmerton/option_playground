# tastylive / Calculated Risk: "Jim Schultz on Short Strangles vs Iron Condors, and When to Use Each." (2026-07-28, 11:08)

_Reviewed 2026-09-24. Jim Schultz solo, an education segment with a live walk-through on the tastytrade platform
(GDXJ, September expiry, 53 DTE). Transcript (`en-orig` auto-captions) in this folder. **There is no study in this
video.** Every number is one quote read off the platform at mid, on one day. Not Sosnoff; Schultz ranks the short put
#1 and the strangle #2 (01:41–01:54)._

## Verdict: 2 / 5

The mechanics are right, and the structural trade-off is described fairly. On his own GDXJ example, buying $5 wings
cuts the credit from $4.00 to $1.50, theta from ~$10 to $2 a day and the buying power sharply, and it makes the worst
case known on entry. That part is a real margin and tail trade-off, and it's the correct reason to choose between
the two.

Three problems cap it:

- **No expectancy claim is supported, and our ledger says neither structure earns at real fills on non-index names.**
  45/20Δ strangles on 44 liquid names: hold **+$0.23/share**, so ≈ flat (TEST_INDEX §1, 21-DTE row). ETF condors: **+0.36%/trade,
  t 0.6**. The only short-premium cell that certifies is **index puts after a selloff with high IV** (SPY bull put
  t 6.07 + SPX condor t 5.21, one bet). That cell is a condor, which is awkward for "I don't love iron condors".
- **"Less credit" is per contract, not per dollar of risk.** His own numbers give almost the same credit per buying
  power: strangle $4.00 on "about a thousand dollars" ≈ 40%, condor $1.50 on a $3.50 max loss ≈ 43%. What the wings
  really cost is **friction**: four legs instead of two. The video never mentions it.
- **Two factual slips.** A short put's risk is large but **not "unlimited"** (04:45, 08:51). Here the cap is ~$79/share.
  And "room to adjust" is sold as the strangle's advantage (02:26–02:31), yet every P&L-conditioned adjustment we
  have tested costs money.

The sizing advice is sound: small accounts and beginners should use defined risk. It's a risk-of-ruin argument, not
an edge argument, and it's the most useful thing in the segment.

## Data audit

| item | what the video gives |
|---|---|
| underlying | GDXJ (demo); XLU named as the other candidate. Screened by "IV rank high to low" on a tasty default watch list (05:16–05:41) |
| period / n | **none**: one live quote on one day |
| entry rule | 30–60 DTE ("closer to 45"); short strikes "around one standard deviation", just outside the platform's expected move (06:40–07:45); skip names with earnings pending (05:43–05:57) |
| structures | short strangle 83P / 115–116C (≈16Δ put, ≈23Δ call); iron condor = the same shorts + 78P / 121C long wings ($5 wide) |
| management | "have your adjustments ready" (01:26, 02:14); no rule given. Condor = "set it and forget it" (10:58–11:00) |
| fills | platform analyzer, i.e. **mid**. Channel disclaimer: "not presented net of all commissions… multi-leg option strategies incur higher transaction costs" |
| control | none; the two structures are compared on entry Greeks only, never on outcomes |
| win rate / avg / tail | none |
| significance | none |
| selection | high-IV-rank names in a gold-miner rally (GDXJ +34% in the trailing window of our August retrospective, `data/studies/august_2026_retrospective.md` l.32). "Serious upside skew" noted (07:51) |

## Numbers as spoken

| @ | number |
|---|---|
| 01:41–01:54 | strategy ranking: short put #1, short strangle "a very, very strong second" |
| 02:00–02:07 | strangle strikes "right around that one standard deviation marker" |
| 06:10–06:18 | XLU IV rank **53.4**, GDXJ IV rank **51.5**, both "really good" |
| 06:40–06:46 | GDXJ September, **53 DTE**; "anywhere between 30 and 60… completely fine" |
| 07:13–07:17 | put 83–84 strike, delta **15–17** |
| 07:41–07:57 | call 115–116, "about a 23, 24, 21 delta"; sells the **23Δ** call |
| 08:05–08:10 | net delta **about −7** (−23 + 16, consistent) |
| 08:12–08:22 | strangle credit **$4**, buying power "only about **a thousand dollars**"; fits a $15–20k account |
| 09:08–09:13 | strangle theta "nine dollars, almost **ten dollars**" a day |
| 09:23–09:31 | condor wings **78P / 121C**, "basically a five dollar wide iron condor" |
| 09:36–09:42 | condor credit **$1.50**; theta "only **two dollars** a day" |
| 10:32–10:42 | accounts **$15–25k or less** → condors "pretty exclusively"; **$30–50k+** → add strangles |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 03:22–03:39 | "I don't love iron condors… they're really hard to make money" | ✅ **Agrees, and we know the mechanism.** Davis XSP put condor (TEST_INDEX §9): the credit spread beats the condor **12 of 12** configurations after costs, because **the two extra legs cost ~3× the friction** (−3.2 to −4.4pp of ROC vs −1.2 to −1.7pp). ETF condor (20 ETFs, 45 DTE, 35/25Δ): **+0.36%/trade, monthly t 0.60** (`etf_condor_call_side_2026-09-16.md`). ⚠ But it's not a condor-vs-strangle result. The strangle is ≈ flat as well (next row). And the one certified short-premium cell is an **SPX condor** (bearish-high-IV, t 5.21, `sosnoff_doctrine.md` l.42). |
| 01:35–01:54, 08:54–08:56 | Short strangle is a top-2 strategy | **NULL on single names/ETFs at real fills.** 14,367 45-DTE/20Δ strangles, 44 names, 9 yrs: hold **+$0.23/share (74% win)**, 21-DTE close −$0.29 (TEST_INDEX §1 21-DTE row, corrected 2026-09-24 FIX-1; `exit_21dte_2026-09-23_fixed.csv`). 30d VRP +0.78vp, t 2.08: the premium is thin at his tenor. `sosnoff_doctrine.md` rule 11: NULL on single names |
| 09:36–09:49 | The condor collects "a lot less" and theta drops to $2, but buying power falls because the max loss falls | ✅ **True per contract; misleading per dollar.** His own figures: strangle $4.00 / ~$1,000 BP ≈ **40%**; condor $1.50 / $3.50 max loss ≈ **43%**. Per unit of capital the credit is about the same. The real difference is (a) a known worst case and (b) **friction** (local check below). |
| 02:33–02:40 | Strangle = "unfiltered exposure" to theta and vega | Correct as Greeks. Having more theta isn't having more edge: the unfiltered exposure is to a premium that's ≈ 0 at real fills (row above) |
| 02:26–02:31, 10:46–10:52 | Strangles are better because "you can make so many adjustments"; they need more skill because there are more decisions | ❌ **No support, negative prior.** Every P&L-conditioned management rule we have tested is a cost: straddle −50% stop INVERTED, BE+1R −0.08R, "extended→tighten" −0.19R (t −2.8). Even the fixed-date 21-DTE close costs return (**−$0.52/share vs hold, t −2.42**; risk only: sd $9.33 vs $17.09). Adjusting more often means more round trips. |
| 04:45, 08:49–08:51 | Undefined risk "unlimited on the downside" | ❌ **Wrong as stated.** A short put's loss is capped at strike − credit (~$79/share here). The *practical* point is right and worth keeping: the worst case (~$7,900/contract) is ~**8×** the ~$1,000 BP, so sizing to BP understates the tail |
| 05:05–05:41 | Both structures suit high IV rank; sort the watch list by IVR | **PARTIAL.** Own-name IV rank as a selector: **NULL** on single-name bull puts (zivr −1.89pp, t −1.25; within-date +0.25pp, t 0.22; TEST_INDEX §1 "IV rank vs credit/width"), and `sosnoff_doctrine.md` C1/C8 read it as contradicted. What sorts names is **credit/width** (+8.57pp, t 3.74). The index-level version (high VIX, after stress) is the certified one. GDXJ/XLU are ETFs, where own-IVR is untested |
| 05:43–05:57 | Avoid names with earnings pending; trade earnings as a separate play | ✅ **Agrees on the avoid half.** Selling the earnings crush: **−0.428% at the bid**, 7 of 8 years negative, costs 171% of gross (TEST_INDEX §9 l.265). Trading it "as a specific earnings play" doesn't survive real fills |
| 10:23–10:42 | Beginners and small accounts ($15–25k): condors only; $30–50k+: add strangles | ✅ **Reasonable, and it's a risk argument.** Defined risk limits ruin; on small accounts one undefined gap can be a large fraction of NAV. Our only non-inverted tail lever is **size / exclusion** (`sosnoff_doctrine.md` rule 25). Nothing here says either structure has an edge at any account size |
| 09:28 | $5-wide wings on a ~$100 ETF | ✅ Consistent with the house wing rule: **anything but the narrowest wing** (rule 16: 0.25Δ-on-0.30Δ wing −0.04% net ROC vs +2.66 to +3.10% for 0.20–0.10Δ, exploratory). His wings sit ~8–9Δ, i.e. wide |
| 10:58–11:00 | The condor is "set it and forget it" | Fine as ergonomics. Held-to-expiry is also the arm that did best in the 21-DTE test (hold > 21-DTE close, t −2.42 for the close) |

### Local friction check (~2 min, `options_cache`, mid-derived, not a backtest)

GDXJ isn't in `stocks.options_cache`. Proxies: **GDX** (its parent, more liquid, so a floor on GDXJ's friction) and
**XLU** (his second candidate). Fridays 2024-01 → 2026-02, expiries 40–60 DTE (GDX n 161, XLU n 138 date×expiry rows).
Structures: 16Δ put / 20Δ call strangle vs the same shorts with 8Δ wings. Friction is the house model, round trip:
25% of each leg's bid-ask per side + $0.65/leg/side. Script:
`scratchpad/ic_friction.py` (session scratch, not committed).

| median | GDX | XLU |
|---|---|---|
| strangle mid credit | $0.94 | $0.87 |
| condor mid credit (share of strangle kept) | $0.50 (57%) | $0.42 (55%) |
| round-trip friction, **strangle, % of credit** | **10%** | **13%** |
| round-trip friction, **condor, % of credit** | **38%** | **43%** |
| condor friction ÷ strangle friction ($) | 1.9× | 1.9× |
| condor credit ÷ max loss | 0.18 | 0.22 |

So on liquid ETFs the wings roughly **double the dollar friction and halve the credit**. Friction goes from ~10% to
~40% of what you collect. That's the same mechanism as Davis (~3×), smaller because here the wings are far OTM. A
round trip overstates it for condors held to expiry with worthless wings, and zero-bid quotes are missing from
`options_cache` except at expiry. Neither changes the order of magnitude. ⚠ His quoted condor kept **38%** of
the strangle credit ($1.50 / $4.00), which is lower than our 55–57%. His wings are closer ($5 on ~$100), and upside skew
was steep on the day.

## What I would take

1. **The account-size rule, as a risk rule:** defined risk below ~$30k NAV. Say it for the right reason (no single
   gap can take a large share of the account), not because the condor is the better trade.
2. **The worst-case-vs-BP ratio as a sizing check:** a naked strangle's BP (~$1,000) was ~8× smaller than its
   downside to zero (~$7,900). Size undefined risk to the gap, never to the BP.
3. **The friction number for the trade-off:** on liquid ETFs, wings take friction from ~10% to ~40% of the credit.
   The tail protection isn't free, and the video never prices it.

## Not tested, could be

- **Paired strangle vs iron condor at real fills, same name/date/shorts, sized to equal max-loss budget.** Liquid
  ETFs + the 44-name strangle panel; 45 DTE, 16/20Δ shorts, wings at 10Δ and 5Δ; hold to expiry and 21-DTE close;
  arms scored per dollar of *stress loss* (not BP). Primary: condor − strangle net return per unit of worst-case
  risk, month-clustered t; report the tail (worst 1%, worst month) separately, because that's the one place the
  condor could win. Reuse the fixed `run_21dte_exit_test.py` harness (and its zero-bid/expiry guard) plus v3 wing
  quotes. **What makes it new:** Davis was a *put* condor vs put spread on XSP; the ETF condor study had no strangle
  arm; nothing in the ledger pairs the two structures at real fills. **Prior: the strangle wins on mean and the condor
  on tail, both ≈ 0**, so it's probably a sizing answer, not an edge. Not queued.
- **Own-IVR on ETFs** (GDXJ/XLU-type names) as a gate on the strangle: the single-name IVR NULL doesn't cover ETFs.
  Cheap on the same harness. Low prior: C1 found the lowest IVR quintile earned most.
