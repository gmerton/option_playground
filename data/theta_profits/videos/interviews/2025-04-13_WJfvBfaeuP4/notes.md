# Supplemental Notes — 2025-04-13 "This Lawyer’s Options Trading Strategy Guarantees No Loss (Here’s How)" (WJfvBfaeuP4)

Human-added context not in the audio: on-screen actions, slides, corrections, the
interviewed trader's name/handle, and anything to verify.

## Interviewee

- Name / handle: **Christian** — 60-year-old lawyer & options trader from **Munich, Germany**;
  trades own capital, on **Discord**, invites readers to reach out. Surname per auto-captions
  is **"Chennich"** but that is almost certainly mis-transcribed — treat the surname as
  UNVERIFIED (`@00:27`). Trading since 2000 (stocks/futures/forex), options since 2020;
  self-described "quite risk averse" after three black-swan events.
- Strategy in one line: A "no-loss-at-expiration" combo — take a butterfly/calendar/condor,
  replace one long-option leg with **synthetic long stock (put-call parity)** so the position
  carries a large debit that earns the **risk-free / Fed-funds carry**; if that interest exceeds
  the structure's loss-zone, the floor lifts to ≥$0 at expiry.

## Corrections & context

- The "guarantee" is REAL but trivial (textbook cost-of-carry), NOT false like Burrito's
  "risk-free." But it is **only at expiration**, earns only ~1-2% base (sub-T-bill), is
  capital-hungry ($50k-$84k/combo), and the headline **20-25%/yr depends on a directional read
  he disclaims** ("really bad at reading the market short term"). Write-up calibrates to those
  gaps. See `strategies/no_loss_combo.md`.
- [01:08] "No loss trade at expiration… absolutely no risk to the downside" — the central claim.
- [09:35]-[11:25] The engine: $52,798 debit × 3.9% Fed funds × (54/365) ≈ $304 carry; "the
  market pays you interest for going long stock / doing debit trades."
- [17:50]-[18:05] Works on stocks/ETFs only (SPY, QQQ, MSFT, HPQ) — NOT cash indexes (no shares).
- [31:22]-[33:43] Altria (~7% dividend) CANNOT form a no-loss trade — dividend > Fed funds.
- [34:41]-[36:04] Admitted real catch: dead in a zero-rate regime ("didn't work for 12 years,"
  2008-2020). References McMillan and old long/short boxes.
- [36:04]-[37:10] No-loss is only at expiration; interim drawdowns are real losses if you close;
  market makers often won't fill the "riskless" prices (slippage drag on a ~1-2% edge).
- [37:10]-[38:18] Early-assignment risk on short calls around ex-dividend.
- Tickers in auto-captions are mangled (e.g. "Hue Packard"/"Pekka"/"Ulip Pekka" = **HPQ /
  HP / Hewlett-Packard**; "IB goes up" ≈ "IV goes up"; "fat funds" = "Fed funds").
