# DC Time Machine (Double Calendar → "Risk-Free" Iron Condor) — Steve Bernich

Source: `2026-06-07_JtGW1wNFNIY` — "How Steve turns Double Calendar Spreads Into Risk-Free Iron
Condors" ([watch](https://www.youtube.com/watch?v=JtGW1wNFNIY)). Guest: **Steve Bernich**
(NavigationTrading; surname per auto-captions `@00:25`, treat as approximate — the company name is
the reliable identifier), career options educator, trading since 1999 / options since 2006, teaching
since 2016. Host: John.

**Identity note — NOT the Flyagonal Steve.** Despite the shared first name and the "double calendar /
risk-free" theme, this is **not** Steve Gunn of `strategies/flyagonal.md` (sjgtrades.com). Different
person, different firm (NavigationTrading vs sjgtrades.com), different structure (a calendar→condor
*transformer*, not a put-diagonal + call-BWB tent). The closest cousin in this KB is actually **Boomer
Dan's Burrito Butterfly** (`strategies/burrito_butterfly.md`) — same "put on a spread, lock it into a
no-lose structure once it's winning, recycle buying power" pitch — and John explicitly points to the
Boomer Dan episode at the end here `@48:12`.

## Verdict

> **Conviction: 2 / 5 · Risk: 4 / 10 (defined-risk on the pre-transform leg) · Tested: PARTIAL (skeleton only)**
>
> **Backtest update (2026-06-25, `backtests/dc_time_machine/`):** the EOD-testable *skeleton* (tight
> +3 Fri/Mon gap, 0.35Δ, hold/PT — no transform) is **net-negative after realistic fills** full-sample
> (−2% to −4% capital-weighted ROC) and does **NOT beat the user's wider-gap SPY dcal**. The tiny ~$0.80
> debit of the Fri/Mon calendar can't absorb 8-leg commissions + slippage (cost destroys ~12 pts of ROC
> vs ~3 pts for a +7-gap calendar). It's positive only in the post-2022 window, and even there earns the
> same ROC% as a wide-gap variant for ¼ the dollars. **Bottom line: the part that's supposed to beat a
> plain double calendar — the intraday transform — is exactly the part that can't be tested on EOD data,
> and the part that can be tested underperforms.** The structure verdict below stands.
> Unlike the Burrito Butterfly, the "risk-free" claim here is **structurally true in its narrow sense**:
> once you collect a net credit ≥ the iron-condor wing width, that condor genuinely cannot lose at
> expiration (cash-settled SPX, no assignment, no pin risk). That earns it above Burrito (1) and roughly
> level with Flyagonal (1.5). But the branding **inverts where the risk lives**: ALL of it sits in the
> *un*-transformed double calendar — which he can only convert ~**60% of the time**, carries **no hard
> stop**, and is exposed to overnight/black-swan gaps for its full debit (~$800–1,500/contract). The
> ~40% that don't transform, plus the hidden fact that **transforming a winner can LOCK IN LESS profit
> than just closing it** (you swap a sure ~$1k gain for a $300 floor + a lottery on the tent), are the
> real story the headline buries. Evidence is **3 months of self-reported P&L (Feb–Apr 2026), dollars
> only (no ROC), wild profit-factor swings (12.7 → 1.44 → 5.41)**, and the entry edge is a **proprietary,
> paywalled IV-ratio tool**. To his credit he is openly honest that the pre-transform risk is real. Cap
> is the thin/un-auditable record and an un-testable, gated entry signal — not a refuted structure.

## Mechanics

- **Underlying:** **SPX almost exclusively** — European/cash-settled (no assignment; no shares to be
  put), and §1256 60/40 tax treatment in the US. Works on "any underlying with liquid options" but he
  sticks to SPX. `@09:28`, `@09:41`
- **Structure — double calendar (entry):** a **put calendar below** the current price + a **call
  calendar above**, combined. Each calendar = **same strike, two expirations**: **sell the front
  (nearer) expiration, buy the back (further) expiration**, net **debit**. `@04:46`, `@04:58`, `@05:09`
- **Strikes (entry):** **30–40 delta** on both the put and call side — deliberately *close* to the
  money. Can go wider (15–20 delta) for a wider final condor, but tighter strikes transform to
  risk-free **faster**, which is his priority. `@09:53`, `@10:29`, `@10:41`
- **DTE:** front legs in **the following week — ~6–15 DTE**. Back leg is **very tight to the front: 1–4
  days later**. A favorite is the **Friday-short / Monday-long** pair, "almost always in backwardation"
  (front IV > back IV). `@11:14`, `@12:48`, `@12:59`, `@13:10`
- **Entry timing (the discretionary alpha):** any time, but he wants the **front IV to decay faster
  than the back IV** *after* entry. Uses a self-built, members-only tool called **"Flux"** that plots
  the **front-IV / back-IV ratio** (intraday 1-min, plus 5-day / 20-day views) and a scanner across
  0–30 DTE combos. He enters when the ratio **spikes**, betting on IV mean-reversion to pull it back
  down (which feeds the calendar profit). Explicitly **"not a prediction tool… provides context."**
  `@13:54`, `@15:11`, `@16:48`, `@17:47`, `@18:24`
- **Debit / size:** "normal" single-contract debit **~$800–1,500** depending on duration (= the max
  loss on the double calendar). He trades multiples (examples on **20-lots**). `@35:34`
- **The "transformer" (the core trick):** once the double calendar shows **~5–10% profit**, place **one
  order** that (a) **sells/closes the back-dated long options** and (b) **buys wings in the FRONT
  expiration** (e.g. 5 pts beyond each short strike), converting the position into an **all-front-month
  iron condor**. `@01:03`, `@19:45`, `@20:08`, `@20:22`
- **The no-loss rule (arithmetic):** the transform must net a **credit ≥ (original debit + wing width)**.
  Example: paid **$10.10** debit → to lock a 5-wide condor he must collect **≥ $15.10**; he collected
  **$15.25**, i.e. **$5.15 net credit on a $5-wide condor → guaranteed min profit $0.15** (= **$300 on
  the 20-lot**) and **max ~$10,300** if SPX pins inside the tent. For 10-wide wings he'd need credit ≥
  debit + $10. `@21:16`, `@21:42`, `@22:32`, `@22:45`
- **Time to transform:** "no typical." Often **same day** (entered near open, transformed ~1.5 h before
  close); in vol spikes as fast as **7–20 min**; some days it never reaches the threshold. `@23:18`,
  `@24:09`, `@24:31`
- **If it won't transform (~40% of days):** close for a small profit/loss, OR hold overnight to retry
  next day. He can also pre-place the transformer order right after entry and let it fill passively, or
  **transform half the lot** early and the rest later for a higher credit. `@12:16`, `@25:02`, `@25:34`
- **Stop (pre-transform only):** **mental stop at −20%** of the double calendar. **No hard/broker stop**
  ("you'll get spiked out"). Risk is "managed at order entry" via **position size** — size so a full
  black-swan max loss still lets you "trade tomorrow." `@31:52`, `@34:37`, `@36:23`
- **Exit (post-transform):** **no management needed**; ideally **let it expire** (cash-settled) for max
  profit if SPX lands inside the tent, else collect the locked min. Will **scale out early** if a news
  shock threatens the tent (cites an SPX "war news" spike). Statistically hits max profit **~25%** of
  the time. `@28:19`, `@29:05`, `@32:20`, `@39:23`
- **Variations (not detailed):** he claims **6–7 "transformer" strategies** (vertical, IC, butterfly →
  risk-free), and many DC-transform variants (broken-wing IC, directional with risk left on one side).
  Today's is the "foundational" version. `@01:50`, `@26:21`, `@27:08`
- **Self-rated risk:** double calendar pre-transform **3–4**; post-transform **0**. `@37:52`, `@38:16`

## Claimed edge & returns

Self-reported, "clean stats… the last 3 months" (Feb–Apr 2026): `@38:30`

- **Feb 2026:** +$16,000 on **16 trades**, **81% win**, avg win $1,300 / avg loss $465, biggest win
  $6,505 / biggest loss $600, **profit factor 12.7**. `@38:38`
- **Mar 2026:** +$5,538 on **48 trades**, **64.6% win**, avg win $588 / **avg loss $747** (losers bigger
  than winners), biggest win $3,500 / biggest loss $3,100, **PF 1.44** — "barely hit any" max profits
  (~1 of 48 vs an expected ~25%). `@39:08`, `@39:23`
- **Apr 2026:** +$44,000 on **42 trades**, **54.8% win** (his lowest), avg win $2,300 / avg loss $561,
  biggest win $9,800 / biggest loss $1,700, **PF 5.41** — driven by hitting "a lot more max profits than
  normal." `@40:06`, `@40:33`
- **3-month total:** **~$66,000 on 106 trades, 63% win.** `@40:47`
- **Transform success:** "about **60%** of the time… same day or next day." `@33:47`
- He **dismisses win rate** ("I really don't care about win rate") and leads with **profit factor**.
  `@41:36`

## Objective assessment (where to be skeptical)

1. **"Risk-free" is true post-transform but the label hides where risk lives.** Math checks out: a
   credit iron condor with **net credit ≥ wing width** has max loss ≤ 0 → can't lose at expiry, and SPX
   cash settlement removes assignment/pin risk. *That* part is real (the key contrast with Burrito,
   where "risk-free" was false). **But the entire risk of the strategy sits in the pre-transform double
   calendar** — and (a) he transforms only **~60%** of the time, (b) uses **no hard stop**, (c) is
   exposed to **overnight gaps / black-swan moves** for the full debit ("you're going to be at risk for
   whatever the max loss is"), which he forthrightly admits `@34:17`, `@36:34`. The headline advertises
   the safe 60%; the danger is in the other 40% and the gap tail. He is honest about this in the body —
   the *title* is the oversell, not him.
2. **Transforming a winner can REDUCE locked profit — a hidden cost the pitch never frames.** He
   transforms at **5–10% DC profit** (≈ **$1,000–2,000 on a 20-lot** at a $10 debit), but the locked
   **min** profit is only **$300**. So in the **~75% of transformed trades that DON'T pin the tent**, he
   ends with **$300 — less than he could have simply *closed* the winning calendar for.** The transform
   is really a **convexity swap**: give up a near-sure ~$1k to floor at $300 with a shot at ~$10k. Net
   EV vs "just close the winner" is **unproven** and entirely depends on the pin probability — it is
   **not** "free." `@01:03`, `@21:42`, `@39:38`
3. **3 months, self-reported, dollars-only.** n=106 over a single Feb–Apr 2026 window; **no ROC / % of
   capital** is given, so the returns **can't be normalized or ranked** against other strategies, and
   the dollar totals depend on undisclosed sizing. The **profit factor swing (12.7 → 1.44 → 5.41)** and a
   month (March) where **avg loser > avg winner** and biggest loss ($3,100) **exceeded the "typical"
   max** show the result is **regime/pin-luck dominated**, not a stable edge. One ungapped, unstopped DC
   in a black-swan could erase a quarter. Un-auditable and cherry-startable.
4. **The entry edge is un-testable and paywalled.** The win-determining step is **when** to enter
   (front IV about to fall faster than back IV), judged via the proprietary **"Flux"** tool, members-only
   at NavigationTrading. The logic (IV mean-reversion) is plausible, but as used it's **discretionary,
   unspecified, and not reproducible** — the published stats are inseparable from that gated signal.
   `@18:24`
5. **"Recycle buying power" is true but adds no edge.** Post-transform the broker releases margin
   (defined max-loss ≤ 0), freeing capital — a real **efficiency** point, not a source of expectancy.
   `@43:45`
6. **Costs hand-waved.** Entry is a 4-leg SPX order, the transform is another 2–4 legs, and he likes to
   "transform half, then the rest" (more fills). On a **$300 floor (= $15/contract)**, SPX commissions +
   multi-leg slippage are material; only the ~25% that pin make the costs trivial. No commission
   accounting shown (contrast Flyagonal, which at least claimed commissions were included).
7. **"6–7 transformer strategies / infinite variations" + members-only tooling** is a soft sales frame
   ("learning from the classes that I teach" `@46:12`). The shown version is explicitly the
   "foundational" one — standard "beginner version vs how I really trade it" pattern.

## What's genuinely sound (the diamond)

- **The transform arithmetic is real, not marketing.** A credit iron condor where **net credit ≥ wing
  width** truly cannot lose at expiry on a cash-settled index — there is no pin/assignment escape hatch.
  This is the legitimate core and is **categorically more honest than Burrito's false "can't lose."**
- **He explicitly debunks his own headline.** "There is risk when you first put on the double calendar…
  no such thing as a free lunch… position-size to take the full max loss." `@34:17`, `@35:34` That risk
  candor is unusually good for this channel.
- **Sensible risk discipline:** size for a full black-swan loss, mental −20% stop, cash-settled SPX (no
  assignment), no naked short premium beyond the defined-debit calendar.
- **Locking a winning spread into a no-loss structure and freeing margin** is a legitimate, well-known
  management technique (rolling a winner into a defined-credit condor) — sound when the floor genuinely
  exceeds what you'd otherwise net (see red flag #2 for when it doesn't).
- **A coherent, falsifiable IV thesis** (front-vs-back IV decay differential drives calendar P&L) that
  is at least directionally testable on EOD data even if his intraday tool isn't.

## Backtestability

- **Testable mechanical skeleton:** SPX double calendar, **30–40Δ** both sides, front **6–15 DTE**, back
  **+1–4 days** (incl. Fri-short / Mon-long), enter for debit; then model the transform: at each EOD,
  check whether the chain permits a **transform credit ≥ (debit + wing width)** (sell the backs + buy
  5-wide front wings) → if yes, lock the **min/max** condor and carry to expiry; if not by EOD day-0/
  day-1, exit at small profit / **−20%** / hold. Measure transform-rate, locked-min vs DC-close P&L, max
  profit hit-rate, max loss, and **EV after multi-leg SPX commissions + slippage**.
- **The decisive caveat — this is an *intraday* strategy on EOD data.** The whole edge is a **same-day
  intraday transform** triggered by an IV-ratio that "updates every 1 minute." Daily resolution can
  only check transformability **at the close**, which **understates** his transform rate (it misses
  intraday windows that briefly hit the threshold) and **cannot replay** the Flux-timed entries or the
  scale-out-on-news exits. So an EOD test is a conservative **floor**, structurally biased *below* his
  record — more so than for Time Flies/Flyagonal, whose cadence is genuinely once-a-day.
- **✅ Data confirmed for SPX:** Athena `silver.options_daily_v3` has **SPX (46M rows, 2010 → 2026-02-20,
  full greeks + bid/ask)** and **XSP**, with **short-DTE expirations present**, so the calendars +
  wings are constructible at EOD. **No intraday** (EOD only). **RUT/IWM and QQQ would need confirming**,
  but he trades SPX almost exclusively so they're not needed for the core test.
- **Honest null comparisons:** (a) **just hold the double calendar to its best EOD exit** — does the
  transform add EV over simply closing the winner (red flag #2)? (b) a **plain weekly SPX iron condor**
  at matched strikes/exits — does the calendar→condor path beat opening the condor directly? (c) measure
  whether **entering on an IV-ratio spike** (EOD proxy of Flux) beats entering on random days.

## Open questions / next step

- **Does the transform add expectancy over closing the winning calendar**, or does flooring at $300 and
  betting on a ~25% pin actually *cost* EV outside benign months? This is the central testable question.
- What is the **EOD-achievable transform rate** vs his claimed 60% intraday — i.e. how much of the
  strategy is unreachable without intraday data?
- Over a longer/stressed window (2018, 2020, 2022, Aug-2024, Apr-2025), what is the **untransformed-DC
  tail** with no hard stop and overnight gaps — the part the "risk-free" label ignores?
- Does an **EOD IV-ratio (front/back) spike** filter have any measurable edge, or is the Flux signal
  inseparable from intraday discretion?
- Report results as **% of capital / max-loss**, not dollars, so it can be ranked against the framework.
- **Next step (on command only):** backtest the mechanical skeleton under `backtests/dc_time_machine/`,
  ideally on the same SPX engine as `backtests/burrito_butterfly/` (both are "lock a winner into a
  no-loss structure" claims and should be compared head-to-head).
</content>
</invoke>
