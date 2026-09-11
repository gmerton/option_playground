#!/usr/bin/env bash
# Start the intraday alert monitor in this terminal (run ~09:25 ET / 06:25 PT).
#   ./start_alerts.sh            focus universe (data/watchlist/universe_focus.txt + today's plan)
#   ./start_alerts.sh --full     preferred-list union instead
#   ./start_alerts.sh AMD LITE   explicit symbols only
# Alerts print here (with a chime) and go to the journal site (alerts.html); no macOS dialogs.
#   alerts are graded A/B (loud) / C (dimmed) / F (saved as out of play) by lib/alerts/grading.py; --index-gate is a no-op.
# Preflight checks the environment LOUDLY before anything starts.
set -u
cd "$(dirname "$0")"
# secrets live in ~/.trading_env (sourced by the shell profiles too); load it here so the
# monitor works even from a shell that skipped its profile
[ -f "$HOME/.trading_env" ] && source "$HOME/.trading_env"

RED=$'\033[1;31m'; YEL=$'\033[1;33m'; GRN=$'\033[1;32m'; OFF=$'\033[0m'
fail=0
banner() { echo; echo "$1################################################################"; echo "#  $2"; echo "################################################################$OFF"; }

# --- required by this tool ---------------------------------------------------
if [ -z "${TRADIER_API_KEY:-}" ]; then
  banner "$RED" "MISSING: TRADIER_API_KEY  (the market-data feed -- cannot start)"
  echo "  fix: add   export TRADIER_API_KEY=<key>   to ~/.trading_env"
  fail=1
fi
[ -x .venv/bin/python3 ] || { banner "$RED" "MISSING: .venv/bin/python3  (run the venv setup in CLAUDE.md)"; fail=1; }

# --- wanted by the rest of the desk (warn only; the monitor itself runs without them) ---
for v in MYSQL_PASSWORD IBKR_FLEX_TOKEN ANTHROPIC_API_KEY; do
  if [ -z "${!v:-}" ]; then
    banner "$YEL" "WARNING: $v is not set (journal/review scripts need it; the monitor does not) -- add it to ~/.trading_env"
  fi
done

# --- website publishing needs working AWS credentials -------------------------
export AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}"
extra=()
if ! aws sts get-caller-identity --query Account --output text >/dev/null 2>&1; then
  banner "$YEL" "WARNING: AWS credentials for profile '$AWS_PROFILE' are not working -- alerts will NOT reach the website"
  echo "  fix: check ~/.aws/credentials for [$AWS_PROFILE]; starting with --no-publish (terminal + log only)"
  extra+=(--no-publish)
fi

if [ "$fail" -ne 0 ]; then
  banner "$RED" "NOT STARTED -- fix the items above and rerun ./start_alerts.sh"
  exit 1
fi
# before the bell: which plan levels are already dead from a gap, which holds gapped through their stops
if [ "$(TZ=America/New_York date +%H%M)" -lt 0930 ]; then
  .venv/bin/python3 run_premarket_gaps.py 2>/dev/null || echo "(pre-market check skipped)"
fi
echo "${GRN}preflight ok${OFF}: TRADIER_API_KEY set, venv present, AWS profile $AWS_PROFILE$( [ ${#extra[@]} -eq 0 ] && echo ' (publishing to the journal site)' )"
export PYTHONPATH=src
exec .venv/bin/python3 run_universe_monitor.py --sound ${extra[@]+"${extra[@]}"} "$@"
