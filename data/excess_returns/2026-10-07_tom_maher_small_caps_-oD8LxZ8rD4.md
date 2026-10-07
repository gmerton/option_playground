# Excess Returns — Tom Maher: "You Own the Mag Seven. Small Caps Are Building What AI Needs." (2026-10-07)

Video `-oD8LxZ8rD4`, published 2026-10-07, 66 min, 1.4k views at review. Guest: Tom Maher, PM of Hilton Capital's small/mid-cap
strategy (Russell 2500 universe, 50–75 names, 2-year investment horizon, ~20% of the book below $4B). Transcript:
`transcripts/-oD8LxZ8rD4_tom_maher.txt`.

## Score: 2/5 — articulate process, no testable edge, two trade rules the ledger already contradicts

**Incentive flag first.** A long-only small/mid-cap manager making the case for small/mid caps. He says so himself ("nothing warms
my heart when the market's run by seven gigantic stocks"). No performance numbers anywhere in 66 minutes; the strategy's record is
not mentioned once. Everything below is a claim about the future or a description of his process.

## Claims, and what the ledger says

| # | claim (timestamp) | type | ledger |
|---|---|---|---|
| 1 | Small/mid-cap earnings growth (20–30%/yr expected) is now accelerating faster than mega-cap; AI capex, reshoring and an ISM recovery flow to small industrials; passive S&P flows have left the space under-owned, so a "trickle" of reallocation moves it a lot (01:39–11:13, 36:48–38:25) | macro narrative | **Untestable as stated** and off-goal. What we HAVE tested on small caps: 12-1 momentum and the precision breakout below the $50M ADDV filter are both NULL, and survivorship flatters the momentum spread (TEST_INDEX §4, `smallcap_tests_2026-09-29.md`). His universe (up to $25–30B) is mostly already inside `liquid_panel_2009`, so "small caps" in his sense is not a new universe for us. |
| 2 | **"Don't be afraid to book partial profits on the way up"** — peel off as the thesis plays out, redeploy (63:25) | trade rule | **CONTRADICTED.** Profit-lock study: every trim costs; Qullamaggie partial-then-trail [WL-4] INVERTED (−1.87pp, t −4.39, every arm loses); Tito's spike override NULL as return, a risk lever only; "extended → tighten" INVERTED. On this book the right tail pays and partials cap it. The one untested axis — a resting limit that fills intraday — is pre-registered (`run_spike_limit_partial.py`), not run; his version (sell at the close as the thesis "plays out") is the tested one. |
| 3 | **"If a stock reacts the reverse of what you expect to news, pay close attention"** — beat-and-sell-off, or a cyclical missing by 20% and rallying 15% (64:14) | trade rule / diagnostic | **Half right, no edge.** PEAD on the actual EPS surprise: NULL for the surprise, `corr(surprise, reaction)` = 0.20 — so a mismatch between result and reaction is common, not rare. The reaction itself (the tape signal) is the only thing that carried anything: PARKED, +0.24R t 1.89, straddle pool only. The specific divergence cell (surprise sign ≠ reaction sign) has not been run; it is a sliver of a PARKED result with small expected return — not queued (off-goal). |
| 4 | ETF/theme-basket flows move a small cap for 6–12 months regardless of its fundamentals; a name "clobbered because it's in a basket people are selling" is an opportunity (39:14–40:50) | tape claim with a fundamentals gate | **The tape proxy is INVERTED here.** Buying a name that is weak while its group is weak = buying relative weakness / drawdown: the crash-leader veto (never buy deep drawdowns in a healthy tape) and "held up in the correction" RS INVERTED (−3.51pp, t −3.33). His gate is fundamental conviction, which we cannot code; the part we can code says no. |
| 5 | Idea source #3: a weekly/monthly/quarterly "what's working" sector review, then find a name that passes the stock filter (48:56–50:32) | process | **Consistent with the desk's industry pulse, no measured edge.** Industry rotation cannot be front-run (21d/63d RS NULL); sector 12-1 spread NULL as return, pays only in crises. Using it to direct research time is what we do; using it as a signal is what failed. |
| 6 | Valuation screen: 10-year percentile of EV/EBITDA (P/E, P/S, P/B by sector), cut BOTH tails, hunt the middle; "as wary of really cheap as really expensive" (46:30–48:06) | fundamental screen | **Untested, no data, off-goal.** Point-in-time multiples are not in the catalog (yfinance eps_act only). He also says mean-reversion value "really suffers" in small caps right now — i.e. he does not expect it to pay either. |
| 7 | Quality (self-funding, low leverage) matters more as rates rise; unprofitable Russell constituents are the deterioration (16:50–18:27, 33:37–36:01) | factor narrative | Untested here (no balance-sheet panel). Off-goal: a quality tilt is a small-premium story. |
| 8 | Book breadth responds to the tape: 5–7 new "lines in the water" at pivot points, shrink to high-conviction names when it gets rough (20:50–21:38) | portfolio process | Not contradicted; the house equivalent (book gate, Luk-style whole-book switch) is NULL as a return lever and kept as a drawdown tool only. |
| 9 | Diminishing returns to knowing more: ~3 things drive any small-cap stock; if your thesis plays out and "the market yawns", the thesis was not what the market is paying for (61:51–62:38) | process | Agrees with the house stance that selection, not information depth, is the edge; nothing to test. |
| 10 | Management: judge in retrospect; willingness to admit mistakes; acquisitions that do not fit the stated strategy are the tell (52:59–56:11) | qualitative | Not codable. |

## What is genuinely useful (and it is not a trade)

- **Theme definition that cuts across sectors** (digital infrastructure = optical, storage, servers → data-center builders, electrical
  equipment, fiber crews → regional utilities and banks in the build zones). That is a universe-construction idea, not a signal, and it
  matches how the desk already groups the AI-infrastructure names.
- **The reaction-vs-expectation diagnostic (#3)** is the right instinct and our data agree the reaction carries the information, not
  the surprise. It is a reason to keep the post-catalyst tape signal PARKED rather than dead.

## Not queued

Nothing. Claims #2 and #4 are already answered with INVERTED results; #3's open sliver has a small ceiling and would re-run a PARKED
cell; #6 and #7 need fundamental panels we do not have and target premiums far below the book's goal.
