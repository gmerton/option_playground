#!/usr/bin/env bash
# Deploy + launch the Polygon 1-min backfill as a one-off ECS Fargate task (2026-09-25).
# No Docker build: the task runs the stock python:3.12-slim image, pip-installs 4 packages, pulls backfill.py from S3.
# Reuses options-cluster, the options-daily-updater roles (execution role reads the polygon-api-key secret; task role
# writes S3) and its network config. Own log group: /ecs/polygon-1min-backfill.
#
# Usage (repo root):  services/polygon-1min-backfill/deploy_and_run.sh [--tickers-file FILE] [--no-run]
#   Re-running is safe: the job skips chunks already marked done in S3.
#   Watch:  aws logs tail /ecs/polygon-1min-backfill --follow
#   Pull down one name:  aws s3 sync s3://gmerton-stock-data/backfill/intraday_1min/bars/NVDA data/cache/intraday_backfill/NVDA
set -euo pipefail
export AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}" AWS_DEFAULT_REGION=us-west-2
HERE="$(cd "$(dirname "$0")" && pwd)"
BUCKET=gmerton-stock-data; PREFIX=backfill/intraday_1min
FAMILY=polygon-1min-backfill; LOG=/ecs/polygon-1min-backfill
ACCT=919061006621
TICKERS=""; RUN=1
while [ $# -gt 0 ]; do case "$1" in --tickers-file) TICKERS="$2"; shift 2;; --no-run) RUN=0; shift;; *) echo "unknown $1"; exit 2;; esac; done

aws s3 cp "$HERE/backfill.py" "s3://$BUCKET/$PREFIX/code/backfill.py" --only-show-errors
[ -n "$TICKERS" ] && aws s3 cp "$TICKERS" "s3://$BUCKET/$PREFIX/tickers.txt" --only-show-errors
aws logs create-log-group --log-group-name "$LOG" 2>/dev/null || true
aws logs put-retention-policy --log-group-name "$LOG" --retention-in-days 30

CMD="pip install -q --no-cache-dir boto3 pandas pyarrow requests && python -c \"import boto3;boto3.client('s3').download_file('$BUCKET','$PREFIX/code/backfill.py','/tmp/backfill.py')\" && python -u /tmp/backfill.py"
cat > /tmp/$FAMILY-taskdef.json <<EOF
{
  "family": "$FAMILY",
  "requiresCompatibilities": ["FARGATE"], "networkMode": "awsvpc", "cpu": "256", "memory": "1024",
  "executionRoleArn": "arn:aws:iam::$ACCT:role/options-daily-updater-execution-role",
  "taskRoleArn": "arn:aws:iam::$ACCT:role/options-daily-updater-task-role",
  "containerDefinitions": [{
    "name": "backfill", "image": "public.ecr.aws/docker/library/python:3.12-slim", "essential": true,
    "entryPoint": ["sh", "-c"], "command": [$(printf '%s' "$CMD" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')],
    "environment": [
      {"name": "BUCKET", "value": "$BUCKET"}, {"name": "PREFIX", "value": "$PREFIX"},
      {"name": "START", "value": "${START:-2024-10-01}"}, {"name": "END", "value": "${END:-2026-09-24}"},
      {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"}
    ],
    "secrets": [{"name": "POLYGON_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-west-2:$ACCT:secret:polygon-api-key-Z30TYi:POLYGON_API_KEY::"}],
    "logConfiguration": {"logDriver": "awslogs", "options": {"awslogs-group": "$LOG", "awslogs-region": "us-west-2", "awslogs-stream-prefix": "ecs"}}
  }]
}
EOF
TD=$(aws ecs register-task-definition --cli-input-json file:///tmp/$FAMILY-taskdef.json --query 'taskDefinition.taskDefinitionArn' --output text)
echo "task definition: $TD"
[ "$RUN" = 1 ] || exit 0
RUNNING=$(aws ecs list-tasks --cluster options-cluster --family "$FAMILY" --desired-status RUNNING --query 'length(taskArns)' --output text)
if [ "$RUNNING" != "0" ]; then echo "already running ($RUNNING task) -- not starting another (two would share the 5/min limit)"; exit 0; fi
aws ecs run-task --cluster options-cluster --launch-type FARGATE --task-definition "$TD" \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-f48d1cac,subnet-46474322,subnet-051d0d57060717071],securityGroups=[sg-0e24462e33a46f81c],assignPublicIp=ENABLED}' \
  --query 'tasks[0].taskArn' --output text
echo "started. logs: aws logs tail $LOG --follow"
