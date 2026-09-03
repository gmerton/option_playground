#!/usr/bin/env bash
# Sync the trade-journal price cache (data/cache/journal_daily/,
# data/cache/journal_intraday/ -- see src/lib/journal/price_cache.py) with S3,
# so it isn't purely local/ephemeral and survives across machines.
#
# The cache is *.parquet, git-ignored (repo blanket rule) -- this bucket is
# its only backup/durability, and lets a fresh checkout on another machine
# skip a cold-cache rebuild by pulling first.
#
# Infra (clarinut account, us-west-2):
#   S3 bucket: gmerton-trade-journal-cache (private, no CloudFront -- accessed
#   directly via S3, not part of the public website in gmerton-trade-journal)
#
# Usage:
#   AWS_PROFILE=clarinut-gmerton ./sync_journal_cache.sh push   # local -> S3 (default)
#   AWS_PROFILE=clarinut-gmerton ./sync_journal_cache.sh pull   # S3 -> local

set -euo pipefail
cd "$(dirname "$0")"

BUCKET=gmerton-trade-journal-cache
DIRECTION="${1:-push}"

case "$DIRECTION" in
  push)
    echo "Pushing local cache -> s3://$BUCKET/ ..."
    aws s3 sync data/cache/journal_daily/    "s3://$BUCKET/journal_daily/"
    aws s3 sync data/cache/journal_intraday/ "s3://$BUCKET/journal_intraday/"
    ;;
  pull)
    echo "Pulling s3://$BUCKET/ -> local cache ..."
    mkdir -p data/cache/journal_daily data/cache/journal_intraday
    aws s3 sync "s3://$BUCKET/journal_daily/"    data/cache/journal_daily/
    aws s3 sync "s3://$BUCKET/journal_intraday/" data/cache/journal_intraday/
    ;;
  *)
    echo "Usage: $0 [push|pull]" >&2
    exit 1
    ;;
esac
echo "Done."
