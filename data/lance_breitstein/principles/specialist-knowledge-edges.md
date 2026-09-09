# Five "hidden" edges — specialist knowledge first, charts second

> **Verdict:** A list of niches, one live case (STRC put sale), and one item that bears on a position the user held the day this was written up (SKHY's ADR premium).
> **Type:** edge-sourcing (not a setup)
> **Conviction:** 2/5 · **Testability:** index-rebalancing is an EOD event study; the rest need domain data · **Tested?** no
> **Source:** `e4m5smJxiVY` — 5 Hidden Trading Strategies That Most Traders Will Never Discover (2026-08-19)

---

## 1. The five, with what he actually says

1. **Exchange-traded debt / preferreds** [02:03–05:04]: the STRC case — a MSTR preferred that pays a variable monthly dividend the issuer adjusts to hold par at $100; it fell sharply in late June 2026 on volume; he **sold short-dated puts** on the view that a dividend cut was unlikely (cash reserve built for it, need for debt-market access) and high IV gave margin of safety. "A quick AI stress test also confirmed the probabilities." Valuation frame: yield, credit risk, probability of receiving par.
2. **Biotech clinical literacy** [05:04–07:39]: primary vs secondary endpoints, effect size vs statistical significance, AdCom votes (14–2), CRL cause (manufacturing vs efficacy), PDUFA dates. "Markets are less efficient when participants interpret specialized information in real time."
3. **M&A** [07:39–08:38]: strategic vs PE buyer, spread width, regulatory risk; "through intensive training and data tracking I was able to get a very clear sense of exactly where the stock would end up after some of these headlines." His most profitable niche at Trillium.
4. **Index rebalancing** [08:38–09:39]: forced passive flows; two Millennium units "allegedly made nearly $4 billion in a single month." Study the add/delete criteria and the flow dynamics around the effective date.
5. **ADR / dual-listing arbitrage** [09:45–10:37]: "**SK Hynix trading at a significant premium in the US after its IPO, compared to its main listing.**" Premiums persist where conversion is impractical; otherwise they are temporary distortions. Use the chart only to execute once the gap is understood.

Common thread [10:37–11:49]: none starts with the chart; the chart executes a trade the knowledge found. "Freedom to specialize" is the individual's advantage over a mandated firm.

## 2. ⚠ The sizing-lever question

Not applicable; no entry mechanics.

## 3. Claimed edge & evidence

STRC: one trade, outcome not stated, and it is the monthly "best opportunity" in his paid course (pitch at [05:00]). M&A: a career claim with no numbers. Millennium: a press report. Course-marketing discount applies to the whole video.

## 4. ⚠ Prop-infrastructure dependency

M&A headline trading at his speed is prop-grade (news feeds, execution). ADR arb needs multi-exchange access and settlement. Index rebalancing and preferred-stock valuation are the two a retail account can actually do.

## 5. Collisions with the repo

- ⚠ **SKHY, directly.** The user held SKHY overnight on 2026-09-09 after a +22% three-session run to an all-time high. If the US line carries a premium to the Korean listing, the overnight is a bet on the premium as well as on memory; the Korean session prints first. Worth a one-off check of the US/KRX ratio before the next hold.
- **Index rebalancing** is a clean EOD event study the repo has never run: S&P/Russell add/delete announcements → effective-date returns. Data: announcement lists are public; prices are on disk.
- **Biotech literacy** is exactly what the RVMD note (daraxonrasib FDA window) and the ILMN/TGTX/HALO group trades lacked. The repo trades biotech setups blind to the catalyst calendar.
- Method note: he uses "a quick AI stress test" as a sanity check on a probability — consistent with the `ai-trading-trap.md` position (AI as a check on a diagnosis, not a source of ideas).
