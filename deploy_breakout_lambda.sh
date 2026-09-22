#!/bin/bash
#
# Deploy the preferred-ticker breakout scan as an AWS Lambda + EventBridge schedule.
# Idempotent: creates resources on first run, updates them on subsequent runs.
#
# Prereqs: AWS profile with Lambda/EventBridge/S3 perms; TRADIER_API_KEY in env
# (sourced from ~/.bash_profile by this script). Run from repo root.
#
set -eo pipefail

# ---- config -----------------------------------------------------------------
PROFILE="${AWS_PROFILE:-clarinut-gmerton}"
REGION="us-west-2"
FUNCTION="preferred-breakout-scan"
ROLE_ARN="arn:aws:iam::919061006621:role/LambdaAdministrator"
RUNTIME="python3.12"
HANDLER="lib.interface.breakout_lambda.lambda_handler"
MEMORY=1024
TIMEOUT=120
BUCKET="gmerton-stock-data"
PREFIX="breakouts"
CODE_KEY="lambda/breakout_function.zip"
LAYER_NAME="pandas-numpy-py312"
LAYER_KEY="lambda/${LAYER_NAME}.zip"
SCHEDULE="cron(15 23 ? * MON-FRI *)"   # 23:15 UTC = 4:15pm PDT / 3:15pm PST, after close
RULE="preferred-breakout-eod"
# Set FORCE_LAYER=1 to rebuild+republish the pandas/numpy layer; otherwise an
# existing layer version is reused (it rarely changes).

export AWS_PROFILE="$PROFILE"
export AWS_DEFAULT_REGION="$REGION"

# shellcheck disable=SC1091
[ -f "$HOME/.bash_profile" ] && { source "$HOME/.bash_profile" || true; }
: "${TRADIER_API_KEY:?TRADIER_API_KEY not set (expected in ~/.bash_profile)}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
echo ">> Deploying to account $ACCOUNT, region $REGION, profile $PROFILE"

PIP_PLATFORM=(--platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all:)

# ---- 1. build + publish the pandas/numpy layer (reused unless FORCE_LAYER) ----
LAYER_ARN="$(aws lambda list-layer-versions --layer-name "$LAYER_NAME" \
  --query 'LayerVersions[0].LayerVersionArn' --output text 2>/dev/null || echo None)"
if [ "$LAYER_ARN" = "None" ] || [ -n "$FORCE_LAYER" ]; then
  echo ">> Building pandas/numpy layer..."
  rm -rf layer_build "${LAYER_NAME}.zip"
  mkdir -p layer_build/python
  .venv/bin/python3 -m pip install "${PIP_PLATFORM[@]}" --target layer_build/python pandas numpy >/dev/null
  # trim test suites + caches to keep the layer lean
  find layer_build/python -type d \( -name tests -o -name __pycache__ \) -prune -exec rm -rf {} +
  ( cd layer_build && zip -qr9 "../${LAYER_NAME}.zip" python )
  echo ">> Layer: $(du -h "${LAYER_NAME}.zip" | cut -f1) zipped, $(du -sh layer_build/python | cut -f1) unzipped"
  aws s3 cp "${LAYER_NAME}.zip" "s3://$BUCKET/$LAYER_KEY" --only-show-errors
  LAYER_ARN="$(aws lambda publish-layer-version --layer-name "$LAYER_NAME" \
    --description "pandas + numpy for python3.12 x86_64" \
    --content "S3Bucket=$BUCKET,S3Key=$LAYER_KEY" \
    --compatible-runtimes python3.12 --compatible-architectures x86_64 \
    --query LayerVersionArn --output text --no-cli-pager)"
  echo ">> Published layer: $LAYER_ARN"
else
  echo ">> Reusing existing layer: $LAYER_ARN  (set FORCE_LAYER=1 to rebuild)"
fi

# ---- 2. build the slim function package (code + aiohttp only) -----------------
# pandas/numpy come from the layer above; boto3 is in the runtime. typing_extensions
# is an aiohttp-stack dependency that must ship with the function.
echo ">> Building function package..."
rm -rf build breakout_function.zip
mkdir -p build
.venv/bin/python3 -m pip install "${PIP_PLATFORM[@]}" --target build \
  aiohttp typing_extensions >/dev/null
# copy ONLY the modules this Lambda imports (its closure) -- the full lib/ tree
# carries a committed .venv (414M) and a data dir (lib/output, 238M) we don't want.
MODS=(
  interface/breakout_lambda.py
  interface/breakout_artifacts.py
  interface/premarket_watchlist.py
  tradier/get_daily_history.py
  tradier/tradier_client_wrapper.py
  commons/get_underlying_price.py
  commons/list_contracts.py
  commons/list_expirations.py
)
for m in "${MODS[@]}"; do
  mkdir -p "build/lib/$(dirname "$m")"
  cp "src/lib/$m" "build/lib/$m"
done
for d in "" "interface/" "tradier/" "commons/"; do touch "build/lib/${d}__init__.py"; done
echo ">> build/lib (closure only): $(du -sh build/lib | cut -f1)"
( cd build && zip -qr9 ../breakout_function.zip . )
echo ">> Package: $(du -h breakout_function.zip | cut -f1) zipped, "\
"$(du -sh build | cut -f1) unzipped"

# ---- 2. upload code to S3; the ticker universe is S3-owned -------------------
# The preferred list in S3 is written nightly by the preferred-list-refresh Lambda (and by
# run_refresh_preferred.py --push). Never push the local copy over it: on 2026-09-20 this step
# replaced the fresh 89-name list with a July 23 local file. Seed S3 only if it has no list yet;
# otherwise pull S3 down so the local copy (read by the desk scans) stays current.
echo ">> Uploading code to s3://$BUCKET/$CODE_KEY..."
aws s3 cp breakout_function.zip "s3://$BUCKET/$CODE_KEY" --only-show-errors
LIST_URI="s3://$BUCKET/$PREFIX/preferred_tickers.txt"
if aws s3 ls "$LIST_URI" >/dev/null 2>&1; then
  aws s3 cp "$LIST_URI" data/preferred_tickers.txt --only-show-errors
  echo ">> Ticker list: kept S3's copy ($(grep -c . data/preferred_tickers.txt) names), synced it to data/preferred_tickers.txt"
else
  aws s3 cp data/preferred_tickers.txt "$LIST_URI" --only-show-errors
  echo ">> Ticker list: none in S3 yet, seeded from data/preferred_tickers.txt"
fi

# ---- 3. create or update the function ----------------------------------------
ENV_VARS="Variables={TRADIER_API_KEY=$TRADIER_API_KEY,BREAKOUT_BUCKET=$BUCKET,BREAKOUT_PREFIX=$PREFIX}"
if aws lambda get-function --function-name "$FUNCTION" >/dev/null 2>&1; then
  echo ">> Updating existing function code + config..."
  aws lambda update-function-code --function-name "$FUNCTION" \
    --s3-bucket "$BUCKET" --s3-key "$CODE_KEY" --no-cli-pager >/dev/null
  aws lambda wait function-updated --function-name "$FUNCTION"
  aws lambda update-function-configuration --function-name "$FUNCTION" \
    --runtime "$RUNTIME" --handler "$HANDLER" --role "$ROLE_ARN" \
    --memory-size "$MEMORY" --timeout "$TIMEOUT" --environment "$ENV_VARS" \
    --layers "$LAYER_ARN" --no-cli-pager >/dev/null
else
  echo ">> Creating function..."
  aws lambda create-function --function-name "$FUNCTION" \
    --runtime "$RUNTIME" --handler "$HANDLER" --role "$ROLE_ARN" \
    --code "S3Bucket=$BUCKET,S3Key=$CODE_KEY" \
    --memory-size "$MEMORY" --timeout "$TIMEOUT" --environment "$ENV_VARS" \
    --layers "$LAYER_ARN" --no-cli-pager >/dev/null
fi
aws lambda wait function-updated --function-name "$FUNCTION"
FN_ARN="$(aws lambda get-function --function-name "$FUNCTION" --query Configuration.FunctionArn --output text)"
echo ">> Function ARN: $FN_ARN"

# ---- 4. EventBridge weekday after-close schedule -----------------------------
echo ">> Wiring EventBridge rule $RULE ($SCHEDULE)..."
aws events put-rule --name "$RULE" --schedule-expression "$SCHEDULE" \
  --state ENABLED --description "Daily preferred-ticker breakout scan (after close)" \
  --no-cli-pager >/dev/null
aws lambda add-permission --function-name "$FUNCTION" \
  --statement-id "${RULE}-invoke" --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:$REGION:$ACCOUNT:rule/$RULE" \
  --no-cli-pager >/dev/null 2>&1 || echo "   (invoke permission already present)"
aws events put-targets --rule "$RULE" \
  --targets "Id=1,Arn=$FN_ARN" --no-cli-pager >/dev/null

echo ">> Done. Test now with:"
echo "   AWS_PROFILE=$PROFILE aws lambda invoke --function-name $FUNCTION --no-cli-pager /tmp/out.json && cat /tmp/out.json"
echo "   AWS_PROFILE=$PROFILE aws s3 cp s3://$BUCKET/$PREFIX/eod_latest.txt -"
