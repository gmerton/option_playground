"""Build Ariel Hernandez's #live-long-ideas trade ledger from the Discord extract.

Inputs  (data/ariel_hernandez/discord/):
  live_long_ideas_messages.json   every channel message, ET timestamps (scraped 2026-10-22 from the rendered page)
  extract_{1..4}.jsonl            one row per action, hand-read per EXTRACTION_BRIEF.md
  short channel (--channel short): live_short_ideas_messages.json, short_extract_*.jsonl -> short_actions.csv,
  short_trades.csv, short_price_fixes.csv
Outputs:
  actions.csv                     all action rows, validated (quote is a substring of its first message)
  trades.csv                      actions stitched into round trips per (ticker, direction)

Stitching: a trade ends without a posted exit (status stale / exit_unposted) after >30 days with no action, or when
he posts a fresh entry/short on a later day while the ledger still shows it open. a position opens on entry/reentry/short when flat (an "entry" while open is counted as an add);
add raises the tranche count; trim multiplies the remaining fraction by (1 - fraction_of_position) when known;
exit/stopped_out/cover close it unless the row says position_after == "partial". Exit price = the
fraction-weighted average of stated sell prices where fractions are known, else the last stated sell price.
ret_stated = the stated-price return (sign-adjusted for shorts), clean trades only, unweighted by size. Trades that
cannot be scored or are not his call are kept in trades.csv with an exclude_reason; trades_clean.csv drops them.
"""
import argparse
import csv
import json
from pathlib import Path

import pandas as pd

D = Path("data/ariel_hernandez/discord")
OPEN = {"entry", "reentry", "short"}
SELL = {"trim", "exit", "stopped_out", "cover"}
STALE_DAYS = 30
# split dates in the sample (yfinance split history); a trade spanning one has stated prices on two bases
SPLITS = {"CRWD": ["2026-07-02"], "NOW": ["2025-12-18"], "SNXX": ["2026-06-03"], "SQQQ": ["2025-11-20"],
          "TQQQ": ["2025-11-20"], "ETHU": ["2025-04-09"], "XXRP": ["2026-06-29"]}
# trades that are not his channel call as posted (ticker, channel) -> reason
EXCLUDE = {("SI", "short"): "silver futures hedge, not an equity call",
           ("WDC", "short"): "posted as a short for his wife's account",
           ("VLO", "short"): "reads as a long posted in the short channel"}

ap = argparse.ArgumentParser()
ap.add_argument("--channel", choices=["long", "short"], default="long")
CH = ap.parse_args().channel
P = "" if CH == "long" else "short_"  # file prefix

msgs = {m["msg_id"]: m for m in json.load(open(D / f"live_{CH}_ideas_messages.json"))}
rows, bad = [], []
for path in sorted(D.glob(f"{P}extract_*.jsonl")):
    i = int(path.stem.rsplit("_", 1)[1])
    for line in open(path):
        r = json.loads(line)
        m = msgs.get(r["msg_ids"][0])
        if m is None or r["quote"] not in m["text"] or any(x not in msgs for x in r["msg_ids"]):
            bad.append(r)
        r["batch"] = i
        rows.append(r)
rows.sort(key=lambda r: (r["ts_et"], int(r["msg_ids"][0])))

# price typos found by check_ariel_discord_prices.py (stated number kept in price_stated / stop_price_stated)
fixes = {}
if (D / f"{P}price_fixes.csv").exists():
    for f in csv.DictReader(open(D / f"{P}price_fixes.csv")):
        fixes[(f["msg_id"], f["ticker"], f["action"], f["field"])] = float(f["corrected"]) if f["corrected"] else None
# actions posted without a number, priced from the 1-min bar at the post (run_price_ariel_discord_from_bars.py)
barpx = {}
if (D / f"{P}bar_prices.csv").exists():
    for f in csv.DictReader(open(D / f"{P}bar_prices.csv")):
        if f["price_bar"]:
            barpx[(f["msg_id"], f["ticker"], f["action"])] = float(f["price_bar"])
n_fixed = n_bar = 0
for r in rows:
    r["price_source"] = "stated" if r["price"] is not None else ""
    for field in ("price", "stop_price"):
        r[f"{field}_stated"] = r[field]
        k = (r["msg_ids"][0], r["ticker"], r["action"], field)
        if k in fixes:
            r[field] = fixes[k]
            n_fixed += 1
            if field == "price":
                r["price_source"] = "fixed" if r[field] is not None else ""
    k = (r["msg_ids"][0], r["ticker"], r["action"])
    if r["price"] is None and k in barpx:
        r["price"], r["price_source"] = barpx[k], "bar"
        n_bar += 1

seen, dups = set(), 0
dedup = []
for r in rows:
    k = (tuple(r["msg_ids"]), r["ticker"], r["action"])
    if k in seen:
        dups += 1
        continue
    seen.add(k)
    dedup.append(r)
rows = dedup

cols = ["ts_et", "ticker", "underlying", "direction", "action", "price", "price_stated", "price_source", "size_pct", "size_text",
        "fraction_of_position", "stop_text", "stop_price", "stop_price_stated", "setup", "position_after", "confidence",
        "quote", "notes", "msg_ids", "batch"]
with open(D / f"{P}actions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({**r, "msg_ids": " ".join(r["msg_ids"])})

trades, book = [], {}
def status(t):
    return t.get("status") or ("closed" if t["close_ts"] else "open")


for r in rows:
    a = r["action"]
    if a == "watch" or r["ticker"] in ("?", None):
        continue
    key = (r["ticker"], "short" if r["direction"] == "short" else "long")
    t = book.get(key)
    day = r["ts_et"][:10]
    if t is not None:
        # an unposted exit: a long silence, or a fresh open on a later day while the ledger still shows it open
        gap = (pd.Timestamp(day) - pd.Timestamp(t["last_ts"][:10])).days
        if gap > STALE_DAYS or (a in OPEN and day != t["last_ts"][:10]):
            t["status"] = "stale" if gap > STALE_DAYS else "exit_unposted"
            del book[key]
            t = None
    if t is None and (a in OPEN or a == "add"):
        t = book[key] = {"ticker": key[0], "underlying": r.get("underlying"), "direction": key[1],
                         "open_ts": r["ts_et"], "entry_price": r["price"], "size_pct": r["size_pct"],
                         "size_text": r["size_text"], "stop_text": r["stop_text"], "stop_price": r["stop_price"],
                         "setup": r["setup"], "adds": 0, "trims": 0, "remaining": 1.0, "remaining_known": True,
                         "sells": [], "close_ts": "", "close_action": "", "inferred_rows": 0,
                         "opened_without_entry": a == "add", "msg_ids": [], "notes": []}
        trades.append(t)
    elif t is None:
        # a sell/stop with no open position on record (entry predates the channel or was never posted)
        if a in SELL:
            trades.append({"ticker": key[0], "underlying": r.get("underlying"), "direction": key[1],
                           "open_ts": "", "entry_price": None, "size_pct": None, "size_text": "",
                           "stop_text": "", "stop_price": None, "setup": "", "adds": 0, "trims": int(a == "trim"),
                           "remaining": None, "remaining_known": False, "sells": [(r["fraction_of_position"], r["price"])],
                           "close_ts": r["ts_et"], "close_action": a, "inferred_rows": int(r["confidence"] == "inferred"),
                           "opened_without_entry": True, "msg_ids": r["msg_ids"][:1], "status": "orphan_sell",
                           "notes": [r["notes"] or ""]})
        continue
    else:
        if a in OPEN or a == "add":
            t["adds"] += 1
        elif a == "stop":
            t["stop_text"], t["stop_price"] = r["stop_text"] or t["stop_text"], r["stop_price"] or t["stop_price"]
    t["msg_ids"].append(r["msg_ids"][0])
    t["notes"].append(r["notes"] or "")
    t["last_ts"] = r["ts_et"]
    t["inferred_rows"] += r["confidence"] == "inferred"
    if a in SELL:
        fr = r["fraction_of_position"]
        closes = a != "trim" and r["position_after"] != "partial"
        if closes:
            fr = 1.0 if fr is None else fr
        t["sells"].append((fr * t["remaining"] if fr is not None and t["remaining_known"] else None, r["price"]))
        if a == "trim":
            t["trims"] += 1
            if fr is None:
                t["remaining_known"] = False
            else:
                t["remaining"] *= 1 - fr
        if closes:
            t["close_ts"], t["close_action"] = r["ts_et"], a
            del book[key]


def exclude_reason(t, exit_px):
    st = status(t)
    if st != "closed":
        return {"open": "exit not posted yet", "stale": f"no action for >{STALE_DAYS}d: exit never posted",
                "exit_unposted": "re-opened on a later day: earlier exit never posted",
                "orphan_sell": "exit with no posted entry"}[st]
    if t["opened_without_entry"]:
        return "first posted action is an add: entry never posted"
    if t["entry_price"] is None or pd.isna(t["entry_price"]):
        return "no entry price"
    if exit_px is None:
        return "no exit price"
    for d in SPLITS.get(t["ticker"], []):
        if t["open_ts"][:10] < d <= t["close_ts"][:10]:
            return f"split {d} inside the trade: stated prices are on two bases"
    for k, why in EXCLUDE.items():
        if t["ticker"] == k[0] and CH == k[1]:
            return why
    return ""


out_cols = ["ticker", "underlying", "direction", "open_ts", "entry_price", "size_pct", "size_text", "stop_text",
            "stop_price", "setup", "adds", "trims", "close_ts", "close_action", "exit_price_last",
            "exit_price_weighted", "sold_fraction_priced", "ret_stated", "status", "exclude_reason", "inferred_rows",
            "opened_without_entry", "n_actions", "msg_ids"]
out = []
for t in trades:
    priced = [(fr, p) for fr, p in t["sells"] if fr is not None and p is not None]
    wsum = sum(fr for fr, _ in priced)
    last = next((p for _, p in reversed(t["sells"]) if p is not None), None)
    wavg = round(sum(fr * p for fr, p in priced) / wsum, 4) if wsum else None
    exit_px = wavg if wavg is not None else last
    why = exclude_reason(t, exit_px)
    ret = None
    if not why:
        ret = round((exit_px / t["entry_price"] - 1) * (1 if t["direction"] == "long" else -1), 4)
    out.append({**{k: t.get(k) for k in out_cols if k in t}, "exit_price_last": last, "exit_price_weighted": wavg,
                "sold_fraction_priced": round(wsum, 3) if priced else None, "ret_stated": ret, "status": status(t),
                "exclude_reason": why, "n_actions": len(t["msg_ids"]), "msg_ids": " ".join(t["msg_ids"])})
for name, keep in ((f"{P}trades.csv", lambda o: True), (f"{P}trades_clean.csv", lambda o: not o["exclude_reason"])):
    with open(D / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        w.writerows(o for o in out if keep(o))

from collections import Counter
print(f"actions {len(rows)} (quote failures {len(bad)}, duplicate rows dropped {dups}, price fixes applied {n_fixed}, priced from bars {n_bar})")
print(f"trades {len(out)}: {dict(Counter(o['status'] for o in out))}")
print(f"clean {sum(not o['exclude_reason'] for o in out)}; excluded:")
for why, n in Counter(o["exclude_reason"] for o in out if o["exclude_reason"]).most_common():
    print(f"  {n:4d}  {why}")
for r in bad:
    print("BAD", r["msg_ids"][0], r["quote"][:60])
