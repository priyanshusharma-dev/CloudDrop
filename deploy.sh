#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-clouddrop}"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-south-1)}"
REGION="${REGION:-ap-south-1}"

echo "==> Building the application (SAM)"
sam build

echo "==> Deploying the stack '${STACK_NAME}' to ${REGION}"
sam deploy \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo "==> Reading stack outputs"
outputs_json=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs" \
  --output json)

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

API_URL=$(get_output ApiUrl)
USER_POOL_ID=$(get_output UserPoolId)
USER_POOL_CLIENT_ID=$(get_output UserPoolClientId)
FILES_BUCKET=$(get_output FilesBucketName)
WEBSITE_BUCKET=$(get_output WebsiteBucketName)
WEBSITE_URL=$(get_output WebsiteURL)
CLEANUP_FUNCTION=$(get_output CleanupFunctionName)

echo "==> Preparing frontend (dist/index.html)"
mkdir -p dist
sed \
  -e "s|{{API_URL}}|${API_URL}|g" \
  -e "s|{{USER_POOL_ID}}|${USER_POOL_ID}|g" \
  -e "s|{{USER_POOL_CLIENT_ID}}|${USER_POOL_CLIENT_ID}|g" \
  -e "s|{{REGION}}|${REGION}|g" \
  frontend/index.html > dist/index.html

echo "==> Uploading frontend to s3://${WEBSITE_BUCKET}"
aws s3 cp dist/index.html "s3://${WEBSITE_BUCKET}/index.html" \
  --region "${REGION}" \
  --content-type "text/html" \
  --cache-control "no-cache"

echo ""
echo "======================================================"
echo " CloudDrop deployed"
echo "======================================================"
echo " API URL:            ${API_URL}"
echo " Website URL:         ${WEBSITE_URL}"
echo " Cognito User Pool:   ${USER_POOL_ID}"
echo " Cognito Client Id:   ${USER_POOL_CLIENT_ID}"
echo " Files bucket:        ${FILES_BUCKET}"
echo ""
echo " If the website URL shows 403 Forbidden (account blocks public"
echo " buckets), open dist/index.html directly in your browser instead;"
echo " it talks to the same cloud backend."
echo ""
echo " To manually run the cleanup function:"
echo "   aws lambda invoke --function-name ${CLEANUP_FUNCTION} --region ${REGION} /tmp/cleanup-out.json && cat /tmp/cleanup-out.json"
echo "======================================================"
