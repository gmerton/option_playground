# Watch Before Trading 0DTE Options

**Video:** `U9UZ2U6bozQ` · **Type:** talks · **Watched:** 2026-09-19 · 10:05, solo talk

Written up as [`principles/zero-dte-expansion-events.md`](../../../principles/zero-dte-expansion-events.md).

## Raw notes

Structure: 60% is a generic options-101 explainer (intrinsic vs extrinsic, theta, IV), 25% is
his actual rule, 15% is risk management and the course pitch. **There is not a single number in
the video that is a result** — no win rate, no P&L, no trade count, no base rate. The only
quantity he states about his own behaviour is frequency: *"a few times per year."*

- [00:00]–[00:31] Framing. 0DTE "are not a shortcut to easy money… used too frequently, and they
  will drain your account faster than you can refresh your P&L." Admits "I have had hundreds of
  these expire worthless on me" [00:54].
- [01:04]–[03:17] Theta explainer. SPX at 5,000, buy the 5,000 strike at 10:00 for $50; flat at
  1pm → $30; flat at 3pm → $15; close at 5,000 → zero. Ends on the real point: **"time decay
  accelerates into the close"** [03:17].
- [03:37]–[04:33] IV explainer. Standard.
- [04:33]–[05:39] ⭐ **The thesis.** "The best opportunities for zero DTE options occur ahead of
  major daily breakouts or right during breaking news events." You get paid twice — direction
  *and* IV expansion. Worked (hypothetical) example: stock quiet $98–100 for days, IV low, 0DTEs
  cheap; surprise news, it explodes through $100 on volume; you capture the move *and* the vol
  pop.
- [05:39]–[06:11] The failure mode he names: right on direction, too slow/too small a move, theta
  and falling IV cancel the delta gain. "Many beginner traders end up shocked when the stock
  moves in the direction they thought it would, but they still lose on the option."
- [06:33] Vol crush: buy *after* vol has already exploded and the move stalls → "you can be right
  on direction and still lose."
- [06:56]–[07:17] ⭐ **The three situations**, verbatim below.
- [07:28]–[08:10] Sizing. Premium looks small in dollars → people oversize. "You can see a 50,
  70%, or even 90% drawdown in minutes. It's totally, completely normal in this world."
- [08:10]–[08:31] ⭐ **Invalidation, stated in advance** — the one genuinely mechanical part.
- [08:31]–[08:51] "There will be entire weeks where conditions do not justify this kind of
  leverage… the smartest trade is often patience and avoidance."
- [09:02] Defined risk = premium paid, as the structural virtue.
- [09:24]–[09:43] Course pitch. [09:45] WallStreetBets jab, subscribe ask.

## Named setups appearing here

- [x] **0DTE expansion-event long** — universe gate (expansion events only) + frequency cap +
      defined risk + a stated invalidation. Promoted to
      [`principles/zero-dte-expansion-events.md`](../../../principles/zero-dte-expansion-events.md).
- Three sub-arms, in his words [07:07]: (1) "exceptional breakout setups in a strong momentum
  market", (2) "breaking news headlines that haven't yet been priced into the market",
  (3) "exhaustion gap daily patterns."
- Arm 3 is the **same exhaustion gap** as ORB use case 1
  ([`opening-range-break.md`](../../../principles/opening-range-break.md)) and the same pattern he
  sells premium into in `eWeGAYvjxh4` — see that video's TIGR example. Three videos, one pattern.

## Claims to verify

- [ ] **"The best opportunities for 0DTE occur ahead of major daily breakouts or right during
      breaking news events"** [04:33]. ⚠ This is the whole video and it is asserted, not shown.
      The repo has tested a *realized-volatility* gate on 1-DTE straddles (`ratio_max` = largest
      prior-5d move / implied move) and it never turns the trade positive: −44% at ratio <1 →
      −23/−25% at ratio ≥3. **A catalyst gate is a different object and has NOT been tested.**
      ⭐ This is the one honest open question the video raises.
- [ ] **"You get paid two ways: the move and the IV expansion"** [05:18]. ⚠ Suspect at 0DTE
      specifically. Vega on a same-day option is tiny; the payoff is almost entirely gamma/delta.
      The two-ways-paid argument is a *30-DTE* argument he has carried over to 0DTE without
      adjusting. Checkable directly off `silver.options_daily_v3` — regress 0DTE/1-DTE P&L on
      realized move vs ΔIV and see how much of the variance ΔIV actually carries.
- [ ] **"A 50, 70%, or even 90% drawdown in minutes… totally, completely normal"** [07:47].
      Plausible and consistent with our distribution (1-DTE long straddle p10 = −56% of premium,
      open win% = 5%), but stated as colour, not measured.
- [ ] **"I'm only using zero DTE options as a tool a few times per year"** [07:02]. Unverifiable,
      but it is the most important sentence in the video and it is the one that makes the rest
      defensible.

## Quotable rules

> "There is pretty much no trading instrument where selectivity is more important." [00:54]

> "This is why I only trade zero DTE options when there are expansion events. Breaking news,
> major economic data, clean technical breakouts with some urgency." [06:11]

> "In practice, there are three specific situations when I tend to play these… exceptional
> breakout setups in a strong momentum market, breaking news headlines that haven't yet been
> priced into the market, and exhaustion gap daily patterns." [06:56]

> "Before entering a trade, you should know exactly what invalidates the trade. If the breakout
> fails and reclaims the prior range, you need to be out. If the news-driven move stalls and
> momentum fades, you're also out." [08:10]

> "There will be entire weeks where conditions do not justify this kind of leverage… the smartest
> trade is often patience and avoidance with zero DTEs." [08:31]

> "When used improperly, they just become lottery tickets disguised as strategy." [09:13]

## Reactions / conflicts

### ✅ Agrees with the repo on the base rate — and he is right

`data/studies/one_day_straddle_study.md` (run 2026-09-19, 152,995 trades, 1,645 names, 2019–2026,
real bid/ask, house cost model) says buying the ATM straddle at the close before expiry loses
**~30% of premium however you exit it**: close exit −30.3% (t −26.9), sell both legs at the open
at fair value −30.2% (t −37.4), settle-at-intrinsic-at-the-open −72.0%. The 0DTE long strangle
base rate is −26%/trade (Theta Profits KB). His "used too frequently, they will drain your
account" is the correct sign, correctly signed, from a practitioner. **No conflict — this is the
most honest opening 30 seconds of any options video in the KB.**

### ⚠⚠ The omission is the whole finding: he never once says "bid/ask"

The single biggest number in the study is not the gate, it is the **spread**:

| both legs' bid/ask as % of straddle mid | n | open @fair value | close exit |
|---|---|---|---|
| <5% | 10,768 | **−1.7%** | −6.8% |
| 5–10% | 20,084 | −8.9% | −12.3% |
| 10–20% | 37,224 | −16.1% | −17.5% |
| >20% | 84,919 | **−45.0%** | −43.1% |

Same trade, same exits, −1.7% vs −45.0% depending on nothing but liquidity. **The bid/ask is the
entire P&L.** He spends 3 minutes on theta, 2 on IV, and zero on the spread — and theta and IV
are both *priced*, while the spread is a pure tax. A 10-minute video on the most spread-sensitive
instrument in the market that never mentions the spread is a material omission, and it is the
same omission in `eWeGAYvjxh4` and `sxjsqauWE9E`. Three for three.

### ⚠⚠ 0DTE forces you into the one bucket the repo has measured as negative twice

A 0DTE position is structurally a **same-day round trip**. The exit-timing study (2026-09-18)
found same-day exits are the negative bucket in *both* books: our pool scalp −0.13R vs trail
+0.89R; Gabe's own 278 same-day cycles −$8.3k at a 19% win rate, and the alert-triggered ones
were no better. Stage A (2026-09-18) found 11,227 intraday trigger fires — unfilled-gap reclaim,
opening-range break above the 9 EMA, level breaks — every arm −0.10 to −0.13R, with a **random**
entry in the same name-day beating the trigger on every arm. Arms (1) and (3) of his three
situations are exactly those triggers, and arm (1) is a breakout trigger that the entry study
says is beaten by simply buying the daily close (paired −0.9 to −2.3pp, t up to −3.4).

**So the repo's position is: the trigger family he wants to express is one we have measured as
having no edge, and he proposes expressing it through the most decay- and spread-hostile
instrument available.** That compounds two known negatives.

### ⚠ The gate he proposes is not the gate we tested — state this honestly

Our `ratio_max` gate is **backward-looking realized vol**. His gate is a **forward-looking
catalyst**. These are different, and the study does not refute him. The nearest thing the repo
has to his claim is the *opposite* result in sign: the catalyst/convexity study (2026-09-18)
found **OTM calls bought before events beat random-date buys on every exit** (0.12Δ, sell after
5 days: +30.7% vs −3.6%; election-eve median +59%) — but the winning exit there is **five
sessions**, not five hours. The repo's own pro-convexity finding argues for buying event
convexity *with runway*, which is an argument against 0DTE, not for it. That comparison is the
most useful thing in this write-up.

### ✅ Two smaller agreements

- **"Exhaustion gap daily patterns"** [07:16] lands on the one condition the gap study found
  genuinely positive (day after a ≥1 ATR move: +11.91 bp, t=6.53 vs +0.84 otherwise), and it is
  his own ORB use case 1. Third independent restatement of the same pattern in this KB.
- **Pre-stated invalidation** [08:10] is exactly the discipline the repo's grading rubric demands
  (`src/lib/alerts/grading.py`), and he states it *before* entry rather than as a post-hoc story.

### ⚠ "Paid two ways" is a 30-DTE argument wearing a 0DTE costume

At one session to expiry, vega is close to zero. If IV is the second payday, you want *time*, and
if you want time you are no longer trading 0DTE. He never resolves this, and it is the technical
error in an otherwise careful video.

---

**Rating: 2.5/5** — correct on the base rate and unusually honest about how often the instrument
should be used ("a few times per year", "entire weeks where conditions do not justify"), with a
pre-stated invalidation that most options content lacks. Marked down hard for: zero numbers of
any kind; never mentioning the bid/ask, which our 153k-trade study says *is* the P&L; the
"paid twice by IV expansion" claim being false-by-construction at 0DTE; and for proposing to
express an intraday trigger family the repo has measured at −0.10 to −0.13R through the most
hostile instrument available. The single useful export is the catalyst gate as an *untested*
hypothesis, and the honest version of it is the repo's own event-convexity finding at a 5-day
horizon rather than a 5-hour one.

**Course-marketing content present: yes** — explicit pitch at [09:24]–[09:43] ("I go deep on that
inside my trading course… the frameworks, the playbooks, and the context"), plus a cross-promo to
his risk-management video at [08:00] and the closing subscribe ask at [09:54].
