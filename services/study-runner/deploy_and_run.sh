#!/usr/bin/env bash
# Run one study script as a one-off ECS Fargate task (2026-09-25; Gabe: local runs were eating swap).
# No Docker build: stock python:3.12-slim, pip-installs pandas/pyarrow/numpy/boto3, pulls a tarball of the listed repo
# files (code + cached data) from S3, runs the script from the repo root with PYTHONPATH=src:., then uploads
# data/studies/ outputs that are newer than the start back to s3://gmerton-stock-data/study-runner/<run-id>/out/.
# Reuses options-cluster and the options-daily-updater roles/network (task role writes S3).
#
# Usage (repo root): services/study-runner/deploy_and_run.sh <script.py> <file-or-dir> [...]   (CPU=4096 MEM=16384 WORKERS=4)
# Watch:  aws logs tail /ecs/study-runner --follow
# Fetch:  aws s3 sync s3://gmerton-stock-data/study-runner/<run-id>/out/ .
set -euo pipefail
export AWS_PROFILE="${AWS_PROFILE:-clarinut-gmerton}" AWS_DEFAULT_REGION=us-west-2
SCRIPT="$1"; shift
BUCKET=gmerton-stock-data; FAMILY=study-runner; LOG=/ecs/study-runner; ACCT=919061006621
RUN_ID="$(date -u +%Y%m%dT%H%M%S)-$(basename "$SCRIPT" .py)"; PREFIX="study-runner/$RUN_ID"
CPU="${CPU:-4096}"; MEM="${MEM:-16384}"; WORKERS="${WORKERS:-4}"
TAR="/tmp/$RUN_ID.tgz"
tar czf "$TAR" "$SCRIPT" "$@"
aws s3 cp "$TAR" "s3://$BUCKET/$PREFIX/bundle.tgz" --only-show-errors
aws logs create-log-group --log-group-name "$LOG" 2>/dev/null || true
aws logs put-retention-policy --log-group-name "$LOG" --retention-in-days 30
CMD="pip install -q --no-cache-dir boto3 pandas pyarrow numpy && mkdir -p /w && cd /w && python -c \"import boto3;boto3.client('s3').download_file('$BUCKET','$PREFIX/bundle.tgz','/tmp/b.tgz')\" && tar xzf /tmp/b.tgz && mkdir -p data/studies/logs && touch /tmp/t0 && (PYTHONPATH=src:. python -u $SCRIPT; echo exit=\$? > data/studies/logs/_exit.txt); find data/studies -newer /tmp/t0 -type f | while read f; do python -c \"import boto3,sys;boto3.client('s3').upload_file(sys.argv[1],'$BUCKET','$PREFIX/out/'+sys.argv[1])\" \"\$f\"; done; cat data/studies/logs/_exit.txt"
cat > /tmp/$FAMILY-taskdef.json <<JSON
{
  "family": "$FAMILY",
  "requiresCompatibilities": ["FARGATE"], "networkMode": "awsvpc", "cpu": "$CPU", "memory": "$MEM",
  "ephemeralStorage": {"sizeInGiB": 40},
  "executionRoleArn": "arn:aws:iam::$ACCT:role/options-daily-updater-execution-role",
  "taskRoleArn": "arn:aws:iam::$ACCT:role/options-daily-updater-task-role",
  "containerDefinitions": [{
    "name": "study", "image": "public.ecr.aws/docker/library/python:3.12-slim", "essential": true,
    "entryPoint": ["sh", "-c"], "command": [$(printf '%s' "$CMD" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')],
    "environment": [{"name": "WORKERS", "value": "$WORKERS"}, {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"}],
    "logConfiguration": {"logDriver": "awslogs", "options": {"awslogs-group": "$LOG", "awslogs-region": "us-west-2", "awslogs-stream-prefix": "ecs"}}
  }]
}
JSON
TD=$(aws ecs register-task-definition --cli-input-json file:///tmp/$FAMILY-taskdef.json --query 'taskDefinition.taskDefinitionArn' --output text)
aws ecs run-task --cluster options-cluster --launch-type FARGATE --task-definition "$TD" \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-f48d1cac,subnet-46474322,subnet-051d0d57060717071],securityGroups=[sg-0e24462e33a46f81c],assignPublicIp=ENABLED}' \
  --query 'tasks[0].taskArn' --output text
echo "run id: $RUN_ID"
echo "fetch:  aws s3 sync s3://$BUCKET/$PREFIX/out/ ."
