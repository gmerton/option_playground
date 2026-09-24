# tastylive — "Use Tom Sosnoff's Daily Routine to Analyze Trades in 2024" (2024-01-07, 7:39, 20k views)

_Reviewed 2026-09-23. "Options Jive"-style segment: a research-team slide deck on "market awareness", read by the
host, who **disagrees with most of it on air** ("this is our research team's writing but I'm going to say
something a little bit different"). Transcript (auto-captions, no speaker labels) in this folder._

**Who is speaking.** **Sosnoff, high confidence.** He dismisses "anything Vonetta has to say about news"
(Vonetta Logan, tastylive's news host). He points viewers at "Bat's watch list — be careful with that one"
(Tony Battista). He refers to himself having "been watching the S&P" for decades. The watchlist he names is "Tom's
default". The co-host is almost certainly Battista. ⚠ The title promises a "daily routine to analyze trades".
The segment contains **no routine and no trade analysis**. It is a philosophy of attention.

## Verdict: 1.5 / 5

It has almost no strategy content and no data. It's valuable for one thing: it's the clearest on-camera statement
of what Sosnoff **refuses** to use:
- news;
- other people's opinions;
- the claim that awareness improves decisions ("so much of that is random");
- forecasting ("you cannot master knowing what's going to happen next").

It also names what he *does* watch: futures, not ETFs, and the VIX term structure. Against that, he says he's "a
big fan of trying to guess market extremes" and offers contrarian entry cues. That is the one family our regime
work has contradicted five times, and it sits awkwardly next to his own "it's random".

## His rules, in codable form

| dimension | rule as stated |
|---|---|
| ignores | **News** (00:28), **other people's market opinions** (00:32), macro top-down assessment as a decision tool (01:08–01:52) |
| watches | **Futures, not ETFs: /ES, /GC, /ZB, /CL**, not SPY/GLD/TLT/USO. Futures have "the most depth and the highest leverage", so they "attract the first dollar" (04:38–05:19) |
| context inputs | Rates, yield-curve inversion, currencies, **the vol curve: contango vs backwardation out 2–3–6–12 months** (04:09–04:30) |
| scanning | Watch many underlyings on watchlists **sorted by a metric** (platform presets, "Tom's default") to train the eye (05:26–06:01) |
| entries | Contrarian: "bearish because everybody else is bullish" (03:17). Buy the dip intraday when bullish: "S&P futures down 35 handles" (03:24–03:31). On unusual moves, e.g. a Bitcoin spike, "lighten up / get short RIOT, MARA or COIN on the opening" (03:37–03:51) |
| regime | "Big fan of trying to **guess market extremes** — doesn't always work" (04:09) |
| management | Familiarity with an underlying lets you "take some heat, do something about it, or close it" rather than hope (06:26–06:53) |

## Data shown

None.

## Claim by claim

| @ | Claim | Our evidence | new vs `data/more_tom` |
|---|---|---|---|
| 00:28–00:36 | Ignore news and other people's opinions | ✅ **Agrees for macro.** Catalyst work: FOMC is noise ("macro no, earnings yes"). The only macro-event result that survives is **convexity**: 0.12–0.25Δ calls bought the session before FOMC/elections, MARGINAL. That's a vol trade, not a news read | dup (More Tom process #8, analysts) |
| 01:08–01:52 | Market awareness does **not** help you avoid poor decisions or optimise good ones, "because so much of that is random" | ✅ **Agrees, and it's our most expensive negative.** Stage A: 11,227 intraday alerts, every arm −0.10…−0.13R, **indistinguishable from a random later minute in the same name**. Regime-conditioned alerts NULL (±0.07R every month) | new (as stated) |
| 02:02–02:48 | Its real value is **engagement**, and the opportunity is "other people thinking they know" | Untestable as stated. It's the same "hobby, not edge" framing as his scalping clip (More Tom process #3), which our data backs: same-day exits are the negative bucket in both books | dup of process #3 in spirit |
| 03:17–03:31 | Contrarian stance; buy intraday weakness when bullish ("futures down 35 handles") | ❌ **Contradicted on entry timing.** Entry study (2026-09-17): the **daily close beats every intraday entry** (t to −3.4). Contrarian sentiment proxy: retail call-buying bursts → next 5 days **−0.039pp, t −1.24** (NULL, leans negative) | new |
| 03:37–03:51 | On an unusual Bitcoin move, short the crypto proxies (RIOT/MARA/COIN) at the open | ❌ **Contradicted by every short test we have.** Short-selectable universe: **0 of 10 cells pass; 10 of 10 have negative excess but 0 of 10 a negative absolute return**, so weak names still drift up. Bouncy-ball short −0.41 to −0.67R. He hedges it himself: "you don't know what's going to happen next" | new |
| 04:09–04:28 | "Big fan of guessing market extremes" | ❌ **Contradicted as timing, ✅ agrees in one form.** Every regime-timing rule failed: FTD as a regime switch NULL (eff. n 16–37); August trailing-30d rules fail 2019–26; strategy localisation persistence ρ −0.01. ⭐ But the one certified bucket is **selling index put risk after a selloff** (bearish-high-IV, SPY t 6.07). That is "fade the extreme" done with volatility, not with direction | dup (More Tom #12 ATH timing) |
| 04:22–04:30 | Watch the vol curve (contango vs backwardation) | **Untested as a signal, adjacent result negative.** VRP panel: "30d/90d/term-structure absent". FVR (front/back vol ratio) doesn't sort the premium. It does sort the *long* 7-DTE straddle (FVR ≥1.20 gate), the opposite side from his | new |
| 04:38–05:19 | Watch **futures, not ETFs** (/ES /GC /ZB /CL): depth and leverage mean the first dollar goes there | **Untested. We have no futures data.** Nearest analogue: SPY and SPX produce the **same** certified bucket (t 6.07 / 5.21, "same stress episodes = one bet"), so at index level the vehicle choice didn't change the answer. ⚠ Per the More Tom review, don't transfer the single-name selling null onto his futures book | ⭐ new (More Tom mentions futures strangles, not "watch futures first") |
| 05:26–06:01 | Watchlists sorted by a metric train the eye | If the metric is IV rank: **IV rank as a cross-sectional sort is NULL** (zivr −1.89pp, t −1.25) while credit/width wins (zcw +2.62pp, t 2.81; within-date t 4.01) | dup (IVR) |
| 06:26–06:53 | The more you trade a name, the better you understand its risk, so you can take heat or close. "Doesn't mean you have any idea where it's going" | **Untested, adjacent null.** Per-name tactic affinity (gap-share trait) ≈ noise. "Take heat" vs "close": our exits say holding beats P&L-conditioned exits. The roll test: 69.8% of breach-cohort trades were better held | new |
| 07:03–07:17 | "You cannot master knowing what's going to happen next" | ✅ Agrees with the whole equity ledger: the breakout population is bimodal and the split can't be called at entry | dup |

## What I would take

1. **The negative list is the doctrine.** No news, no opinions, no forecast, "so much is random". Our intraday and
   regime ledger independently reaches every one of these.
2. **Futures as the primary instrument is a real gap in our evidence, not a refutation of him.** Note it; don't
   fund data for it.
3. **Nothing on entries.** His two concrete cues (buy the intraday dip, short the crypto proxies) are both families
   our data kills.

## Not tested, could be

- **VIX term structure (contango/backwardation) as a gate on the certified index put sale.** VIX futures curve
  or VIX/VIX3M ratio as a filter inside the bearish-high-IV bucket. ⚠ Best-of-k on the one certified cell, the
  same warning as the 1 SD / 2 SD strike sweep. Pre-register one threshold. Effective n is a handful of stress
  episodes, so it's probably UNDERPOWERED before it starts. **Not queued.**
