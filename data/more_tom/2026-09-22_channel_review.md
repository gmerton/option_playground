# More Tom (Tom Sosnoff) — full channel review, 26 videos (2026-09-22)

**Score: 2.5 / 5** (strategy half 2.5, process half 2.5 — scored independently, agreed).
Ledgers: [claims_strategy.md](claims_strategy.md) · [claims_process.md](claims_process.md).
All 26 transcripts captured, zero failures.

## Provenance — genuine, with a real qualification

**It is Tom Sosnoff, on an authorized channel.** Verified independently: the parent channel
**`@Lossdog` has 33,000 subscribers** and is active; "More Tom" is its spinoff, so 496 subscribers three
weeks in is unremarkable rather than suspicious. Audio is unscripted conversation with an interviewer
present. First-person specifics nobody else has: launching thinkorswim with no charting package and only
learning afterward that customers wanted charts; leasing Java charts from Tim Knight in 1999; buying the
tastytrade domain on the company card and negotiating to keep it on exit.

⚠ **But the clips are cut from other people's podcasts, not from original programming.** Eight of the 26
descriptions credit a single 69-minute guest appearance (*In The Money*, Zerodha, 2025-11-16), sliced up
ten months later. One clip still contains an intact ~90-second sponsor read **for a competitor**, left in
the published file. The announcement video's claim that the content comes "from live streams at the
opening bell" is false for every clip checked. Titles are templated and occasionally fabricated — the one
called *"How Much You Should REALLY Risk Per Trade"* contains no sizing content at all.

**Effect on the standard applied:** he is accountable for the words, so the claims were scored on their
merits rather than discounted. Two constraints stand: **context belongs to the editor — never quote a
clip without opening the source at its timestamp** — and in 26 clips there is **not one number**: no
position, no P&L, no sample, no fill, despite repeated appeals to a think tank, PhDs and a database back
to 2005. The person has a track record; the claims carry no evidence.

## ⭐ The two findings worth keeping

### 1. "Charts don't forecast" and "there is no edge" are INDEPENDENT claims, and our data separates them

His strongest video argues both at once. Our own book keeps confirming the **first** against its own
interest: the house breakout averages **+0.014R**; within-date ranking of candidates is **NULL**
(pre-registered primary t −0.11, 71 of 72 cells fail); nine chart features cannot call the bimodal split
against a **1.647R** available spread; `sma_stacked` **inverts**; three leadership filters fail to sort;
the Trend Template ablation left two criteria **retracted as redundant** and the rest underpowered.

The **second** is falsified by his own trade type. Our one certified bucket is index premium selling
(SPY bull put **t 6.07**, cell +6.47% net/trade, month-clustered t 5.62), and the 10-day VRP is **+1.75
vol points, t 8.93, 17 of 17 years**. He is denying the existence of the edge his own P&L is made of —
his definition of "edge" is a market-maker's and never contemplates risk-premium harvesting.

⟹ **Separate them.** "Our chart features do not forecast" is well supported. "There is no edge" is not.

### 2. We have never tested futures options — the arena he actually trades

His book is crude and gold futures strangles. The liquidity objection that sinks our single-name premium
selling (costs = **136% of gross**) does not apply there. **His central claim is untested in the arena he
trades it in.** Do not fund futures data on his say-so — but stop treating the single-name null as a
refutation of him. This is a limit on our evidence, not a verdict on his.

## Where he agrees with results we paid for

| claim | our evidence |
|---|---|
| Spread scanners are useless without an option-volume gate first | our hardest-won result: "liquidity is the gate"; credit/width discriminates only *within* a liquid universe |
| Don't roll a losing put out and wider | roll test: stop −9.51pp on the breach cohort, **69.8% did better held**; re-entry NULL t 1.55 |
| Outlier risk is managed by **position size only** | every non-size tail management INVERTED: straddle −50% stop is a cost (+6.73% unstopped vs +2.89%), BE+1R −0.08R, "extended → tighten" −0.19R t −2.8, 10-EMA trail −0.47R t −4.8 |
| Don't benchmark yourself against outlier traders | the journal is structurally underpowered — n ≈ 1,854 needed for t = 3 vs 272 campaigns |
| Open interest is a tradability gate, never a signal | exactly how we use it |
| Diversify by *strategy*, not by name | our PAIR: corr −0.25, blend t 2.5 where the legs are 1.8 / 1.2 |
| Don't buy extended above the prior high | breakout entry sits **+0.52 ADR** above it vs **−2.09** for the control = 2.6 ADR paid |

## Contradicted

* **"No statistical edge ever, for retail"** — see above.
* **"Think in probabilities" / probability = edge** — the SMB error verbatim. Across credit/width
  quintiles the win rate **falls** 79.6 → 75.7 while net ROC **rises** −2.96% → +4.07% (t 3.74). Higher
  probability, worse trade.
* **IV structurally above RV, "realized wins only ~15%"** — right on sign, wrong on tenor and frequency.
  Significant only at **10d** (+1.75vp t 8.93); **30d +0.78 (t 2.08) and 90d +0.84 (t 1.30) clear
  nothing** — and he trades 30–45 DTE. Realized wins **25–29%** of the time, roughly double his figure.
* **"The only signals you need: IV level + skew"** — both NULL. Skew adds nothing beyond VIX in a joint
  regression (skew t −1.22 vs vix_pct **t +6.54**); it is a noisier VIX, and GEX is the idea done properly.
* **"I haven't bought premium in 26 years"** — our two surviving option strategies include a **long 7-DTE
  straddle** whose gate is the inverse of his rule (own-IV percentile ≤ 30).
* **"There's no such thing as a trend; I fade trends"** — backwards by arena. Single-name fading is what
  our data kills hardest (0-for-5 on reversion); index reversion is our one certified bucket.
* **Scalping** — he calls it a hobby, and our data agrees with the category: scalp **−0.13R vs trail
  +0.89R**; the owner's own log, 278 same-day cycles, **−$8.3k, 19% win**.

⚠ **Most dangerous number:** a portfolio theta budget of 0.1–0.2% of net liq. Untestable as stated, but
after the 2026-09-22 correction exactly ONE bucket certifies. A theta budget presumes somewhere to spend it.

⚠ **Cost flag:** across 26 clips there is not one fill, bid/ask, commission or net-of-cost return. He makes
the cost argument correctly exactly once, which makes its absence elsewhere worse. Everything marked
AGREES agrees about *direction*, never *return* — cf. UVIX +11.0%/93% win at mid → **−8.8%/46% at fills**.

## Why 2.5 and not higher or lower

Above SMB's 2/5 because several agreements are with results we paid real compute for and he reached them
by experience. Capped below 3.0 because **nothing is quantified**, two claims repeat errors we have
already settled, the internal contradictions are never reconciled (no edge exists, yet he scalps thirty
times a morning off a subjective read), and the clips are other people's podcast audio with the context
removed. Had provenance gone the other way this would be 1.5/5.
