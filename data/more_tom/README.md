# More Tom — knowledge base

YouTube channel "More Tom" (`@MoreTom-w2t`, `UCeJY4lXu8w4dhaz2ig9-F4w`): **496 subscribers, 26 videos uploaded
2026-09-01 → 2026-09-22**, 1–6 minute clips of **Tom Sosnoff** — CBOE floor market maker from 1981, co-founder of
thinkorswim (sold to TD Ameritrade, $750M) and tastytrade (sold to IG Group, $1.1B). Content is unmistakably
tastytrade doctrine: sell premium, trade small, trade often, ignore charts, think in probabilities.

The channel is the **second channel of Lossdog** (`@Lossdog`, 33,000 subscribers), Sosnoff's post-tastylive venture.
Every clip ends on the same appended CTA pointing at `lossdog.com` — a free-signup funnel for "portfolio, career
optimization tools, financial forecasting, and our new prediction engine." The channel is a lead funnel, and the
redirect carries a marketer's campaign tag (`utm_campaign=RYAN_Video_Campaign`).

---

## Provenance verdict

**It is genuinely Tom Sosnoff, on an authorized channel. Confidence: high.** But the clips are cut from his guest
appearances on *other people's* podcasts, not from Lossdog's own programming. Confidence on that: high.

**Evidence the speaker and the channel are real** (this was the live question — 496 subs and 26 uploads in 21 days
initially read as a content farm):

- **Lossdog's main channel has 33,000 subscribers and is actively posting.** The 28-second announcement clip
  (`PQq1xmxHvLs`) says "I was told by the gods of YouTube that I should have a separate channel for different style
  content" — which is exactly the relationship that exists. A three-week-old spinoff at 496 subs is unremarkable,
  not suspicious.
- **The audio is unscripted conversational speech with an interviewer present** — interruptions, laughter, snorts,
  self-correction, the interviewer pushing back. Not synthetic narration.
- **First-person specifics nobody else would have:** launching thinkorswim with no charting package and only
  discovering customers used charts after release; cold-calling Tim Knight of ProfitCharts in 1999 to lease his
  Java charts; buying the tastytrade domain on the company credit card and negotiating to keep it on exit; the
  Tony Battista scalping series; Karen the Supertrader (100k → 100M); naming Lossdog ("a name I've been sitting on
  for years").
- The description's career timeline is accurate and self-promotional, and `lossdog.com` is live and matches the
  products named in the outro.

**Evidence the content is repackaged third-party material** (this is the real qualification, not the identity):

- **Six of the 13 process clips carry explicit source credits**: *"From Tom Sosnoff's appearance on In The Money by
  Zerodha. Watch the full episode: youtube.com/watch?v=jstOWsWvbAU. Segment begins at 00:13:26. Credit: In The Money
  by Zerodha."* That source is a **69-minute episode published 2025-11-16 with 117k views** — sliced up ten months
  later. The remaining clips come from at least two further podcasts (a UK prop-trading show, a US finance podcast).
- **`8A5awQSDDB0` still contains an intact 90-second sponsor read for propfirmtrader.com** — a competitor's ad,
  belonging to the host's show, left in the published file. Nobody watched it before upload.
- The announcement clip says the content is "from live streams that we do every week at the opening bell, Monday
  through Thursday." **None of these 13 clips is.**
- Descriptions are identical boilerplate that switches to **third person** mid-way ("He's been on camera nearly
  every trading day for 15 years"), one title is third person ("Tom Sosnoff's Biggest Takeaway..."), titles follow
  a rigid template ("Stop X. Do This Instead." / "What Everyone Gets Wrong About X" / "The Truth About X"), and
  one title (`sLIw2z9wtOI`, "How Much You Should REALLY Risk Per Trade") promises a sizing rule over a clip that
  contains no sizing content at all.
- Engagement is 27–2,031 views, 1–36 likes.

**What this means for the review standard.** Sosnoff is accountable for these words — they are his, on the record,
in sourced interviews where he can be checked — so the claims are scored **on their merits**, not discounted as
anonymous. Two things still constrain them:

1. **Context is the editor's.** Titles and framing are bolted on, sometimes wrongly. **Never quote a More Tom clip
   as a Sosnoff claim without opening the source episode at the timestamp given.**
2. **In 13 clips there is not one number** — no position, no P&L, no sample, no statistic — although he repeatedly
   invokes a think tank, PhDs, a database back to 2005 and "60 hours a day of research." The *person* has a track
   record. The *claims* carry no evidence. **House rule therefore applies to the claims, not to the man: an
   unquantified claim is a hypothesis, not evidence.**

## Skeptic mandate

Same as every creator KB here: record the claims, test what is testable against our own data (real bid/ask + house
costs), score 0–5. A claim without a track record behind it is a hypothesis, not evidence. Prestige is not evidence
either — where our measurements disagree with a 45-year floor trader, our measurements win.

## Layout

```
videos/shorts/<date>_<id>/     transcript.txt + meta.json (26 clips, both halves)
claims_process.md              CLAIM LEDGER — process/psychology half (13 clips), score + queue
claims_strategy.md             CLAIM LEDGER — strategy/mechanics half (13 clips), score + queue
README.md                      this file
```

Two ledgers, one row per video, merged by the session owner who sets the final combined score.

## Half-scores

| Half | Clips | Score | One-line |
|---|---|---|---|
| Process / psychology | 13 | **2.5 / 5** | Four real agreements our own book paid to learn (size is the only outlier defence; scalping is a hobby; "I don't know what happens next"; chart features don't forecast), against two repeats of the settled probability=edge error and zero numbers anywhere |
| Strategy / mechanics | 13 | see `claims_strategy.md` | — |

## Headline findings from the process half

- ⭐ **"Stop using charts, trade mechanically"** is the most interesting claim on the channel, because our own
  equity book keeps confirming it against its own interest: house breakout **+0.014R**, within-date ranking
  **NULL (t −0.11, 71 of 72 cells fail)**, 9 chart features cannot call the bimodal split, **`sma_stacked`
  INVERTS**, and three separate leadership filters fail to sort. See `claims_process.md` row 7 and queue item 2.
- **"There is no edge, ever, for retail" is CONTRADICTED by his own trade type** — our one certified bucket is
  index premium selling (SPY bull put **t 6.07**, cell **+6.47% net/trade, t 5.62, 93% win**) and the 10-day VRP
  is **+1.75vp, t 8.93, 17/17 years**. He is denying the existence of the edge his own P&L is made of.
- **Scalping: he calls it a hobby, and our data says that is the right category** — same-day exits are the negative
  bucket in both books (scalp −0.13R vs trail +0.89R; the owner's own log, 278 same-day cycles, −$8.3k, 19% win).
- **"Think in probabilities"** repeats the SMB Capital error already scored 2/5: a 20Δ win rate is priced, and
  across credit/width quintiles the win rate **falls** (79.6→75.7) while net ROC **rises** (−2.96% → +4.07%).
