#!/usr/bin/env bash
# Morning journal chain (2026-09-18): Flex pull -> review rows -> process grades -> pages -> publish.
# Stops at the first failure. Retries the Flex pull while IBKR says "Statement is not available"
# (the statement for the prior session is usually ready by ~9pm PT; 8am PT is a safe run time).
#
# Scheduled by launchd: ~/Library/LaunchAgents/com.gmerton.morning-journal.plist (08:00 daily).
# Manual: ./morning_journal.sh            (add --no-deploy to skip the CloudFront publish,
#                                          --charts to render the per-trade charts via Tradier)
# Needs ~/.trading_env (IBKR_FLEX_TOKEN, MYSQL_PASSWORD, TRADIER_API_KEY); AWS profile clarinut-gmerton.
set -uo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1090
source "$HOME/.trading_env" 2>/dev/null || true
export PYTHONPATH=src:. AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}"
PY=.venv/bin/python3; LOG=data/journal/logs; mkdir -p "$LOG"; TS=$(date +%F_%H%M); OUT="$LOG/morning_$TS.log"
DEPLOY=1; CHARTS="--no-charts"
for arg in "$@"; do case "$arg" in --no-deploy) DEPLOY=0;; --charts) CHARTS="";; esac; done
exec > >(tee -a "$OUT") 2>&1
echo "== morning journal $(date) =="

# Weekend / holiday guard: skip if no session in the last 3 days would be new (the pull is idempotent anyway).
if [ "$(date +%u)" -ge 6 ]; then echo "weekend -- nothing to pull"; exit 0; fi

# 1. Flex pull (retry up to 6 x 10 min while IBKR has not generated the statement yet)
for i in 1 2 3 4 5 6; do
  if $PY run_daily_journal.py --query-id 1605053 2>&1 | grep -v -i "warn" | tee /tmp/morning_flex.txt | tail -4; then
    if grep -q "Statement is not available\|Too many requests" /tmp/morning_flex.txt; then
      echo "  Flex not ready (attempt $i/6); waiting 10 min"; sleep 600; continue
    fi
    break
  else
    if grep -q "Statement is not available\|Too many requests" /tmp/morning_flex.txt; then echo "  Flex not ready (attempt $i/6); waiting 10 min"; sleep 600; continue; fi
    echo "!! Flex pull failed"; exit 1
  fi
done
grep -q "Wrote data/journal/" /tmp/morning_flex.txt || { echo "!! no journal written (Flex statement still unavailable after 1h)"; exit 1; }
DAY=$(grep -o "data/journal/[0-9-]*\.md" /tmp/morning_flex.txt | head -1 | grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}")
echo "-- journal day: $DAY"

# 2. review rows for that session (idempotent; attaches staged trader notes)
$PY run_build_reviews.py --since "$DAY" --until "$DAY" 2>&1 | grep -v -i "warn" | tail -4 || { echo "!! review builder failed"; exit 1; }

# 3. process grade (rubric entry grades + the session report card)
$PY run_journal_grades.py --since "$DAY" 2>&1 | grep -v -i "warn" | grep -E "^ *$DAY|grade" | head -3 || { echo "!! grades failed"; exit 1; }

# 4. pages
$PY run_trade_review_pages.py $CHARTS 2>&1 | grep -v -i "warn" | grep "Wrote" || { echo "!! page build failed"; exit 1; }

# 5. publish
if [ "$DEPLOY" = 1 ]; then
  ./deploy_trade_journal.sh 2>&1 | grep -v -i "warn" | tail -2 || { echo "!! deploy failed"; exit 1; }
fi
# 6. back up the git-ignored journal parquet cache (its S3 bucket is the only copy; 2026-09-24: last manual push was
#    2026-09-02). Non-fatal: a failed backup never blocks the journal.
./sync_journal_cache.sh push 2>&1 | grep -v -i "warn" | tail -1 || echo "  (journal cache backup failed -- run ./sync_journal_cache.sh push by hand)"
echo "== done $(date) =="
