# tastylive: "The Bullish Strangle Nobody Talks About Almost Doubles Your Return. 20 Years of SPY Data." (2026-05-26, 14 min)

_Reviewed 2026-09-23. Mike (host) plus a co-host, live. The transcript (`en-orig` auto) is in this folder. ⚠ **This is the
same research deck as `2025-07-25_NhgIYLeCA3U`** ("I Abandoned Neutral Strangles…"): identical slide text, arms and
takeaways, re-read 10 months later with a new title. **One study, not two.** Read those notes for the full data audit and
the skew-vs-delta argument; this file records what this cut adds: the "almost twice" number, a clearer arm list, and
the host's live IBIT / micro-ES delta-shifting strangle._

## Verdict: 2 / 5

The new number is "same success rate with **almost twice the annualized return on capital**" for the 30Δ-put / 16Δ-call
bullish strangle vs the 16Δ neutral. It's a real feature of the data they show, and it's exactly what +0.14 of SPY delta
should earn over 20 years of a quadrupling index. There's no delta-matched control, no costs, no n and no t.

The co-host gives the best line in the batch (06:26–07:17): the short call on SPY is "often… just not selling an option for
very much money", and "is there even much of a premium in there to sell that 40 cent call?" **That's our VRP-by-tenor
finding in plain words.**

The host's live trade (a year-long MES strangle, rolled up whenever the call is tested) is n = 1 and its dollar figures are
internally inconsistent.

## Data audit (delta from the 2025-07-25 notes)

| item | this cut |
|---|---|
| Arms (13:03–13:31, clarified on air) | 16Δ/16Δ neutral · **30Δ put / 16Δ call** bullish · 16Δ put / 30Δ call bearish · 30Δ naked put |
| Period / DTE / exit | "past two decades", SPY, 45 DTE, **closed at 21 DTE** (02:27–02:48) |
| Headline | same success rate, "**almost twice the annualized return on capital**" (03:31–03:35) |
| Tail | the largest loss is "just a little bit less" for the neutral (03:45–03:50) |
| Fills / costs, n, t, benchmark | none (same as the original deck) |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 00:27–00:33 | SPX ~1,000 in 2012 → ~7,500 "now" (the sample's drift, stated by the host) |
| 03:18–03:35 | Bullish vs neutral: "very similar success rates", annualised ROC "significantly better… **almost twice**" |
| 03:38–03:50 | Neutral: a little less ROC volatility; largest loss a little lower |
| 04:13–04:40 | Naked 30Δ put vs bullish strangle: the put has a higher success rate and a higher annualised ROC; the strangle is less volatile with smaller max losses |
| 08:57–09:05 | Bearish strangle: still slightly positive annualised ROC, lower success, "significantly lower" ROC |
| 11:01–11:27 | Host's MES trade: started as a 6,600 / 7,100 strangle late last year, now a **7,600 straddle**, "up $1,600", "picked up **534 points** of premium… in SPX terms $53,000… you could close… for a net win of **33 grand on one contract**" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| title / 03:31 | Bullish strangle "almost doubles your return" | **Delta, not premium.** A short put spread has no edge over its own delta on our data (+$7/contract, t 0.26, 4,742 paired entries, real fills). CSP ≈ delta-matched stock minus costs (BCI, 326 names), and the unstopped delta-matched stock beats the put (+0.49 vs +0.36). "Twice the ROC" is what the extra ~0.14 delta should earn on an index that went 1,000 → 7,500. The claim needs a stock arm and doesn't have one |
| 01:14–02:06 | If the call is worth 50¢ against a $2 put, "just get rid of the call and move the put higher" | **Agrees in spirit.** It's a credit-per-risk judgement on each leg, the within-trade cousin of credit/width. ⚠ Our ARM B result: dialling credit/width with *your own* strikes does nothing (non-monotone). Credit/width works **across names**, not by re-striking one name |
| 06:26–07:17 (co-host) | The SPY short call often isn't paid; "is there even much of a premium in there" (implied vs realised) | ✅ **Best claim in the video, and it matches our tenor result.** VRP panel SPY: 10d +1.26vp (t 5.22) clears, **30d +0.69vp (t 1.57) doesn't**, and at VIX < 15 the 30d premium is +0.17 (t 0.49). In a low-vol grind the call side sells almost nothing, and the drift eats it. (Our 44-name strangle panel's per-name losses aren't citable: that sample drops the both-worthless winners. See the notes for `2025-07-25_NhgIYLeCA3U`.) |
| 04:00–04:07 | "The more [SPX] goes down, the more inclined I am to stay in… probabilities of reversals… get substantially higher as you go down 10, 15, 20%" | **Partly supported, as a regime cell.** Selling index puts after a selloff at VIX ≥ 20 is our one certified bucket (SPY t 6.07, SPX t 5.21). ⚠ **Our crash-leader study vetoes the stock-level version** (never buy deep drawdowns in a healthy tape). The index-level version is the certified one. "Probability of reversal rises with depth" is untested as stated |
| 08:21–08:39 | Undefined-risk neutral/skewed strangles are easier to manage in an index/ETF than in a single name like Micron | ✅ Agrees: liquidity and gap risk are the gate. Single-name short-dated selling is net negative (costs 136% of gross) |
| 09:11–09:36 | With 4–5% on cash, perpetually betting "the market not going up" is tough | ✅ Correct and under-appreciated: the bearish tilt and the neutral call leg both fight drift and the risk-free rate. Nothing to test |
| 10:06–12:47 | Host's process: a year-long strangle (IBIT, DraftKings, MES), never take upside risk: when the call is tested, **shift the whole strangle up** so the put becomes the tested side. "Up $1,600", "534 points of premium", "net win of 33 grand" | **n = 1, and the numbers don't reconcile.** MES is $5/point, so 534 points = $2,670 of premium on one MES. "$53,000 in SPX terms" rescales to a $100 multiplier, and "a net win of 33 grand" can't also be "up $1,600" on the same contract. Mechanically it's **rolling the untested side in** until the position is a straddle: the arm tastylive's own 2023 rolling study (`2023-01-23_W9KBp_3BpVM`) found best *among breached trades*, at mid, with no n. On our data it's untested. Every time it rolls it keeps adding long delta in an up-trend, so it's the bullish strangle again, done dynamically |
| 13:38–13:47 | "If you can… shift your delta and adjust your delta as it moves, you can really get out of harm's way" | ❌ **Unfalsifiable as stated.** Our exit and management ledger: every P&L-conditioned adjustment tested is negative. The only management rule on file as certified is the fixed-date 21-DTE exit (+$1.53, t 4.26), and that result now needs a re-run (its sample drops the both-worthless winners). "Get out of harm's way" by rolling toward the money adds gamma |

## What I would take

1. **The co-host's point, adopted as wording:** "the short call on an index in a low-vol grind isn't paid". It's our
   30d-VRP-doesn't-clear finding in one sentence, and it's the mechanism behind the tastylive results in both cuts.
2. **The same caution as the 2025-07-25 notes:** judge any skewed short-premium structure against delta-matched stock.
3. **Nothing to adopt.**

## Not tested, could be

- **The primary test is the same as in the 2025-07-25 notes:** a skew sweep with a delta-matched SPY arm (~1 day).
- **Plus the host's dynamic version, as a fifth arm.** Start from the 16Δ/16Δ neutral. Whenever the short call's delta
  reaches ≥ 0.30 at an EOD close, buy the call at the ask and sell a new 16Δ call and a new 30Δ put at the bid (the "shift
  up"); hold to the 21-DTE close. Compare with the static bullish strangle and with delta-matched stock carried at the
  position's daily delta.
- **Effort:** +½ day on that harness; it needs daily marks.
- ⚠ **Use the path-coverage guard.** A missing-mark day that silently skips a roll is how `run_iv_condor_study.py` reported
  94–99% win.
