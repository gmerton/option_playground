#!/bin/bash
#
# Cron/launchd entrypoint for the daily preferred-ticker breakout scan.
#
# Sources the login profile for TRADIER_API_KEY, runs the EOD (or premarket)
# scan, and logs stdout/stderr to data/watchlist/logs/. The scan itself writes
# the report + bridge artifacts to data/watchlist/ (see run_preferred_breakouts.py).
#
# Usage:
#   ./run_eod_scan.sh            # EOD scan (default)
#   ./run_eod_scan.sh premarket  # pre-market gap overlay
#
# Schedule (local PDT; this Mac is Pacific): market close 1pm, settle ~4pm,
# pre-market ~6am. Suggested crontab:
#   15 16 * * 1-5  /Users/gmerton/v2/options_playground/run_eod_scan.sh
#   0  6  * * 1-5  /Users/gmerton/v2/options_playground/run_eod_scan.sh premarket

set -eo pipefail

REPO="/Users/gmerton/v2/options_playground"
LOG_DIR="$REPO/data/watchlist/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
MODE="${1:-eod}"

# Load TRADIER_API_KEY (and other exports) from the login profile. Guarded so a
# noisy profile can't abort the run under `set -e`.
# shellcheck disable=SC1091
[ -f "$HOME/.bash_profile" ] && { source "$HOME/.bash_profile" || true; }

cd "$REPO"
LOG="$LOG_DIR/scan_${MODE}_${STAMP}.log"
echo "[$(date)] starting $MODE scan" > "$LOG"
PYTHONPATH=src .venv/bin/python3 run_preferred_breakouts.py --mode "$MODE" >> "$LOG" 2>&1
echo "[$(date)] done -> data/watchlist/eod_latest.json" >> "$LOG"
