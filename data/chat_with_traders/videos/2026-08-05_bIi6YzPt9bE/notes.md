# Chat With Traders — "How a 50-Year Veteran Thinks About Risk Management · Peter Brandt" (2026-08-05, 101 min)

_Reviewed 2026-09-23. Host Kevin (CWT's current host) interviews Peter Brandt (Factor LLC; Schwager's *Unknown
Market Wizards*). Transcript (`en-orig` auto-captions) in this folder. Timestamps below are the **transcript's**
(h:mm), not the description's chapter list, which is shifted by the ads. It opens with a ~3-min teaser of
clips from later in the show._

⚠ **Sponsor:** Trade The Pool, a prop-funding firm ("up to $200,000 in buying power"), with ad reads at 0:03 and 0:42.
Brandt himself sells nothing on camera. He says he posts charts and "does not make recommendations" (1:39).

## Verdict: 3 / 5

**Specification is high, evidence is nil, and his central thesis runs against our ledger.**

What's good:
- It's the most **codable** risk-and-entry spec in any KB so far. He gives fixed risk 60–70 bp, no pyramiding,
  and a rectangle of 8–14 weeks within ≤ 15% of price. He adds ADX(14) < 12, a rising 18-day MA, and a
  breakout buy-stop at the boundary + 0.5 × ATR(30). Exits are partials after 1–2 weeks and an 8-day-MA trail.
- He's unusually candid about losing: 19 of the last 21 trades lost (0:29), he's under 50% this year, his
  average loss was 17 bp, and he had 35–50% drawdowns early on.
- He frames trading as a metrics business (EV, profit factor, 200–300 trades, Monte Carlo) and rejects optimisation.

What's weak:
- There's no track record, only self-reported statistics. Schwager's vetting is the only external check, and
  it's asserted, not shown.
- Everything he trades is **futures on weekly charts**, not our daily US-equity book. Every comparison below
  carries that caveat.
- His headline claim is that trade identification is ~5% of the edge and the rest is risk/emotion/process management.
  **On our data it's close to backwards:** no management rule we've tested manufactures edge, and selection
  (by exclusion) is the one lever that measured.

## Provenance

| claim | source | verifiable here? |
|---|---|---|
| 50 years trading; Conti/Factor; *Unknown Market Wizards* chapter | host intro, 0:04; description | Public record. Schwager's vetting is reported, not shown |
| Win rate 54% over the last 12 years; under 50% this year | host asks, Brandt confirms, 0:22 | No |
| 15% of trades ≈ 85% of profits, "year in and year out" | 0:32 | No |
| 19 losers in a 21-trade sequence, "two years ago" | 0:29, repeated 1:36 | No |
| Average loss 17 bp last year; 45% losers | 1:26 | No |
| Drawdowns "< 1% a year", sometimes 2–3%; early years 35–50% | 1:30 | No |
| Best trade in four years: a stock he "didn't know anything about", within the last month | 0:41 | No. It's one anecdote |
| Silver $40 → $120 without breaking the 8-day MA | 1:33 | The price path is checkable; his P&L on it isn't |

## Claim by claim against our ledger

| @ | claim | our evidence |
|---|---|---|
| 0:22–0:23 | Pro win rates sit at 50 ± 6–7%; chasing 80% win rates is "dream world" | **Consistent, and ours is lower.** Precision-tier book: **30% win**, median −1.08R (TEST_INDEX §0). VCP signals 31–33% win (vcp_damped_sine_2026-09-23). A 30% book is normal for a right-tailed breakout system |
| 0:29, 1:36 | 19 losers out of 21, "more than a one-standard-deviation event" | **A large understatement, and it's the most informative number in the interview.** At his claimed 45% win rate, P(≤ 2 wins in 21 independent trades) = **0.00056** (≈ 3.3 SD). At 54% it's **0.000026**. A run like that is far likelier if trade outcomes **cluster by regime**. That matches our breakout book: 47% of months positive, top 8 of 83 months = 68% of positive R, and month-weighted −0.007R vs +0.448R trade-weighted (O'Neil pyramid row, §4). ⚠ This means his "200–300 trades" (0:53) is not 200–300 independent draws |
| 0:30–0:31, 1:15–1:16 | ❌ "Trade identification represents about 5%" of the edge. "My edge comes from risk management, emotional management and process. There is no edge in a head and shoulders" | **Contradicted on our data. The measured split is closer to the reverse.** (1) **Management adds nothing:** every profit-lock/trim/tighten arm is FAIL or INVERTED (profit_lock_2026-09-20: BE+1R −0.08R; trims −0.25…−0.33R, t −3.8/−4.2; 10-EMA-when-extended −0.47R, t −4.8). No stop variant beats simply buying the close (entry study, +5.95%). The 1-ADR stop is ≈ +0.03R and doesn't beat its control (stop_definitions.md). (2) **Selection is the lever:** size-lever study, *excluding* grade C adds **+0.29R OOS**, while amplifying by grade (10×) adds +0.08R. The universe carries the return, the trigger ≈ 0 (universe test). ⚠ Charitable reading: his "risk management" is **survival**. Small fixed risk keeps you in the game long enough for the right tail. That's true, and it's a *variance* statement, not an *expectancy* one. Sizing changes who carries the tail, not the shape (size-lever memo) |
| 0:32 | Pareto: ~15% of trades make ~85% of profits; "the 85% has to break even" | ✅ **Consistent (DESCRIPTIVE).** The house breakout is bimodal: 23.6% never retest, +1.273R; 76.4% do, −0.374R (retrace_entry_2026-09-20). The 20-EMA trail keeps the power moves (+7.1R). His framing of the job is exactly ours: make the 76% cheap without touching the 24% |
| 0:33–0:34 | Floor traders prefer a 30%-right system to a 70%-right one, since a high-win system has no margin for error | Consistent in spirit. Untestable as an opinion poll |
| 0:35–0:36 | Trades everyone on social media agrees with are the losers; contrarian ones become the big winners | **Untested, and we can't test it:** we have no sentiment dataset. The adjacent crowd-agreement proxy is our down-day relative strength. "What held up is obviously strong" is **INVERTED** (−3.51pp, t −3.33), which goes his way in spirit but isn't the same variable |
| 0:36–0:39 | Risk a **fixed 60–70 bp** of capital per trade, identical on every trade and market. 5–10% per trade "is a guaranteed tap out" | ✅ **Consistent with the desk rule.** Fixed small risk (Luk 0.3%) is what the regime-feedback study prescribes, because the paying months can't be forecast. The size lever says don't vary size much *within* the traded set (10× adds +0.08R for more drawdown); exclude instead. His 60–70 bp is ~2× the desk's 0.3%. Both sit far below the 1% he names as the ceiling |
| 0:39–0:40 | Enter all at once. **Never pyramid**: adding to a loser is foolish, adding to a winner raises the average price and makes you "more vulnerable to corrections" | **His rule is fine, but his reason fails on our data.** O'Neil pyramid test (2026-09-22): adds at sessions 3/5/10 earn **+0.30…+0.66R on their own risk** (t 0.4–1.5), and no add condition beats the unconditional add (best +0.15R, t 1.25). Adding scales the same edge. It's neither harmful nor helpful. Not pyramiding costs nothing, but the claimed danger isn't there |
| 0:40 | Take **partial profits** "not real quickly, but within a week or two" once up, which "gives staying power on the other half" | ❌ **Contradicted in the level-based form; the time-based form is untested.** Trim half at +2R: −0.26R (t −3.8). At 2 ADR extension: −0.33R (t −4.2). Those trims were worse per unit of drawdown than simply trading half size (profit_lock_2026-09-20). They "sell the tail to buy comfort": −613R summed on the 167 trades that reach > 5R. It's also in tension with his own 1:35–1:37 ("avoid taking small profits"). His exact trigger (in profit after 5–10 sessions, sell half) isn't one of our arms. See spec B |
| 0:42–0:46 | Weekly routine: scroll weekly charts on Friday, place all orders by Sunday. Entry by resting buy-stop with a **contingent stop attached**. Don't watch intraday; "remove myself from the equation" | **Mostly consistent.** Pivot buy-stop vs buying the close is "a wash" (entry study verdict). Not watching intraday is the fix for our biggest measured leak: same-day round trips, 278 cycles, −$8.3k, 19% win (exit-timing study). ⚠ **Which live stop is this?** He says the protective stop rests with the broker from the moment of entry, i.e. it **executes intraday**. In our framework that is only right for the **disaster stop (1.0 ADR, resting, intraday)**. Resting the **tight stop (entry-bar low, judged on the close)** is what the research rejects (DINO 2026-09-22). He never states his stop's width. On a weekly-pattern futures trade it's probably wide (box-low-like), which makes it the disaster-stop role, not the tight one |
| 0:48–0:55 | Doesn't optimise; rules are imperfect and fixed. Judge them over 200–300 trades with Monte Carlo. Target EV **20–30 bp per trade**, profit factor 3.0 over 100 trades, drawdown < 15% | ✅ **Same method stance** as our freeze-forward (precision tier: the refit recovers none of the published bands → REFRAME) and the parameter-neighbourhood robustness work. ⚠ But see the 19/21 row: trade counts overstate effective n when outcomes cluster. Our effective n is months, not trades. His EV target of 20–30 bp on 60–70 bp risk ≈ **+0.3…+0.5R/trade**, about our honest +0.4R (cap 20) |
| 0:54–0:59 | **The setup:** horizontal continuation patterns only (rectangle, right-angle triangle, H&S continuation; no diagonals), **8–14 weeks** long, **≤ 15% of price** tall. **ADX(14) < 12**, near 10 ("shows me compression"). 18-day MA rising. Entry = buy-stop at the boundary **+ 0.5 × ATR(30)**. Size = fixed $ risk ÷ (entry − protective stop) | **Untested, codable, low prior on our panel.** The closest thing we have is the VCP damped sine: **NULL**, −0.37pp vs same-date other-name breakouts (t −0.70), with an unchanged held-the-level share. ADX < 12 is a compression gate, the same family as Deepvue's RMV reviewed today. Futures on weekly charts may simply be a different animal from our daily equities. See spec A |
| 0:56 | "Indicators are just derivatives of price", but he uses ADX for compression | Fine. ADX is a scale-free trend-strength measure, and "low" means range-bound |
| 1:06–1:07 | Chart patterns were more reliable in the '80s; they work better in less liquid markets | **Untestable here**: no 1980s data, no small exchanges. Consistent with our general finding that published edges decay (freeze-forward: the precision tier is 2023+ only) |
| 1:12–1:13 | His **mentor's** rules (not stated as Brandt's own): never carry a loser over a weekend; take losers off at the end of each day and leave winners on; know when to move the stop to breakeven | **Breakeven is tested:** BE after +1R −0.08R (t −2.0, give-back 39 → 46%). BE after +2R is harmless (+0.01R, t 1.3). **The EOD/Friday loser rule is untested**, and for a *close* entry it's effectively "exit on the first close below entry", i.e. a stop at 0 R-distance. The prior is negative: every tightening arm cost (BE_EXT2 −0.19R, t −2.8). For an *intraday* entry it's a same-day-round-trip generator, which is the book's biggest leak |
| 1:21–1:22 | Stay away from YouTube "experts"; "all they're doing is using a chart to try to sell a service" | Noted. It's the skeptic-default premise of this whole KB directory. Said on a sponsored podcast |
| 1:26 | Average loss last year = **17 bp** with 45% losers, on 60–70 bp risk | **Internally telling, and unexplained.** It means the average loser exits at ≈ −0.25 to −0.28R, so most losses are cut far inside the protective stop. Our book's median trade is −1.08R. Nothing he states produces that (maybe the mentor's EOD/Friday rules, or the 8-day MA). Can't verify |
| 1:30–1:31 | Drawdowns under 1% a year ("2–3% sometimes"); early years had 35–50% drawdowns; "your worst drawdown is the one yet to happen" | Plausible arithmetic: 19 losers × 17 bp ≈ 3.2%. The last line is our crash-weeks rule (test crash weeks before reporting a path sim) in his words |
| 1:33–1:35 | **Manage with an 8-day MA:** stay while price is above it. Silver went $40 → $120 and the NASDAQ legs never broke it | ❌ **Contradicted in form on our book.** A faster trail sells the tail: the 10-EMA trail (once ≥ 2 ADR extended) cost **−0.47R, t −4.8** vs the 20-EMA close trail. Qullamaggie's "overriding the trail loses ¾ of the time" agrees. Silver and the NASDAQ are hindsight examples: the ones where a tight trail happened to work. ⚠ The caveat: his universe is futures on weekly-pattern entries, where an 8-day MA may play the role our 20-EMA does |
| 1:35–1:37 | "You *can* go broke taking small profits"; the math needs small losses and periodic large gains | ✅ **Consistent** with the profit-lock result. It's the same lesson, and it contradicts his own 0:40 partials |
| 0:17–0:19 | Don't quit your job without $100k of *already-made* trading profits plus $100k set aside for living costs | Not testable. Sensible |
| 0:27–0:28, 1:24–1:25 | "5 in 1,000" traders do 30%/yr for 5 years; RenTech ~45%, Druckenmiller ~40%, PTJ "46% in 3 years", ex-Turtles ~30% | **Unsourced.** He cites "a lot of research" without naming any. The RenTech number doesn't match commonly cited Medallion figures. Treat as rhetoric |

## What I would take

1. **Fixed small risk per trade, identical across setups.** It's already the desk rule. He's the most credible
   source for it so far, and it's consistent with the size-lever and regime-feedback results.
2. **The 19-of-21 arithmetic as a teaching number.** Losing streaks this long are near-impossible for independent
   trades at a ~50% win rate, so they're evidence of **regime clustering**. That's our "the paying months can't be
   forecast; stay in at fixed small size" finding, from a 50-year practitioner. It's also a warning that trade
   counts overstate effective n.
3. **Nothing from his management layer.** Partials after 1–2 weeks and the 8-day-MA trail both point in
   directions our profit-lock study measured as costly on the house breakout. His "identification is 5%" is the
   opposite of what our ledger shows.
4. **The ADX < 12 compression gate** goes into the RMV test (Deepvue review, same day) as an exploratory arm.
   It's nearly free there.

## Not tested, could be

**A. Brandt rectangle breakout on the liquid equity panel (daily bars).** ~½ day. Low prior (VCP NULL; weekly
futures ≠ daily equities). Not queued unless asked.
- Box: over the prior W sessions (W = 40–70, i.e. 8–14 weeks; take the longest W that qualifies),
  (max H − min L) / max H ≤ 15%. Horizontal proxy: the top 3 swing highs within 0.5 ADR of the box high.
- Gate: ADX(14) ≤ 12 on t−1; SMA18 rising over 5 sessions.
- Trigger: a buy-stop at box high + 0.5 × ATR(30), filled at max(level, open). Protective stop = box low
  (pre-registered, because he never states his). Size = fixed risk.
- Exit: first close below SMA8, or the stop, max 60 sessions, 0.10% slip per side. Report the 20-EMA exit on the same entries.
- Metric: % per trade. Primary control: **same-date other-name house breakouts** (not a same-name window).
  Bar |t| ≥ 3, both halves, per-year.
- ⚠ Check the ADX ≤ 12 base rate on daily equities first. It may be rare enough to leave n underpowered.

**B. Time-based partial: sell half after 5 / 10 sessions if in profit**, the rest on the 20-EMA trail, paired on
the profit-lock study's 1,968 trades. ~1 hour as an extra arm in `run_profit_lock_study.py`. The prior is negative
(every level-based trim cost −0.25…−0.33R). Qullamaggie's 20–25% "first burst" partial is the natural sibling
arm and is also untested.

**C. Mentor's EOD loser rule for close entries**: exit at the first close below entry, vs the house stop.
~1 hour, same harness. The prior is negative (BE-style tightening cost in every arm). Worth running only
because it would explain his 17-bp average loss if it didn't cost expectancy.
