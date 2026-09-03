# Supplemental Notes — 2026-08-08 "The ONE Options Strategy I will ALWAYS have in my account" (wNaiAmbrLLs)

Human-added context not in the audio: on-screen actions, chart annotations, number fixes.

Screen-share throughout: broker option chain + P&L analyzer (XSP and SPX side by side early on),
then live strike construction from ~[22:16]. 34:08 total. Framed as a small-account video.

Write-up: `../../../strategies/xsp_put_condor.md`

## Number decoding table (auto-caption fixes)

Captions are clean on words but **drop and misplace decimal points constantly**. Conf: ✅ confirmed
by context/arithmetic · 🟡 likely · ❓ unsure.

| Transcript said | Actual | Conf | Notes |
|---|---|---|---|
| "543" (XSP long put) | 547.5 | ✅ | Stated as the XSP equivalent of SPX 5475 |
| "5:1" / "5 1" | 561 | 🟡 | Long put strike in the condor-vs-spread comparison |
| "$1.7" | $1.07 | ✅ | Debit-spread cost; must be < $1.37 credit for the net-credit rule to hold |
| "$4.89" / "$4.94" | $489 / $494 | ✅ | Max losses in the equal-risk comparison |
| "$9" more max profit | $9 | ✅ | SPX vs XSP max-profit difference |
| "8.43 43" | $8.43 | ✅ | Bid on the 541 put |
| "9.31" | $9.31 | ✅ | "Dream price" — the opposite-side quote |
| "$910" / "$873" (car analogy) | $9.10 / $8.73 | ✅ | Option prices, not car prices — he switches units mid-analogy |
| "$1,7 is around there" | ~$1,000 risk | 🟡 | Adjusting the long put to re-hit the $1K risk target |
| "1 is to5" | 1:0.5 | ✅ | Iron condor risk/reward |
| "the 10th" / "tent" | tent | ✅ | His term for the max-profit zone |
| "pop" | POP | ✅ | Probability of profit, from the platform |
| "SBX" / "XPX" / "mini XPX" | SPX / XSP | ✅ | |

Other garbles: "cash settle" = cash-settled · "net"/"natural" = the NAT price on the order slider ·
"OP" = OPP (opposite side) · "hash" = hedge · "condor" here always means the **all-puts (or
all-calls) four-leg condor**, never the iron condor — he distinguishes them explicitly at [20:17].

## On-screen actions (inaudible / not narrated)

- [02:42]–[06:01] Two option chains side by side, SPX left / XSP right, both showing a put credit
  spread built to ~$350 max loss. The point being made is visual: how much further the XSP long
  strike sits from spot at equal dollar risk.
- [06:35]–[07:08] XSP chain with the open-interest column highlighted; several strikes show 0 OI.
- [09:07]–[12:39] Order ticket with the price slider (MID / NAT / OPP) — the "negotiation" segment.
- [17:03]–[21:38] Three equal-max-risk comparisons in the analyzer: put spread vs put condor, then
  iron condor vs put condor at matched risk, then again at matched POP.
- [22:16] onward Live construction. Draws the P&L curve freehand first, then builds it: short put
  ~700 → long put ~690 for ~$1K risk → ATM debit spread 770/769 → checks net credit and POP (~94%).
- [31:56]–[33:24] Widens the short strike to ~20Δ and re-widens the debit spread, walking max
  profit $111 → $193 → $256 → $322 at roughly constant ~$880–1,000 max loss.

## Things to verify against the video

- **DTE is never stated.** Not in the narration and I could not read it off the chain in the
  transcript. Needs a re-watch of the expiry header at ~[22:16] and ~[24:05]. Everything downstream
  (POP, max profit, theta) is undefined without it.
- Exact XSP spot at recording — ~770 is inferred from the strikes used, not stated.
- Whether the analyzer POP is model-based (delta proxy / lognormal) or vendor-specific. Affects how
  much weight the "94%" deserves.

## Other context

- Sales funnel at [21:48]–[22:16] (free "Options Income Blueprint" PDF) and in the description
  (second PDF + 12-month mentorship + student case studies).
- Opens by saying the video exists because viewers asked for **small-account** content — the whole
  XSP-over-SPX argument follows from that framing.
- No positions, no trade log, no backtest shown at any point. Analyzer output only.
