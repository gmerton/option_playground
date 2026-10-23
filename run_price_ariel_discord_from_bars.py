#!/usr/bin/env python3
"""Price the Ariel Discord actions he posted without a number ("AMD closed", "stopped on CAR") from 1-min bars.

For every entry/add/trim/exit/stopped_out/short/cover/reentry row with price null, in both channels:
  price_bar = OPEN of the 1-min bar of the minute the message was posted (ET), i.e. the price at the moment he
              posted; the fill was at or just before it. If that minute has no bar (thin pre/post market), the
              CLOSE of the last bar in the preceding 15 minutes; otherwise unpriced.
Bars: data/cache/intraday_1min/<SYM>_<date>.parquet when the post is in regular hours and the name did not split
in the sample (that cache is split-adjusted and regular-session only); everything else from Polygon minute aggs,
adjusted=false, extended hours included, cached per window in data/cache/polygon_1min_raw/.
Writes data/ariel_hernandez/discord/{,short_}bar_prices.csv (msg_id, ticker, action, price_bar, bar_time, method),
which build_ariel_discord_ledger.py folds in with price_source = "bar".

Free-tier Polygon key: 5 calls/min -> --sleep 12.5. Resumable: cached windows are reused.
"""
from __future__ import annotations
import argparse, os, time
from pathlib import Path
import pandas as pd, requests

REPO = Path(__file__).resolve().parent
D = REPO / "data" / "ariel_hernandez" / "discord"
CACHE_REG = REPO / "data" / "cache" / "intraday_1min"
CACHE_RAW = REPO / "data" / "cache" / "polygon_1min_raw"
PRICED = ["entry", "reentry", "short", "add", "trim", "exit", "stopped_out", "cover"]
SPLIT_NAMES = {"CRWD", "NOW", "SNXX", "SQQQ", "TQQQ", "ETHU", "XXRP"}
WINDOW_DAYS = 55


def fetch_raw(sym, start, end, key, sleep):
    f = CACHE_RAW / f"{sym}_{start}_{end}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{start}/{end}"
           f"?adjusted=false&sort=asc&limit=50000&apiKey={key}")
    rows = []
    while url:
        for attempt in range(5):
            r = requests.get(url, timeout=60)
            if r.status_code != 429:
                break
            time.sleep(15 * (attempt + 1))
        j = r.json()
        rows += j.get("results", []) or []
        url = j.get("next_url")
        url = f"{url}&apiKey={key}" if url else None
        time.sleep(sleep)
    df = pd.DataFrame(rows)
    if len(df):
        t = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
        df = pd.DataFrame({"time": t, "open": df["o"], "close": df["c"]})
    else:
        df = pd.DataFrame(columns=["time", "open", "close"])
    df.to_parquet(f, index=False)
    print(f"  fetched {sym} {start}..{end}: {len(df)} bars", flush=True)
    return df


def price_at(bars, ts):
    minute = ts.floor("min")
    hit = bars[bars.time == minute]
    if len(hit):
        return float(hit.open.iloc[0]), minute, "bar_open_at_post"
    prior = bars[(bars.time < minute) & (bars.time >= minute - pd.Timedelta(minutes=15))]
    if len(prior):
        return float(prior.close.iloc[-1]), prior.time.iloc[-1], "last_close_within_15m"
    return None, None, "no_bar"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=float, default=12.5)
    a = ap.parse_args()
    key = os.environ["POLYGON_API_KEY"]
    CACHE_RAW.mkdir(parents=True, exist_ok=True)
    need = {}
    for P in ("", "short_"):
        x = pd.read_csv(D / f"{P}actions.csv", dtype={"msg_ids": str})
        # rows with no usable number: never stated, blanked by an override, or priced by an earlier run of this script
        unpriced = x.price.isna() | (x.price_source == "bar") if "price_source" in x else x.price.isna()
        x = x[unpriced & x.action.isin(PRICED) & (x.ticker != "?")].copy()
        x["msg_id"] = x.msg_ids.str.split().str[0]
        x["ts"] = pd.to_datetime(x.ts_et)
        need[P] = x
    allx = pd.concat(need.values())
    hhmm = allx.ts.dt.strftime("%H:%M")
    allx["use_cache"] = [
        (hm >= "09:30" and hm < "16:00" and t not in SPLIT_NAMES
         and (CACHE_REG / f"{t}_{d:%Y-%m-%d}.parquet").exists())
        for t, d, hm in zip(allx.ticker, allx.ts, hhmm)]
    # Polygon windows per ticker for the rows the cache cannot serve
    windows = {}
    for sym, g in allx[~allx.use_cache].groupby("ticker"):
        days = sorted(g.ts.dt.normalize().unique())
        start = prev = days[0]
        for d in days[1:]:
            if (d - start).days > WINDOW_DAYS:
                windows.setdefault(sym, []).append((start, prev))
                start = d
            prev = d
        windows.setdefault(sym, []).append((start, prev))
    n = sum(map(len, windows.values()))
    print(f"{len(allx)} unpriced rows; {int(allx.use_cache.sum())} from the regular-hours cache; {n} Polygon windows",
          flush=True)
    raw = {}
    for i, (sym, ws) in enumerate(sorted(windows.items()), 1):
        raw[sym] = pd.concat([fetch_raw(sym, f"{s:%Y-%m-%d}", f"{e:%Y-%m-%d}", key, a.sleep) for s, e in ws])
        print(f"[{i}/{len(windows)}] {sym}", flush=True)
    for P, x in need.items():
        out = []
        for r in x.itertuples():
            ts = r.ts
            hm = ts.strftime("%H:%M")
            cf = CACHE_REG / f"{r.ticker}_{ts:%Y-%m-%d}.parquet"
            if hm >= "09:30" and hm < "16:00" and r.ticker not in SPLIT_NAMES and cf.exists():
                b = pd.read_parquet(cf).reset_index()[["time", "open", "close"]]
                src = "intraday_1min cache"
            else:
                b = raw.get(r.ticker, pd.DataFrame(columns=["time", "open", "close"]))
                src = "polygon unadjusted"
            px, bt, how = price_at(b, ts)
            out.append({"msg_id": r.msg_id, "ticker": r.ticker, "action": r.action, "ts_et": r.ts_et,
                        "price_bar": round(px, 4) if px is not None else None, "bar_time": bt,
                        "method": how, "source": src})
        o = pd.DataFrame(out)
        o.to_csv(D / f"{P}bar_prices.csv", index=False)
        print(f"{P or 'long_'}bar_prices.csv: {o.price_bar.notna().sum()}/{len(o)} priced; "
              f"{o.method.value_counts().to_dict()}", flush=True)


if __name__ == "__main__":
    main()
