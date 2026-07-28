# Fly Diagonal (8-Leg Flyagonal, "Fly D") — Steve Gunn

Source: `2026-04-19_s7dNzX6KWmg` — "This 8-Leg Options Trade Targets Big Returns in Days"
([watch](https://www.youtube.com/watch?v=s7dNzX6KWmg)). Guest: **Steve Gunn** (auto-captioned
"Steve Gans"; email steve@optionsincomeacademy.com — **Options Income Academy**), a 30-yr options
educator who taught for Online Trading Academy and Aeromir, helped Kirk Du Plessis launch the Option
Alpha bot, and works with Charles at **Option Traders Assistant** (the software used to trade/manage
this). Third appearance on the channel; host: John. Sells courses (butterfly, diagonal, and a
forthcoming "flyagonal" class) and an **alert service** — strong course/alert sales motive.

**Cross-reference — read with `strategies/flyagonal.md` and `strategies/time_flies.md`.** This is the
**newest evolution of Gunn's own flyagonal series**, not a new idea. He now runs three variants: the
**Original/"O"** (put diagonal below + call BWB above — the strategy already reviewed in
`flyagonal.md`), a **"B"** (the O with the upper long call pre-rolled to the next expiry), and this
**"D" = "fly diagonal"**: an **ATM iron butterfly with a put diagonal and a call diagonal on either
side** (`@04:30`, `@41:34`). Same delta-neutral, vega-aware family as Simon Black's **Time Flies**;
what changes here is more legs (8), an ATM short (max premium), and an even thinner/newer record.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 4 / 10 (defined-risk index; untested whipsaw tail + no-stop discretion) · Tested: NO**
> The *structure* is the same sound vega-aware tent that earned respect in Time Flies and Flyagonal —
> now with an ATM iron butterfly bolted to a double diagonal to stack "**triple theta**" at the center
> (`@06:15`, `@06:41`). But this variant is **weaker-evidenced than the flyagonal it replaces**, not
> stronger. The "**50/50, 100% win rate**" (`@01:28`) is the textbook vacuous high-win-rate trap on a
> defined-risk fly — and it **broke on camera**: he closed his first loser the day of taping (`@01:39`).
> The single worst thing is the **8-leg fill cost**: a trade targeting **5–7% of ~$3,000 (~$150–210)**
> over a Friday→Monday weekend (`@08:27`, `@16:34`) is exactly the tiny-debit structure that 16 legs
> of bid/ask + commissions eat alive — and the user's **own DC Time Machine backtest already found
> tight-gap Fri/Mon 8-leg structures go net-negative after modeled fills.** Add: **no stops of any
> kind** (`@25:08`), a return engine that leans on **discretionary adjustments taught in a paid
> course** (`@25:59`), and **AI used both to assemble the strikes and to "validate" the results**
> (`@39:20`) — circular in-sample confirmation, not independent evidence. Sits **at the same 1.5 as
> flyagonal**: same clever core, thinner record, more cost drag, louder sales motive.

## Mechanics

- **Underlying:** **SPX** is the main vehicle (`@17:02`). Also SPY (max risk ~$150–250/trade,
  `@44:16`), QQQ ("the Q's"), IWM, Tesla, Microsoft — "anything highly liquid." `@17:12`
- **Structure ("fly diagonal," 8 legs):** delta-neutral, three overlapping pieces sharing the ATM
  center (`@04:30`, `@05:45`):
  - **Center — ATM iron butterfly:** sell the call *and* the put at the current market (max premium),
    with **50-point wings** either side. `@09:45`, `@10:22`
  - **Above — call diagonal:** short call ~**50 pts above** the fly's upper long, long call a further
    ~**20 pts** out (strike grid permitting), at a later expiry. `@18:36`, `@18:49`
  - **Below — put diagonal:** mirror image, short put ~50 pts below, long put ~20 pts further, later
    expiry. `@20:07`
  - Net = an **ATM iron fly + a double diagonal** → a "massive wide tent" with a theta spike at the
    center. To cut buying power he'll swap a diagonal for a plain **calendar** on a side. `@10:32`,
    `@20:18`
- **DTE / expiries:** built around a **Friday→Monday** cadence — **front (short) legs on a Friday**,
  **back (long) legs the following Monday** (sometimes the following Friday). Exploits the Friday
  weekend-vol bump (market makers "spike up Friday vols"), giving slight backwardation to sell into.
  Window **7–14 days**, as short as 7; modeled one at 32 DTE for hands-off students (wider tent,
  flatter T+0). `@16:34`, `@17:47`, `@07:33`, `@12:21`
- **Strike/delta selection:** **~delta-neutral** at entry ("I don't care if I'm ±1–2," not precise);
  strikes snapped to the available 5/25/50-pt grid. `@19:41`, `@19:04`
- **Profit target:** **5–6–7% within the first 24–48 hrs** (sometimes on **day 0**, open in AM →
  close in PM); **10–15%** if held past that window. "Rinse, wash, repeat." Avg **~4 days** in trade.
  `@08:27`, `@08:53`, `@50:03`
- **Stop/exit:** **NO stops of any type** (`@25:08`). Rationale: on a hard fast move, resting stops
  fill through blown-out bid/ask. Instead relies on **defined risk + adjustments**; "I'm a guy that
  doesn't close out at a loss." `@23:21`, `@24:44`
- **Adjustments (the real engine):** **5+ categorized downside adjustments** taught in the course
  (`@25:59`). Down move → buy back short calls, resell them closer to market (bring in premium, tilt
  the tent open); if vol/backwardation rises, **add a whole new diagonal below** (`@30:42`). Up move →
  roll short puts up (but you get *less* premium adjusting into an up-move — "harder to right the
  ship"). Uses loose chart support/resistance, "doesn't have to be precise." `@26:35`, `@29:08`,
  `@33:24`, `@28:21`
- **Sizing / risk:** SPX ~**$3,000 max risk** per trade at entry (worst case if never adjusted); SPY
  **$150–250**. Self-rated **3–4/10** ("defined risk → automatically lower half"). `@20:18`, `@23:33`,
  `@44:03`, `@44:55`
- **Vega (note the mismatch):** double diagonal **+11 vega**, iron fly **−19 vega** → **net ~−8, i.e.
  net short vol, NOT vega-neutral.** He explicitly does **not** neutralize vega and warns "just because
  a trade models positive vega doesn't mean it acts that way… calendars/diagonals depend on which
  expiry vol hits." `@14:56`, `@15:20`

## Claimed edge & returns

- **Fly-D personal record:** "**50 of these, 100% win rate, 50/50**" — but **the first loser closed
  the day of taping** (a "small loser," excluded from the stats shown). `@01:28`, `@01:39`
- **~120% total return in ~5 months, "about 300% annualized," avg ~4 days/trade.** `@00:00`, `@07:33`
- **Alert-service record (all three variants blended, since Aug 2025):** **95% win rate, profit factor
  6.98, avg 5.2 days, 100% winning months, 72% needed no adjusting, 31 wins in a row (current streak),
  2 losing weeks.** `@46:27`, `@46:45`, `@47:09`
- **"Trade Year" account:** ~**$28k (Jul) → $59k (Apr 6), ~106% in ~9 months (~$30k)** — screenshots
  from the platform. `@47:31`, `@47:46`
- **Self-named worst case:** the **"whipsaw"** — big down move → you adjust (pay to reset the tent) →
  market rips **back up through** the new tents = double loss. Happened in COVID and the "tariffs on/
  tariffs off" episode; "**7 events like that in 20 years**." Second-worst = a big fast up-grind
  (market "up 10% in 9 days, one 3% gap up"). `@36:52`, `@37:54`, `@38:47`, `@32:32`
- **Assembly & validation:** "**AI helped me assemble this**" — fed the three variants' P&L diagrams to
  **ChatGPT, Gemini, and Claude**, all "agreed Fly D is best," then fed his own trade logs and "AI was
  right in its assessment." `@39:20`, `@41:48`, `@50:39`

## Objective assessment (where to be skeptical)

1. **"100% win rate" is the classic vacuous claim — and it already failed.** 50/50 on a defined-risk
   fly measures nothing but P(no big move) over a benign window; such structures print long strings of
   small wins punctuated by rare near-max losses, so **0 losers in 50 tells you the tail hasn't been
   sampled, not that it's absent.** The first loser arriving *on camera* (`@01:39`) is the sample
   correcting itself in real time. With **n=50 over ~5 months** (roughly late-2025→early-2026, low-vol)
   the confidence interval is wide and the loss distribution is unestimated — even thinner than
   flyagonal's already-thin 60.
2. **8 legs is the killer cost problem.** Open + close = **16 leg fills**, each crossing bid/ask, plus
   commissions, to capture **~$150–210 (5–7% of $3k)** over a weekend — or on **SPY, 5% of a $150–250
   risk = $7–12**, which multi-leg fills would consume *entirely*. This is precisely the tiny-debit,
   Friday→Monday, 8-leg pattern the user **already backtested** in `backtests/dc_time_machine/`:
   *tight +3 Fri/Mon gaps produce ~$0.80 debits that 8-leg fills eat, netting negative after costs.*
   That is a strong prior that the *modeled-fill* version of this trade is far worse than the mid-price
   demo. He says "after commissions" (`@22:22`) but never shows realized slippage on 16 legs.
3. **The return engine is discretionary adjustment skill, sold in a course.** "No stops of any type"
   (`@25:08`) + "I don't close at a loss" means the 100%/95% win rates are **manufactured by
   adjustments** — 5+ categorized moves, chart-read timing, "which one models best." 72% needed no
   adjusting → **~28% did**, and those are the trades that decide the tail. This is un-automatable,
   un-testable, regime-dependent judgment (the same un-falsifiable "artistry" ceiling as Time Flies),
   and it is the thing the paid course exists to sell.
4. **AI assembly + AI "validation" is circular, not independent.** Feeding P&L diagrams to three
   chatbots that "predict" Fly D is best, then feeding **his own in-sample, benign-regime logs** and
   declaring "AI was right," is confirmation of an in-sample optimization — the LLMs read a payoff
   diagram, they did not run an out-of-sample test. Presenting it as third-party corroboration
   (`@41:48`) overstates the evidence.
5. **Net short vega into his own second-worst scenario.** He admits net ~−8 vega and that a big up-move
   brings a **vol crush that hurts the diagonals** (`@34:50`) — and that up-moves are the adjustment he
   gets *paid least* to fix. So the structure is most exposed exactly where it's hardest to defend, and
   the "vega-neutral, agnostic to vol regime" framing (`@11:56`) is contradicted by his own greeks.
6. **The whipsaw tail is admitted, defined, and unsampled.** He names the double-loss whipsaw (adjust
   down, then rip back up) as the true worst case, "7 events in 20 years." A 5-month record contains
   ~none. When it hits, you've *paid* for adjustments and *then* taken the reset-tent loss — worse than
   the nominal $3k max on the un-adjusted trade, because adjustments add buying power (`@27:44`,
   `@38:06`).
7. **The 50/50 headline isn't separable from the blended service.** The auditable-looking numbers (PF
   6.98, the Trade Year screenshots) are the **alert service = all three variants combined**
   (`@46:03`); the clean "Fly-D 100%" is the personal, AI-summarized, un-published log. Better than
   Burrito's "can't untangle it," but still self-reported and not independently verifiable.
8. **Denominator + single-name smuggling.** Returns are "% of capital deployed at open" (self-chosen
   basis, like flyagonal). Running it on **Tesla/Microsoft** (`@17:12`) adds earnings gaps,
   American-style assignment, and idiosyncratic jumps that the cash-settled-SPX framing quietly drops.

## What's genuinely sound (the diamond)

- **The core vega design is the same real idea** as Time Flies/Flyagonal — long-vol diagonals to catch
  selloff IV spikes, short-vol fly to harvest grind-up IV bleed — and stacking three overlapping
  structures for concentrated central theta is a legitimate mechanical property, not just marketing.
- **Defined risk, cash-settled index version, no assignment, no blow-up** beyond a known per-trade max.
  The self-rated 3–4 is defensible *for the SPX/SPY version, un-adjusted*.
- **The Friday-vol / weekend-theta harvest is a small real edge** (market makers do elevate Friday
  expiries), and the discipline is sound: quick 5–10% profit-taking, out fast, "rinse-wash-repeat,"
  exit before terminal gamma.
- **He leads with the worst case.** Naming the whipsaw as *the* failure mode and building a "what
  breaks this trade" lesson (`@36:16`) is more honest than the channel norm — the risk is disclosed,
  just under-weighted against a 100% headline.

## Backtestability

- **Partially testable skeleton (index only):** SPX, ATM iron fly (50-pt wings) + call diagonal short
  ~50 pts up / call diagonal + put diagonal short ~50 pts down, later-expiry longs ~20 pts further,
  **Friday entry → following-Monday back expiry**, delta-neutral at open; exit at **+5–7% (48h) / +10–
  15% (later)** of entry capital. Measure win rate, mean, **max loss, and EV after 16-leg SPX
  commissions + modeled bid/ask** — the last is decisive.
- **Honest floor / strong prior:** the user's **`backtests/dc_time_machine/`** already tested this exact
  tight-gap Fri/Mon 8-leg family on SPY 2018–26 and found **the debit is too small for the fills to
  clear → net-negative after costs.** Expect the same here; the demo tents are OptionStrat/OTA **mid
  prices**, not fills. This is the ceiling to state plainly.
- **NOT faithfully testable:** the **same-day (day-0/day-1) 5% exits** and **~4-day intraday
  management** need intraday bars — `silver.options_daily_v3` is **EOD-only**; and the **5+
  discretionary adjustments + chart reads** are un-mechanizable. The no-stops "heal the wound"
  adjustment logic that manufactures the win rate is the un-testable heart of the strategy.
- **Data:** SPX/XSP confirmed in Athena (46M rows, 2010→2026-02, full greeks + bid/ask, short-DTE
  present) — the index skeleton is constructible at daily close; RUT/IWM + QQQ coverage would need
  confirming; TSLA/MSFT single-name variants should be excluded (earnings/assignment).
- **Highest-value comparison:** run this Fly-D skeleton on the **same engine** as flyagonal and Time
  Flies (all three are one family) and against a plain weekly iron fly / plain double diagonal at
  matched widths — does adding legs 5–8 add anything over the 4-leg cousin, or just quadruple the fill
  drag? The dc_time_machine prior suggests the latter.

## Open questions / next step

- Does the modeled-fill skeleton clear its own 16-leg transaction cost, or does it replicate the
  dc_time_machine net-negative result on the tiny Fri/Mon debit? **The fill cost is the whole question.**
- With the first loser only just arrived, how big is the realized loss distribution once the benign
  regime ends — and what does a whipsaw event (COVID/tariff-type) actually cost *after* paid
  adjustments, vs the nominal $3k max?
- How much of the 95%/PF-6.98 service record is the un-testable adjustment discretion vs the structure?
- **Next step (on command only):** backtest the mechanical skeleton under `backtests/eight_leg_trade/`,
  **reusing the `dc_time_machine` / `double_calendar_study.py` engine** (same tight-gap Fri/Mon 8-leg
  family, strong existing prior) and sharing with `backtests/flyagonal/` if built — but the honest
  expectation, given dc_time_machine, is that the fills eat it. Low priority.
