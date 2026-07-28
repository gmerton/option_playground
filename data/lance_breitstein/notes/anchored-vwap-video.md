# The Anchored VWAP Edge Most Traders Never Discover

**Video:** `D2P-0xh6aEM` · **Type:** talks · **Published:** 2025-07-15 · **Watched:** 2026-07-26
**Length:** ~9:20, 51 transcript blocks (~10k chars)

⚠ Auto-captions render "VWAP" as "VWOP" throughout, and "Qullamaggie" as "Kalamagi". Quotes
below are cleaned.

## Raw notes

- Frames the whole video as evaluating **Brian Shannon's** (Alpha Trends) AVWAP work — he is
  reviewing someone else's tool, not claiming it.
- Standard VWAP = average cost basis of the day. Its value is that **institutional execution
  algos are benchmarked to it**, so it functions as a real reference point rather than a drawn
  line. Below VWAP = average buyer underwater.
- Limitation: standard VWAP **resets daily**, so continuity across a catalyst is lost. AVWAP
  fixes the anchor at a chosen event and runs forward.
- **Anchor choices he actually uses:** high-volume catalyst events — earnings, big headlines,
  capitulation days, key breakout days, IPO day, episodic pivots (credits Qullamaggie by name).
  He explicitly **rejects time-based anchors** (quarter/year end) for his timeframes, allowing
  they may suit longer-horizon traders modelling pension/hedge-fund psychology.
- Mechanism claim: "markets are about positioning… if price is above anchored VWAP, the average
  buyer since that key moment is in profit. If below, they're underwater. And people who are
  underwater behave differently. They panic, they sell, they chase."

### ⚠ The central quote — he does NOT use it as a level

> "I personally don't use anchored VWAP or VWAP as a literal level. What I mean by that is I am
> not buying or selling simply because we get above or below that line. Instead, I am more so
> viewing it as an **indicator of trend**." (05:44)

### The one concrete rule he states

> "I don't want to short a stock above VWAP unless it has capitulated, [and] I don't want to long
> a stock below VWAP unless it has capitulated." (06:06) — applied to AVWAP the same way.

This is a **directional veto**, not an entry.

### Worked examples

- **CRCL (Circle), post-IPO:** held above AVWAP anchored to the IPO through a run from ~$110 to
  ~$300. His rule kept him from shorting the whole way. A capitulation day on **2025-06-23** then
  "allowed me to start attacking the stock on the short side."
- **UNH, 2025-05-15:** criminal-investigation headline (alleged Medicare fraud), some of the
  largest volume ever, capitulated lower then closed strong. Held above AVWAP anchored to that
  day since. He offers this as a **swing-long structure**: "that is one way to structure a swing
  long where, as of the time of this video, you still haven't been stopped out."

## Claims to verify

- [ ] **AVWAP anchored to a high-volume catalyst day, held as a trailing exit, beats a
      conventional trailing stop.** ⭐ **EOD-testable right now** and directly comparable to the
      exits already measured in `risk_architecture/` (`close<50EMA` was the best exit tested).
      This is the highest-value item in the video.
- [ ] The directional veto ("don't short above AVWAP unless capitulated") — testable as a filter
      on a short book, though "capitulated" is a discretionary joint.
- [ ] Implicit: that a catalyst-anchored average is more informative than a fixed-lookback
      moving average. That is the falsifiable core, and the natural null is "AVWAP is a
      variable-lookback trend line dressed up."

## Reactions / conflicts

- **⚠ This is a negative result for the reason I ingested it.** The KB priority queue put this
  first on the theory that AVWAP would be his precise *entry-location* tool — the mechanism
  behind the 6× sizing lever in `HOW_THEY_DO_IT.md`. He explicitly disclaims that use. AVWAP is
  **context/trend**, not entry location, and not a stop level. The entry-precision question is
  still open and this video does not touch it.
- **Convergence with Luk is weaker than hoped but not zero.** Luk cites AVWAP for *stop
  placement* (a level); Breitstein refuses to use it as a level. They agree the tool matters and
  disagree on how — worth noting rather than merging.
- **The obvious skeptical read**, per the house checklist: AVWAP is a volume-weighted moving
  average with a hand-picked start point, so "holding above AVWAP" ≈ "still trending since the
  catalyst." The anchor choice is discretionary and unfalsifiable in the general case — but is
  fully mechanical if you define the anchor as, e.g., the highest-volume day of the last N.
- **Low-hype for the genre, and worth crediting.** He is reviewing another author's tool, states
  the limits, says there is "no one right way," and closes by telling viewers to test it
  themselves or backtest simple rules. That is the opposite of the Carter/Theta Profits pattern.
- **Marketing present but light:** one course plug ("for those that aren't a part of my course"),
  repeated subscribe asks, and an opening credential claim — "8-figure P&L per year, over $100
  million in verified profits" — asserted, with no evidence in the video.
