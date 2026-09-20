# Trend definition, the counter-trend entry, and the VWAP veto

> **Verdict:** Six ways to draw a trend, of which five reduce to "price crossed a line" — the
> family this repo's ledger has now failed twice. The value is in the two rules he states **with
> their invalidation attached**: never counter-trend *until* the break of prior bar highs, and never
> long below VWAP *unless it capitulates*. Both are specced below; the long side of the prior-bar
> break has never been tested.
> **Type:** entry-location (+ trend definition, veto) · **Conviction:** 2.5/5
> **Testability:** EOD for the counter-trend entry ⭐ · intraday-needed for the VWAP veto · **Tested?** no
> **Source:** `ZOHG-OnQuos`@[02:15–10:40] — "99% of Traders Don't Know How to Trade with the Trend" (2025-12-20),
> with the setup precondition quantified in `vGqaqTUxMG4`@[03:28] — "Can YOU Spot the 4 KEY Days!?" (2025-05-31)

---

## 1. Mechanics

**His six trend definitions** [02:15–05:56]: slope / higher-highs-and-higher-lows stairstep;
shallow pullbacks with continuous legs; holding VWAP; holding a moving average; holding a trendline;
and ⭐ the **reference price** — "the unaffected price before a catalyst" (AMD's pre-news $83.50:
above it the news is being read positively, below it "something is off"). Only the last is new to
this KB.

**The counter-trend entry** [06:47–07:30] — the tradeable rule:

- **Instrument / universe:** hyper-in-play names; his example is GME on 28 Jan 2021.
- **Session / timeframe:** unspecified, per the README's standing timeframe problem. The GME
  illustration is intraday; the FRC and BABA illustrations are daily.
- **Setup condition:** an accelerating down leg, far extended, into capitulation. He supplies no
  number here; `vGqaqTUxMG4`@[03:28] supplies it for the index — **~20% from the moving average,
  "almost unheard of for something like the NASDAQ"**, i.e. extension measured against the
  instrument's own normal range. That is the ADR-unit restatement the README asks for.
- **Trigger:** **the break of prior bar highs.** "I would be buying in this bar if possible."
- **Entry:** at/through the prior bar's high. ⚠ The repo's entry study says take this on the
  **close**, not intraday — the close entry beat every intraday variant by 0.9–2.3pp paired.
- **Stop:** he does not state one. The only defensible reference is the **flush low** (the signal
  bar's low), which is also what `right-side-of-the-v.md` says his framework implies: the right
  side of the V is worth more than the left precisely *because* a real stop exists there.
- **Implied position size** at a 0.3% risk budget: undetermined — the stop distance is whatever the
  signal bar's range happens to be, which in a capitulation bar is wide. ⚠ This is the honest
  answer and it cuts against the sizing-lever thesis: a capitulation-bar stop is the *widest* stop
  in his repertoire, so this setup buys the **smallest** position, not the largest.
- **Exit:** prior bar lows as a trailing stop [04:58] — "prior bars is a very common trailing stop
  that I use." Harness arm: `trail_bar`.
- **Vetoes:** don't average down into the fall ("if you buy $210 thinking this is overextended,
  guess what? We just went another 100 points"); don't trade rangebound names at all [02:36]; and
  the VWAP veto below.

**The VWAP veto** [08:00–08:32], credited jointly to "Kenny at SMB Capital": *"we never want to be
long a stock if it's steadily holding below VWAP unless it capitulates. and vice versa. I never want
to be short a stock above VWAP unless it capitulates."* He immediately names the discretionary
joint: "you have to define everything. What does capitulation mean to you."

## 2. ⚠ The sizing-lever question

- **Stop distance as % of entry:** the signal bar's range. In a capitulation bar that is *multiples*
  of normal ADR — call it 3–10% on a single name, not 1.5%.
- **Position that buys at 0.3% risk:** 3–10% of account, i.e. **at or below** the 3.3% the 9.2%-ATR
  sims already used. No lever here.
- **Does he state or imply a stop-out rate?** No. He gives a directional claim instead — "when I
  started to wait for the counter trend, I stopped drawing down significantly" [07:30] — which is
  about *avoided losses*, not about stop-out frequency.
- **What would settle it:** the daily test below settles whether the trigger has any edge at all.
  The tightness question needs 1-min bars, and `data/cache/intraday_1min` already exists for the
  Stage A universe — the VWAP veto is runnable there via `run_intraday`.

⭐ **Read in the context of the open question, this principle is evidence *against* the 6× lever,
not for it.** His widest-stop setup is the one he credits with transforming his biggest losses.

## 3. Claimed edge & evidence

None quantified. The evidence offered is (a) a retrospective review of his own trade log — "a deep
forensic dissection of my entire body of work" [00:53] — concluding that his best trades were with
the trend and "worked immediately", asserted as "not hindsight… a repeatable heuristic" [01:20]; and
(b) eight charts, all winners, all chosen after the fact (SPY, NVDA, FSLR, FRC, Bank of Hawaii,
TSLA 2021, GME, BABA). ⚠ By the repo's own house rule a trade log is evidence about execution and
conformance, never about setup selection — and that rule applies to his log as much as to Gabe's.
Course pitch at [11:19]; subscribe plug at [02:06].

## 4. ⚠ Prop-infrastructure dependency

- **Depends on:** nothing structural for the daily version. The intraday version needs real-time
  VWAP, an in-play list, and the ability to buy through a prior bar high in a fast tape.
- **Retail-viable as stated?** The counter-trend entry: **yes** on daily bars. The VWAP veto:
  **partly** — the tool is free, the "steadily holding" and "unless it capitulates" judgements are
  not mechanical as stated.

## 5. Decay risk

Low-to-moderate. These are structural claims about trend persistence, not attention-flow niches.
⚠ But the illustrations are dated where it matters: GME Jan 2021 and BABA/Xi are extreme-dispersion
events, and the FRC example is a failed bank in March 2023. Nothing here was demonstrated in an
ordinary tape.

## 6. Objective assessment

- Five of six trend definitions are line crossings. **Stage A tested that family intraday — 11,227
  fires across gap reclaim / ORB-above-9-EMA / level break — and every arm returned −0.10 to −0.13R,
  losing to a random entry in the same name-day.** The README's asymmetry rule applies (a null at
  one interval does not refute a fractal claim), but the prior is now poor.
- "That's not hindsight" [01:20] is asserted about a conclusion drawn with outcomes in hand.
- No stop is ever stated for the entry he calls career-changing.
- "Steadily holding below VWAP" and "unless it capitulates" are the two joints where all the
  discretion lives, and he flags both himself — to his credit.

## 7. What's genuinely sound

- **The pairing.** Both rules come with their invalidation attached, which is what this KB values
  most: don't counter-trend *until* the prior-bar-high break; don't take the counter-side of VWAP
  *unless* capitulation. Most creator material gives the entry and skips the condition that voids it.
- **"Don't average down into the fall"** is the same claim as `right-side-of-the-v.md` and the same
  claim as the crash-leader veto, reached from three directions.
- **The price-acceptance framing** [10:07] — consolidation as agreement, its absence as a sign the
  trend is ending — is now the third independent statement of that idea in this corpus.
- **The reference price** [05:35] is genuinely new here and is the cleanest formulation of "was the
  news taken well?" I have seen from any source in the repo.

## 8. Overlap / conflict with the rest of the repo

| repo finding | this video |
|---|---|
| Veto below the 200 SMA / 6-month return < −10% (rotation study) | the daily-bar version of "don't fight the trend" — **agrees**, and is quantified where he is not |
| Long-call winning cell = **0.3–1 ADR over a rising 21 EMA**; the August leak = entries **1–2 ADR** above it | he never gives a distance. [10:01] ("larger, accelerating legs ⇒ trend ending") is the qualitative shadow of exactly this measurement |
| EMA-pullback entries (Luk/Ariel) +1.2–2.4%/trade, **below** the plain breakout (+2.6%); pullback entries need a stop-only exit, not an EMA trail | his counter-trend entry is a deeper, capitulation-grade pullback with a **prior-bar trail** — the exit our pullback study specifically found wrong for pullback entries. Test both arms |
| Bouncy-ball short (prior-bar-low break after lower highs): **−0.34R daily vs control +0.34/+0.48, t −4.3; −0.41R intraday, t −10.9** | this is the **mirror image, long side** — untested. If it also fails, the prior-bar-break family is 3 for 3 dead |
| Precision-tier breakout best arm = **ema20 trail, +0.79R** | he prescribes the **prior-bar (`trail_bar`) trail**. Free head-to-head, already instrumented |
| Stage A: intraday triggers have no edge; random entry in the same name-day beats them | five of his six trend definitions are that family |
| `right-side-of-the-v.md`, `capitulation-and-trade-writeups.md`, `setup-grading-chart-nuance.md` | all consistent with this video; the counter-trend rule here is the compact statement of the first |

⚠ **Do not merge with Luk.** Luk's EMA-pullback entry is a shallow retracement inside an uptrend;
this is a capitulation-flush reversal. Same trigger word ("pullback"), opposite regime.

---

## Harness spec

`src/lib/studies/pattern_test.py`, `run_daily`. Long side. Two arms, run as A/B — the gate is the
whole question.

```python
# A -- capitulation counter-trend long (his GME rule + the vGqaqTUxMG4 [03:28] precondition)
def breitstein_counter_trend(P, k_adr=3.0):
    ext  = (P.ema20 - P.close) / (P.close * P.adr / 100.0)     # ADR units BELOW the 20 EMA
    down = P.close < P.close.shift(5)                          # still in the down leg
    setup = (ext.shift(1) >= k_adr) & down.shift(1)            # yesterday was the flush
    hit  = setup & (P.close > P.high.shift(1)) & P.elig        # trigger: CLOSE above prior bar high
    return daily_signals(hit, stop=P.low, side="long")         # stop = the signal bar's low

# B -- control gate: same trigger, NO extension precondition (his rule without the setup)
def prior_bar_high_break(P):
    hit = (P.close > P.high.shift(1)) & (P.close < P.close.shift(5)) & P.elig
    return daily_signals(hit, stop=P.low, side="long")
```

- **Boolean condition (A):** `(ema20 − close)/(close·ADR/100) ≥ 3` and `close < close[−5]`, both as
  of the prior session, **and** today's `close > high[−1]`, on `elig` names.
- **Stop reference:** the **low of the signal bar** (`P.low` at the signal index) — the flush low,
  the only invalidation his framework admits. Harness enters at the next open and computes
  R = move ÷ (entry − stop).
- **Side:** long.
- **Sweeps:** `k_adr ∈ {2, 3, 5}`; and a volume arm — capitulation per
  `capitulation-and-trade-writeups.md` needs `dolvol ≥ 2× its 20-day mean` on the flush bar, which
  requires adding `dolvol` to `DailyPanel` (one pivot line in `load_panel`; the column is already in
  `liquid_panel_2019.parquet` and is what `liquidity_mask` reads).
- **Exit arms:** the harness's five. The specific comparison he provokes is **`trail_bar` (his
  stated trail) vs `ema20` (our best arm at +0.79R)**.
- **Bar to pass:** beats the same-name random control, positive in both halves, |t| ≥ 3.
- **Prior:** poor. The mirror-image short failed at −0.34R with the control at +0.34/+0.48.
- **Expected diagnostic value regardless of outcome:** A-vs-B isolates whether the *extension
  precondition* carries the rule or whether the prior-bar break alone does. B failing while A passes
  would be the first evidence in this KB that his setup selection — not his trigger — is the edge,
  which is the claim the whole KB exists to test.

**Intraday arm (VWAP veto), `run_intraday` on `data/cache/intraday_1min`:** signal = long entries in
names trading **above** session VWAP for ≥ 15 consecutive minutes; control cohort = the same
detector firing **below** VWAP without a preceding capitulation bar (bar range ≥ 2× the trailing
30-minute mean range). Stop = session low at entry. Side: long. This tests the veto as a *filter on
an existing detector*, which is what it is — not as a standalone entry.
