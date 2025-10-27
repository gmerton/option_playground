# -----------------------------
# Athena / Catalog configuration
# -----------------------------
CATALOG   = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"  # from QueryExecutionContext
WORKGROUP = "dev-v3"                                               # Athena engine v3
S3_OUTPUT = "s3://athena-919061006621/"                            # WG output location (safe to keep)
DB        = "silver"
TABLE     = "options_daily_v2"                                     # referenced as silver.options_daily_v2
TMP_S3_PREFIX = "s3://athena-919061006621/tmp_targets/" 
CONTRACT_MULTIPLIER = 100
GLUE_CATALOG = "AwsDataCatalog"  # Glue Data Catalog name
S3TABLES_CATALOG = CATALOG       # your existing "awsdatacatalog/..." string

WEEKDAY_ALIASES = {
    "MON":0,
    "TUE":1,
    "WED":2,
    "THU":3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6
}