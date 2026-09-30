import json
import os
import re
import time

import boto3

REGION = os.environ.get("AWS_REGION", "ap-south-1")
TABLE_NAME = os.environ.get("TABLE_NAME", "")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXPIRY_SECONDS = {120, 900, 3600, 86400}  # 2 min, 15 min, 1 hour, 24 hours
PRESIGN_EXPIRES_IN = 300  # 5 minutes
CLEANUP_TTL_BUFFER = 86400  # DynamoDB TTL fires one day after link expiry

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client(
    "s3",
    region_name=REGION,
    endpoint_url=f"https://s3.{REGION}.amazonaws.com",
    config=boto3.session.Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)


def table():
    return dynamodb.Table(TABLE_NAME)


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


def response(status_code, body=None, headers=None):
    resp_headers = dict(CORS_HEADERS)
    if headers:
        resp_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": resp_headers,
        "body": json.dumps(body) if body is not None else "",
    }


def get_owner_id(event):
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )
    return claims.get("sub")


def parse_body(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def sanitize_file_name(name):
    name = os.path.basename(name)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:255] or "file"


def now_epoch():
    return int(time.time())
