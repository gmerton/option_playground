# Ariel's 9/23 watchlist vs our INT scan (2026-09-22)

First side-by-side of his published nightly list against our own scan, run the same evening. Source:
`videos/watchlists/2026-09-22_O6vgCjCXjR4/`. Our side: the EOD breakout scan run on the **INT 50**
universe with the `prev_green` gate removed the same night — i.e. tomorrow's list, tonight.

## Overlap: 11 of 32

His list has 35 named symbols; ours has 32 candidates. Eleven appear on both.

| ticker | his read |
|---|---|
| **NTAP** | acted well since earnings, nothing wrong, no distribution; "could be played as a higher low" but must take out **199** |
| **PANW** | very tight session, closed green; take out today's high ~**378** |
| **CRWD** | acting great |
| **RBRK** | acting great |
| **FTNT** | consolidating; over the prior-day high **176.10** *only on a volume pickup* |
| **HPE** | likes the base, would welcome a **bigger check back** to the 10/20 day; not in a rush |
| **OKTA** | near $200, new closing high |
| **AMD** | "arguably one of the best names out there at the moment" |
| **MU** | back in a leadership role |
| **SNDK** | breaks the 1,800 neckline; owned it yesterday; wants a **backtest** to 1,800 then a 620 |
| **MRVL** | semis shaping up — but **no way in tomorrow**, waiting for a higher low |

⭐ **NTAP is the headline.** It is on our list *only because* `prev_green` was removed from the Potent
gate a few hours earlier (see TEST_INDEX: the gate was NULL and cost 46.5% of EMA-lead name-days). The
untested filter was hiding the single name Ariel spends the most time on — and he wants the same entry
we would: a higher low, not a chase.

## ⚠ His own criteria exclude the names he actually watches

24 of his names are not on ours. ETFs (GDX, IGV, XBI, MAGS, XLK) and the gold complex (NEM, WPM, AEM,
GFI, AU, IAG) are outside our equity universe — expected. The **mega-caps are not**:

| ticker | above its 252d low | passes `a1` (>= 70% above the low) |
|---|---|---|
| AMZN | 1.32x | **FAIL** |
| NVDA | 1.38x | **FAIL** |
| MSFT | 1.44x | **FAIL** |
| GOOGL | 1.51x | **FAIL** |
| NOW | 1.69x | **FAIL** (narrowly) |
| PLTR | 1.72x | pass (but fails INT on the Trend-Template side) |

**Every mega-cap he is actively watching fails our implementation of *his own* published criterion.**
Either the implementation in `run_universe_test.py` is wrong, or his stated scan is not the universe he
trades from — he is plainly running the Mag-7 on a separate track regardless of the >= 70%-off-low rule.
His own words: "Mags continue to act great. Therefore, I want to make sure I've got Amazon and… Nvidia
and… Google on the radar."

### Why this matters

We switched production to **INT = TT AND AH** on 2026-09-22, partly because AH was the stronger parent
(20d excess t 2.08 vs TT's 1.00) and INT had the best control-adjusted edge of the five arms (+0.079R).
INT inherits `a1`, and `a1` is precisely what strips the mega-caps out — it accounts for 36 of the 48
names the switch dropped.

This does **not** invalidate the switch. The universe test measured the rule as implemented, not his
discretion, and INT still won on the numbers. But it does mean **INT encodes his published rule, not his
practice**, and the gap between the two is now concrete rather than hypothetical.

⟹ It also raises the value of the already-queued **Ariel criterion ablation**: `a1` is the binding
constraint inside the intersection, it is the one that halved the list, and its own author appears to
override it nightly. That ablation should run before anyone treats INT as "Ariel's universe."

## Method note

His entry language is our entry-extension finding almost verbatim — "find a higher low", "wouldn't mind
a bigger check back", "I don't know that I chase it", "wait for a morning pull, reclaim VWAP", "any kind
of backtest into 1,800". Closing line: *"Pullbacks still feel like the best way to get involved."*

⚠ But the **sign differs**, exactly as in the Mari Trades review: every one of his actual triggers buys
a **higher** price after the pullback (take out 199 / 378 / 59, over the 20 SMA), where our tested
retrace arm buys the **lower** one. Same axis, opposite direction, and neither of us has tested his
version. Third independent creator to land on this shape.

## Follow-up

* Score these 11 calls forward — this is where the hit rate accrues (README: `analysis/` is the ledger).
* ⚠ "INFQ" is unresolved and has no matching US listing; do not act on it.
