# The four IPO strategies

> **Verdict:** ⭐ Lands squarely on the repo's **known structural blind spot** — every backtest here
> excludes new listings via SMA200 and a 400-bar minimum. Two of the four strategies plus the
> lockup mechanic are **EOD-testable**, which makes this the cheapest route into a universe the
> harness has never seen.
> **Type:** setup (event-driven) · **Conviction:** 2.5/5 · **Testability:** 2 of 4 EOD ⭐ · **Tested?** no
> **Source:** `dGjqaXTeiTU` (2026-04-25) · companion `i8NgzZgc5L4` (SpaceX/large IPOs)

---

## 1. Why the edge is claimed to exist — structural, and checkable

- **Underpricing.** Banks deliberately price below expected clearing price so the deal succeeds
  and institutional clients stay happy. He cites average US first-day returns of **~15–20%**
  historically, **30–40%** in the 2020–21 euphoria. ⚠ This is a real, well-documented finance
  literature effect — it is one of the few claims in the whole KB with independent academic
  support — but note **the first-day pop accrues to allocation holders, not to open-market buyers.**
  He is trading the *post-open* behaviour, which is a different thing, and the video slides
  between the two.
- **Constrained float.** Only a fraction of shares trade on day one. "Tight supply creates an
  environment where price can move extremely fast."
- **No overhead resistance.** "The stock has never traded before, so there are no trapped longs
  waiting to sell." This is the cleanest structural argument in the video and it is genuinely
  specific to new listings.
- **Lockup expiry (90–180 days).** Insider shares unlock → supply shock → downward pressure.
  "Something traders like myself watch very closely."

## 2. The four strategies

1. **Opening drive** — first 10–30 min, strong relative volume, aggressive bids, price holding
   above the opening range, shallow pullbacks. A scalp at its core. *(intraday)*
2. **Counter drive** — the first real pullback once the opening drive exhausts. Signals: failed
   pushes to new highs, heavy selling into strength, break of intraday support or **prior bar
   lows**. Explicitly "requires experience — you're stepping against dominant momentum." *(intraday)*
3. **Later-day breakout** — after hours of consolidation, a tight base breaking above the range on
   strong volume. *(intraday)*
4. **⭐ Overnight momentum** — if the IPO **closes near the highs of the day on heavy volume**
   (especially after strategy 3), hold overnight; excitement, social spread and fresh demand carry
   into the next open. *(EOD-TESTABLE)*

**The three alignment conditions:** hot sector, tight float, bullish market backdrop. "Market
environment matters more than almost anything else."

Worked examples: **CRCL** (priced $31, opened $69 — strategies 1 and 2 only, no later-day
breakout) and **FIGMA** (priced $33, opened $85 — strategies 1, 3 and 4; strategy 2 was weak,
"maybe you take a small loss, which is fine"). Notably this is the **only place in the batch he
mentions a losing leg**, even in passing.

## 3. ⭐ Two tests the repo can run on data already on disk

Both address the blind spot named in `HOW_THEY_DO_IT.md` §4.

**(a) Overnight momentum.** Fully mechanical: for a recently-listed name, `close within X% of the
day's high` **and** `volume ≥ k × its short trailing average` → measure the **close-to-next-open**
return. This is the same overnight/intraday decomposition already built for the gap study, which
found *the entire equity risk premium accrues overnight* (SPY +1204% overnight vs +29% intraday,
1993–2026). If overnight drift is where index returns live, a conditional overnight edge in hot
new listings is a plausible place to look — and it costs nothing to check.

**(b) Lockup-expiry supply shock.** Event study at **T+90 / T+180 trading days** from first listing
vs a matched control. Fully mechanical, needs only a listing date.

⚠ **Listing dates are approximable but imperfect.** The broad panel (`broad_history/`, 2,684 names,
2006–2026) gives each ticker's first available bar, which proxies the listing date for anything
that came public *inside* the window. Two caveats: yfinance sometimes starts a series late for
unrelated reasons, and the panel is **survivorship-filtered to names alive today** — which for
IPOs is a severe bias, since failed listings are exactly what is missing. Any positive result here
should be treated as an upper bound until a delisting-inclusive panel exists.

## 4. Red flags

- CRCL and FIGMA are both large 2025 winners in an explicitly "extremely hot market" — he says so
  himself, which is honest, but it also means the sample shown is the most favourable regime
  possible for the strategy.
- Course plug; "$100M verified profits" opener.
- ⚠ **Regime-dependence is stated but not quantified.** "IPOs thrive in hyper-bullish markets…
  when markets are defensive and fearful, the same IPO might struggle to hold its opening price."
  Given `REGIME.md` found the market gate to be the single most valuable variable in the entire
  study, an IPO strategy is likely to be *more* regime-dependent than anything tested so far, not
  less.
- Strategies 1–3 need tape reading and minute bars; he says outright that "reading the tape is
  critical" for IPO opens. Not retail-testable here.

## 5. Overlap with the rest of the repo

- **The blind spot itself:** `arch_lib.entry_tiers` requires SMA200 and `run()` skips names with
  <400 bars, so **no IPO can ever appear in any result produced so far.** Qullamaggie's biggest
  winners are frequently young stocks. This is the concrete fix.
- Fresh IPOs are one of his three [in-play](in-play-stocks.md) categories.
- The overnight test reuses machinery already written for
  [`opening-gap-fade.md`](../../carter_mastering_the_trade/setups/opening-gap-fade.md).
