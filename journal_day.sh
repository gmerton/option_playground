#!/usr/bin/env bash
# One command for a session's journal: Flex pull -> rubric review rows -> process grade -> review pages -> site deploy.
# Run the morning after the session (Flex NAV data lands ~1 session behind; see run_daily_journal.py).
# Requires in the environment: IBKR_FLEX_TOKEN, MYSQL_PASSWORD, TRADIER_API_KEY, AWS_PROFILE (for the deploy).
#   ./journal_day.sh                 latest available session
#   ./journal_day.sh --date 20260918 backfill a specific session (YYYYMMDD, passed to run_daily_journal.py)
#   ./journal_day.sh --force         overwrite an existing day's markdown (loses hand-written notes)
#   ./journal_day.sh --no-deploy     stop after the pages (nothing pushed to S3/CloudFront)
#   ./journal_day.sh --no-charts     pages without Tradier chart data (fast)
set -euo pipefail
cd "$(dirname "$0")"
# secrets live in ~/.trading_env; load them like morning_journal.sh / start_alerts.sh / daily_desk.sh do
# (2026-09-24 housekeeping: this was the one orchestrator that depended on the launching shell)
if [ -f "$HOME/.trading_env" ]; then set +u; source "$HOME/.trading_env"; set -u; fi
export AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}"
PY=.venv/bin/python3; export PYTHONPATH=src:.
PULL_ARGS=(); PAGE_ARGS=(); DEPLOY=1
while [ $# -gt 0 ]; do
  case "$1" in
    --date)      PULL_ARGS+=(--date "$2"); shift 2 ;;
    --force)     PULL_ARGS+=(--force); shift ;;
    --no-deploy) DEPLOY=0; shift ;;
    --no-charts) PAGE_ARGS+=(--no-charts); shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
for v in IBKR_FLEX_TOKEN MYSQL_PASSWORD TRADIER_API_KEY; do
  [ -n "${!v:-}" ] || { echo "missing \$$v" >&2; exit 2; }
done
quiet() { grep -v "UserWarning" | grep -v "pd.read_sql" || true; }

echo "== 1/5 Flex pull (run_daily_journal.py)"
PULL_OUT=$($PY run_daily_journal.py ${PULL_ARGS[@]+"${PULL_ARGS[@]}"} 2>&1 | quiet)
echo "$PULL_OUT" | tail -4
SESSION=$(echo "$PULL_OUT" | sed -n 's/.*NAV row for \([0-9-]*\).*/\1/p' | tail -1)
if [ -z "$SESSION" ]; then
  # Pull refused to overwrite (no --force) or printed nothing usable: fall back to the newest journal file.
  SESSION=$(ls data/journal/[0-9]*-[0-9]*-[0-9]*.md | sed 's#.*/##; s#\.md##' | sort | tail -1)
  echo "  (session date taken from the newest journal file: $SESSION)"
fi

echo; echo "== 2/5 rubric review rows for $SESSION (run_build_reviews.py)"
$PY run_build_reviews.py --since "$SESSION" --until "$SESSION" 2>&1 | quiet | tail -4

echo; echo "== 3/5 process report card (run_journal_grades.py)"
$PY run_journal_grades.py 2>&1 | quiet | tail -12

echo; echo "== 4/5 review pages (run_trade_review_pages.py)"
$PY run_trade_review_pages.py ${PAGE_ARGS[@]+"${PAGE_ARGS[@]}"} 2>&1 | quiet | tail -2

if [ "$DEPLOY" = 1 ]; then
  echo; echo "== 5/5 deploy (deploy_trade_journal.sh)"
  ./deploy_trade_journal.sh 2>&1 | grep -v "^upload:\|^Completed" | tail -8
else
  echo; echo "== 5/5 deploy skipped (--no-deploy)"
fi
echo; echo "journal: data/journal/$SESSION.md   grid: data/journal/days/$SESSION.html   grades: data/studies/journal_process_grades.md"
