#!/usr/bin/env bash
# Deploy the trade journal (data/journal/) to the private, basic-auth-gated
# CloudFront site. Run this after regenerating pages
# (run_trade_review_pages.py) whenever you want the hosted copy updated --
# regeneration alone only updates the local files, it does not auto-publish.
#
# Usage:
#   AWS_PROFILE=clarinut-gmerton ./deploy_trade_journal.sh
#
# Infra (clarinut account, us-west-2):
#   S3 bucket:            gmerton-trade-journal (private, CloudFront OAC only)
#   CloudFront dist:      E2VZA7AMN3NFDL  (d1z4hclel0mtsn.cloudfront.net)
#   Basic auth username:  gmerton
#   Basic auth password:  aws ssm get-parameter --name /trade-journal/basic-auth-password
#                          --with-decryption --query Parameter.Value --output text
#   (Changing the password requires updating the SSM param AND re-deploying the
#   gmerton-trade-journal-basicauth CloudFront Function with the new base64
#   "user:pass" -- the function can't read SSM at request time.)

set -euo pipefail
cd "$(dirname "$0")"

BUCKET=gmerton-trade-journal
DIST_ID=E2VZA7AMN3NFDL

echo "Syncing data/journal/ -> s3://$BUCKET/ ..."
aws s3 sync data/journal/ "s3://$BUCKET/" --delete

echo "Invalidating CloudFront cache ..."
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" \
  --query "Invalidation.{Id:Id,Status:Status}" --output table

echo "Done. https://d1z4hclel0mtsn.cloudfront.net/ (invalidation takes ~1-2 min to finish propagating)"
