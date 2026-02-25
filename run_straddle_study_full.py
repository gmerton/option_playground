#!/usr/bin/env python3
"""
Full re-run of the 50-50 straddle study with delta/DTE guardrails.

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 run_straddle_study_full.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.mysql_lib import get_study_tickers
from lib.condor_tools import straddle_study

tickers = get_study_tickers()
print(f"Tickers loaded from MySQL: {len(tickers)}")

straddle_study(
    tickers,
    ts_start="2020-12-15",
    ts_end="2026-03-16",
    study_description="50-50 straddle (delta/DTE filtered)",
)
