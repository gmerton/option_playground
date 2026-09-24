# Does the RVOL gate make the tier buy too late? (2026-09-24)

**Question (Gabe, after TWLO):** "a typical trader would say 9/22 is too late; a couple of days earlier is the
natural buy." TWLO's clean cross on 09-17 (1.4 ADR above the 21 EMA) failed only RVOL (0.77); the first qualifying
signal came 09-22 at 3.5 ADR. **Script:** `run_rvol_gate_timing.py` (pre-registration in the docstring); log
`data/studies/logs/rvol_gate_timing.log`; episodes `rvol_gate_timing_2026-09-24.csv`.

**Design — a policy test, because the obvious comparison is rigged.** Comparing a rejected early cross with the
qualifying cross that followed it conditions on the future (the follow-up exists only because the stock kept rising).
So on EVERY tier breakout rejected only by RVOL < 1.1 (1,239 episodes, 559 names, 2019-10 →): policy **A** (today's
rules) buys the first RVOL-qualifying tier signal within 10 sessions, else stays flat; policy **B** (no gate) buys the
early cross. House process both sides, % of price.

| | W = 10 (PRIMARY) | W = 5 | W = 20 |
|---|---|---|---|
| B − A per episode | **+0.54%, t 0.56** | +0.67%, t 0.68 | +0.47%, t 0.53 |
| halves (pre-2023 / 2023+) | −0.03 / +0.95 | −0.03 / +1.17 | −0.21 / +0.96 |
| in R | +0.26, t 1.11 | +0.29, t 1.14 | +0.23, t 1.15 |

Per year (W 10): 2019 −3.15, 2020 +2.15, 2021 −1.96, 2022 −2.73, 2023 +1.00, 2024 +0.62, 2025 +2.38 → 4 up / 4 down.

**FAIL — NULL. The gate neither costs nor pays.**

**Why the intuition feels right and still does not hold:**
- A follows only **23%** of the time. On those 288 episodes the early buy did +8.3% vs A's +3.2% — the TWLO pattern.
- But on the other **77%** (951 episodes) there is no follow-up, and the early buy **loses −0.84%**. You only see the
  follow-up cases on a chart after the fact; the rest are the rejected crosses that went nowhere.
- ⚠ The biased comparison (early +7.58% vs late +3.24% on the follow set) is what a chart review produces. It is
  conditioned on the later breakout and is NOT evidence.
- The typical delay is small: median **3 sessions**, extension **2.09 → 2.43 ADR** (+0.34). TWLO's 1.4 → 3.5 was an
  outlier, not the rule.

**Verdict: keep the gate** (no evidence either way; precision over recall). Early entries have a real payoff when the
move continues, and the policy test says that payoff is paid for by the ones that don't.
