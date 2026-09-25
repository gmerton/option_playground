# Short Put (tastytrade house version): Dr. Jim Schultz

Source: `2026-09-20_SNz3dSutLzc` ("After 10 Years at Tastylive, This Is Still My #1 Options Strategy", 60 min).
Reviewed 2026-09-24. Schultz spent 2015–2026 on the tastytrade network, left about a month before this recording,
and now runs his own service ("Options on Caps"). The service is a sales motive, mild here.

## Verdict box

**Conviction 2 / 5 · Risk 6/10 on single names (4/10 on indexes) · Tested? PARTIAL: every component is in our
ledger.** This is an honest, competent statement of tastytrade doctrine applied to one leg. The mechanics are clear,
with no "risk-free" language, and he volunteers the gotchas ("for every gimme there's a gotcha"). But the
**selection rule (IV rank > 30) is the part our data rejects**. The **management rules (21-DTE roll, 2–3× stop) do not
earn their keep**. The single-name version is **stock at the same delta minus costs**. The return claim
(13–15%/yr) has no record behind it.

## Mechanics (as stated)

| item | rule | @ |
|---|---|---|
| universe | Tom's / tasty default watchlist, or build your own from the S&P 100/500: **high volume, tight bid-ask** | 1:4x–10:xx (transcript lines 60–70) |
| selection | sort by **IV rank**; **> 30 = sell**, teens or single digits = wait; "stocks are interchangeable" after that | lines 70–78 |
| price | matters only for margin (Apple ≈ $5–6k per naked put; GDX ≈ $1.5k) | lines 78–82 |
| tenor | **30–60 DTE, monthlies**; weeklies only around events; 0–7 DTE "not compensated for the risk" | lines 82–92 |
| strike | **30–35Δ baseline**, 25Δ before events, up to 45Δ for more portfolio delta; **never ~9Δ** ("vomma", people oversize them); premium efficiency (credit ÷ buying power) ≥ 10%, prefer 15–20% | lines 92–110 |
| profit | **50% of max**; exception: 30% within the first few days | lines 110–118 |
| time exit | **14–21 DTE**: take it off if "economically significant" (≥ $0.25–0.30/share), otherwise **roll** to the next cycle; red trades roll too | lines 118–130, 150–160 |
| loss | his own: **no stop**, case by case. For others: **2–3× credit** | lines 130–140 |
| assignment | "just take the stock"; hold the shares naked if the put went deep ITM, and sell calls only near the basis | lines 160–175 |
| size | **1–5% of account in buying power per position**; buying power ≈ a 2-SD move = "practical worst case" | lines 175–195, 260–270 |
| claimed return | market-like returns with less risk, or **13–15%/yr** "with enough skill" | lines 300–310 |

## Objective assessment against our ledger

| claim | verdict | evidence |
|---|---|---|
| liquid names only | **AGREES** ⭐ | Liquidity is the gate. 10-DTE single-name selling: costs = 136% of gross (`vrp_shortdte_names`) |
| **IV rank > 30 selects better puts** | **CONTRADICTED** | Single-name bull puts: IV rank sort **zivr −1.89pp (t −1.25)**, and the **lowest** IVR quintile earned most (`ivrank_vs_cw_2026-09-22`). Low own-IV is a signal to *buy* the 7-DTE straddle. Ranking CSPs by yield (≈ IV level) = **beta, excess t 0.65** (`csp_yield_rank_2026-09-24`) |
| "stocks are interchangeable" after the two checks | **AGREES, in a way he wouldn't like** | Names don't matter because the single-name put is **stock at its delta minus costs**. BCI CSP study, 326 names 2018–26: excess vs delta-matched stock ≈ 0 or negative; the equal-weight weekly CSP book compounds **+1.2%/yr vs SPY +10.5%** |
| 30–60 DTE; short tenor "not compensated" | **PARTIAL / backwards on the premium** | The variance premium lives at the **short** end: 10d +1.75vp, t 8.93, vs 30d +0.78vp, t 2.08 (VRP panel). On single names the 10-DTE premium is eaten by costs, so his tenor is the cost-efficient choice. That's a friction point, not a premium point |
| 30–35Δ, never ~9Δ | **AGREES in direction** | Near-the-money beats far-OTM on every structure we priced: the 1-day SPY fly 2× vs 16/5Δ; "90%-win spreads risk $9 to make $1" (OptionsPlay filters). But a 30Δ CSP is still ≈ stock at 0.30Δ minus costs |
| 50% take | **AGREES on spreads** | ETF bull puts: 50% take, no stop +5.70%/trade (weekly t 4.87) vs held +0.6% (`etf_put_spread_exit_rule_2026-09-16`). Not tested on naked single-name puts |
| roll / close at 14–21 DTE | **CONTRADICTED on return, risk reducer only** | 45-DTE 20Δ strangles, fixed run, honest subset: 21-DTE close − hold **−$0.51/share, t −2.04**; it halves sd (FIX-1, TEST_INDEX §1). Rolling red trades out = "roll the loser", untested with a negative prior (every call-side rescue negative; Sosnoff's own rule: never roll a loser out and wider) |
| 2–3× credit stop | **CONTRADICTED** (on spreads) | 50% take + 2× stop −4.3%/trade (t −5.4) vs take-only +5.70% (`etf_put_spread_study` §2). Stops on short premium are a cost |
| "just take the stock" | **framing, not a defence** | Assignment is the loss realised as stock bought above market. The CSP book's drawdowns are the stock's drawdowns, at a lower mean |
| buying power ≈ worst case; −10% SPX days happen "2–4 times ever" | **MISLEADING** | Single-day −10% is rare, but the risk is **multi-day**: Feb–Mar 2020 (−34% in 23 sessions), 2008, 2022. A 35Δ put book at 5% BP per name × 20 names is fully correlated in exactly those windows. BCI crash windows show the CSP pool losing with the stock |
| 13–15%/yr possible with short puts only | **UNSUPPORTED** | No record, no sample. Our only certified index put sale is **conditional** (bearish-high-IV, t 6.07); unconditional QQQ bullish-low-IV is −4.8%. The single-name book above is +1.2%/yr |
| skew makes OTM puts rich, "a king's ransom" | **UNTESTED as an edge / NULL as a signal** | Skew level adds nothing beyond VIX (SPY 25Δ skew t 1.44). Whether the skew premium survives costs at 30Δ vs ATM isn't in the ledger |

**Red flags (checklist):** no separable track record ✔ ("I take more losses than your average viewer", no numbers);
return claim with no evidence ✔; costs barely mentioned (only in the "economically significant" cutoff). Not
present: "risk-free", winners-only examples. He shows the hurt-locker case and the vomma trap, to his credit.

## What's genuinely sound

The index version: selling 30–45 DTE puts on SPX/SPY, small, is the one short-premium family with a certified cell
here, **but only after a selloff with high VIX**. His universe advice (liquid only), his warning against 9Δ
income-selling, and his sizing (1–5% of BP) are all right. Strip the IVR selector and the single names, and add the
regime condition, and what's left is our certified bucket.

## Backtestability

Fully mechanical except the case-by-case loss handling. Every piece is already answered in the ledger (see the table).
**No new test proposed** under the only-new-ideas rule. The one untested axis is **naked 30–35Δ index puts,
unconditional, 45 DTE, 50% take, vs delta-matched SPY**. It's near-identical to the certified cell's unconditional
arms (QQQ/SPY bull puts by regime), which fail outside bearish-high-IV. So its prior is low.
