# Recap Audit — "$218K Premiums in 6 Months" (Jan–Jul 2025)

> **Audit verdict:** The most transparent video on the channel — he volunteers "for full transparency, that
> was about a 22% return" next to the $218K headline. Taking BOTH numbers at face value, the implied
> non-premium P&L (share MTM etc.) was **negative** — roughly −$20K to −$85K depending on the capital base —
> even in a half-year that ended with a V-recovery to all-time highs. Gross premium overstated economic
> profit by ~10–40%. That is the wheel's true anatomy, demonstrated by his own numbers in his *best* case.
> Source: `videos/recaps/2025-07-18_ttN5dCDDE5c` (recorded Jul 15, 2025).

## The claim set

- **$218K premiums collected** in 6 months (Jan 15 – Jul 15, 2025), shown as a platform tab screenshot.
- **"About a 22% return in the portfolio"** over the same window (≈48% annualized — consistent with the
  recurring "40%/yr for 5 years" claim, and resting on the same unauditable base).
- Window includes the **April 2025 tariff crash**: per the underwater-CC video, his account was **−18% at the
  bottom** of this very window — never mentioned in this recap.
- He **deposited $100K of new money** at the VIX-60 bottom (stated here) — muddies any account-value-based
  return math (simple vs money-weighted never specified).

## The decomposition (the point of the audit)

Portfolio base is not stated. Bounding it from adjacent videos ($660K shown Nov 2024; ~$1M implied by Sep
2025's "realized ~$300K this year"): call it **$700–900K** average capital.

| Base | 22% return ($) | Premiums | Implied non-premium P&L |
|---|---|---|---|
| $700K | ~$154K | $218K | **−$64K** |
| $800K | ~$176K | $218K | **−$42K** |
| $900K | ~$198K | $218K | **−$20K** |

**If both of his numbers are true, premium was 110–140% of the actual profit — the share/assignment leg net
LOST money across a window that ended at all-time highs.** In a tape that doesn't V-recover, that cost line
doesn't shrink; it dominates. This is the cleanest internal evidence for the KB's core red flag: "premium
collected" is the gross revenue line of a business whose cost of goods (assignment MTM) is reported nowhere
— except accidentally, here.

Secondary observation: 22%/6mo *is* a strong result if real — but it was earned with (a) a −18% intra-window
drawdown, (b) a $100K top-up deployed at the exact bottom (timing that IS the return, not the wheel), and
(c) a market that fully recovered within ~3 months. All three are the favorable branch of every risk his
system carries.

## Other audit findings

1. **He doesn't follow his own ladder.** VIX 15–20 prescribes 25–50% cash; on camera: "I have about 15%
   cash... not quite following my VIX allocation levels." The discipline being sold is discretionary in practice.
2. **The 2022 origin story changed.** This video: the market rolled over when Powell signaled hikes in
   **November 2021** (roughly correct — peak Jan 2022). The bear-market video (reviewed earlier): the bear
   "started December 2022/January" after the June 2022 hikes (wildly wrong). Same event, two incompatible
   tellings, both narrated as "I saw it coming." Appended as a credibility note to `wheel_bear_regime.md`.
3. **CME FedWatch "100% right since 1998 at 55%+"** — the tool predicts the *Fed's decision* (it's just fed
   funds futures pricing), not market direction. True-ish claim, irrelevant edge; conflated on camera.
4. **No-stop short premium, win-rate framing again:** "winning 80–90% of the time... I don't set stop losses,
   those don't make sense." Same unsampled left tail as the Feb 2025 video.
5. **Parameter drift** (worth tracking for any backtest spec): covered calls here = 30Δ / 20–30 DTE, entered
   "on a green day"; Feb 2025 video said 20–30Δ / 7–14 DTE. CSP spec stable at 25–35Δ / ~30–45 DTE / 3–5%/mo target.
6. Marketing density is higher than the earlier videos: mastermind (250 members), testimonials, "book a call."
   The recap is the funnel; the $218K is its headline.

## What this changes

- **STRATEGIES.md cross-finding upgraded from "suspected" to "internally evidenced":** his own paired
  numbers show premium > profit even in the best half-year the strategy will ever see.
- Any future wheel_core backtest should report exactly this decomposition (premium collected vs net P&L incl.
  assignment MTM) so results are directly comparable to his headline framing.
