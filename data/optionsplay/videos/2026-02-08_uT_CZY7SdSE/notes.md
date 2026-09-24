# OptionsPlay: "How to Protect Your Investments at Zero Cost" (Tony Zhang, Growth Lab, 2026-02-08, 35 min)

_Reviewed 2026-09-24. A live-quoted explainer of the zero-cost protective collar on three single names (AMZN, NVDA,
AAPL) going into earnings. No backtest, no sample, no statistic. The last ~2 minutes are the platform and trial pitch._

## Verdict: 2 / 5

The mechanics are right, and more honest than the title. He says plainly that the call caps your upside (06:57), and
that the collar **is** a call vertical by put-call parity (13:21, 18:27). But **"zero cost" is false as a claim about
cost.** Zero premium is not zero cost. What you pay is:

1. **Every dollar above the call strike.** He gives it up himself in AMZN (11:41: "anything beyond 250, you're not
   going to be able to capture").
2. **Skew.** You sell the cheap wing and buy the rich one. His own AAPL collar is $10 of upside for $15 of
   unprotected downside (24:06–24:31: "puts tend to be more expensive than calls").
3. **Two legs of bid/ask**, re-paid every 30 days on the monthly roll he recommends (10:23, 27:31).

When the collar is used is set by a **discretionary bearish outlook** (entry into earnings, "exit if your outlook turns
neutral or bullish" 28:37). So the rule as taught can't be tested. What can be tested is the mechanical
always-on version, and each of its two halves already fails against delta-matched stock in our ledger (see below).

**Selection rule:** own the stock. Sell a **30-DTE, 30Δ call** (he calls this more aggressive than the 10–15Δ he
normally sells for income, 06:03). Buy the put whose premium matches the call's. At the put strike, if you're still
bearish, **roll to a new 30-day collar re-struck at the current price**. If the stock goes sideways, roll the same
strikes. Exit on any change of outlook.

## Data audit

| item | what was shown |
|---|---|
| Sample | 3 hand-picked names on one day (AMZN, NVDA, AAPL), two of them days before earnings |
| Period / backtest | none. No history of any collar, rolled or not |
| Prices | platform quotes, live and from the previous night's slides (13:51: "options prices are quite different from the slide"). Mid vs fill not stated; the net credits ($0.75, $0.28, $0.15) are the size of one leg's half-spread |
| Costs | not mentioned. A monthly roll is 24 option fills a year |
| Control | none. No comparison with holding fewer shares (the collar's net delta), with an outright put, or with just selling |
| Outcome | none. The trades are set up, never followed to expiry |
| Pitch | 33:18–35:05: members-only Q&A, 14-day free trial, "use this tool". The collar builder is the product |

## Claims as spoken

| @ | claim |
|---|---|
| 00:29–01:39 | Macro scene: gold/silver crashing, BTC near 52-week lows, software selling off, rates ~4.3%, payrolls tomorrow: "cracks starting to show" |
| 03:43–04:18 | Sell a covered call, use its premium to buy a put, "at essentially zero cost… without having to pay 2–3% of the stock's value" |
| 05:54–06:24 | For protection, sell a **30-day, 30Δ** call instead of the usual 10–15Δ; "30 delta… about a 30% chance the stock will be above that strike" |
| 07:59–08:32 | Choose the put whose premium matches the call's. The payoff "is synthetically the same as a vertical spread" |
| 08:32–09:05 | "similar, if not identical protection, but for zero cost because you've essentially limited the upside" |
| 09:30–13:51 | AMZN slide: stock 233, sell Mar-6 250C $6.28, buy 215P ~$5.53, **net credit $0.75**; "roughly $16,700 in upside… protected from downside beyond $1,800"; "even if the stock were to drop 20% on earnings… you'll get some downside protection" |
| 14:20–18:54 | AMZN live: ~225, sell 245C $4.95 (29Δ), buy 205P $4.80, net credit $0.28; "virtually identical" to the 205/245 call vertical "because of put-call parity" |
| 14:49–15:19 | Why hedge instead of selling: a low cost basis (tax bill), or keeping the dividend |
| 18:54–19:49 | One contract per 100 shares; you can hedge part of the position |
| 19:49–22:34 | NVDA ~175 into earnings: 190C $4.40 / 160P $4.25, net $0.15. "$15 in upside… $15 more in downside" |
| 22:34–25:47 | AAPL: 285C ~$3.45 / 260P $3.50, $10 up vs $15 down. Uneven because "puts tend to be more expensive than calls". **Pre-earnings collars are more even** because the call is richer |
| 26:21–28:37 | At the put strike: still bearish → roll to a new 30-day collar re-struck at the current price, 30Δ call, matched put. Neutral/bullish → exit |
| 29:08–30:07 | Sideways: roll to a new 30 days at the same strikes, adjusting to keep it zero-cost |
| 30:07–31:41 | (Q from Edward) The put keeps protecting below the strike. Answer: only for 30 days, hence the roll |
| 32:15–33:18 | "Great rotation" out of tech; tech has lagged the S&P for 3+ months |

## Claims vs our ledger

| @ | claim | tag | our evidence |
|---|---|---|---|
| 08:32–09:05, title | **"Protection at zero cost"** | **CONTRADICTED as framed** (zero premium ≠ zero cost) | The cost is the upside above the call strike, plus skew, plus friction. His examples show it: AAPL $10 up / $15 down. The put half has a measured carry. SPY 5% OTM puts, 75 DTE, rolled monthly lose **−25.6% of premium per month held**, and 10% OTM puts lose −32.3%. Real-fill friction is only ~1pp/month of that (`put_overlay/put_overlay_2026-09-20.md` §1). The call half was tested through parity: an OTM covered call is the same trade as a short put at that strike, and 0.30Δ puts on 326 names earn **what the stock at the same delta earns, minus costs** (W 0.30Δ excess −0.06%, t −1.8; `bci_csp_study_2026-09-17.md` §1, "The ITM covered call is the same trade"). Neither half beats delta-matched stock, so the expected cost of the pair is about zero plus friction, before skew |
| 07:59–08:32, 18:27 | Collar = a call vertical (put-call parity) | **AGREES** (arithmetic) | Correct, ignoring dividends and early exercise. It is honest, and it matters: the AMZN collar is a ~0.7Δ/0.3Δ long call spread with the stock already owned. Our nearest vehicle test is a **30Δ/15Δ** call debit spread (a different strike pair): +$97/contract over delta-matched stock, t 2.29, **not adopted** because it failed the SPY < 200 SMA bar (t 1.25) (`vehicle_benchmark_2026-09-22.csv`, TEST_INDEX "Vehicle vs DELTA-MATCHED STOCK") |
| 06:15 | 30Δ ≈ 30% chance of finishing above the strike | PARTIAL | Delta is N(d1). The risk-neutral probability is N(d2), a little lower. Close enough for a 30-day option; a minor point |
| 13:40–13:48 | AMZN slide: "$16,700 upside"; protection "if the stock were to drop 20%" | **Misspoken** | 250 − 233 = $17 → **$1,700** per 100 shares. The 215 put is **7.7%** below 233, so protection starts at −7.7%, not −20% |
| 24:31–25:25 | Puts cost more than calls, so post-earnings collars skew against you; pre-earnings they are more even | AGREES (observation) · UNTESTED (as a timing rule) | Skew is standard. "Collar into earnings because the call is richer" means you buy the put at an equally inflated IV. It is net-vega about flat, not a free lunch. The earnings ledger (vol premium real at mid, gone at the bid) is about selling straddles, not collars. Untested |
| 26:21–28:37 | At the put strike, if still bearish, **re-strike a new collar at the current price** | UNTESTED · the prior is negative | Re-striking after a drop books the loss and lowers the cap, so a V-recovery is sold at the new, lower call strike. Our crash evidence says recoveries are the norm at these horizons: on the 75 certified SPY stress entries, **every crash bounced above the 5Δ strike by expiry** (WL-5f, `spy_tail_overlay_2026-09-23.md`). A rule that locks in the drop and caps the rebound is the wrong shape for that tape |
| 00:29–01:39, 32:15 | Late-cycle "cracks", "great rotation": protection is more valuable now | UNTESTABLE (narrative) | No rule is stated. The nearest tested "warning" is coincident: VIX/VIX3M first inverts only after the index is already down 3.4–9.3% (TEST_INDEX, tastylive VIX-regime batch row) |
| 14:49–15:19 | Hedge instead of selling for tax or dividend reasons | Not an edge claim | A legitimate reason to prefer an overlay to a sale. ⚠ Not verified here: tight collars on appreciated stock can raise constructive-sale questions. Not our domain |

## What the collar is, for our book

The book holds no index. Its drawdowns are mostly **not SPY-driven**: book-vs-SPY monthly correlation is **0.22**,
and **5 of the book's 10 worst months had SPY UP** (2018-11, 2019-04, 2018-09, 2022-11, 2020-08;
`put_overlay/put_overlay_2026-09-20.md` §3, re-confirmed in `logs/sector_overlay_test.log`). A SPY collar laid over a
book that owns no SPY is a **short risk reversal**: a banded SPY short. Its short call **loses** in exactly those
up-SPY bad months. The pre-registered **same-vol SPY short control already cut no drawdown** (full book maxDD
24.97 → 24.97 at 50%, Sharpe −0.49; no-straddle 38.1 → 38.9; `sector_overlay_test_2026-09-24.csv`). The **sector
momentum spread 12-1 K3** is the only sleeve that genuinely hedges the book: maxDD 25.0 → 20.9 at 50% of book vol,
survives de-meaning (−4.5), averages +1.0% in the book's 10 worst months (same file). **A collar-vs-sector-spread
test on the book is therefore NOT worth specifying.** Its best case is the SPY-short control, which has already lost.

## Not tested, could be

Collars are absent from TEST_INDEX (grep "collar" → no row). The **one new axis** is the standalone question for
someone who holds the index, not for our book. Low priority, **not queued**:

- **Spec (codable, v3 only, ~½ day of Athena pulls):** SPY 2010-02 → 2026-02, monthly. Hold 100 shares. On the first
  session of each month sell the **30-DTE call nearest 0.30Δ at the bid** and buy the put whose ask is closest to that
  bid (the "zero-cost" match), hold to expiry, settle at intrinsic from the chain spot (`chain_spot.py`, v3 strikes
  are raw), house cost model on both legs.
  - Arms: (A) collar; (B) **SPY at the collar's entry net delta** (the parity control: same exposure, no options);
    (C) buy-and-hold SPY; (D) SPY + the 12-1 sector spread sized to match the collar's realised vol.
  - Primary: A − B monthly return, month-clustered t. It isolates skew plus friction, and should be negative.
  - Secondary: maxDD and the 2020-03/04, 2022 and 2025-04 paths for A vs D. This is the "which hedge costs less per
    point of drawdown" question.
  - Add his re-strike-at-the-put rule as arm A2.
  - Must-pass: 2020-04 and 2022-11 (V-rallies), where the cap binds.
  - Prior: A − B negative, from the put carry and the covered-call ≈ delta-stock results; D beats A on drawdown per
    unit of return given up.
  - ⚠ Leave single names into earnings (his actual use) out. It is event-conditioned, with n ≈ 4 events per name per
    year.
