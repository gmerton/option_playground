# Levitation Trades — Dan Westbrook ("Boomer Dan")

Source: `2025-11-09_DHViE1YZ710` — "The 0DTE strategy with zero risk? Boomer Dan's 'Levitation
trades' explained" ([watch](https://www.youtube.com/watch?v=DHViE1YZ710)). Guest: Dan Westbrook
("Boomer Dan"), ex-film/video editor, ~15+yr options-income trader, runs a free Discord trading
school; host: John. **Same trader as [Burrito Butterfly](burrito_butterfly.md)** — read that
write-up alongside this one: it is the same "remove all risk" thesis, the same "I can't untangle
my results," and the same "the version I showed is the beginner version" tell, and its core
"risk-free" claim was **backtested and refuted** (1/5, negative EV). Carry that calibration here.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 4 / 10 (defined-risk, but the modal entry loses) · Tested: NO
> (only a crude EOD skeleton is testable — see Backtestability)**
> The "zero risk / minus-zero" headline is, as usual on this channel, **conditional**: the trade is
> only risk-free *after* you have already won a directional 0DTE bet and used that realized gain to
> buy the opposite spread, "levitating" the whole structure above the zero line. Dan is more candid
> than in the Burrito interview — he repeatedly states the trade **starts with real risk** and that
> you "have to be right on direction or somewhat right" `@43:12` — but that candor is exactly the
> admission that sinks the pitch: the part the whole thing depends on (intraday direction) is one he
> claims no firm edge on, and the **most common non-trending outcome is a slow theta "sag" you
> eventually take as a loss** `@38:04`. There is no separable track record ("it's difficult for me
> to say exactly what the numbers are… my best guess… 7 or 8 times out of 10") `@41:40`, the demo is
> winners-friendly, and the shown trade is explicitly the entry to a larger portfolio he nets
> together. The genuine core — *once* you book a gain and lock it into a structure that is positive
> at every price, it really is risk-free for the rest of the day — is sound accounting, not magic;
> the catch is that "once" does all the work.

## Mechanics

- **Underlying:** SPX (cash-settled, no assignment) — and you must be able to hold to the cash
  settle without getting assigned, which is why he insists on cash-settled indexes; XSP/SPY for
  smaller size. `@11:11`, `@40:14`, `@35:13`
- **DTE:** **0DTE** is the showcased version (also works 1-day / weekly / monthly). `@01:19`
- **Entry timing:** discretionary chart trigger from his "caveman chart" — example entry ~15 min
  after the open (6:45 Pacific). `@08:04`, `@09:00`
- **Step 1 — initial directional bet:** sell an **at-the-money 5-wide credit spread**, side chosen
  by his directional read (bullish → ATM put credit spread; bearish → ATM call credit spread).
  Targets **~$2.50 credit on a 5-wide ≈ 1:1 risk/reward** (~$245 max loss / $255 max gain).
  ATM is deliberate — far more credit to manage with than a 10-delta condor. `@11:08`, `@11:51`,
  `@12:18`
- **Step 2 — hedge the entry (the "safe" version):** immediately buy a **same-expiry 0DTE option
  ~$1.00** on the protected side (long put under a put-spread, long call over a call-spread), put on
  within ~20 seconds of the spread. Caps the immediate adverse-move loss to ~$10–50 and turns a fast
  crash *toward* the hedge into a profit. Alternative hedge: **1 MES futures** per spread (no
  vega/theta/bid-ask drag, "more robust"). `@15:54`, `@16:05`, `@19:10`, `@38:16`
- **Step 3 — "the flip" (levitation):** *if the credit spread moves into profit* (direction was
  right), buy the **opposite-side debit spread sharing the same short strike**, converting the
  position into a **butterfly that sits entirely above the zero line** — a locked-in guaranteed
  profit (he targets **10–20% of the ~$250 risk ≈ $25–50**, ~a $0.25 spread-vs-spread gap) plus a
  "lottery tent" of up to ~$500–600 if price pins the peak. `@13:13`, `@13:50`, `@20:39`
- **Step 4 — "wall of butterflies":** as price keeps moving his way, repeat (sell next ATM credit
  spread → flip to butterfly), stacking butterflies/condors across roughly one ATR (~50 SPX pts).
  Each added, levitated structure raises the guaranteed floor (e.g. $100 → $200 → $300). `@22:05`,
  `@23:48`, `@29:42`
- **Wing buy-backs:** once price has travelled past a butterfly, buy its now-worthless far wing back
  for ~$0.05 to remove the upper cap; can then sell a fresh full-credit spread off that level.
  `@28:07`, `@30:15`
- **Profit/loss management of the *entry*:** if right, often done in ~10–15 min. If wrong or it
  just sits, **"cry uncle" at ~$50–100 loss per contract** (or sooner). `@18:26`, `@34:33`, `@42:50`
- **Self-rated risk:** **"zero or minus-zero"** once levitating; **1–2** at the hedged initiation.
  `@40:05`

## Claimed edge & returns

- "Make the trade completely risk-free as quickly as possible… close the laptop and walk away
  knowing no matter what the trade is going to be a winner." `@00:00`, `@05:48`
- Once levitating: **"there's no way you can lose"**, rated **"a zero or a minus-zero."** `@03:00`,
  `@40:05`
- Hit-rate into the floating state: **"my best guess… 7 or 8 times out of 10"** he can maneuver into
  a floating position (includes his discretionary tweaks; "a newbie may not have the nimbleness").
  `@41:40`
- A big adverse-but-hedged move "paid off really well" (cites an Oct 2025 China/Trump headline day).
  `@06:35`
- **No quantified standalone results** — see below.

## Objective assessment (where the pitch breaks down)

1. **"Zero risk" is conditional on first winning a directional bet.** The risk-free state exists
   *only after* the entry spread has moved into profit and you've bought the opposite spread with
   that gain. He says it plainly: "there was a prerequisite — your put credit spread turned into
   profitable, right? And life is not always like that" `@15:18`; "you have to be right on direction
   or somewhat right" `@43:12`. **If the first leg loses, you do not get a free butterfly — you take
   a loss.** Identical to the Burrito's "if you're wrong we lock in a slight loss."
2. **He admits no firm directional edge — yet the trade opens as a directional bet.** The entry side
   is chosen by a discretionary chart signal; the strategy's whole payoff hinges on that read, which
   is the one thing he can't systematize. Same structural flaw as Burrito (`burrito_butterfly.md`
   point 3).
3. **The modal failure mode isn't a crash — it's a meander.** By his own account the *worst* thing
   that can happen is the SPX "just sits there and does nothing," so the pink (current P&L) line
   "sags lower and lower" through the day until you cry uncle. `@38:04`, `@39:28`. On a flat,
   rangebound day you neither reach the tent (no flip) nor get a hedge payoff — you bleed theta and
   take the stop. This is a frequent 0DTE outcome, not a tail.
4. **No separable track record.** "This trade is just one of many… I start to combine the other
   positions… manage them all on a portfolio basis… so it's difficult for me to say exactly what the
   numbers are." `@41:18`–`@41:53`. Same untangle excuse as Burrito → no win rate, no P&L curve, no
   falsifiable evidence. The lone number ("7–8 of 10 *get into* a float") is a guess about reaching
   the state, not a P&L or expectancy.
5. **Beginner-version tell.** "The setup I just showed you is the initial setup trade for a bigger
   trade" `@45:18`; the demoed simple call-flip he "would never trade." `@09:00`. The shown thing
   isn't the real thing — exactly as in the Burrito interview.
6. **Winners-friendly demo.** The main walkthrough is a day he knew the outcome of ("I know what's
   going to happen on this particular day") `@25:38` and that "went our way beautifully" `@32:16`.
   Even the staged "what if I'm wrong" example is rigged benign — the hedge turns it into a **+$47.50
   profit** before he exits `@33:49`. No losing trade is carried to the sag-stop or to settlement.
7. **0DTE pin/gamma + model-price risk.** The "guaranteed" lines are Thinkorswim risk-graph
   projections; he himself notes the pink line "looks kind of funky… because of the way Thinkorswim
   looks at its data" `@27:07`. A truly levitated structure (positive at all prices) IS safe into
   settlement, but every step *before* full levitation carries 0DTE gamma, and SPX is AM/PM
   cash-settled on the close — the demoed mid-structures are model marks, not fills.
8. **Costs are hand-waved on a thin target.** The process legs in constantly: ATM credit spread +
   long-option hedge + debit-spread flip + repeated butterflies + $0.05 wing buy-backs + condors.
   Each is multi-leg SPX commission and bid/ask. On a **10–20% target (~$25–50)** these frictions
   are material and unmodeled.
9. **Contradicts "set and forget."** He concedes it is "not a 100% mechanical strategy," "requires
   a lot of discretion and trader judgment throughout the day," and you must watch the sag — high-
   attention, intermediate-trader work, not the laptop-closed dream of the cold open. `@42:38`,
   `@36:38`

## What's genuinely sound (the diamond)

- **The "levitation" accounting is real, not magic.** Once you have actually booked an intraday gain
  and used it to buy a structure whose payoff is positive at every underlying price, that position
  *is* risk-free for the rest of the day. That's a true statement about locked realized profit — and,
  unlike the Burrito's "valleys of death," a fully levitated butterfly genuinely has no loss zone.
  The deception is only in implying you *start* there.
- **More candor than the Burrito pitch.** He repeatedly volunteers that the trade "starts off with
  some risk" `@01:53`, that the prerequisite is being right on direction, and rates the *initiation*
  1–2 (not 0). That honesty is worth a half-point over the refuted Burrito.
- **ATM-credit-spread point is legitimate.** Selling ATM (1:1) brings in far more premium to defend
  with than a 10-delta wing — a fair critique of cheap far-OTM iron condors. `@44:28`
- **Defined risk, cash-settled, hedged entry.** Per-trade max loss is small (~$50 stop, ~$345
  absolute), no assignment, and the long-option/MES hedge can convert a fast adverse move into a
  gain. You cannot blow up on one trade.

## Backtestability

- **Crude EOD skeleton only.** Athena `silver.options_daily_v3` has **SPX/XSP confirmed**
  (2010 → 2026-02-20, full greeks + bid/ask, 0-DTE rows present). You could test a *mechanical*
  proxy: enter an ATM 5-wide 0DTE credit spread + ~$1 long hedge, and a rule-based flip to the
  butterfly. But — **as with the Burrito — the strategy is fundamentally INTRADAY**: the entire edge
  claim is "leg in, *then* add the opposite spread once the first leg has gained," and **EOD-only
  data cannot replay that intraday legging** (we have one price per day; there is no intraday path to
  detect the "moved into the tent" moment, the sag, the wing buy-backs, or the wall-stacking). So a
  backtest can only price a *static* one-shot version (e.g. enter butterfly-or-spread at the close,
  settle at expiry), which is **not the levitation strategy** — same limitation flagged in
  `burrito_butterfly.md`, where the testable skeleton came out negative-EV.
- **Not faithfully testable:** the discretionary entry signal ("caveman chart"), the timing of the
  flip, the sag-stop ("cry uncle"), the wall-of-butterflies stacking, the wing buy-backs, and the
  portfolio-netting — all intraday and discretionary.
- **Honest null comparison (if ever run):** a static ATM 0DTE butterfly / credit spread held to
  cash settlement, after modeled commissions + multi-leg slippage, to see whether the conditional
  legging adds anything over its parts. Given the admitted absence of directional edge, the prior is
  ~breakeven-minus-costs — the Burrito's actual result.

## Open questions / next step

- Is the **realized** win/loss distribution anywhere near the claimed "7–8 of 10 reach a float"?
  Reaching a float ≠ net profitable across all entries, since the failures-to-float are the losses.
- How often does SPX *sit and sag* (the named worst case) vs. trend enough to flip? That base rate,
  not the flip mechanics, decides EV.
- Do total commissions + bid/ask on the multi-leg legging swamp the 10–20% target?
- **Next step (on command only):** a static EOD skeleton under `backtests/levitation_trades/`,
  understood up front to be a lower-bound proxy that cannot capture the intraday legging — exactly
  the caveat that limited the Burrito test.
