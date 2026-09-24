# TraderLion -- "THIS is How Leif Soreide Finds 90%+ Winners (High Tight Flags and More)" (2024-10-09, 12 min)

_Reviewed 2026-09-23. A 12-minute cut from a longer Leif Soreide presentation (CELH, CRSR, DQ, Tiger, ZIM, one
unnamed fertilizer name). Transcript is auto-captions (`transcript.txt`); tickers checked against the chart talk
where possible. Companion to the 50-min [HTF podcast](../2024-10-27_rdmjsbDVuoU/notes.md). Setup write-up and
codable spec: [setups/soreide_high_tight_flag.md](../../../setups/soreide_high_tight_flag.md)._

⚠ **The title misstates the video.** "90%+ winners" never appears. What he says at [01:02] and [02:24] is that the
*pole* has to rise **90% or more in eight weeks or less**. The 90% is the size of the move before the pattern, not a
win rate. He says the opposite about win rate himself at [11:44]: "it's not a magic pattern, I wish it was ... stops
happen on these too." The title turns a definition into a performance claim.

## Verdict: 2 / 5

- **Useful as a definition.** In 12 minutes he gives the most complete HTF rule set in these KBs: pole >= 90% in
  <= 8 weeks, flag 3-5 weeks (down to 7 days, halved for IPOs), flag depth ~25%, volume dry-up through the flag, a
  volume-confirmed pivot, and a smooth ~45-degree pole without a base inside it. Almost all of it can be coded
  on daily bars.
- **The evidence is zero.** Six hand-picked charts, one admitted stop-out, no count of the HTFs he passed on or
  lost on, and no return figure. "Context is key" [07:21] and "if you have to argue whether it's an HTF, it might
  not be the best pattern" [07:07] leave room for discretion to absorb any failure.
- **Nothing here has been tested.** No HTF row exists in TEST_INDEX. The nearest results (house breakout, VCP,
  trend smoothness, profit-lock trims) are below.

## Provenance

- Leif Soreide is billed as **2019 US Investing Championship (USIC) champion** (description). The return figure,
  division and account size are **not stated** in this video. USIC results come from broker statements checked
  by the organiser, not from an independent audit. Entry is opt-in, and it covers one calendar year. It shows that
  one account did well in 2019. It says nothing about the HTF rule.
- He sells an HTF class and a members' platform (see the companion video), and a Deepvue scan carries his name.
- The case studies are from 2019-2024 and chosen after the fact.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| title | "Finds 90%+ winners" | ❌ **Not said.** The 90% is the pole's rise [01:02]. He concedes stops are routine [11:44] |
| 01:02, 02:24 | HTF = a rise of >= 90% (100%+ preferred) in <= 2 months, then a flag of 3-5 weeks | **Untested; codable.** TEST_INDEX has no HTF row. Spec in the setup file |
| 02:17, 07:21, 07:55 | Best in a bull market; "might not work last month, maybe next month it works again"; his own red/green signal ("red signal wasn't until Feb 12") | **Nearest result is PARKED.** The breakout-activity percentile sorts the house book (Q1 +0.06R -> Q5 +0.86R, t 2.59, both halves) but has **no plateau**, raw counts are flat to inverted, and it fails the Sidak correction. The index-level signals (FTD, trailing regime rules) are all **NULL**: "the paying months cannot be forecast". His red/green signal is not defined, so it can't be tested |
| 02:55, 05:03 | Volume must decline from the top of the pole to the flag low. Buy on a pivot *with* a volume trigger | **Partly supported, as a trigger gate, not a pattern.** The MPA row cites volume-confirmed breakouts at RVOL >= 1.8 (+0.86pp/63d) and all breakouts pooled NEGATIVE. **The tightening itself failed**: VCP as a damped sine is **NULL** (same-date other-name breakouts **-0.37pp, t -0.70**). A volume dry-up flag is a different, untested variant |
| 03:24, 09:40 | Draw diagonals only with more than two touch points; otherwise "you're putting it where you want to buy it" | Sound discipline and untestable as stated. It argues for a horizontal pivot (flag high) in the spec |
| 03:04-05:10 | CELH: 161% in 8 weeks, sold into the earnings pop; "the tighter they are, the more you can just buy the top" | **One winner.** Selling into strength is the profit-lock family: trims **-0.25 to -0.33R**, "extended -> tighten" **INVERTED** (-0.19R, t -2.8). Tito's spike exit on calls: **NULL** on the primary (B-A +1.2pp, t 0.18). It is a risk lever, not a return lever |
| 05:12-05:40 | CRSR: a 7-day flag counts; for IPOs "I just cut the rules in half" | **Discretionary range, flagged in the spec** (flag length 5-25 sessions, IPO halving not codable on our panel: first-base IPOs are mostly outside the liquid universe) |
| 05:44 | Exit warning: ATR "kind of doubled", big down volume coming in | **Untested as an exit.** The closest exits (spike and extension overrides of the 20 EMA trail) are NULL or INVERTED. See the row above |
| 06:02-06:14 | "Put the tiniest stop and just got really lucky ... that takes care of a lot of losers and then you can size up" | ⚠ **Tiny stops inflate R, not returns.** House rule 2026-09-23: judge stop changes in **percent**. Our stop study: entries 0-1.5% above the low **stop out 76%**. The size-lever study says the stop-distance cell fails as a quality grade. "Got really lucky" is his own word |
| 06:22-07:05 | Measure the pole from the low; a smooth ~45-degree rise with no base inside it; a base inside the pole is "almost a strike against it" | **Codable (base-inside-pole test), but the prior is weak.** Trend smoothness as a signal is **NULL** (leaders: slopes don't sort; the DINO-style smooth profile was *worse*, -1.99pp/60d, t -1.35) |
| 08:07-08:36 | Flag depth ~25% tolerance (17-20% fine; slightly over 25% allowed "with a more powerful rise"); Tiger came out on 10x relative volume | Discretionary: default 25%, range 20-33% in the spec. The 10x RVOL is one example |
| 09:11 | "Skyscraper bars" in the pole | Codable as >= 1 session in the pole with a range >= 3 ADR on RVOL >= 3. Untested |
| 10:44-10:52 | Get in "as low as I can" with a stop below the prior day; don't buy in the middle of the bar | Consistent with the entry-extension finding (the breakout buys +0.52 ADR above the prior 20d high vs -2.09 ADR for a random later entry). Entry-timing results: **buying the close beats every intraday entry** (ORB -1.22pp, t -3.4) |
| 11:19-11:46 | April attempt stopped out and "confirmed my red signal"; "it's not a magic pattern" | ✅ Honest, and the only loss shown |

## What I would take

1. **The definition.** It is specific enough to pre-register, which is more than the Minervini VCP video gave.
   Spec and test design: [setups/soreide_high_tight_flag.md](../../../setups/soreide_high_tight_flag.md).
2. **The title correction** as a worked example of how a headline number changes meaning between the speaker and
   the thumbnail.
3. Nothing to adopt. Every management rule shown (sell into strength, tiny stops, ATR-doubling exit) is either
   contradicted here or untested.

## Not tested, could be

- **The HTF itself** as a daily pattern on the liquid panel, against same-date house breakouts in other names.
  Count the signals first. HTFs are rare, and on a $50M-ADDV panel from 2019 the count may leave it UNDERPOWERED
  before any return is looked at. Design in the setup file.
