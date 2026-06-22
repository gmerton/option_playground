# Tito Adhikary — Interview Notes (raw)

Additional observations from Tito's interview. **These are notes, not validated findings.**
Most do not map onto the archetypes (A Breakout / B Earnings / C Exhaustion-fade / D Catalyst)
or the validated fade rule yet. Each is captured verbatim-ish with a mechanism gloss and a
cross-reference to anything in `tito_selection_playbook.md` it touches or contradicts.

---

## Note 1 — Extreme IV → use a DEBIT SPREAD, not a naked option (GME, 2021)

**The story.** GME 2021, the quintessential meme stock, ran to ridiculous prices. Many wanted to
short it via **long puts** — but the puts "didn't really pay" because IV was so high the premium was
enormous. Same problem on the long side: **buying a naked call** was prohibitively expensive for the
same reason. **The thing that worked was a debit CALL SPREAD** (long lower-strike call + short
higher-strike call), which "still captured a great deal of the upside" — *"somehow the IV of the two
call legs offset enough for this to work."*

**Mechanism (why it works).** In a vertical debit spread you **pay** rich IV on the long leg but
**collect** rich IV on the short leg, so the inflated vol largely **nets out** — the spread's net
debit is far cheaper than the naked long, and the position is roughly **vega-neutral**. You give up
unlimited upside (capped at the short strike) in exchange for paying only a fraction of the IV tax.
On a name where IV is extreme, the spread can be the *only* structure with a sane risk/reward.

**Generalizable principle:** *extreme IV → prefer defined-risk debit verticals over naked
directional options.* The richer the IV, the more a naked long is a bad deal and the more the spread's
short leg subsidizes it.

**Cross-references / implications for our work:**
- **Vehicle thread** (playbook: "vehicle = long calls, delta scales inverse to DTE"). This is a
  *conditional refinement*: the naked-long prescription assumes normal IV. **When IV is extreme,
  switch to a debit spread.** Add an IV gate to the vehicle-selection rule.
- **⚠ Directly relevant to our fade study (archetype C).** We modeled the exhaustion fade as a **naked
  0DTE put** and found higher entry IV **compresses** returns badly (median +515% → +206% as IV goes
  60% → 120%, mid). Tito's GME logic says the fix on extreme-IV fade names (SMCI/NVDA/MSTR/DJT — all
  high-IV) may be a **debit PUT spread** (long ATM put + short OTM put) instead of a naked put, to
  offset the IV tax. **Testable hypothesis, NOT a conclusion** — caveat: capping with a short lower
  put also caps the payoff on the huge −23% days, so it's a genuine trade-off, not a free lunch.
  Worth a variant in `scratch_fade_trigger.py`: reprice each leg as a put *spread* and compare net.
- Note the regime difference: GME was a multi-week runaway (longer-dated spread); our fade is 0DTE
  intraday. The *principle* (spread offsets IV) transfers; the *parameters* (strikes, width, DTE) do not.

---

## Note 2 — Compressed IV after a multi-year base → buy CHEAP LEAPS on the breakout (XLE, XOM, 2026)

**The story.** XLE and XOM both formed **multi-year bases**. Through that long sideways base, **IV
decayed** (no movement → realized vol falls → implied vol falls), so the **LEAPS were very cheap**.
When they finally **broke out (2026)**, that made it a **great opportunity to buy LEAPS** — long-dated
calls bought at depressed vol right as a new uptrend started.

**Mechanism (why it works — the double tailwind).** A long base compresses both realized and implied
vol, so long-dated calls trade at **cheap time value / cheap vega**. The breakout then pays the LEAP
**twice**: (1) **delta** as price trends up over the long runway, and (2) **vega** as IV *expands* off
the compressed base. You bought cheap optionality right before vol and price both turned up. The long
expiry means you don't need to time the move precisely and theta bleed is slow.

**Generalizable principle:** *compressed IV (esp. after a long base) + a breakout → buy naked,
LONG-dated calls (LEAPS).* The cheap IV is exactly what makes the long-dated premium affordable.

**The symmetry with Note 1 — an IV-conditional vehicle map:**
| IV regime | Vehicle | Why |
|---|---|---|
| **Extreme HIGH IV** (meme/parabola, GME) | **debit spread** | short leg's rich IV offsets the long; avoid paying the IV tax; ~vega-neutral |
| **Compressed LOW IV** (post multi-year base, XLE/XOM) | **naked LEAPS** | cheap vega + long runway; win on delta AND vega expansion |
| *(normal IV)* | *(playbook default: long calls, delta scales inverse to DTE)* | baseline |

So the vehicle is a **function of the IV regime**, not just the setup. This is the missing axis the
playbook's vehicle rule didn't have.

**Cross-references / implications:**
- **Vehicle thread** (playbook). Note 1 + Note 2 jointly say: gate vehicle choice on IV percentile/rank,
  not just DTE. Low-IV-after-base → LEAPS; high-IV → debit spread; middle → the existing rule.
- **Toolkit already has relevant machinery:** `src/lib/commons/vol_compression.py` (detects the IV/RV
  compression), `src/lib/leaps/leap_finder.py` (LEAP screening — currently a *collar* structure on
  <$30 names; this note is a *naked* LEAP on a base-breakout, a different use). A future study could
  wire vol_compression → base-breakout detection → naked-LEAP candidate (IV-rank gate).
- **Setup archetype:** this is a longer-horizon cousin of **archetype A (Breakout)** — but it's a
  **multi-year base / Stage-1→Stage-2 transition** (Weinstein/Minervini), position-trade timeframe,
  not the playbook's shorter swing breakout. The *trigger* (breakout over the base) rhymes; the
  *horizon and vehicle* (LEAPS) differ.
- ⚠ Note: XLE/XOM 2026 is **n=2, in-sample, recent** — and energy had a real fundamental catalyst that
  year. The IV-compression→LEAPS logic is sound, but this is anecdote, not tested edge.
