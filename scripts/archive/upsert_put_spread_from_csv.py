#!/usr/bin/env python3
"""
One-off: upsert put spread study from saved CSVs into MySQL.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
from lib.mysql_lib import create_study, upsert_study_detail, upsert_study_summary

DETAIL_CSV  = "src/lib/output/put_spread_study_detail_20260222154422.csv"
SUMMARY_CSV = "src/lib/output/put_spread_study_20260222154422.csv"
DESCRIPTION = "50-15 put spread"

print(f"Loading detail CSV: {DETAIL_CSV}")
detail_df = pd.read_csv(DETAIL_CSV)
print(f"  {len(detail_df)} rows")

print(f"Loading summary CSV: {SUMMARY_CSV}")
summary_df = pd.read_csv(SUMMARY_CSV)
print(f"  {len(summary_df)} rows")

print(f"Creating study: '{DESCRIPTION}'")
study_id = create_study(DESCRIPTION)
print(f"  study_id = {study_id}")

print("Upserting study_detail...")
detail_affected = upsert_study_detail(detail_df, study_id)
print(f"  {detail_affected} rows affected")

summaries_mid   = summary_df[summary_df["pricing"] == "mid"  ][["ticker","n_entries","roc","return_on_credit","win_rate"]].to_dict("records")
summaries_worst = summary_df[summary_df["pricing"] == "worst"][["ticker","n_entries","roc","return_on_credit","win_rate"]].to_dict("records")

print(f"Upserting study_summary ({len(summaries_mid)} mid + {len(summaries_worst)} worst)...")
summary_affected = upsert_study_summary(summaries_mid, summaries_worst, study_id)
print(f"  {summary_affected} rows affected")

print(f"\nDone. MySQL study_id={study_id}")
