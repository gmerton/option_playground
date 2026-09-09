#!/usr/bin/env bash
# Start the intraday alert monitor in this terminal (run ~09:25 ET / 06:25 PT).
#   ./start_alerts.sh            focus universe (data/watchlist/universe_focus.txt + today's plan)
#   ./start_alerts.sh --full     preferred-list union instead
#   ./start_alerts.sh AMD LITE   explicit symbols only
# Alerts print here and go to the journal site (alerts.html); no macOS dialogs.
# Needs TRADIER_API_KEY in the environment (AWS_PROFILE for the site upload).
set -u
cd "$(dirname "$0")"
: "${TRADIER_API_KEY:?set TRADIER_API_KEY first}"
export AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}" PYTHONPATH=src
exec .venv/bin/python3 run_universe_monitor.py --no-dialog "$@"
