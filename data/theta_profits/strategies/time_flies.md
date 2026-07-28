# Time Flies (Time Fly Spread) — Simon Black

Source: `2026-05-24_319lHEiewRY` — "How Simon Black made 100% with his Time Flies options
strategy" ([watch](https://www.youtube.com/watch?v=319lHEiewRY)). Guest: Simon Black, Wellington
NZ, electrical/software engineer, ~3 yrs trading this; host: John. This is a **second** interview
on the same strategy (the first was ~1 year prior), so it's an update with a longer track record.

## Verdict

> **Conviction: 2.5 / 5 · Risk: 4 / 10 (defined-risk) · Tested: NO (only partially testable)**
> A genuinely well-designed delta-neutral weekly index structure with — unusually for this channel —
> a **separable, weekly-published, multi-year track record** and an honest, self-skeptical presenter
> who quotes his losses, adjustment rate, and a deliberately conservative capital basis. That earns
> conviction well above the Burrito Butterfly. The cap is that the **edge lives in discretionary
> "artistic" curve-shaping he explicitly says cannot be automated** — so the headline results are
> not faithfully backtestable, and the 3-year record sits inside a mostly benign 2023–2026 regime.
> The mechanical *skeleton* can be tested; the alpha-bearing discretion cannot.

## Mechanics

- **Underlying:** RUT (Russell 2000) is his favorite — switched from SPX after tastytrade changed
  margin requirements; says RUT gives a "better looking curve and a wider range." Also valid on
  SPX, QQQ, and /NQ /ES futures options. Prefers **cash-settled indexes (no assignment risk)**.
  `@08:58`, `@10:47`
- **Structure ("time fly"):** a combination of two pieces, **delta-neutral**, sharing one short
  expiration: `@03:28`, `@07:19`
  - **Below the market:** a **put diagonal** (sell near-dated put, buy a further-dated put at a
    different strike) — designed to *benefit from a volatility expansion* (the usual companion of a
    selloff). `@04:42`, `@10:08`
  - **Above the market:** a **call broken-wing butterfly** (unequal wing widths) — designed to
    *benefit from a volatility contraction* (the usual companion of a grind-up). `@06:32`, `@10:08`
  - (At `@16:51` he describes a live trade as put-BWB below + call-BWB above; the diagonal/BWB
    pairing is the canonical description he repeats.)
- **DTE:** **minimum 7 days**; sweet spot 7–14 (found 7–14 gave similar results). His routine: enter
  **Thursday** for the *following* Friday's expiry (~8 DTE short); diagonal long leg is the week
  after. Nothing magic about Thursday — lifestyle choice. `@11:11`, `@11:51`
- **Strike selection (the crux — discretionary):** no formula. Aim for a "**perfect curve**" — a
  smooth, round, even tent peaked at the current price (= visibly delta-neutral). VIX-scaled width:
  VIX ~17 → strikes ~2.2–2.3% either side; VIX 20–25 → ~3%. The **diagonals are consistent
  week-to-week; the BWB widths change almost every week** purely to shape the curve. He has been
  repeatedly asked to automate it (e.g. "sell the 20-delta") and **refuses — "every week volatility
  is different… I want the trade to look good," an "artistic approach."** `@14:21`, `@21:21`,
  `@21:31`
- **Profit target:** **~10% of buying power** (BP ≈ max loss here), taken quickly. Has hit 20% and
  once ~40% (vol spike). "Take the money and run" — emphasized more this year. `@22:21`, `@23:17`
- **Hard time stop:** **out with ~24 hours to go — by Thursday, never hold into the final Friday.**
  Last day = gamma "whips around," a profit can flip to a loss on a 1% move + vol drop. `@27:09`,
  `@28:46`
- **Loss management:** a 1–2% loss is "who cares"; will definitely close at **30–40% down**. "I'm in
  a delta-neutral trade; if the market moves a lot, I was wrong" — happy to take the loss. `@25:18`,
  `@25:45`
- **Adjustments (~15–20% of trades):** "**defense mode**" — minimize loss, rarely a big win. Downside:
  add a **calendar or diagonal** below (benefits from rising vol). Upside (counterintuitive): add a
  **call calendar/diagonal** to give price a target, accepting that vol contraction hurts calendars,
  on the bet vol has "already dropped." Every adjustment costs more, lowering the profit ceiling.
  Also pre-skews the initial trade to carry less upside risk. `@30:13`, `@34:17`, `@33:08`
- **Self-rated risk:** 4–5. Defined-risk ("not selling naked strangles… won't wake up $40k
  underwater"), but diagonals + BWBs "are not beginner strategies." `@40:48`, `@41:08`

## Claimed edge & returns

- **2026 YTD:** 19 trades, **16 winners (~84%)**, "up about 40% after 4 months." `@42:17`
- **2025 (last year):** "just snuck over 100%" — **103%** (took a deliberate Christmas-Day trade
  exited for an $11.60 profit to cross 100%). `@42:47`, `@43:17`
- **3 years consistently profitable**, results published **every week**. `@41:50`, `@43:39`
- **Host John (independent user):** 57 trades over ~a year, **46 winners (~81%)**, avg net profit
  **5.33%/trade**, avg **5.7 days** in trade. `@46:37`, `@47:01`
- **Capital basis (important):** he reports returns as a % of **allocated capital ($3,000/contract)**,
  not buying power / max loss (~$1,000–1,300/contract). John notes that on the usual BP basis the
  numbers would be "**twice or 300%**" higher. So the 100% headline is the *conservative* framing.
  `@43:49`, `@44:52`, `@45:33`

## Objective assessment (where to be skeptical)

1. **The alpha is unfalsifiable discretion.** He's explicit and repeated: the trade *cannot* be
   reduced to a rule ("can I automate this? … no"), and the win-determining step (BWB widths to get
   the "perfect curve") is "artistic," changing every week by feel. So the published win rate is
   inseparable from a skill that can't be specified, replayed, or independently reproduced. A
   mechanical version is **not** the strategy that produced the results. `@21:31`
2. **Self-reported, benign regime.** 2023–2026 was largely a strong/low-vol equity regime favorable
   to a short-gamma-ish delta-neutral tent. Worst loss was 40% (Trump reelection, Nov 2024); "a
   couple of" 20% losses; a 10% crash = "near full loss." The tail is real (defined, but a full
   max-loss week), and the record hasn't been through a sustained high-vol/trending bear.
3. **Pricing is theoretical.** Curves/P&L shown via OptionStrat ("you can't trust exactly… it's a
   guess"); he sometimes leaves a closed trade running in OptionStrat to "see how it would have
   developed." Entry/exit prices in his log are real, but the demoed P&L tents are model prices.
   `@28:01`, `@18:37`
4. **Adjustments don't add edge** by his own account — "almost all my adjustments… just lead to a
   minimized loss." So adjustment skill is loss-mitigation, not a profit engine. `@33:08`
5. **Capital basis cuts both ways.** Reporting on 3× buying power is *honest* (he wants to survive a
   full loss without ruin) and understates the headline %, but it also means **capital efficiency is
   low** (<½ BP deployed) and the eye-catching "100%" is on a self-chosen denominator — compare
   strategies on a common basis before ranking.

## What's genuinely sound (the diamond)

- **Vega design is clever and correct.** Net long vol on the downside (diagonal) and short vol on the
  upside (BWB) deliberately matches the empirical price↔vol correlation (vol rises on selloffs, bleeds
  on grind-ups) — the structure gets a "free" assist from the most common vol behavior in both
  directions. This is a real, thoughtful edge, not marketing.
- **Defined risk, cash-settled, no assignment, no blow-up** beyond a known per-contract max — and he
  sizes (3× BP/contract) specifically to survive a full loss.
- **Separable, multi-year, weekly-published track record** with Discord witnesses and trading
  statements — the single most credible evidence base of any strategy in this KB so far (contrast
  Burrito Butterfly's "I can't untangle the results"). Per-contract reporting lets a reader rescale.
- **Honest, self-skeptical presenter:** quotes losses, adjustment frequency (~15%), a conservative
  capital basis, "take the loss," "I have no edge picking direction," and recommends *Fooled by
  Randomness*. Low oversell relative to the channel norm.
- **Sound discipline:** hard 24h time stop, fast 10% profit-taking, small-loss tolerance, no naked
  short premium.

## Backtestability

- **Testable skeleton:** RUT (or SPX/QQQ), 8 DTE short (enter Thu / next-Fri expiry), put diagonal
  below + call BWB above, VIX-scaled width (~2.2% at VIX≤17 → ~3% at VIX≥20), exit at +10% of max
  loss or close by 24h-to-expiry, hard stop ~−35%. Measure win rate, avg P&L, max loss, EV after
  commissions + multi-leg slippage. That's the honest **floor** — it strips the discretionary
  curve-shaping, so expect it to *underperform* his discretionary record by construction.
- **Not faithfully testable:** the per-week "perfect curve" width-tuning (the claimed edge), and the
  defensive calendar/diagonal adjustments (discretionary, regime-dependent).
- **Data:** likely workable — `silver.options_daily_v3` has SPX/XSP confirmed (Burrito note); need to
  confirm **RUT/IWM and QQQ** coverage with greeks + short-DTE expirations. ⚠ **EOD-only** ("daily"
  resolution) means once-a-day entry/exit fits his "look once a day" style *well* (a genuine plus
  vs intraday strategies), but the 24h-to-go exit and any same-day adjustment can only be approximated
  at the daily close.
- **Honest null comparison:** vs a plain weekly iron condor / plain BWB at matched widths and the
  same exit rules — to see whether the diagonal-below construction adds anything over a generic
  delta-neutral tent.

## Open questions / next step

- Does the mechanical skeleton have positive EV after costs in 2021–2026, and how big is the gap to
  his discretionary record (i.e. how much of the edge is the un-testable curve-fitting)?
- How does it perform isolated to high-vol/bear windows (2022, Aug 2024, Apr 2025) vs the benign
  stretches? The published record is dominated by favorable regime.
- Confirm RUT/IWM + QQQ short-DTE option coverage in Athena.
- Related: host references **Steve Gunn's "fly diagonal" strategy** as mechanically similar
  (independently developed) — worth cross-referencing if that interview gets ingested.
- **Next step (on command only):** backtest the skeleton under `backtests/time_flies/`.
