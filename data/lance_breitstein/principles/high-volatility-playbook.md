# The high-volatility playbook (size, horizon, overnight, vehicle)

> **Verdict:** One piece of arithmetic that is correct and already matches this repo's harness
> (size ∝ 1/stop, dollar risk need not fall), wrapped around a regime *switch* the repo has never
> tested — and which survives our standing regime nulls on a technicality that matters: he
> conditions on **contemporaneous volatility**, not on trailing returns, and he switches **horizon
> and size**, not direction. ⚠ Its central instruction — shorten the horizon, cut overnight exposure
> — is the losing bucket in both of our books.
> **Type:** regime + sizing · **Conviction:** 2.5/5
> **Testability:** EOD ⭐ (the gate) · process/unfalsifiable (the rest) · **Tested?** no
> **Source:** `mjfONTBf6M0` — "Best Practices to Navigate High-Volatility Markets" (2025-04-10),
> recorded the day after the 9 Apr 2025 tariff-pause rally

---

## 1. Mechanics

- **Instrument / universe:** index products first (NQ, ES, SPY, SPXL), plus pre-built **baskets**
  organised by headline exposure — "do we know what countries RH are most exposed to? … Apple? …
  Nike? … oil?" [13:20].
- **Session / timeframe:** intraday, extended to pre-market ("we've had a couple China escalations
  pre-market, maybe 6:00 and 7 a.m." [12:34]).
- **Regime condition:** "any high VIX period" [01:33]. ⚠ He **refuses to set a threshold**: "I don't
  think it's so important that I define a high volatility period super specifically… most people can
  judge it pretty accurately qualitatively." Use the VIX index, not VXX (decay) [01:46].
- **What changes when the condition fires** — the playbook itself, in his order:
  1. **Shorten the horizon.** "I'm not trying to have lots of equity on for large periods of time
     either way, short or long… because you're opened up to headline risk" [02:10].
  2. **Go leg for leg**, expect violent reversals [02:26, 04:27].
  3. ⭐ **Size down as the stop widens.** "If your risk is expanding like this you need to decrease
     your size… Well, yes, in dollar value of risk… your share size might be going down, but that
     doesn't mean your dollar risk is going down" [04:39–05:57].
  4. **Don't overstay without capitulation**; take partials, "you can always get back in" because
     commissions are cheap and the spread is tight [07:18–08:18].
  5. **Reduce overnight exposure — do not eliminate it.** "That doesn't mean take no overnight
     risk… That means just reduce it and be more aware of the fat tails" [10:22].
  6. **Daily loss limit, and spend it late.** "What you don't want to do is hit that loss limit too
     early in the morning and give away P&L before the actual move happens… save your bullets…
     don't fight the front side… wait for the turn" [10:44–11:15].
  7. **Be more selective** — "wait for the pocket aces" [12:09].
  8. **Be present** — "your ass in the seat", cover pre-market [12:13].
  9. **Choose the vehicle for capital efficiency** — SPY vs SPXL (3×) vs ES futures, "all of those
     really really really make massive differences in your P&L on a percentage basis", motivated by
     the retail **buying-power constraint** [12:46].
  10. **Aggressive order entry** — "if you're queuing up 5 cents… when there's some massive
      headline, you're not going to get it" [13:49].
- **Entry / trigger / stop:** none given. This is a risk layer applied over whatever setup you
  already have, not a setup.

## 2. ⚠ The sizing-lever question

- **Stop distance as % of entry:** not stated, but the whole point is that it **expands with the
  regime**. His SPY worked example: normal daily range "a couple of points", event-day range ~50
  points (10%) [05:03–05:40].
- **Position that buys at 0.3% risk:** falls by the same factor the range rises — a 10× wider stop
  buys a 10× smaller position. He accepts that and says the **dollar** risk may still rise because
  the opportunity is richer.
- **Does he state or imply a stop-out rate?** No. But he makes the fragility point implicitly:
  using prior-bar lows as a stop in that tape is "just kind of asinine… given the ranges and how far
  away this is" [04:27]. ⚠ That is the same stop he endorses in `ZOHG-OnQuos`@[04:58]; the two are
  reconcilable only as a volatility-scaling statement, which he never actually makes.
- **What would settle it:** the harness spec below settles the *gate*. The sizing arithmetic itself
  needs no test — it is identity arithmetic, and the repo's harness already sizes in R.

⭐ **Net effect on the 6× thesis: deflationary again.** Every one of his volatility rules moves size
*down* and horizon *shorter*. The only expansionary lever he names is discretionary dollar-risk
escalation into a rich opportunity set — and the repo's size study found the lever that pays is
**exclusion (A+B only, +0.29R OOS)**, not a 10× risk spread (+0.08R, more drawdown).

## 3. Claimed edge & evidence

No numbers beyond a hypothetical (50,000 SPY × 50 points = "a $2.5 million trade"). Evidence is one
week of charts with the outcome known, plus social proof — "a lot of seven figure days at Trillium
and SMB" [14:22]. ⚠ One unverifiable accusation is load-bearing for his read of 9 Apr: "about 10
minutes prior… massive massive massive waves of call volume" before the tariff-pause tweet, which he
prefers to the alternative explanation he himself raises ("maybe it's because we were breaking above
this area") [03:17–03:40]. Course marketing at [15:00]: "I might produce this in more formal proper
fashion for Magnum Opus."

## 4. ⚠ Prop-infrastructure dependency

- **Depends on:** a firm-enforced daily loss limit; hotkeys and routing aggressive enough to lift
  offers on a headline; futures access; staffed pre-market coverage; a maintained basket/exposure
  map; colleagues and a risk desk.
- **Retail-viable as stated?** **Partly.** The concepts — size down as stops widen, cap the daily
  loss, hold less overnight into binary headlines, know your exposure map — transfer intact. The
  *execution speed* does not, and he says so himself: the retail alternative he names is choosing a
  levered **vehicle** (SPXL, ES) to get exposure without the buying power, which is a different
  trade with different path risk.

## 5. Decay risk

The specific tape (a single-tweet-reversible policy shock) is unusual, and he flags that this is
what made it different from 2020: "there was no putting COVID back into the bottle" [00:30]. The
generic claim — that high realised/implied volatility changes what pays — is structural and does not
decay. Dated 2025-04; the VIX regime it describes ended within weeks.

## 6. Objective assessment

- **"Change your playbook" with no threshold** is not a rule, it is a disposition. He refuses the
  definition explicitly, and "most people can judge it qualitatively" is precisely the judgement the
  repo's regime work found people cannot make.
- Recorded mid-event, one week, all examples retrospective.
- He calls the post-tweet rally "a very very very obvious short" [06:23] after watching it retrace —
  with no trigger and no stop — which is the exact behaviour his own ORB write-up forbids.
- The front-running claim is asserted, not evidenced.
- Much of the list (be in your seat, don't be on Instagram, game-plan your baskets) is sound and
  **unfalsifiable**. Filed as process.

## 7. What's genuinely sound

- **The arithmetic.** position = risk ÷ stop, so a widening stop cuts shares while leaving dollar
  risk free to be set independently. Correct, repo-consistent, and the single most often-inverted
  idea in retail volatility advice ("bet bigger, vol is high").
- **The overnight qualifier.** "Reduce, don't eliminate" plus the reason — the overnight headline is
  variance "not in your control and **not part of the edge**" [10:11] — is a cleaner statement of
  exposure-vs-edge than most of this corpus.
- **Spend the loss limit late.** Framing the daily stop as a *budget with a schedule* rather than a
  tripwire is a real idea, and it is checkable on our journal.
- **Vehicle choice as a capital-efficiency lever** — a distinct axis from entry quality, and one the
  repo's vehicle study deliberately held fixed.

## 8. Overlap / conflict with the rest of the repo

| repo finding | this video |
|---|---|
| **Regime management = fixed small sizing, not a switch**; every trailing-30d rule from Aug 2026 failed 2019–26; paying months unforecastable (47% positive, top decile = 68% of positive R) | ⚠ **conflict — but a different object.** Those rules conditioned on *trailing returns / breadth* to predict *payoff*. His conditions on **contemporaneous volatility** (persistent, observable) and changes **horizon and size**, not direction. Untested here |
| SPY short-dated selling pilot: **VIX < 20 is NEGATIVE** | ✅ precedent that a VIX state flips a strategy's sign — his claim is not prima facie dead |
| Gap study: **high-VIX tercile +6.90bp (t=3.65)** vs −0.83 low VIX | ✅ agrees that high-vol tape is a different animal |
| Exit-timing study: **same-day exits are the negative bucket in BOTH books** (pool: scalp −0.13R vs trail +0.89R; Gabe: 278 same-day cycles −$8.3k, 19% win) | ⚠⚠ **direct conflict** with "shorten your horizon" |
| Entry study: **buying the daily CLOSE beats every intraday entry** (−0.9 to −2.3pp paired, t to −3.4) | ⚠⚠ the overnight hold *is* our return; his "cut overnight exposure" would move us into the losing bucket |
| August vehicle study: **no vehicle fixes entries** | **complementary, not contradictory** — his vehicle point is capital efficiency under a buying-power constraint, a size lever, not an entry-quality claim |
| Size study: the lever is **exclusion (A+B only, +0.29R OOS)**, not a 10× risk spread | ✅ "wait for the pocket aces" [12:09] is the same conclusion in prose |
| `stops-and-sizing.md`, `risk-management-15-lessons.md` ("3× wider stop → ⅓ size"), Luk's near-constant risk | ✅ third statement of the same arithmetic in this KB |
| `feedback_precision_over_recall`, `feedback_conviction_selection_is_the_strategy` | ✅ "be super selective", "save your bullets" |

**⚠ Scope is the resolution of the big conflict, not a verdict.** He is an intraday prop trader with
a firm loss limit and no overnight mandate, describing a binary-headline week. We are a swing book
whose return lives in the overnight hold. His playbook is **not importable as stated** — but the
*gate* underneath it is testable on our own book, and that is what to extract.

---

## Harness spec

`src/lib/studies/pattern_test.py`, `run_daily`. Long side. This tests **the gate, not a new entry**:
take the house breakout signal and split it by contemporaneous market volatility. His claim predicts
the high-vol half should favour **fast** exits (`t1R`) and the low-vol half **slow** ones
(`ema20` / `trail_bar`). Our exit-timing result predicts the opposite in both halves.

```python
# market vol state from the panel itself -- no new data, no VIX file needed
def _hivol(P, pct=0.80, win=20):
    rv  = P.close.pct_change(fill_method=None).rolling(win).std()      # per-name 20d realised vol
    mkt = rv[P.elig].median(axis=1)                                    # cross-sectional median = market state
    hi  = mkt > mkt.expanding(252).quantile(pct)                       # point-in-time, no lookahead
    return pd.DataFrame(np.repeat(hi.values[:, None], P.close.shape[1], axis=1),
                        index=P.close.index, columns=P.close.columns)

def breakout_hivol(P):                                                 # arm A: high-vol regime
    brk = (P.close > P.high.shift(1).rolling(20).max().shift(1)) & (P.adr >= 3) & P.elig
    return daily_signals(brk & _hivol(P), stop=P.close - P.close * P.adr / 100.0, side="long")

def breakout_lovol(P):                                                 # arm B: everything else
    brk = (P.close > P.high.shift(1).rolling(20).max().shift(1)) & (P.adr >= 3) & P.elig
    return daily_signals(brk & ~_hivol(P), stop=P.close - P.close * P.adr / 100.0, side="long")
```

- **Boolean condition:** `close > max(high[−21:−1])` and `ADR ≥ 3` and `elig`, **AND** (arm A) the
  cross-sectional median 20-day realised vol is above its own trailing-252 80th percentile, or
  (arm B) it is not.
- **Stop reference:** **1 × ADR below the signal close** — deliberately *not* the prior bar low,
  because his complaint at [04:27] is that the prior-bar stop is the wrong scale in a wide-range
  tape. An ADR-normalized stop is the scale-free restatement of his objection, and it makes the two
  arms comparable (the same *number of ADRs* of risk in both regimes, so any difference is the
  regime, not the stop width).
- **Side:** long.
- **Sweeps:** `pct ∈ {0.70, 0.80, 0.90}`; stop ∈ {1 ADR, 2 ADR}; and a VIX-close version of `_hivol`
  as a robustness check if a VIX series is on disk.
- **What each outcome means.** Arm A's best exit = `t1R` while arm B's = `ema20` ⟹ his playbook
  switch is real and horizon-shaped, and the repo's "fixed small sizing, no switch" conclusion needs
  a volatility carve-out. Both arms preferring the slow exit ⟹ the switch is folklore and the
  exit-timing result generalises across regimes. Both arms negative ⟹ nothing to gate.
- **Bar to pass:** beats the same-name random control, positive in both halves, |t| ≥ 3 — noting
  that here the *interesting* statistic is the **A-vs-B difference in best arm**, which the ledger
  row will not capture on its own. Record it in the note field.
