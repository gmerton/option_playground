#!/usr/bin/env bash
# Evening desk routine (run ~15:45 ET for the live read, or after the close). Writes everything to data/watchlist/.
# Requires: AWS_PROFILE, TRADIER_API_KEY, MYSQL_PASSWORD in the environment; .venv activated or use the paths below.
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python3; export PYTHONPATH=src
D=$(date +%F); OUT=data/watchlist; mkdir -p "$OUT"
echo "== 1/5 regime read (descriptive; see run_regime_validation.py for why it is not a forecast)"
$PY run_trailing_retro.py --window 21 2>/dev/null | sed -n 1,25p | tee "$OUT/regime_$D.txt"
echo; echo "== 2/5 Adhikary scan (precision=YES + SETUP pivots are the actionable rows)"
$PY run_adhikary_scan.py 2>/dev/null | tee "$OUT/adhikary_$D.txt" | sed -n 1,60p
echo; echo "== 3/5 breakout scan on the preferred list (house Luk/Qullamaggie EOD screen)"
$PY run_preferred_breakouts.py 2>/dev/null | tail -25
if [ "$(date +%u)" = 5 ] || [ "${STRADDLE:-0}" = 1 ]; then
  echo; echo "== 4/5 long-straddle gates (Friday entry day): FVR on the 323 pool, then the print-based IV percentile gate"
  $PY run_straddle_fvr_scan.py --universe data/watchlist/straddle_pool_323.txt --concurrency 2 2>/dev/null | tee "$OUT/straddle_scan_$D.txt" | tail -30
  cp "$OUT/straddle_scan_$D.txt" "$OUT/straddle_scan_latest.txt"
  $PY run_straddle_iv_gate.py --from-scan "$OUT/straddle_scan_latest.txt" --out "$OUT/straddle_ivgate_$D.csv" 2>/dev/null
else
  echo; echo "== 4/5 straddle gates: skipped (not Friday; STRADDLE=1 to force)"
fi
echo; echo "== 5/5 journal: pending trader notes waiting for the Flex pull"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}" $PY - <<'PYEOF' 2>/dev/null
from lib.mysql_lib import get_pending_notes
p = get_pending_notes(applied=False)
print(p[["id","underlying_symbol","note_date"]].to_string(index=False) if len(p) else "none")
PYEOF
echo; echo "alerts file: $OUT/alerts_latest.csv"
