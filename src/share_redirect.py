from common import BUCKET_NAME, PRESIGN_EXPIRES_IN, now_epoch, s3, table

EXPIRED_HTML = """<!DOCTYPE html>
<html>
<head><title>Link expired</title>
<style>body{{font-family:sans-serif;text-align:center;margin-top:15%;color:#333}}</style>
</head>
<body>
<h1>This link has expired</h1>
<p>{message}</p>
</body>
</html>"""


def _html_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "text/html"},
        "body": EXPIRED_HTML.format(message=message),
    }


def handler(event, context):
    file_id = event.get("pathParameters", {}).get("id")
    item = table().get_item(Key={"fileId": file_id}).get("Item")

    if not item:
        return _html_response(404, "This share link does not exist.")

    if now_epoch() > int(item["expiresAt"]):
        return _html_response(410, "The file is no longer available.")

    table().update_item(
        Key={"fileId": file_id},
        UpdateExpression="SET downloadCount = downloadCount + :one",
        ExpressionAttributeValues={":one": 1},
    )

    download_url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": item["s3Key"],
            "ResponseContentDisposition": f'attachment; filename="{item["fileName"]}"',
        },
        ExpiresIn=PRESIGN_EXPIRES_IN,
    )

    return {
        "statusCode": 302,
        "headers": {"Location": download_url},
        "body": "",
    }
