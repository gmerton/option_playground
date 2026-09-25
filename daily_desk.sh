#!/usr/bin/env bash
# Evening desk routine (run ~15:45 ET for the live read, or after the close). Writes everything to data/watchlist/.
# Requires: AWS_PROFILE, TRADIER_API_KEY, MYSQL_PASSWORD in the environment; TWS/Gateway open on Fridays (straddle screen); .venv activated or use the paths below.
set -u
cd "$(dirname "$0")"
# secrets live in ~/.trading_env; load them here like start_alerts.sh / morning_journal.sh do, so the desk does not
# depend on the launching shell (2026-09-24: the GEX paper-trade step had logged nothing since it was added 9/21)
if [ -f "$HOME/.trading_env" ]; then set +u; source "$HOME/.trading_env"; set -u; fi
for v in TRADIER_API_KEY MYSQL_PASSWORD; do [ -n "${!v:-}" ] || echo "  ⚠ $v is not set -- add it to ~/.trading_env"; done
PY=.venv/bin/python3; export PYTHONPATH=src
D=$(date +%F); OUT=data/watchlist; mkdir -p "$OUT"
# The regime read and the liquid-panel build read the local copy of the nightly Lambda day-matrix; pull it first
# (2026-09-20: a 9/04 local copy silently produced a two-week-old regime read).
aws s3 cp s3://gmerton-stock-data/breakouts/minervini_matrix.parquet data/cache/minervini_matrix.parquet --only-show-errors \
  || echo "  (day-matrix pull failed; regime read uses the local copy -- check its as-of date)"
# The preferred list is S3-owned (written nightly by the preferred-list-refresh Lambda); the breakout scan, the
# reversal monitor and the alert monitor's --full universe read the LOCAL copy. Pull it every run
# (2026-09-21: the local file was two months stale, from 2026-07-23). Keep the local copy if the pull fails or
# comes back suspiciously short (the refresh Lambda itself refuses to write fewer than 20 names).
LIST_TMP=$(mktemp)
if aws s3 cp s3://gmerton-stock-data/breakouts/preferred_tickers.txt "$LIST_TMP" --only-show-errors \
   && [ "$(grep -c . "$LIST_TMP")" -ge 20 ]; then
  mv "$LIST_TMP" data/preferred_tickers.txt
  N_LIST=$(grep -c . data/preferred_tickers.txt)
  REFRESH=$(aws s3 cp s3://gmerton-stock-data/breakouts/refresh_latest.txt - 2>/dev/null)
  N_REF=$(echo "$REFRESH" | sed -n 's/.*list: \([0-9]*\).*/\1/p' | head -1)
  echo "  preferred list: $N_LIST names, refresh Lambda: $(echo "$REFRESH" | head -1 | sed 's/.*data through/data through/')"
  # the list was written by something other than the last refresh (e.g. an old deploy pushed a local copy)
  [ -n "$N_REF" ] && [ "$N_REF" != "$N_LIST" ] && \
    echo "  ⚠ LIST MISMATCH: the refresh Lambda wrote $N_REF names but S3 now holds $N_LIST -- something overwrote it after the refresh"
else
  rm -f "$LIST_TMP"
  echo "  (preferred-list pull failed or too short; scans use the local copy from $(date -r data/preferred_tickers.txt +%F))"
fi
# SPY positive-gamma 1-day iron fly, forward paper trade (data/studies/gex_spy_ironfly_2026-09-21.md): settle due
# trades, compute live GEX, log the signal and a paper fly if gamma is positive. Needs 15:30 ET or later; idempotent.
echo "== 0 GEX iron-fly paper trade"
mkdir -p "$OUT/logs"; GEX_LOG="$OUT/logs/gex_fly_$D.log"
if $PY run_gex_fly_paper.py --close >"$GEX_LOG" 2>&1; then
  tail -6 "$GEX_LOG"
else
  echo "  ⚠⚠ GEX fly step FAILED -- the forward sample misses tonight. Full output: $GEX_LOG"; tail -12 "$GEX_LOG"
fi
[ -f data/paper/gex_fly_signals.csv ] && echo "  signals logged so far: $(($(wc -l < data/paper/gex_fly_signals.csv) - 1))"
echo "== 1/6 regime read (descriptive; see run_regime_validation.py for why it is not a forecast)"
$PY run_trailing_retro.py --window 21 2>/dev/null | sed -n 1,25p | tee "$OUT/regime_$D.txt"
echo; echo "== 1b open book (Flex snapshot + live Tradier marks): what expires and what it is worth"
# Source is journal_open_positions (broker basis + mark), NOT journal_campaigns -- campaign
# net_premium is cumulative cash including rolls, so it cannot give a cost basis. Snapshot lands
# one session late, so --live re-marks the option legs. Full table in the log; only the urgent
# rows and the totals reach the terminal.
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}" $PY run_position_monitor.py --live 2>/dev/null \
  | tee "$OUT/positions_$D.txt" | sed -n '1,2p; /EXPIRES\|EXPIRED/p; /^net:/,$p'
echo "  full table: $OUT/positions_$D.txt"

# The Adhikary scan and the cluster view both read the liquid panel; refresh it first (~75s). Off-hours the scan
# scores the panel's last cached close, so a stale panel meant a stale scan (2026-09-23: an evening run scored 9/21).
# The builder also fills sessions yfinance silently drops (2026-09-22) from Polygon; its gap-check lines are shown here.
if PANEL_LOG=$($PY run_build_liquid_panel.py 2>&1); then
  echo "$PANEL_LOG" | grep -E "gap check|WARN|dropped today|^wrote" | sed 's/^/  /'
else
  echo "  (panel refresh failed; the scan and clusters use the cached panel)"; echo "$PANEL_LOG" | tail -3 | sed 's/^/  /'
fi
echo; echo "== 2/6 Adhikary scan (precision=YES + SETUP pivots are the actionable rows)"
$PY run_adhikary_scan.py 2>/dev/null | tee "$OUT/adhikary_$D.txt" | sed -n 1,60p
echo; echo "== 2c industry clusters of the scan's qualifiers (watchlist pointer, NOT a signal: group strength has no edge, see group_move_study_2026-09-17.md)"
PYTHONPATH=src:. $PY run_scan_clusters.py 2>/dev/null | tee "$OUT/clusters_$D.txt" | cut -c1-220
echo; echo "== 3/6 breakout scan on the preferred list (house Luk/Qullamaggie EOD screen)"
# The preferred-breakout-eod Lambda runs this same scan at 19:15 ET into S3. Once today's copy exists, use it
# instead of rescanning (house rule: check S3 before scanning locally; 2026-09-24 housekeeping). Before 19:15 ET,
# or if the pull fails, scan locally as before. The Lambda's JSON is a superset of the local one.
EOD_S3=s3://gmerton-stock-data/breakouts
if aws s3 ls "$EOD_S3/eod_$D.txt" >/dev/null 2>&1 \
   && aws s3 cp "$EOD_S3/eod_$D.txt" "$OUT/eod_$D.txt" --only-show-errors \
   && aws s3 cp "$EOD_S3/eod_latest.json" "$OUT/eod_latest.json" --only-show-errors \
   && aws s3 cp "$EOD_S3/monitor_latest.json" "$OUT/monitor_latest.json" --only-show-errors; then
  echo "  (from the preferred-breakout-eod Lambda, $EOD_S3/eod_$D.txt -- no local rescan)"
  tail -25 "$OUT/eod_$D.txt"
else
  echo "  (no Lambda scan for $D yet -- it runs at 19:15 ET; scanning locally)"
  $PY run_preferred_breakouts.py 2>/dev/null | tail -25
fi
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
