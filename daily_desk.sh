#!/usr/bin/env bash
# Evening desk routine (run ~15:45 ET for the live read, or after the close). Writes everything to data/watchlist/.
# Requires: AWS_PROFILE, TRADIER_API_KEY, MYSQL_PASSWORD in the environment; TWS/Gateway open on Fridays (straddle screen); .venv activated or use the paths below.
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python3; export PYTHONPATH=src
D=$(date +%F); OUT=data/watchlist; mkdir -p "$OUT"
echo "== 1/6 regime read (descriptive; see run_regime_validation.py for why it is not a forecast)"
$PY run_trailing_retro.py --window 21 2>/dev/null | sed -n 1,25p | tee "$OUT/regime_$D.txt"
echo; echo "== 2/6 Adhikary scan (precision=YES + SETUP pivots are the actionable rows)"
$PY run_adhikary_scan.py 2>/dev/null | tee "$OUT/adhikary_$D.txt" | sed -n 1,60p
echo; echo "== 3/6 breakout scan on the preferred list (house Luk/Qullamaggie EOD screen)"
$PY run_preferred_breakouts.py 2>/dev/null | tail -25
if [ "$(date +%u)" = 5 ] || [ "${STRADDLE:-0}" = 1 ]; then
  echo; echo "== 4/6 long-straddle screen (Friday entry day): all 5 playbook gates on the 323 pool (Tradier data; IBKR for the IV percentile)"
  # IBKR is used for the IV-percentile gate (falls back to the stale Athena table if TWS is closed).
  # Live TWS by default; override IB_PORT=4002 (paper Gateway) in the environment if that is what is running.
  # Read-only: historical IV only, no orders. Writes data/watchlist/straddle_screen/straddle_screen_<date>.csv.
  IB_PORT="${IB_PORT:-7496}" IB_ALLOW_LIVE="${IB_ALLOW_LIVE:-1}" PYTHONPATH=src:. \
    $PY run_straddle_screen.py 2>/dev/null | grep -v "^Unknown contract\|^Error " | tee "$OUT/straddle_screen_$D.txt" | sed -n '/data source/p; /QUALIFIERS/,$p'
else
  echo; echo "== 4/6 straddle gates: skipped (not Friday; STRADDLE=1 to force)"
fi
echo; echo "== 5/6 journal: pending trader notes waiting for the Flex pull"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}" $PY - <<'PYEOF' 2>/dev/null
from lib.mysql_lib import get_pending_notes
p = get_pending_notes(applied=False)
print(p[["id","underlying_symbol","note_date"]].to_string(index=False) if len(p) else "none")
PYEOF
echo; echo "== 5b process report card (grade per session; rubric in run_journal_grades.py)"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}" $PY run_journal_grades.py 2>/dev/null | tail -12
echo; echo "== 6/6 live-alert scorecard for today, then the universe for tomorrow (edit $OUT/universe_focus.txt to change it)"
$PY run_alert_scorecard.py 2>/dev/null | tail -8
$PY run_alert_scorecard.py --oop 2>/dev/null | tail -2      # out-of-play alerts: saved, never shown -- scored for comparison
$PY -m lib.alerts.universe 2>/dev/null
echo; echo "alerts file: $OUT/alerts_latest.csv"
echo "tomorrow 09:25 ET:  ./start_alerts.sh     (UR + ORB9 on the focus universe, terminal display; --full for the preferred list)"
