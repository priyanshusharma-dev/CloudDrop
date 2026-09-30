import uuid

from common import (
    ALLOWED_EXPIRY_SECONDS,
    BUCKET_NAME,
    CLEANUP_TTL_BUFFER,
    MAX_FILE_SIZE,
    PRESIGN_EXPIRES_IN,
    get_owner_id,
    now_epoch,
    parse_body,
    response,
    s3,
    sanitize_file_name,
    table,
)


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return response(200)

    owner_id = get_owner_id(event)
    if not owner_id:
        return response(401, {"message": "Unauthorized"})

    try:
        body = parse_body(event)
    except ValueError:
        return response(400, {"message": "Invalid JSON body"})

    file_name = body.get("fileName")
    file_size = body.get("fileSize")
    content_type = body.get("contentType") or "application/octet-stream"
    expiry_seconds = body.get("expirySeconds")

    if not file_name or not isinstance(file_name, str):
        return response(400, {"message": "fileName is required"})
    if not isinstance(file_size, (int, float)) or file_size <= 0:
        return response(400, {"message": "fileSize must be a positive number"})
    if file_size > MAX_FILE_SIZE:
        return response(400, {"message": "File exceeds the 10 MB limit"})
    if expiry_seconds not in ALLOWED_EXPIRY_SECONDS:
        return response(400, {"message": "Invalid expiry option"})

    safe_name = sanitize_file_name(file_name)
    file_id = str(uuid.uuid4())
    s3_key = f"{owner_id}/{file_id}/{safe_name}"

    uploaded_at = now_epoch()
    expires_at = uploaded_at + int(expiry_seconds)

    table().put_item(
        Item={
            "fileId": file_id,
            "ownerId": owner_id,
            "fileName": safe_name,
            "s3Key": s3_key,
            "size": int(file_size),
            "contentType": content_type,
            "uploadedAt": uploaded_at,
            "expiresAt": expires_at,
            "downloadCount": 0,
            "ttl": expires_at + CLEANUP_TTL_BUFFER,
        }
    )

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key, "ContentType": content_type},
        ExpiresIn=PRESIGN_EXPIRES_IN,
    )

    return response(
        200,
        {
            "fileId": file_id,
            "uploadUrl": upload_url,
            "s3Key": s3_key,
            "expiresAt": expires_at,
        },
    )
