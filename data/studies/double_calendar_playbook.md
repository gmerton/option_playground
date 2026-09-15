# Double calendar playbook (2026-09-15)

Source: `calendar_path_study.md` (steps 1–5, real daily bid/ask 2018-11 → 2026-07, house cost model on four legs,
hold-to-expiry settlement). Supersedes the per-ticker calendar notes; `spy_double_calendar_playbook.md` and
`iwm_calendar_playbook.md` carry the ticker detail.

## The trade

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
| Mega-cap stocks, tight markets, no earnings | +7.6% | +7.2% | 56–58% | +7 / +8 | not in the screener yet |

Pooled ETF result 8 of 9 years positive (2019 the exception); monthly-mean t 5–6; ~60% win with a fat right tail.
**Do not size on the win rate** -- the mean comes from the winners.

## Entry rules

1. **Friday entry**, ATM-relative strikes by the short legs' delta (0.35 / 0.35). Not 0.25 (+8% / +6%) and not the
   asymmetric 0.35P / 0.10C (+8% / +2%): the strike set is the single biggest lever in the study.
2. **Bid-ask gate:** each leg ≤ 25% (screener), and the whole structure's entry bid-ask ≤ 25% of the debit. Below 10%
   is where the best numbers live. On ETFs this is automatic; on stocks it is the whole edge (>25% = −12 to −15%).
3. **Stocks:** debit ≥ ~$1.50 (cheap names with penny debits lose), **no earnings inside (entry, long expiry]**
   (−3pp), mega-caps only (NFLX, TSLA, NVDA, META, AAPL, GOOG/GOOGL, MSFT, AMD, AVGO scored +11–22%; AAL, BAC, CSCO,
   XOM, PLTR, INTC ≤ +1%).
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

Rolling the short legs at the short expiry (calendar as a campaign); the call-side-only calendar; intraday exits;
unequal deltas other than 0.35/0.10; bid/ask data end July 2026 -- re-cut when it extends. A screener entry for the
stock version (debit / bid-ask / earnings gates) is queued.
