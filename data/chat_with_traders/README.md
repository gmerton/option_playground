# Chat With Traders KB

A long-form trader-interview podcast: the original host was Aaron Fifield, and it's hosted by Kevin since ~2025.
Guests are practitioners, some verified and many not. The show is **sponsor-funded**: Trade The Pool, a prop-funding
firm, reads ads in the 2026 episodes. Guests usually aren't selling on camera, which makes it a better source of
*rules* than the course-seller channels. It's still a source of **self-reported** records, with no data behind them.
Skeptic-default scoring like every KB here.

`videos/<date>_<id>/` holds `transcript.txt` (timestamped auto-captions), `meta.json` and `notes.md`.
Timestamps in the notes are the transcript's. The description's chapter list is shifted by ad reads.

Related: the Qullamaggie CWT #212 interview (2021) is filed under `data/qullamaggie/videos/2021-03-01_K0F73Sq90j0/`
because that KB is organised by trader.

## Videos

| video | date | verdict |
|---|---|---|
| [How a 50-Year Veteran Thinks About Risk Management · Peter Brandt](videos/2026-08-05_bIi6YzPt9bE/notes.md) | 2026-08-05 | **3/5.** The most codable risk/entry spec in any KB: fixed 60–70 bp risk, no pyramiding, 8–14-week rectangles ≤ 15% tall, ADX(14) < 12, buy-stop at +0.5 × ATR(30), partials after 1–2 weeks, 8-day-MA trail. He's candid about losing (19 of 21 losers; average loss 17 bp). ✅ Fixed small risk and the "15% of trades = 85% of profits" shape both match our ledger. ❌ His central claim ("identification is ~5% of the edge, the rest is risk management") is close to **backwards** on our data: no management rule manufactures edge, and exclusion is the lever. ❌ Partials and fast trails point where our profit-lock study measured cost. Weekly futures ≠ daily equities throughout |

## Cross-KB notes

- Brandt's **19-of-21 losing streak** is P ≈ 0.0006 for independent trades at a 45% win rate. Streaks like
  that are evidence of **regime clustering**, which is the same thing our breakout book shows
  (month-weighted ≈ 0 vs trade-weighted +0.45R). Trade counts overstate effective n.
- His **ADX < 12 compression gate** is the same family as Deepvue's RMV (`data/deepvue/`). Test them together.
