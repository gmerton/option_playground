# Double calendar / diagonal / condor playbook (2026-09-15, rev 2026-09-16) — ⚠️ WITHDRAWN 2026-09-16

> **Every number in this playbook came from a sim whose daily path was cut off after ~2% moves (chain pull strike
> window), so losses beyond 3% never registered. Corrected settlement on the ETFs: calendar +3.5 / −2.2%, diagonal
> +2.8 / −2.5%, condor +0.8 / −6.6% (12/19d / 20/27d), win ~50%, monthly t ≈ 0, 2018–2020 and 2023 negative.
> There is no measured edge (confirmed on the clean re-run: best cell +4.4%, t 0.5; 20/27d negative). The Friday
> screener's IWM / QQQ / SPY entries were REMOVED 2026-09-16; the stock screener is RETIRED: on the clean stock run every structure loses 5–18% of max risk per trade on the liquid roster (monthly t −3.4 to −5.0).** Erratum with the corrected tables:
> `calendar_path_study.md`.


Source: `calendar_path_study.md` (steps 1–11, real daily bid/ask 2018-11 → 2026-07, house cost model on four legs,
hold-to-expiry settlement). Supersedes the per-ticker calendar notes; `spy_double_calendar_playbook.md` and
`iwm_calendar_playbook.md` carry the ticker detail.

## Current structure by universe (rev 2026-09-16)

| universe | structure | shorts | longs / wings | expiry | hold | size on |
|---|---|---|---|---|---|---|
| **IWM / QQQ / SPY** | **iron condor, same expiry** (step 11) | 0.35Δ put + 0.35Δ call, ~20 DTE (12 DTE also fine) | ~2% of spot beyond each short, SAME expiry | one | to expiry, no profit take | width − credit |
| stocks, no earnings in the window | 2% double diagonal (steps 7b/7e) | 0.35Δ, ~20 DTE | 2% wider, next weekly | two | to short expiry | net debit + wing |
| stocks, earnings between the expiries | same-strike double calendar (step 7c) | 0.35Δ, ~20 DTE | same strikes, next weekly | two | to short expiry | net debit |

**The condor was tested on stocks (step 12) and LOST to the diagonal** (+7.6 / +10.1% vs +12.4 / +12.6% on the 60-name tight cut, paired −$0.28, worse in every earnings cell; 0.10Δ wings +2–3%): single-name front-month wings are dear and the next-week long keeps value into events. Stocks stay diagonal / calendar; the condor is an ETF structure only. **The Friday screener builds the
ETF condor since 2026-09-16** (`same_expiry_wings` on the IWM / QQQ / SPY entries; prints credit, max risk = width − credit,
breakevens; sizing table uses max risk). Live 2026-09-15 close: IWM 281/290 shorts, 275/296 wings, Oct 2, credit $3.08
on $2.92 risk; QQQ 694/716, wings 680/731, credit $7.48 on $7.53 risk. SPY's old regime gate is REMOVED (2026-09-16): the
SPY condor alone was positive in every regime cell in both halves (12/19d: Bear_HiVIX +47, Bear_LoVIX +11, Bull_HiVIX
+31, Bull_LoVIX +16; 20/27d: +40 / +28 / +48 / +21), so SPY enters in all four regimes like IWM and QQQ. SPY now uses the
20-DTE short like IWM and QQQ (the 12-DTE target landed on SPY's Monday / Wednesday expiries; the study is Friday weeklies).

## ETFs: the iron condor replaces the double diagonal (study step 11, 2026-09-16)

Same Friday entries, same 0.35-delta shorts, same short expiry; the only change is WHERE the long legs sit. The
double calendar buys the longs at the same strikes one week later; the diagonal buys them 2% wider one week later;
the condor buys them 2% wider in the SAME expiry. 765 paired entries at 12/19d, 651 at 20/27d, hold, ROC on max risk:

| structure | 12/19d ROC | win | halves | 20/27d ROC | win | halves | ROC / day | $ / spread | tail 5% / 1% (% max risk) | months + | monthly t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| same-strike double calendar | +11.0% | 60% | +6.7 / +15.3 | +19.5% | 59% | +17.1 / +22.1 | 0.90 / 0.96 | +$0.39 | −75 / −116 | 72% | 6.3 |
| 2% double diagonal | +19.1% | 77% | +19.0 / +19.1 | +27.0% | 82% | +26.3 / +27.8 | 1.54 / 1.33 | +$1.31 | −29 / −58 | 97% | 16.5 |
| **iron condor, 2% wings, same expiry** | **+31.8%** | 75% | +32.5 / +31.2 | **+41.4%** | 81% | +41.1 / +41.8 | **2.58 / 2.04** | +$1.49 | −45 / −84 | 99% | 16.0 |
| iron condor, 0.10Δ wings | +20.5% | 84% | +19.4 / +21.6 | +21.8% | 88% | +21.5 / +22.1 | 1.67 / 1.07 | +$1.77 | −22 / −59 | 99% | 19.1 |

Why the condor wins, and where it does not:
- **Paired on identical entries** the 2%-wing condor adds $0.17 per spread over the diagonal (t 5.7 / 7.2, better in
  62–64% of entries) on **25% less max risk** (credit ~$3.1 on ~$4.9 at 12/19d vs the diagonal's ~$6.4). The
  0.10Δ-wing condor adds $0.45 on 40% more risk: most dollars and the best tail, lower ROC.
- **Robust on every cut:** all three tickers (IWM 24 → 41 / 34 → 54, QQQ 20 → 34 / 30 → 45, SPY 14 → 23 / 21 → 30),
  every regime cell (Bear_LoVIX 20 → 30, Bear_HiVIX 34 → 62), every year 2018–2026 (2019 14 → 23, 2022 31 → 53),
  every entry-VIX bucket (< 15: 14 → 19; > 30: 38 → 80).
- **VIX path:** the condor wins when VIX falls over the trade (fell > 3: 20 → 41) and only TIES when VIX rises more
  than 3 points (25.0 vs 25.7). That is the one week the next-week longs earn their cost.
- **Settlement:** inside 1% of entry the condor makes +66 vs +38; 1–2% away +40 vs +24; beyond 2% both ≈ 0.
- **The cost:** the worst ten condor trades are the same 2.5–4% moves that hurt the diagonal, and the condor loses
  $1–3 more on each (the diagonal's longs keep some value). Dollar 1% tail −$4.1 vs −$3.4 per spread.
- **Management is unchanged:** hold beats a 50% take (31.8 vs 26.1; 41.4 vs 34.0), a 2x-credit stop rarely triggers,
  and the last day is worth ~10pp (closing the day before: 21.3).

Reading: on the index ETFs the back-month long legs are a cost, not a hedge. The study walked from long-the-back-month
(calendar) to less-long (diagonal) to not-long (condor), and each step paid.

**Live example, SPY 2026-09-15 close, spot 758.25, expiry 2026-10-02 (17 DTE):** sell 748P ($5.89) / 766C ($4.74),
buy 733P ($3.19) / 782C ($0.72). Credit $6.73, wings $16, **max risk $9.27/shr ($927/contract)**, credit 73% of risk,
breakevens 741.3 / 772.7. (Trade it with equal 15-point wings, 733/781, rather than the literal 2% strikes.) The
0.10Δ version: buy 710P / 780C, credit $8.26 on $29.74 risk.

**Entry rules for the ETF condor:** Friday; weekly nearest 20 DTE (12 also works, lower ROC per trade, higher per
day); shorts at 0.35Δ each side; wings ~2% of spot beyond each short (round to equal widths); every leg ≤ 25%
bid-ask; every regime; no IV or term-structure gate (the condor is short vega throughout, and high-VIX entries
were its best cells). **Size on max risk = width − credit**, Tier B for IWM / QQQ, SPY per the allocation framework.

## History: the DOUBLE DIAGONAL step (study step 7, 2026-09-15; still the STOCK structure)


**On IWM / QQQ / SPY the long legs now sit 2% of spot WIDER than the short strikes** (long put at the largest
next-weekly strike <= Kp x 0.98, long call at the smallest >= Kc x 1.02; rev 2026-09-15 evening from 1% after the
width sweep in study step 7d: 1% +15.0 / +21.3, 1.5% +17.8 / +23.6, **2% +19.1 / +25.2**, 3% +18.8 / +22.0 on max
risk; 2% is best or within 0.5pp in every regime cell and both halves; 3% sells too much vega and gives back the
vol-spike years). Same Friday entry, same 0.35-delta shorts,
same two expiries, same hold. Tested on the same 1,971 entries as the calendar (`run_ddiag_path_sim.py`):

| hold, ROC on max risk | calendar | diagonal, 1% wider | win | halves (diagonal) |
|---|---|---|---|---|
| 12 / 19 days | +12.1% | **+15.6%** | 60% → 67% | +15.2 / +16.0 |
| 20 / 27 days | +19.1% | **+22.5%** | 60% → 72% | +19.1 / +25.9 |

Paired +$0.33 per spread (t = 19.6), better in 72% of entries, on all three tickers, in 8 of 9 years (2019 turns
positive), in every regime cell but one flat one; largest gain when VIX falls during the trade; smaller tail (worst 5%
−51% of max risk vs −74%). Management unchanged: hold; profit takes still −3 to −7pp.

**Sizing changes:** the structure is often near-zero cost or a small credit, so **max risk = net debit + the wider
wing width** (only one wing can be breached at the short expiry) -- the screener prints it and sizes on it. Live
example 2026-09-15: IWM 281/290 shorts, 278/293 longs, credit $0.51, max risk $2.50; QQQ 694/716 shorts, 687/724
longs, credit $1.14, max risk $6.87. Gates unchanged (each of the four legs ≤ 25% bid-ask).

**Stocks (step 7b, same evening):** the same 1% diagonal on the tight-market cut: 60-name pool +9.9% vs +6.5% (12/19d)
and +10.1% vs +6.3% (20/27d), 30-name generalisation set +9.8% vs +7.3% and +7.8% vs +4.5%; win 55-58% → 63-66%;
paired t = 10-12, better in 71-72% of entries, both halves, 16 of 17 set-years. The lift is on the middle of the
roster (PLTR, BAC, INTC, QCOM, FDX, ORCL, TSM); the top mega-caps are flat. **The stock version is the diagonal too, at the same 2% width** (step 7e sweep: 1% +10.1, 1.5% +10.3, 2% +10.9, 3% +10.9 on 12/19d; the calendar→1% step is the big one, 2% adds ~0.7pp on both halves).
Liquidity gate for stocks = the SAME-STRIKE calendar's four-leg bid-ask ≤ 25% of its debit (the diagonal's own debit
is ~0 so a %-of-debit gate is meaningless); size on max risk.

## History: the original double calendar (steps 1–6)

Put calendar below the market + call calendar above it, same two expiries. Short legs on the nearer expiry at
**0.35 delta each side**, long legs at the **same strikes** on the next expiry. Net debit = max loss.

| Structure | Short leg | Long leg | Use |
|---|---|---|---|
| 20 / 27 days | ~20 DTE | next weekly (+5..9d) | the screener's default: scored higher on every name |
| 12 / 19 days | ~12 DTE | next weekly | the original SPY double-calendar legs; fine, lower ROC |

## Universe and expected results (held to the short expiry, after costs)

| Name | 20/27d ROC | 12/19d ROC | win | halves (20/27) | tier |
|---|---|---|---|---|---|
| IWM | +25.6% | +15.4% | 63–64% | +23 / +28 | B |
| QQQ | +19.4% | +14.3% | 59–60% | +11 / +28 | B |
| SPY | +12.5% | +7.5% | 55–57% | +11 / +14 | C (dcal playbook, regime-gated) |
| Mega-cap stocks, tight markets (earnings between the expiries preferred, see rule 3) | +7.6% | +7.2% | 56–58% | +7 / +8 | `run_stock_dcal_screener.py` (2026-09-15) |

Pooled ETF result 8 of 9 years positive (2019 the exception); monthly-mean t 5–6; ~60% win with a fat right tail.
**Do not size on the win rate** -- the mean comes from the winners.

## Entry rules

1. **Friday entry**, ATM-relative strikes by the short legs' delta (0.35 / 0.35). Not 0.25 (+8% / +6%) and not the
   asymmetric 0.35P / 0.10C (+8% / +2%): the strike set is the single biggest lever in the study.
2. **Bid-ask gate:** each leg ≤ 25% (screener), and the whole structure's entry bid-ask ≤ 25% of the debit. Below 10%
   is where the best numbers live. On ETFs this is automatic; on stocks it is the whole edge (>25% = −12 to −15%).
3. **Stocks:** debit ≥ ~$1.50 (cheap names with penny debits lose), mega-caps only (NFLX, TSLA, NVDA, META, AAPL,
   GOOG/GOOGL, MSFT, AMD, AVGO scored +11–22%; AAL, BAC, CSCO, XOM, PLTR, INTC ≤ +1%).
   **Earnings rule (rev 2026-09-15 evening, replaces "no earnings in the window"):** the position of the earnings
   date decides it, on the tight cut:
   | earnings date | 12/19d | 20/27d | rule |
   |---|---|---|---|
   | between the short and the long expiry (ideally 3–4 days after the short) | +10.4% (n=851, 66% win, +8/+13) | +15.1% (n=540, 66%, +10/+19) | **preferred** |
   | none in the window | +7.2% | +7.4% | fine |
   | before the short expiry (the "earnings crush" placement) | +1.4% (n=311, 50% win) | +10.4% (n=178) | **avoid on 12/19d**; allowed on 20/27d |
   The old −3pp "earnings hurt" number came from the pooled 90-name table, where wide-market names dominated.
   **Structure by earnings position (step 7c):** earnings between the expiries → the SAME-STRIKE calendar (the
   diagonal earns the same dollars on ~20% more max risk: +10.2 vs +11.2% and +13.9 vs +16.7%, both halves); no
   earnings → the 1% diagonal (+9.9 vs +6.6%); earnings before the short expiry → the diagonal if traded at all
   (12/19d +6.9 vs +1.7%, 20/27d +16.9 vs +10.5%).
4. **No term-structure or IV gate.** FVF and the IV ratio separated nothing on the liquid names; own-IV percentile
   > 80 leaned better on small samples -- note it, do not require it.
5. **Regime:** enter in every regime. High-VIX cells were the best on the ETFs (Bear_HiVIX +26 / +32%, 69–75% win);
   Bull_LoVIX is positive overall but was negative before mid-2022 -- size it smaller if you want to respect that.
   An FOMC inside the window did not hurt (12/19d +22% with the Fed inside vs +8% without; 20/27d indifferent).

## Management: hold

**Hold to the short expiry. Both short legs settle at intrinsic; sell both long legs at the close.** Every exit rule
tested lost to holding on paired tests, on ETFs and on stocks:

| Rule | vs hold (ETF 20/27) | vs hold (stocks, tight cut) |
|---|---|---|
| Profit take 25 / 50 / 75% | −8 / −4 / −2pp | −7 / −2 / −1pp |
| Stop at 40 / 60% of debit | −2 / −1pp (rarely triggers) | −2 / −0pp |
| Re-center once on a 2σ move | −4pp | −6pp |
| Close the far side when a strike is tested | −10pp | −11pp |
| Close a side at half its debit | −3pp | −4pp |
| Term-structure inversion exit (oquants) | −16pp | −11pp |

Profit takes raise the win rate to 70%+ and cut the mean; the position is a defined-risk debit, so there is nothing
to protect by stopping it. The same result held for long straddles and single calendars.

## Sizing

Tier B for IWM / QQQ (screener), SPY per the dcal playbook (1.5% alongside the put spread). Debit = max loss; a 60%
win rate with a fat right tail means a run of losers is normal. Cap combined calendar debit as the allocation framework
already does for correlated index entries.

## Not tested / open

Tested and rejected 2026-09-16 (study steps 8–10): 30-day and 47-day fronts, short delta 0.40/0.45, closing 1–2 days early, asymmetric widths, a 14-day gap, the triple calendar, and rolling weekly shorts against a longer-dated long. **Open after step 12:** the ETF condor with 0.10Δ wings as a lower-ROC / higher-dollar alternative.


**Long-dated structures (front ~49 DTE / back ~76, 27-day gap, the My Trading Journey recipe) -- queued 2026-09-15, needs a 45–85 DTE chain pull;**   the call-side-only calendar; intraday exits;
unequal deltas other than 0.35/0.10; bid/ask data end July 2026 -- re-cut when it extends. A screener entry for the
stock version is `run_stock_dcal_screener.py` (built 2026-09-15): 26-name roster, shorts 0.35Δ ~20 DTE on strikes shared by both weeklies, gate on the same-strike calendar (4-leg bid-ask ≤ 25% of debit, debit ≥ $1.50), structure by earnings position (none → diagonal `--widen`, between → calendar, before-short → MARGINAL), max risk printed; writes `data/watchlist/stock_dcal_<date>.csv`. **Run it during market hours on Friday** -- after-hours quotes are 90–200% wide and fail the gate.
