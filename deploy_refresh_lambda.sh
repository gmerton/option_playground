#!/bin/bash
#
# Deploy the nightly preferred-list refresh Lambda + EventBridge schedule.
# Idempotent. Companion to deploy_breakout_lambda.sh (which deploys the 4:15pm
# scan that CONSUMES the list this one produces).
#
# Uses the AWS managed AWSSDKPandas layer (pandas+numpy+pyarrow+awswrangler) —
# our custom pandas layer lacks pyarrow, which parquet + Iceberg staging need.
#
# Prereqs: POLYGON_API_KEY in env/~/.bash_profile. Run from repo root.
set -eo pipefail

PROFILE="${AWS_PROFILE:-clarinut-gmerton}"
REGION="us-west-2"
FUNCTION="preferred-list-refresh"
ROLE_ARN="arn:aws:iam::919061006621:role/LambdaAdministrator"
RUNTIME="python3.12"
HANDLER="lib.interface.refresh_lambda.lambda_handler"
MEMORY=2048
TIMEOUT=900
BUCKET="gmerton-stock-data"
PREFIX="breakouts"
CODE_KEY="lambda/refresh_function.zip"
# 07:30 UTC Tue-Sat = Mon-Fri 12:30am PDT (1 session later in PST — fine): late
# enough that Polygon's free tier has published the session (verified NOT yet
# published at 8:25pm PT), 15h before the 4:15pm PT breakout scan consumes the list.
SCHEDULE="cron(30 7 ? * TUE-SAT *)"
RULE="preferred-list-refresh-nightly"
SDK_PANDAS_ACCOUNT="336392948345"     # AWS-managed AWSSDKPandas layer publisher
LAYER_BASE="arn:aws:lambda:$REGION:$SDK_PANDAS_ACCOUNT:layer:AWSSDKPandas-Python312"

export AWS_PROFILE="$PROFILE"
export AWS_DEFAULT_REGION="$REGION"

# shellcheck disable=SC1091
[ -f "$HOME/.bash_profile" ] && { source "$HOME/.bash_profile" || true; }
: "${POLYGON_API_KEY:?POLYGON_API_KEY not set (expected in ~/.bash_profile)}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
echo ">> Deploying $FUNCTION to account $ACCOUNT, region $REGION"

# ---- 1. managed AWSSDKPandas layer — PINNED ----------------------------------
# v24 verified working 2026-07-24. v29 (newest at the time) SEGFAULTS on any
# pyarrow parquet read under runtime python:3.12.mainlinev2.v18 — if bumping,
# re-verify with the handler's {"debug_stage":"load"} probe before trusting it.
LAYER_ARN="$LAYER_BASE:24"
aws lambda get-layer-version-by-arn --arn "$LAYER_ARN" >/dev/null || { echo "!! pinned layer missing"; exit 1; }
echo ">> Managed layer: $LAYER_ARN"

# ---- 2. build the function package (closure + polygon client) ----------------
echo ">> Building function package..."
rm -rf refresh_build refresh_function.zip
mkdir -p refresh_build
# --no-deps: the managed layer already ships urllib3/certifi (botocore-matched);
# bundling our own versions shadows the layer's and crashes the runtime.
# websockets (streaming only) is unused by the REST client.
.venv/bin/python3 -m pip install --platform manylinux2014_x86_64 --implementation cp \
  --python-version 3.12 --only-binary=:all: --no-deps --target refresh_build \
  polygon-api-client websockets >/dev/null
MODS=(
  constants.py
  minervini/scan.py
  minervini/equity_daily.py
  interface/refresh_lambda.py
)
for m in "${MODS[@]}"; do
  mkdir -p "refresh_build/lib/$(dirname "$m")"
  cp "src/lib/$m" "refresh_build/lib/$m"
done
for d in "" "minervini/" "interface/"; do touch "refresh_build/lib/${d}__init__.py"; done
find refresh_build -type d \( -name tests -o -name __pycache__ \) -prune -exec rm -rf {} +
( cd refresh_build && zip -qr9 ../refresh_function.zip . )
echo ">> Package: $(du -h refresh_function.zip | cut -f1) zipped"

# ---- 3. upload + create/update function ---------------------------------------
aws s3 cp refresh_function.zip "s3://$BUCKET/$CODE_KEY" --only-show-errors
ENV_VARS="Variables={POLYGON_API_KEY=$POLYGON_API_KEY,BREAKOUT_BUCKET=$BUCKET,BREAKOUT_PREFIX=$PREFIX}"
if aws lambda get-function --function-name "$FUNCTION" >/dev/null 2>&1; then
  echo ">> Updating existing function..."
  aws lambda update-function-code --function-name "$FUNCTION" \
    --s3-bucket "$BUCKET" --s3-key "$CODE_KEY" --no-cli-pager >/dev/null
  aws lambda wait function-updated --function-name "$FUNCTION"
  aws lambda update-function-configuration --function-name "$FUNCTION" \
    --runtime "$RUNTIME" --handler "$HANDLER" --role "$ROLE_ARN" \
    --memory-size "$MEMORY" --timeout "$TIMEOUT" --environment "$ENV_VARS" \
    --ephemeral-storage Size=1024 \
    --layers "$LAYER_ARN" --no-cli-pager >/dev/null
else
  echo ">> Creating function..."
  aws lambda create-function --function-name "$FUNCTION" \
    --runtime "$RUNTIME" --handler "$HANDLER" --role "$ROLE_ARN" \
    --code "S3Bucket=$BUCKET,S3Key=$CODE_KEY" \
    --memory-size "$MEMORY" --timeout "$TIMEOUT" --environment "$ENV_VARS" \
    --ephemeral-storage Size=1024 \
    --layers "$LAYER_ARN" --no-cli-pager >/dev/null
fi
aws lambda wait function-updated --function-name "$FUNCTION"
FN_ARN="$(aws lambda get-function --function-name "$FUNCTION" --query Configuration.FunctionArn --output text)"
echo ">> Function ARN: $FN_ARN"

# ---- 4. EventBridge nightly schedule ------------------------------------------
echo ">> Wiring EventBridge rule $RULE ($SCHEDULE)..."
aws events put-rule --name "$RULE" --schedule-expression "$SCHEDULE" \
  --state ENABLED --description "Nightly Minervini refresh of preferred_tickers.txt + equity_daily append" \
  --no-cli-pager >/dev/null
aws lambda add-permission --function-name "$FUNCTION" \
  --statement-id "${RULE}-invoke" --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:$REGION:$ACCOUNT:rule/$RULE" \
  --no-cli-pager >/dev/null 2>&1 || echo "   (invoke permission already present)"
aws events put-targets --rule "$RULE" --targets "Id=1,Arn=$FN_ARN" --no-cli-pager >/dev/null

echo ">> Done. Test with:"
echo "   AWS_PROFILE=$PROFILE aws lambda invoke --function-name $FUNCTION --cli-read-timeout 900 --no-cli-pager /tmp/refresh_out.json && cat /tmp/refresh_out.json"
echo "   AWS_PROFILE=$PROFILE aws s3 cp s3://$BUCKET/$PREFIX/refresh_latest.txt -"
