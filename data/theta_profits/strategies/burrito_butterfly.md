# Burrito Butterfly — Dan ("Boomer Dan")

Source: `2026-06-14_KuQdL4-1IcM` — "This butterfly strategy aims to remove risk as fast as
possible" ([watch](https://www.youtube.com/watch?v=KuQdL4-1IcM)). Guest: Dan ("Boomer Dan"),
~20yr options-income trader; host: John.

## Verdict

> **Conviction: 1 / 5 · Risk: 4 / 10 (defined-risk) · Tested: YES (2026-06-25) → refuted**
> Backtested on SPX 2-DTE, 2023–2026 (~385 trades, EOD, intrinsic settle — see
> `../backtests/burrito_butterfly/RESULTS.md`). The data **falsifies the pitch**: the structure
> has real, bounded losses and **negative expectancy** (−10.6% of risk at realistic costs); its
> ~54% win rate masks a negative mean. Crucially, **adding the butterfly DESTROYS expectancy** vs.
> just buying the debit spread (+1.5% → −10.6%), and that debit spread's tiny edge is only SPX drift
> (always-bullish in a bull market), not strategy edge. His advocated +10%/−10% management made it
> *worse*. Defined-risk (can't blow up) is the one real virtue. **"Risk-free magic money rainbow"
> is marketing; not a diamond.** Caveat: intraday management isn't EOD-testable, but "can't lose"
> is already disproven and the burden of proof is on the claim.

## Mechanics (the shown "beginner" version)

- **Underlying:** SPX (cash-settled, no assignment). XSP (1/10 size) for small/fine-tuning.
  Explicitly avoids stocks (assignment risk). `@37:47`, `@06:53`
- **DTE:** 2–3 days standard; says best results ≤14 DTE; has done 0–14 DTE. `@07:19`
- **Core structure:** ATM butterfly, **15 points wide** (~$0.75 / $75 debit at 2–3 DTE). `@07:05`
- **Directional lean:** add a **5-pt debit spread** to one side, sharing the butterfly's long
  strike (call spread = bullish, put spread = bearish). `@07:54`, `@12:18`
- **Max loss = total debit paid** (~$350 typical, 1 contract). Defined risk. `@08:21`, `@45:00`
- **Profit target:** **5–10% of risk** (~$35–70 on $350), taken quickly. `@11:25`
- **"Build the burrito":** once one side is in profit, add the *opposite* debit spread cheaply
  (funded by the gain) so both wings "float above zero" → claims locked-in profit "no matter
  what" up or down, plus the center butterfly's theta. `@13:42`, `@14:28`
- **"Valleys of death":** two notches in the payoff that are short-butterfly loss zones; he
  claims P&L won't droop into them until the **last 2–3 hours of expiration**, and they can be
  removed by buying butterflies at those strikes. `@15:03`, `@34:51`
- **Adjustments if wrong:** (a) 1:1 stop (~5–10%); (b) add the losing-side debit spread to flatten;
  (c) buy a ~$1 far-OTM option to freeze P&L; (d) "choo-choo train" — add more 15-wide butterflies
  to widen into a condor; (e) "clawback" — overlay XSP debit spreads to lift underwater wings back
  above zero. `@24:40`–`@36:00`
- **Self-rated risk:** 3–4 (5 for beginners). `@41:11`

## Claimed edge & returns

- "5–10% in 2–3 days, no matter what" once converted to the floating structure, with upside to
  "many multiples of risk" if SPX lands in the tent. `@16:31`, `@20:27`
- "Risk-free floating butterfly… there's no way this position can lose… bulletproof." `@00:00`, `@36:06`
- Results "really good" — **but unquantified** (see below).

## Objective assessment (where the pitch breaks down)

1. **"Risk-free / can't lose" is false.** The valleys of death are genuine expiration loss zones;
   he admits worst case "you're exposed to that risk." `@37:18` It's pin/gamma risk at expiry —
   precisely when a 2–3 DTE structure's gamma is largest. "Slow to lose" is a gamma statement that
   **breaks down into expiration**, which is the whole holding period here.
2. **The "free butterfly" is conditional on a winning directional leg.** You fund the opposite
   wing with profit from being *right* on direction. **If you're wrong, you lock in a LOSS**, not a
   free trade ("we would have a slight loss built in"). `@25:27`
3. **He admits NO directional edge** ("I have no clue… absolutely no edge in guessing direction")
   `@08:52` — yet the trade *starts* as a directional bet. His actual "fix" is to always go bullish
   as a hedge to a *separate* bearish strategy — i.e. it only makes sense **inside a larger
   portfolio**, not standalone. `@09:16`
4. **No separable track record.** Asked for results: "it's really difficult for me to untangle
   them from the bigger positions… they all become one big massive trade." `@42:20` = no win rate,
   no P&L curve, no falsifiable evidence. Also: "the way I showed is the beginner version; I trade
   it more advanced" `@41:46` — the demoed strategy isn't the real one.
5. **Winners-only demo.** The live example is a *winning* day ("I was bullish, turned out correct")
   `@19:17`; payoff snapshots are favorable. No losing trade carried to expiry.
6. **Costs hand-waved.** Every adjustment (extra wings, valley-fill butterflies, $1 options, XSP
   clawback) "nicks profit" — multi-leg SPX commissions + butterfly/condor slippage are real and
   eat a **thin 5–10% target**. With no directional edge, base-case EV is plausibly
   ~breakeven-minus-costs unless the adjustment management itself adds edge (unproven).
7. **Operational load contradicts "safe/simple."** Requires active monitoring ("don't walk away"),
   fast reactions, discretionary reads, and good fills — a high-skill, high-attention process, not
   a set-and-forget money rainbow.

## What's genuinely sound (diamond potential)

- **Defined risk, no blow-up:** max loss = debit, cash-settled, no assignment. You cannot get
  destroyed on one trade — real and valuable.
- **Converting a directional winner into a delta-neutral floating structure** (scaling a fly into
  a broken-wing condor as price moves) is a legitimate, widely-used management idea.
- **Low capital per trade** (~$75–350 risk) and a sensible "take small wins fast" discipline.
- **It is partially backtestable** (the mechanical core), so the claims can be checked.

## Backtestability

- **Testable mechanical core:** SPX, 2–3 DTE, 15-wide ATM butterfly + 5-wide one-sided debit spread,
  exit at +5–10% of risk or a fixed stop, else hold to expiry. Measure win rate, avg P&L, max loss,
  and EV *after modeled commissions + slippage*. That's the honest "floor" — it strips the
  discretionary adjustments (which can't be faithfully replayed without rules).
- **Not faithfully testable:** the choo-choo/clawback/valley-fill adjustments and the "always
  bullish as a portfolio hedge" framing — discretionary and portfolio-dependent.
- **✅ Data confirmed (2026-06-25):** Athena `silver.options_daily_v3` has **SPX** (46M rows,
  2010 → 2026-02-20) and **XSP** (21M, same span), with full greeks + bid/ask. Short-DTE
  expirations ARE present (0-DTE daily, 1-DTE ~daily, 2–3 DTE most days), so the structure is
  constructible. **Caveat: EOD ("daily" resolution) only — no intraday**, so the test is a
  mechanical EOD version (enter at close, exit next close on target/stop, else hold to expiry);
  the intraday tactical management can't be replicated. SPX ends 2026-02-20 (~4mo stale).
- A clean test would also compare against the null: a plain ATM butterfly (no debit spread) and a
  plain debit spread, to see whether the "burrito" adds anything over its parts.

## Open questions / next step

- Does the mechanical core have positive EV after costs, given admitted zero directional edge?
- Confirm SPX/XSP option data availability for a backtest.
- **Next step (on command):** backtest the mechanical core under `backtests/burrito_butterfly/`.
