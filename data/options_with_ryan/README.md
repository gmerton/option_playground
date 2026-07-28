# Options With Ryan — Knowledge Base

An archive of the **Options With Ryan** YouTube channel (single creator, "Ryan"), seeded from a
56-video playlist (`channel_videos.txt`). Unlike `data/theta_profits/` (many guests, many
strategies), this is **one trader with a handful of recurring systems**, closer to
`data/martin_luk/` / `data/paycheck2portfolio/` — but the deliverable follows the theta_profits
pattern: an **objective, skeptic-default write-up per strategy**, because the channel's framing
is heavy on income claims.

## The recurring systems (from playlist titles — refine as videos are reviewed)

1. **The Wheel** (the core franchise) — CSPs → assignment → covered calls, run per-ticker with
   named plans: PLTR, SOFI, NVDA, HOOD, IREN, CLS, COHR, WDC, GLW, QQQ. Claims like
   "$448K premiums collected."
2. **LEAPS calls** — long-dated calls as a retire-early vehicle (SPY framework, "masterclass").
3. **SPY/QQQ swing trading** — RSI-based directional options swings ("$29K/month", live backtests).
4. **Supporting mechanics** — PMCC, verticals for small accounts, rolling, earnings trades,
   deep-underwater covered-call repair.

## Prime directive: skepticism (the wheel-channel edition)

> **"Premium collected" is not profit.** The signature red flag of wheel content: headline
> gross premiums with no marked-to-market accounting of assigned shares. A $448K-premium year
> can be a losing year if the assigned stock is deep underwater. For every claim, ask:
> - Gross premium vs **total return incl. unrealized stock P&L** (and vs buy-and-hold of the same names).
> - **Survivorship in ticker picks** — wheels shown on names that went up (PLTR, HOOD, NVDA...).
>   What happened to plans on names that fell? (see the "deep underwater" video — that's the tell).
> - **Bull-market-only track record** — high-IV momentum names wheeled through 2023–2025;
>   never bear-tested. Same critique as paycheck2portfolio.
> - Position sizing / concentration — portfolio size quoted ($600K) vs per-name exposure.
> - Swing-trade "PROOF" screenshots — selected periods, no full trade log.

Default conviction LOW until independently tested. Stay open — mechanics may still be sound
(the user actively runs CSPs/wheel; extracting Ryan's *management rules* — strike selection,
rolling triggers, earnings handling — has value even if the income claims don't survive audit).

## Layout

```
README.md               This file.
channel_videos.txt      Playlist manifest + review checkboxes ([x] = written up).
STRATEGIES.md           Index / leaderboard: strategy · conviction (0–5) · risk (1–10) · tested? · verdict.
strategies/<slug>.md    One objective write-up per SYSTEM (not per video — videos repeat;
                        per-ticker wheel videos fold into wheel_<ticker>.md or the master wheel.md).
videos/<type>/<date>_<id>/   transcript.txt · meta.json · notes.md
backtests/<slug>/       (on demand) scripts + results.
```

## Ingest

```bash
.venv/bin/python3 add_luk_video.py <url-or-id> --kb data/options_with_ryan --type <type>
```

Types: `wheel` · `leaps` · `swing` · `mechanics` (tutorials: rolling, PMCC, verticals) ·
`recaps` (monthly P&L recaps). Tick the video off in `channel_videos.txt` when its content has
been folded into a strategy write-up.

## Suggested review order

Start with the evergreen system explainers (wheel 101, LEAPS masterclass, swing strategy), then
the per-ticker 2026 plans (current thinking), then recaps only as evidence for/against claims.
