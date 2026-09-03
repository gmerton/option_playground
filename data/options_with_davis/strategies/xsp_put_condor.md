# XSP Put Condor — credit spread financing an ATM debit spread

> **Verdict:** A legitimate, well-explained four-leg structure sold on a misleading headline. The
> quoted "94% POP" counts as a win any outcome where you keep a ~$5 token credit; the advertised
> $111–322 max profit requires the index to *fall* 0–9% by expiry, and the 6% tail loses ~$880.
> The embedded ATM put debit spread is a structurally negative-expectancy leg (long index puts pay
> the variance risk premium), financed by the one leg that has positive expectancy. No DTE stated,
> no exit rules, no backtest, no trade log.
> **Conviction 1/5 · Risk 6/10 · Tested: YES — claim refuted, see Backtest below.**
> Source: `videos/strategies/2026-08-08_wNaiAmbrLLs` ("The ONE Options Strategy I will ALWAYS have
> in my account", 34:08).

## Vehicle: XSP, not SPX

Davis argues small accounts should trade **XSP** (mini-SPX, 1/10 notional) rather than SPX, and
this part of the video is sound:

- Cash-settled, European-style (no early assignment), and for US filers the 60/40 §1256 treatment.
- **The granularity argument is the real one and he explains it well.** For a fixed dollar risk,
  SPX's $100 multiplier on a ~5,500 index buys a spread only a few index points wide, so the long
  strike sits very close to the short. On XSP the same dollar risk buys a spread ~10× wider in
  percentage terms, pushing the long strike much further from spot. Same max loss, materially
  harder to reach it.
- **Open interest ≠ liquidity** on index options. His explanation is correct: market makers quote
  both sides and hedge in the open market; a zero-OI strike is fillable if you price toward the
  bid. Overstated as "guaranteed to get filled" — quotes can be pulled or widened — but the
  substance is right, and it's a genuine misconception among small-account traders.

## Structure (as constructed on-screen)

Four put legs, all same expiry. With XSP ≈ 770:

| Leg | Role | Example strike |
|---|---|---|
| Long put | debit spread, long | ~770 (ATM) |
| Short put | debit spread, short | ~769 (1–3 pts below) |
| Short put | credit spread, short | ~700 (~9% OTM, 10–20Δ) |
| Long put | credit spread, long | ~690 (10–11 pts below) |

Ordered by strike this is `+770 / −769 / −700 / +690` — a **long put condor with deliberately
asymmetric wings** (broken-wing), entered for a small net credit.

- The **wide OTM put credit spread** generates the credit and defines max risk.
- Part of that credit buys the **narrow ATM put debit spread**.
- Sizing: pick the short put by delta, then set the credit-spread width to hit your dollar risk
  (~10–11 XSP points ≈ $1,000). Widen the debit spread for more max profit, at the cost of a
  lower POP and a smaller net credit.
- **Net credit must stay positive** — that is the entire "no risk to the upside" claim.

**Payoff arithmetic** (confirmed against his on-screen numbers):
- Max profit ≈ debit-spread width × 100 + net credit → **$111 at 1.1 wide, $322 at ~3.2 wide**
- Max loss ≈ (credit width − debit width) × 100 − net credit → **~$878–951**
- Max profit zone: index between the credit-spread short (700) and the debit-spread short (769)

He also describes the mirror-image **call condor** for a bullish tilt. Same logic, calls.

## What checks out

- The structure does what he says: net credit means no loss if the index rallies, and max profit
  sits in a wide band below spot.
- The comparison method is fair in form — he equalizes **max risk** before comparing the condor to
  a put credit spread and to an iron condor, rather than comparing raw premiums.
- He is explicitly honest that a high win rate still means losses ("85% win rate means 15% of the
  time you lose"), and that structure choice is a POP-vs-max-profit trade-off, not a free lunch.
- The versatility claim is true: the four strikes give real control over the risk/reward shape.

## Red flags

1. **"94% POP" is doing dishonest work.** Break the outcomes down. Index **up or flat** — every put
   expires worthless, you keep the net credit, roughly **$5**. That is the modal outcome and it
   counts as a "win." Index **down 0–9%** — you reach the $111–322 tent. Index **down >9%** — you
   lose up to ~$880. So the advertised max profit requires being *right about direction*, and the
   headline win rate is mostly composed of $5 outcomes. He never presents the payoff this way.

2. **The embedded debit spread is long ATM index puts — a negative-expectancy leg.** Index puts
   are persistently rich relative to realized (the variance risk premium is the whole basis of the
   short-vol book we already run). His central claim is that adding this leg *improves* on a plain
   put credit spread at equal risk. That is a claim that a negative-EV component plus a positive-EV
   component beats the positive-EV component alone. It might be true if the credit spread's tail is
   sufficiently reduced — but it needs evidence, and he offers none.

3. **No DTE anywhere in 34 minutes.** POP, max profit, theta and the entire risk/reward comparison
   are undefined without it. This is the single biggest gap.

4. **No exits, no management, no adjustment rules.** No profit target, no stop, no roll, no
   guidance on what to do when the index enters the tent early or approaches the short strike.

5. **Zero evidence.** No backtest, no trade log, no equity curve, no track record. The entire video
   is strike selection inside a broker analyzer. The POP figures are the platform's model output,
   not observed frequencies.

6. **The casino analogy is wrong.** He justifies a ~2% win-rate advantage by comparing it to a
   casino's house edge. A casino's edge is *positive expected value per bet*; a 2% higher win rate
   paired with a worse tail is not automatically positive EV. Win rate and EV are different
   quantities and he substitutes one for the other.

7. **Tail correlation.** Per-trade risk is capped, but the loss scenario is a broad index decline —
   which would hit every open condor simultaneously, plus the rest of a short-vol book. Defined
   risk per position is not diversified risk across positions.

## Testable claims (ranked)

1. **Does the condor beat a put credit spread at equal max risk?** His headline claim. Direct test:
   4-leg put condor vs 2-leg put credit spread on SPX (scale to XSP), same short strike, same max
   loss, held to expiry, across our full options history. Compare capital-weighted return, not win
   rate. This is the one that matters and we have the data to settle it.
2. **Does the ATM debit spread pay for itself?** Decompose realized P&L into the credit-spread leg
   and the debit-spread leg separately. Prior: the debit spread is a persistent drag whose value is
   tail insurance, not profit.
3. **DTE sensitivity.** Since he never specifies one, sweep it — the structure's behavior at 7 vs
   30 vs 45 DTE is likely very different.
4. **Is the "no upside risk" net-credit constraint binding in practice?** He shows the credit
   collapsing to zero as he moves the short strike further out, and concedes you must give up a few
   cents to get filled on XSP. Test whether the structure is actually enterable for a net credit at
   realistic fills, or only at mid.

## Backtest (2026-08-08) — claim refuted

`run_davis_condor_study.py` · output `davis_condor_study.csv` · XSP 2018-01-01 → 2026-02-20,
Friday entry and expiry, held to expiry, no management. Settlement from put-call parity on the
expiry chain. Condor vs a put credit spread on the **same short strike**, long strike chosen from
the live chain so max loss matches — Davis's own comparison method. Priced at mid and again with
50% of each leg's bid-ask crossed on entry.

### 1. The structure usually cannot be built at a net credit

His "no risk to the upside" rule requires a positive net credit. Rejection rates on Fridays where
a structure was otherwise constructible:

| Debit width | Rejected for no-credit |
|---|---|
| 1 strike, 0.20Δ | 33–51 of ~390 (8–13%) |
| 1 strike, 0.15Δ | 100–183 of ~390 (26–47%) |
| 1 strike, 0.10Δ | 293–344 of ~390 (75–87%) |
| **3 strikes, any Δ** | **360–369 of ~390 (93–95%)** |
| **5 strikes, any Δ** | essentially always |

**His on-screen demo of widening the debit spread to lift max profit from $111 to $322 is not
reproducible.** That is the mechanism that makes the payoff attractive, and it survives the
net-credit constraint on roughly 1 Friday in 20. Only the 1-strike debit spread has a usable
sample, and its max profit is the minimum the structure can produce.

### 2. Head to head at equal max risk (1-strike debit, the only viable width)

Capital-weighted ROC per trade, mid / with costs:

| DTE | Δ | n | Condor | Spread | Winner (cost) |
|---:|---:|---:|---|---|---|
| 7 | 0.10 | 26 | +1.42 / −0.32 | +2.49 / **+2.00** | spread |
| 7 | 0.15 | 186 | +3.02 / +0.74 | +2.86 / **+2.10** | spread |
| 7 | 0.20 | 319 | +3.28 / +0.55 | +2.97 / **+1.90** | spread |
| 14 | 0.15 | 217 | +0.15 / −3.05 | +0.79 / **−0.31** | spread |
| 14 | 0.20 | 335 | +0.23 / −2.74 | +1.12 / **+0.07** | spread |
| 30 | 0.10 | 54 | −2.81 / −6.71 | −2.23 / **−3.64** | spread |
| 30 | 0.15 | 257 | +0.09 / −3.30 | +1.21 / **+0.02** | spread |
| 30 | 0.20 | 331 | −0.49 / −3.89 | +0.75 / **−0.53** | spread |
| 45 | 0.15 | 264 | −0.04 / −4.45 | +1.33 / **−0.33** | spread |
| 45 | 0.20 | 334 | +0.91 / −3.73 | +2.25 / **+0.35** | spread |

**The credit spread wins 12 of 12 configurations once costs are included** (10 shown; the two
0.10Δ rows at 14/45 DTE behave the same). At mid the condor edges ahead in 3 of 12 — which is the
comparison Davis implicitly makes, since every number in the video is analyzer output at mid.

### 3. Why: the extra two legs cost about 3× the friction

The condor loses ~3.2–4.4pp of ROC to slippage; the spread loses ~1.2–1.7pp. At 30 DTE / 0.15Δ:
condor +0.09 → −3.30 (−3.4pp), spread +1.21 → +0.02 (−1.2pp). **The incremental friction of the
two extra legs exceeds the entire claimed edge.** Davis concedes on-screen that XSP spreads are
not tight and that you must give up a few cents to fill — so the 50%-of-spread assumption is
realistic, not conservative.

### 4. The claimed win-rate advantage does not appear

He claims ~2pp. Observed condor 87.9–96.2% vs spread 87.8–96.2% — indistinguishable, and the
spread is *higher* in several configs.

### 5. His own example sits at the worst delta

His demo short strike (700 against spot 770) is ~9% OTM, far further out than the 15–20Δ he
verbally recommends. The closest tested delta, 0.10Δ, is where the condor performs **worst**:
−2.81 to −3.39 at mid and −6.71 to −6.92 with costs.

### Caveats

Friday-to-Friday only; held to expiry with no management (he provides no exit rules, so there is
nothing else to test). The 50% slippage assumption is the load-bearing one — at 0% the condor is
competitive, at 50% it loses everywhere. Anyone wanting to rescue the structure would need to show
fills materially better than half-spread on all four legs.

## Notes

Our own book already sells index/ETF premium via defined-risk spreads, so the relevant question is
narrow: **does grafting a financed ATM put debit spread onto a bull put spread improve risk-adjusted
return?** That is a clean, self-contained backtest against work we've already done, and it does not
require adopting anything else from this channel.
