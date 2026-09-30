#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-clouddrop}"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-south-1)}"
REGION="${REGION:-ap-south-1}"

echo "==> Looking up buckets for stack '${STACK_NAME}'"
outputs_json=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs" \
  --output json 2>/dev/null || echo "[]")

get_output() {
  echo "${outputs_json}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for o in data:
    if o['OutputKey'] == '$1':
        print(o['OutputValue'])
        break
"
}

FILES_BUCKET=$(get_output FilesBucketName || true)
WEBSITE_BUCKET=$(get_output WebsiteBucketName || true)

if [ -n "${FILES_BUCKET:-}" ]; then
  echo "==> Emptying s3://${FILES_BUCKET}"
  aws s3 rm "s3://${FILES_BUCKET}" --recursive --region "${REGION}" || true
fi

if [ -n "${WEBSITE_BUCKET:-}" ]; then
  echo "==> Emptying s3://${WEBSITE_BUCKET}"
  aws s3 rm "s3://${WEBSITE_BUCKET}" --recursive --region "${REGION}" || true
fi

echo "==> Deleting stack '${STACK_NAME}'"
sam delete --stack-name "${STACK_NAME}" --region "${REGION}" --no-prompts

echo "==> Done. All CloudDrop resources have been removed."
