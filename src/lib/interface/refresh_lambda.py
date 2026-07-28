"""
Nightly preferred-list refresh — Lambda handler.

Runs Mon-Fri evenings (EventBridge, after Polygon publishes the session's
grouped-daily). One run:

  1. Download the day-matrix parquet from S3 -> /tmp.
  2. Incremental top-up (steady state: ONE Polygon call for the session).
  3. Upload the refreshed parquet back (always — even if the screen is skipped).
  4. Append the newly fetched sessions to silver.equity_daily (Iceberg,
     idempotent delete+insert).
  5. Trend Template screen -> union manual adds -> safety rails -> diff ->
     write preferred_tickers.txt + history archive + report to S3.

The breakout-scan Lambda reads the refreshed list at the next 4:15pm PT run.

Env: POLYGON_API_KEY, BREAKOUT_BUCKET (gmerton-stock-data), BREAKOUT_PREFIX
(breakouts). Timezone note: the schedule fires ~03:30 UTC = the prior PT
evening; UTC "today" has no data yet, which the today-exception excuses.
"""
from __future__ import annotations

import json
import os
from datetime import date

import boto3

from lib.minervini.scan import build_table, load_cache, pull_matrices, save_cache, screen

BUCKET = os.environ.get("BREAKOUT_BUCKET", "gmerton-stock-data")
PREFIX = os.environ.get("BREAKOUT_PREFIX", "breakouts")
CACHE_KEY = f"{PREFIX}/minervini_matrix.parquet"
UNIVERSE_KEY = f"{PREFIX}/polygon_cs_tickers.txt"
LIST_KEY = f"{PREFIX}/preferred_tickers.txt"
MANUAL_KEY = f"{PREFIX}/preferred_manual_adds.txt"
TMP = "/tmp/minervini_matrix.parquet"

RS_MIN = 70.0
ADDV_MIN = 200e6
LOOKBACK_DAYS = 430
PACE = 12.5
MAX_DAYS_PER_RUN = 55          # ~12 min at PACE; leftover days roll to next night
MIN_LIST_SIZE = 20             # refuse to overwrite on suspicious output


def _get_text(s3, key):
    try:
        return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
    except s3.exceptions.NoSuchKey:
        return ""


def _put_text(s3, key, text):
    s3.put_object(Bucket=BUCKET, Key=key, Body=text.encode())


def lambda_handler(event, context):
    def log(msg):
        print(msg, flush=True)

    stage = (event or {}).get("debug_stage")
    log("stage: enter")
    s3 = boto3.client("s3")
    if stage == "enter":
        return {"ok": "enter"}

    # 1. cache + universe down
    s3.download_file(BUCKET, CACHE_KEY, TMP)
    log(f"stage: downloaded {os.path.getsize(TMP)} bytes")
    if stage == "download":
        return {"ok": "download"}

    prior = load_cache(TMP)
    log(f"stage: cache loaded {prior[0].shape}")
    if stage == "load":
        return {"ok": "load", "shape": list(prior[0].shape)}

    universe = {ln.strip() for ln in _get_text(s3, UNIVERSE_KEY).splitlines() if ln.strip()}
    if not universe:
        raise RuntimeError(f"empty universe file s3://{BUCKET}/{UNIVERSE_KEY}")
    log(f"stage: universe {len(universe)}")

    from polygon import RESTClient
    log("stage: polygon imported")
    if stage == "polygon":
        return {"ok": "polygon"}

    # 2. incremental top-up
    client = RESTClient(os.environ["POLYGON_API_KEY"])
    frames, failed, long_rows = pull_matrices(
        client, universe, LOOKBACK_DAYS, PACE, prior=prior,
        max_days=MAX_DAYS_PER_RUN, log=log)

    # 3. refreshed cache up (always — pulled days must never be lost)
    save_cache(frames, TMP)
    s3.upload_file(TMP, BUCKET, CACHE_KEY)

    # 4. lakehouse append (best-effort: a failure here must not block the list).
    # Dead-letter protocol: rows that fail to append are parked as parquet under
    # equity_daily_pending/ and retried on every subsequent run — a day pulled
    # into the cache is otherwise never re-fetched, so losing its append loses
    # its open/volume/vwap forever.
    import pandas as pd
    equity_rows = 0
    equity_err = None
    pend_prefix = f"{PREFIX}/equity_daily_pending/"
    pending_keys = [o["Key"] for o in
                    s3.list_objects_v2(Bucket=BUCKET, Prefix=pend_prefix).get("Contents", [])]
    batches = []
    for k in pending_keys:
        s3.download_file(BUCKET, k, "/tmp/pending.parquet")
        batches.append(pd.read_parquet("/tmp/pending.parquet"))
        log(f"replaying dead-letter {k}")
    if len(long_rows):
        batches.append(long_rows)
    if batches:
        all_rows = pd.concat(batches, ignore_index=True).drop_duplicates(
            subset=["trade_date", "ticker"], keep="last")
        try:
            from lib.minervini.equity_daily import append_rows
            equity_rows = append_rows(all_rows, log=log)
            for k in pending_keys:
                s3.delete_object(Bucket=BUCKET, Key=k)
        except Exception as e:
            equity_err = f"{type(e).__name__}: {e}"[:300]
            log(f"equity_daily append FAILED (non-fatal): {equity_err}")
            all_rows.to_parquet("/tmp/pending_out.parquet", index=False)
            dl_key = f"{pend_prefix}rows_{date.today().isoformat()}.parquet"
            s3.upload_file("/tmp/pending_out.parquet", BUCKET, dl_key)
            for k in pending_keys:
                if k != dl_key:
                    s3.delete_object(Bucket=BUCKET, Key=k)
            log(f"dead-lettered {len(all_rows)} rows to {dl_key}")

    # Tolerate a missing UTC-today AND a not-yet-published latest session
    # (Polygon free tier publishes the day's grouped bars late in the evening PT;
    # if it's late, screen through the prior session rather than skip — the next
    # night's run pulls the stragglers). Older missing days still block.
    from lib.minervini.scan import trading_dates
    # Two newest trading dates: at any UTC evening hour those are "UTC today"
    # (not yet traded) and the just-closed PT session (possibly unpublished).
    excusable = {date.today().isoformat(), *trading_dates(LOOKBACK_DAYS)[:2]}
    excused = sorted(set(failed) & excusable)
    failed = [d for d in failed if d not in excusable]
    if excused:
        log(f"excused not-yet-published session(s): {excused}")
    if failed:
        msg = f"{len(failed)} days still missing (e.g. {sorted(failed)[:5]}) — screen skipped, list untouched"
        log(msg)
        return {"status": "incomplete", "detail": msg, "equity_rows": equity_rows}

    # 5. screen -> list
    close, high, low, dolvol = frames
    t = build_table(close, high, low, dolvol, slope_days=20)
    out = screen(t, RS_MIN, ADDV_MIN)
    passing = sorted(out[out.pass_all].index)
    if len(passing) < MIN_LIST_SIZE:
        msg = f"only {len(passing)} passers — refusing to overwrite the list"
        log(msg)
        return {"status": "refused", "detail": msg, "equity_rows": equity_rows}

    manual = sorted({ln.strip().upper() for ln in _get_text(s3, MANUAL_KEY).splitlines() if ln.strip()})
    new = sorted(set(passing) | set(manual))
    old = sorted({ln.strip().upper() for ln in _get_text(s3, LIST_KEY).splitlines() if ln.strip()})
    adds = [x for x in new if x not in old]
    drops = [x for x in old if x not in new]

    asof = frames[0].index.max().date().isoformat()
    if old:
        _put_text(s3, f"{PREFIX}/preferred_history/preferred_{asof}_prev.txt", "\n".join(old) + "\n")
    _put_text(s3, LIST_KEY, "\n".join(new) + "\n")

    report = (f"preferred-list refresh — data through {asof}\n"
              f"template passers: {len(passing)}  manual: {len(manual)}  list: {len(new)}\n"
              f"vs previous ({len(old)}): +{len(adds)} / -{len(drops)}\n"
              f"ADDS:  {', '.join(adds) or '(none)'}\nDROPS: {', '.join(drops) or '(none)'}\n"
              f"equity_daily rows appended: {equity_rows}"
              + (f"  (append error: {equity_err})" if equity_err else "") + "\n")
    _put_text(s3, f"{PREFIX}/refresh_latest.txt", report)
    log(report)

    return {"status": "ok", "asof": asof, "list": len(new), "adds": len(adds),
            "drops": len(drops), "equity_rows": equity_rows, "equity_err": equity_err}
