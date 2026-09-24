# Freedom Income Options — "I Tested Tom Sosnoff's Strategy for 3 Months — Here's What Happened" (2026-05-28, 12 min)

_Reviewed 2026-09-23. Solo talking-head recap of a 3-month forward test of weekly 45-DTE short ES puts, plus a
reply to a commenter's backtest, a Malcolm Gladwell detour (Roseto) and a members-community pitch. Transcript
(`en-orig` auto-captions) and meta in this folder. 28.7k views. The companion video "45-Day Put Selling Strategy |
Tom Sosnoff's Proven Trade" (`0f2kr2iOXzg`) and the launch video (`Q3Rmbs5_nEM`) aren't downloaded._

**His rules (@00:38, and restated in the description):** $75,000 **simulation** account. ES futures puts only.
One contract per trade, one new trade per week. 10-delta short put (he also tried 9Δ). Enter at 45 DTE. Close or
roll at 21 DTE. Take profit at 50% of credit.

⚠ **The description contradicts the video.** The description says "This is real money documented week by
week, not theory." The video says "$75,000 on a simulation account" (@00:38). ⚠ The two also disagree on the
delta. The description says "10 delta short puts (adjusted from Tom's approach)". The video says "Tom used the 10
delta. I tested the 10 and the 9" (@02:46). Sosnoff's own stated #1 trade is a ~20Δ strangle
([OptionsPlay interview](../../../optionsplay/videos/2024-10-14_pQlGgcyrUoQ/notes.md)), not a 10Δ naked put.

## Verdict: 2 / 5

The rule set is complete, mechanical and tastytrade-orthodox. He says himself that "3 months isn't a good test"
(@06:56), which is more candour than most of this genre. The vehicle (ES options) is one where friction is small,
so it avoids the cost trap that sinks single-name selling.

The evidence is one simulated quarter with zero losing trades. That quarter was close to the best possible for
the rule: a 9% selloff into VIX 31, then a V-shaped rally to new highs. He annualises it to "$45,000 a year, 60%".
Two of his three lessons get the mechanism backwards:
- **"You make more money when the market crashes."** New entries collect more premium. The positions already on
  lose.
- **"Four bear markets in 20 years, so 16 of 20 years are profitable."** This miscounts the bear markets, and it
  assumes short puts lose only in bear years.

His position sizing on a $75k account puts roughly **$1–1.4M of notional short put exposure** on the book. He
calls that sizing the "guardrail". It isn't one against a 2020-type gap.

The one real finding in the video is one he doesn't know he has: **his best month (March) is exactly our one
certified cell** (selling index put risk after a selloff with VIX ≥ 20). The rest of his window, the LowIV weeks,
is the regime where our index put-selling tests don't pay.

## Results audit

| item | what he says / shows | audit |
|---|---|---|
| Window | "3 months in", uploaded 2026-05-28. "March was my most money." "I did this test in a 9% drop" | ≈ late Feb → late May 2026. The exact start date is in the launch video, which isn't downloaded |
| Trades | 1 per week | **≈ 12–13 entries.** The last ~3 (entered after ~early May) can't have hit 21 DTE yet, so they're either 50% takes or still open. **He doesn't say whether $11,357.50 is realised or includes open marks** |
| Underlying | ES (E-mini S&P) puts, 1 lot | ES ≈ $50 × SPX ≈ **$340k notional per contract** in the window (SPX ≈ 6,300–7,600) |
| Account | $75,000, simulated | With 45→21-DTE holds and one entry a week, **3–4 puts are open at once** ≈ $1.0–1.4M notional, ≈ 15–18× the account. Delta is only ~0.10 each (≈ $34k of long delta per contract) until a gap turns 0.10 into 0.50 |
| P&L | **$11,357.50**. Best week $1,345. "On one trade you make 700… in a down market 1,500" | ≈ $874 per entry. **Internally plausible at sim fills.** Modelled 10Δ 45-DTE SPX put (Black-Scholes, VIX × 1.0–1.25 as the put IV, no quotes): ≈ 23–29 SPX points at VIX 20 ($1,165–1,470 per ES). A 50% take on that ≈ $600–735, which matches his "$700". At VIX 27–31 the credits are roughly 1.5× larger, which fits the $1,345 best week |
| Losses | "no losses… I did have some trades underwater, but… market bounced first" (@06:17) | See the entry-by-entry table below. **This depends on the start date.** A 10Δ put sold 2026-02-27 (VIX 19.9) would have been ≈ −100% of its credit at its 21-DTE date (2026-03-23, SPY 655), *modelled*. Under his own 21-DTE rule that's a realised loss. So either his first entry was ~2026-03-06 or later, or the rule was not applied to it. Unverifiable without his log |
| Fills / commissions | Not stated. Simulation account | **Paper fills, almost certainly at or near mid. Commissions unknown.** On ES this matters far less than on single names. The house model (25% of a ~0.25–0.5-pt quoted spread per side, plus exchange fees) is ≈ $15–30 per round trip against ≈ $874 average P&L, i.e. 2–4%. ⚠ ES option spreads are assumed, not measured here: **we have never tested futures options** (TEST_INDEX §9 More Tom row). Friction isn't what's wrong with this record. The sample and the regime are |
| Annualised | "$45,000 a year… 60%" (@07:02). "Two contracts → 90K" | One quarter × 4, from the quarter that contained the ideal vol spike and recovery. Doubling contracts doubles the tail, not just the income |
| Community claims | "just under $40,000 since Feb 2025" as a community. "$100 account → $5,500" | Unverifiable. The case study sits behind a funnel (freedomincomeoptions.com, members community) |

### What the market did in his window (SPY via yfinance, VIX from `data/cache/vix_daily.parquet`)

| Friday entry | SPY close | our regime (SPY vs 50MA × VIX ≥ 20) | VIX | modelled 10Δ strike (SPY) | min SPY low, entry → 45d later | modelled outcome under his rules |
|---|---|---|---|---|---|---|
| 2026-02-20 | 689.4 | Bull_LowIV | 19.1 | ~621–633 | 629.3 | 21-DTE close ≈ −22% of credit |
| 2026-02-27 | 686.0 | Bear_LowIV | 19.9 | ~616–627 | 629.3 (**at/through the strike, on the σ = VIX version**) | 21-DTE close ≈ **−106%** of credit |
| 2026-03-06 | 672.4 | **Bear_HighIV** | 29.5 | ~574–589 | 629.3 | 50% take |
| 2026-03-13 | 662.3 | **Bear_HighIV** | 27.4 | ~572–586 | 629.3 | 50% take |
| 2026-03-20 | 648.6 | **Bear_HighIV** | 26.8 | ~562–575 | 629.3 | 50% take |
| 2026-03-27 | 634.1 | **Bear_HighIV** | 31.1 | ~537–551 | 629.3 | 50% take |
| 2026-04-02 (Thu; Good Friday) | 655.8 | **Bear_HighIV** | 23.9 | ~577–589 | 645.1 | 50% take |
| 2026-04-10 → 05-22 (7 entries) | 679 → 746 | Bull_LowIV | 16.7–19.2 | 5–9% below spot | never within 3.6% of the strike | winners (rally to all-time highs) |

**Window summary.** SPY peaked 2026-02-25. It fell **−8.8% close-to-close (−9.3% intraday)** to a 2026-03-30 low of
629.3, with VIX peaking at **31.05** on 03-27. It then rallied **+20%** to 756 by 05-29 (new highs). Over the window
SPY was **+10.6%** and mean VIX was **21.0** (68th percentile of 2018–2026). This is close to the ideal path for a
short-put seller:
- a vol spike that inflates new credits;
- no gap large enough to reach a 10Δ strike sold at high IV;
- a V-shaped recovery that turns every open position into a fast 50% take.

The weeks that *could* have hurt him are the ones sold **before** the spike, at VIX ≈ 19–20 (Feb 20/27). Those
look like losers at their 21-DTE dates.

⚠ The strikes and outcomes in the table are **Black-Scholes approximations** (put IV = VIX × 1.0–1.25, no sticky-strike
dynamics). `options_cache` ends 2026-02-20 and v3 bid/ask ends ~Mar 2026, so there are no real quotes for this window.
Read them as direction and rough size, not fills.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:00 | "$11,357.50 in profit" in 3 months testing Sosnoff's strategy | **One simulated quarter, n ≈ 13 overlapping entries, all winners, all on one index, all in one vol episode. Effective n ≈ 1.** Our bar is \|t\| ≥ 3 with both halves the same sign. A single regime can't produce a t at all. Nothing can be certified from this, and he says so himself @06:56 |
| 00:38 | Rules: 45 DTE, 10Δ short ES put, 50% take, manage at 21 DTE, 1 lot per week | **The mechanics are tested here in pieces, never as this exact trade.** (a) **21 DTE vs hold** on a 45-DTE/20Δ strangle, real fills, 7,265 trades / 44 names: paired **+$1.53, t +4.26, PASS, but both arms negative** (A −2.55 / B −1.02). Primary artefact `exit_21dte_2026-09-23.csv`, SPY rows (n 242, credit ≈ $5.15/sh): hold **−$1.77**, 21-DTE **−$0.46**, i.e. −34% and −9% of credit. So the 21-DTE rule is the part of his rules our data likes most, and it still doesn't make an unconditional 20Δ SPY strangle pay at real fills. (b) **50% take**: carries the ETF bull put result ("the exit rule is the edge", 45 DTE 0.35/0.25, 50% take, no stop: +5.70%/trade after the ceiling-filter erratum, monthly t 3.13, "substantially long-beta"). (c) **Ungated SPY 45-DTE 0.35/0.25 bull put, 50% take**: n 409, per-trade t 1.9, **monthly t 1.2**, 2018/2022/2026 negative (`project_what_survives`). **Not tested: a naked 10Δ put, and anything on futures options** |
| 01:55 | Best week $1,345, because "the market was falling… 9% drop… volatility created higher profits" | ✅ **Half right, and it's our one certified cell.** `tierab_significance_2026-09-22.csv`: **SPY bull put Bearish_HighIV** (below 50MA, VIX ≥ 20; 20 DTE 0.25/0.15, 50% take): **75 trades / 37 months, month-mean +8.70%, t 6.07, 8/9 years, 94.7% win.** **SPX condor Bearish_HighIV** (45 DTE, 50% take / 2× stop): **t 5.21**. These are one bet ("sell index put risk after a selloff when VIX ≥ 20"). Five of his ~13 entries (03-06 → 04-02) fall in that regime. ⚠ The same file has the regime most of his *other* entries were in going the wrong way: QQQ bull put Bullish_LowIV **month-mean −4.78%, t −0.87** (QQQ, not SPY; there is no SPY LowIV row), and the SPX playbook says of VIX < 20: "no entry; edge disappears" |
| 02:24 | Lesson 1: every closed trade frees capital, so "compounding" weekly cash flow | **Framing, not a claim.** Frequent 50% takes raise turnover, and our cost work says turnover is where friction compounds. That's cheap on ES, lethal on single names (10-DTE single-name selling: costs = 136% of gross, **FAIL**). "Weekly paycheck" describes when the P&L arrives, not whether there's an edge |
| 02:53 | Lesson 2: went 10Δ / 9Δ "for more safety… ~90% probability" | ❌ **POP ≠ edge. Contradicted across our ledger.** Win rate is priced in: in the More Tom review, win rate **falls 79.6 → 75.7%** as net ROC **rises −2.96 → +4.07%** (t 3.74). Going further OTM also raises the share of the P&L sitting in the tail, and it doesn't make the trade safer per dollar of notional. It's a vol-selling choice, not a safety choice |
| 03:17–05:00 | Commenter "you'll get crushed in a downturn". Reply: 4 bear markets in 20 years ("2008, 2009, 2020, 2022"), so "16 years profitable, 4 not"; guardrails = size + the 21-DTE rule | ❌ **Wrong arithmetic, and the wrong object.** 2008 and 2009 are **one** bear market (−56.8%, trough 2009-03-09). Separately, a 10Δ put book doesn't lose only in >20% years. Near-bear drawdowns: 2011 −19.4%, 2018 −19.8%, 2025 −18.9% (^GSPC). A put book is hit hardest by *fast* moves: 2018-02, 2015-08, 2024-08 (−8.5%), 2025-04. "Loss years" is not "bear years". **The commenter's point stands.** Our crash-week rule (`feedback_test_crash_weeks_before_reporting`) exists because paths like this get truncated in backtests. At ~$1–1.4M notional on $75k, a 2020-style −34% leaves 3–4 ES puts (struck ~9% OTM) ~25% in the money: ≈ **$75–85k loss per contract at intrinsic** (≈1,700 SPX pts × $50), several times the account. His guardrail (one lot, 21-DTE roll) doesn't reach that gap. Our sizing rule is size by max loss, and on a naked put max loss is the strike |
| 05:04 | "Don't over-leverage and roll before expiration": the 21-DTE rule *is* the guardrail | **Partly supported.** 21-DTE **halves the variance** in our test (sd $11.86 vs $23.58, worst −$259 vs −$617 per strangle). That's a risk result, not a return result, and it doesn't protect against a gap inside the 45→21 window. **Rolling** as a rescue is contradicted: roll test, 69.8% better held |
| 05:42–06:40 | Lesson 3: "when the market starts to crash, you make more money… even if you take a couple of small losses by rolling, that will be offset by a bigger win next time" | ⚠ **Conflates new-entry premium with open-position P&L.** The *new* entries after a spike are the certified cell (above). The positions *already on* when the spike starts are the losers (his 02-20/02-27 weeks, modelled at their 21-DTE dates). "Offset next time" assumes the bounce, which he got in one quarter. Our ledger on the adjacent claim, "IV stays inflated after a big move": **FAILS vs VIX-matched days** (post-shock premium). The richness is the VIX *level*, which the regime gate already captures |
| 06:17 | "I did this test in a 9% drop and had no losses… the market bounced before I had to roll a negative trade" | **Survivorship of one path.** True only if his first entry was on or after ~2026-03-06 (see audit). In our SPY 21-DTE rows, 2020 is **−$8.48/strangle held, −$3.50 managed**. In 2020 the bounce came after the gap, not before the roll |
| 06:41 | "$45,000 a year… 60% on $75,000"; two contracts → $90K | ❌ **Annualising one best-case quarter.** Even our certified index stress cell has ~43% of its trades in one year (month-mean +8.7% on margin, not on account). The LowIV weeks that make up most of a normal year are the ones that don't pay |
| 07:40 | Start with /MES at $2,500, or $100 in cash-secured puts on small stocks | ❌ **The $100 route is the BCI FAIL plus the liquidity gate.** CSPs ≈ stock at the same delta minus costs (326 names, 8 years), and small-stock option spreads are the UVIX/UVXY friction pattern. /MES at $2,500 is ~$34k notional per contract: the same leverage at 1/10 scale |
| 10:51 | Community "just under $40,000" since Feb 2025, "real trades", case study | **Marketing.** Unaudited, pooled, winners-selected. Not evidence |

## What I would take

1. **Nothing to adopt.** The trade he forward-tested is the tastytrade 45/21/50 put sale. The one cell of it our
   data certifies is the **bearish-high-IV index put sale**, which we already hold (Tier S, "Index stress bucket").
   His March happens to be that cell, and it proves nothing extra.
2. **A clean worked example of regime conditioning.** His "best week" and "best month" are the certified cell. The
   weeks before the spike (VIX ~19–20, sold right before the selloff) are where an always-on book gets hurt.
   The unconditional weekly rule is not what paid him.
3. **Notional leverage is the check to run on any "one lot per week" futures-option claim.** ES at ~$340k per
   contract × 3–4 concurrent on $75k is the real risk number. The video never states it.

## Not tested, could be

**Does the ledger already answer Sosnoff 45-DTE / 50% take / 21-DTE on SPY at real fills?** Partly, not exactly.
- The **21-DTE leg** is answered: `run_21dte_exit_test.py`. It includes SPY (n 242), at real fills, as a **20Δ
  strangle**. The rule helps, t 4.26 pooled, but the trade is negative in both arms.
- The **50% take** is answered on **put spreads**: the ETF roster, and SPY 45 DTE 0.35/0.25 at monthly t 1.2.
- The **regime-gated index version** is answered and certified: SPY 20-DTE bull put t 6.07, SPX 45-DTE condor
  t 5.21.
- **Never run:** a *naked 10Δ put*, 45 DTE, exit on 50% or 21 DTE (whichever comes first), every week, on
  SPY/SPX. Also never run: anything on ES options (no futures-option data).

**Spec (if wanted).** `run_sosnoff_45dte_put.py`, pre-registered.
- **Data:** SPY (and SPX) `options_daily_v3` 2010-01 → 2026-02 (the bid/ask cliff). The ES proxy is SPX:
  European, cash-settled, same underlying.
- **Entry:** every Friday, the expiry nearest 45 DTE, sell the ~0.10Δ put **at the bid**.
- **Exit:** buy back **at the ask** at the first of 50% of credit or the first session ≤ 21 DTE. House cost model.
- **Path handling:** path-coverage guard mandatory, `lib.studies.path_coverage`. Zero-bid marks are missing from
  `options_cache`, so pull from v3.
- **Arms:** A = always-on, the primary (his rule). B = Bearish_HighIV only (our cell, as a naked put). C = hold to
  expiry.
- **Control:** delta-matched long SPY (entry-delta shares, same holding days). The 10Δ put is mostly short vol plus
  a sliver of long beta.
- **Report:** return on **notional** and on a SPAN-like margin, the worst week, and **every crash week
  explicitly** (2010-05, 2011-08, 2015-08, 2018-02, 2018-12, 2020-02/03, 2022, 2024-08, 2025-04).
- **Bar:** A minus the control, month-clustered t ≥ 3, both halves and per-year the same sign.
- **Prior:** A ≈ the VRP (10d +1.75vp, t 8.93, real) minus a fat left tail. Expect A to be positive on mean but
  not certifiable, and B to replicate the certified cell. The question it answers is whether "always-on" adds
  anything beyond the regime gate. I expect it doesn't.
- **Effort:** ~½ day. `put_spread_study` with the wing removed, or a far-OTM wing as the naked proxy.

**Not queued** unless asked. The informative arm (B) already certifies as a spread, and the futures-option
question (the one thing genuinely new here) still has no data.
