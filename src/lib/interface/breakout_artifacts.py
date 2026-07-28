"""
Shared post-processing for the preferred-ticker breakout scan.

Turns the raw EOD scan results (from premarket_watchlist.run_eod_scan) into the
derived artifacts consumed downstream:

  monitor_config()  -> breakout_monitor.py CONFIG-shaped dict (the intraday
                       trigger bridge): names coiling under / just through pivot.
  buckets()         -> {confirmed, broke_light, coiling} for reporting.

Kept in src/ (not the repo-root runner) so both run_preferred_breakouts.py and
the AWS Lambda handler import one implementation.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Monitor-eligibility band: arm the intraday trigger monitor for names that are
# coiling under their pivot or just nudging through it -- an actionable break can
# still happen intraday. Names already extended above the pivot have no fresh
# break left to catch, so they are reported but not monitored.
MONITOR_DIST_LOW = -8.0    # deepest below pivot still worth arming
MONITOR_DIST_HIGH = 1.0    # at/just-under pivot; > this is already broken out
COILED_BAND = -3.0         # within this of pivot -> 20-day-high trigger (coiled)


def monitor_config(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Translate near-pivot results into breakout_monitor.py CONFIG entries."""
    cfg: Dict[str, Dict[str, Any]] = {}
    for r in results:
        dist = r.get("pivot_dist_pct")
        if r.get("pivot") is None or dist is None:
            continue
        if not (MONITOR_DIST_LOW <= dist <= MONITOR_DIST_HIGH):
            continue
        # coiled right at the pivot -> 20d-high trigger; deeper in base -> early 5d
        coiled = dist >= COILED_BAND
        tier = "A" if r.get("is_potent") else ("A-" if r.get("is_leader") else "B")
        vr = r.get("vol_ratio")
        vr_str = f"RVOL {vr:.1f}x" if vr is not None else "RVOL --"
        misses = r.get("optional_misses") or []
        miss_str = "; " + " ".join(f"!{m}" for m in misses) if misses else ""
        cfg[r["ticker"]] = {
            "trigger_lb": 20 if coiled else 5,
            "tier": tier,
            "note": f"{dist:+.1f}% to pivot ${r['pivot']:.2f}; {vr_str}; 1M {r.get('pct_1m')}%{miss_str}",
            # less-imminent names (further below pivot) -> terminal/log only, no popup
            "watch": dist < (COILED_BAND - 1.0),
        }
    return cfg


def buckets(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Split results into confirmed breakouts / broke-on-light-volume / coiling."""
    confirmed = [r for r in results if r.get("breakout_confirmed")]
    broke_light = [r for r in results
                   if r.get("is_breakout") and not r.get("breakout_confirmed")]
    coiling = [r for r in results
               if r.get("pivot") is not None
               and r.get("pivot_dist_pct") is not None
               and MONITOR_DIST_LOW <= r["pivot_dist_pct"] < 0]
    confirmed.sort(key=lambda r: -(r.get("vol_ratio") or 0))
    coiling.sort(key=lambda r: -(r.get("vol_ratio") or 0))
    return {"confirmed": confirmed, "broke_light": broke_light, "coiling": coiling}
