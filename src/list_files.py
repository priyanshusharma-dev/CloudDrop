from boto3.dynamodb.conditions import Key

from common import get_owner_id, now_epoch, response, table


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return response(200)

    owner_id = get_owner_id(event)
    if not owner_id:
        return response(401, {"message": "Unauthorized"})

    result = table().query(
        IndexName="ownerId-index",
        KeyConditionExpression=Key("ownerId").eq(owner_id),
    )

    now = now_epoch()
    files = []
    for item in result.get("Items", []):
        time_left = int(item["expiresAt"]) - now
        files.append(
            {
                "fileId": item["fileId"],
                "fileName": item["fileName"],
                "size": int(item["size"]),
                "contentType": item.get("contentType"),
                "uploadedAt": int(item["uploadedAt"]),
                "expiresAt": int(item["expiresAt"]),
                "downloadCount": int(item.get("downloadCount", 0)),
                "timeLeft": max(time_left, 0),
                "status": "expired" if time_left <= 0 else "active",
            }
        )

    files.sort(key=lambda f: f["uploadedAt"], reverse=True)

    return response(200, {"files": files})
