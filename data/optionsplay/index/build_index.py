"""Build video_index.csv for the OptionsPlay channel from the raw yt-dlp listings.

Inputs (flat-listed with yt-dlp, metadata only, 2026-09-24):
  playlists_raw.tsv          26 playlists of @OptionsPlay
  playlist_videos_raw.csv    every playlist entry
  channel_tabs_raw.tsv       the channel's videos / streams / shorts tabs (newest first)

Score is a triage heuristic only (see README.md). Run from the repo root:
  .venv/bin/python3 data/optionsplay/index/build_index.py
"""
import re
from pathlib import Path

import pandas as pd

D = Path(__file__).parent
REVIEWED = {"pQlGgcyrUoQ", "YfrZT_kTo_4", "iXOULnIGEKk", "lV8Jkl37h4M",
            # Tier 1, reviewed 2026-09-24
            "bk9Co7V6AI4", "gUOWa-i4R70", "wG0yvxmDuXI", "jLUPi1Im9cw", "VSLc-kHxFlw", "n1T3PUyS4uQ",
            "Uvk_no85Yj4", "2VzqGw2_ZFs", "5IvhBIQVujs", "m2-bo0kxMu0", "p477UMpfVxI"}

# (points, regex on the title) -- tied to what the ledger can check
RULES = [
    (4, r"sosnoff"),
    (4, r"credit spread|premium|filters?\b|iron condor|strangle|straddle"),
    (3, r"sell(ing)? (put|option)|cash.secured|wheel|covered call|income"),
    (3, r"earnings"),
    (3, r"0 ?dte|butterfl|gamma"),
    (3, r"backtest|we found|data|statistic|probabilit|edge"),
    (3, r"volatil|\biv\b|vol\b"),
    (3, r"liquidity|market maker|fill price|order flow"),
    (3, r"breakout|trend following|leading stocks|winners|adjust|manag|roll|losing"),
    (2, r"hedg|protect|index option|nasdaq-100|leaps?|calendar|diagonal|debit"),
    (2, r"screen|find(ing)? (the|your)|worth trading|choose|optimal"),
    (-3, r"market (outlook|today|movers|overview|review)|outlook|fed\b|inflation|election|tariff|war\b|"
         r"stagflation|oil|macro|private credit|trillion|recession"),
    (-3, r"chatgpt|grok|\bai\b|automated"),
    (-3, r"walkthrough|tutorial|platform|tools? & services|integration|dashboard|thinkorswim|fidelity|paper trading"),
    (-3, r"beginner|101|crash course|explained|basics|greeks|introduction|psychology|mindset|meme|bitcoin"),
    (-2, r"trade ideas|growth lab|ideas (worth|from)|setups? to watch|stocks to watch|in the money"),
]


def score(title, duration):
    t = str(title).lower()
    s = sum(p for p, rx in RULES if re.search(rx, t))
    if pd.isna(duration) or duration < 120:
        s -= 4
    return s


def main():
    tabs = pd.read_csv(D / "channel_tabs_raw.tsv", sep="\t", header=None,
                       names=["video_id", "title", "duration", "upload_date", "views", "tab"])
    tabs["channel_rank"] = tabs.groupby("tab").cumcount() + 1   # 1 = newest in its tab
    pl = pd.read_csv(D / "playlist_videos_raw.csv")
    pls = pl.groupby("video_id")["playlist"].apply(lambda s: " | ".join(sorted(set(s.dropna()))))

    base = tabs.drop_duplicates("video_id")[["video_id", "title", "duration", "tab", "channel_rank"]]
    extra = (pl[~pl.video_id.isin(base.video_id)].drop_duplicates("video_id")
             [["video_id", "title", "duration"]].assign(tab="playlist_only"))
    idx = pd.concat([base, extra], ignore_index=True)
    idx["playlists"] = idx.video_id.map(pls).fillna("")
    idx["reviewed"] = idx.video_id.isin(REVIEWED)
    idx["score"] = [score(t, d) for t, d in zip(idx.title, idx.duration)]
    idx = idx.sort_values(["score", "tab", "channel_rank"], ascending=[False, True, True])
    idx.to_csv(D / "video_index.csv", index=False)
    print(f"{len(idx)} unique videos; tabs: {idx.tab.value_counts().to_dict()}")
    print(f"score >= 9: {(idx.score >= 9).sum()}, >= 7: {(idx.score >= 7).sum()}, >= 5: {(idx.score >= 5).sum()}")


if __name__ == "__main__":
    main()
