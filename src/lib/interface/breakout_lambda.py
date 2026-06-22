"""
AWS Lambda handler for the daily preferred-ticker breakout scan.

Reads the ticker universe from S3, runs the Luk/Qullamaggie EOD screen
(Stage 2 + EMA stack + ADR + dollar-volume + tight-base pivot + breakout volume
confirmation), and writes the text report + bridge artifacts back to S3.

Triggered by EventBridge on a weekday after-close schedule.

Environment:
  TRADIER_API_KEY    (required)  Tradier token
  BREAKOUT_BUCKET    S3 bucket          (default: gmerton-stock-data)
  BREAKOUT_PREFIX    S3 key prefix      (default: breakouts)
  BREAKOUT_TICKERS_KEY  ticker-list key (default: <prefix>/preferred_tickers.txt)

Packaging: pandas/numpy come from the AWS-managed SDK-for-pandas layer; only
aiohttp is bundled in the zip. boto3 is provided by the Lambda runtime.

Writes:
  <prefix>/eod_<YYYY-MM-DD>.txt   per-day report (archive)
  <prefix>/eod_latest.txt         most recent report
  <prefix>/monitor_latest.json    intraday-monitor CONFIG bridge
  <prefix>/eod_latest.json        full structured results
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timezone, datetime
from typing import Any, Dict, List

import boto3

from lib.interface.breakout_artifacts import buckets as derive_buckets
from lib.interface.breakout_artifacts import monitor_config
from lib.interface.premarket_watchlist import format_eod_output, run_eod_scan
from lib.tradier.tradier_client_wrapper import TradierClient

_s3 = boto3.client("s3")

BUCKET = os.environ.get("BREAKOUT_BUCKET", "gmerton-stock-data")
PREFIX = os.environ.get("BREAKOUT_PREFIX", "breakouts").strip("/")
TICKERS_KEY = os.environ.get("BREAKOUT_TICKERS_KEY", f"{PREFIX}/preferred_tickers.txt")


def _load_tickers() -> List[str]:
    obj = _s3.get_object(Bucket=BUCKET, Key=TICKERS_KEY)
    text = obj["Body"].read().decode("utf-8")
    return [ln.strip().upper() for ln in text.splitlines() if ln.strip()]


def _put(key: str, body: str, content_type: str) -> None:
    _s3.put_object(
        Bucket=BUCKET, Key=f"{PREFIX}/{key}",
        Body=body.encode("utf-8"), ContentType=content_type,
    )


async def _scan(api_key: str, tickers: List[str]) -> List[Dict[str, Any]]:
    async with TradierClient(api_key=api_key) as client:
        return await run_eod_scan(client, tickers)


def lambda_handler(event, context):
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        raise RuntimeError("TRADIER_API_KEY env var not set on the function")

    tickers = _load_tickers()
    results = asyncio.run(_scan(api_key, tickers))

    as_of = date.today()
    report = format_eod_output(results, as_of)
    monitor = monitor_config(results)
    bk = derive_buckets(results)

    confirmed = [r["ticker"] for r in bk["confirmed"]]
    structured = {
        "as_of": str(as_of),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_tickers_scanned": len(tickers),
        "n_candidates": len(results),
        "confirmed_breakouts": confirmed,
        "monitor_list": list(monitor.keys()),
        "results": results,
    }

    _put(f"eod_{as_of}.txt", report, "text/plain")
    _put("eod_latest.txt", report, "text/plain")
    _put("monitor_latest.json", json.dumps(monitor, indent=2), "application/json")
    _put("eod_latest.json", json.dumps(structured, indent=2), "application/json")

    summary = {
        "scanned": len(tickers),
        "candidates": len(results),
        "confirmed_breakouts": confirmed,
        "monitor_count": len(monitor),
        "output": f"s3://{BUCKET}/{PREFIX}/eod_{as_of}.txt",
    }
    print(json.dumps(summary))
    return {"statusCode": 200, "body": json.dumps(summary)}
