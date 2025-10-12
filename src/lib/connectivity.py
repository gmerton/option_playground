import boto3, time, pandas as pd

REGION   = "us-west-2"
WG       = "dev-v3"  # your Engine v3 workgroup
CATALOG  = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"
DB       = "silver"
S3_OUT   = "s3://athena-919061006621/"

ath = boto3.client("athena", region_name=REGION)

q = 'SELECT * FROM "silver"."options_daily_v2" LIMIT 1'

qe = ath.start_query_execution(
    QueryString=q,
    QueryExecutionContext={"Database": DB, "Catalog": CATALOG},
    WorkGroup=WG,
    ResultConfiguration={"OutputLocation": S3_OUT},
)
qid = qe["QueryExecutionId"]

while True:
    s = ath.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
    if s["State"] in ("SUCCEEDED","FAILED","CANCELLED"):
        print("State:", s["State"], "| Reason:", s.get("StateChangeReason"))
        break
    time.sleep(1)

if s["State"] == "SUCCEEDED":
    res = ath.get_query_results(QueryExecutionId=qid)
    cols = [c["Label"] for c in res["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
    rows = res["ResultSet"]["Rows"][1:]
    print(pd.DataFrame([[d.get("VarCharValue") for d in r["Data"]] for r in rows], columns=cols))
