from common import BUCKET_NAME, get_owner_id, response, s3, table


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return response(200)

    owner_id = get_owner_id(event)
    if not owner_id:
        return response(401, {"message": "Unauthorized"})

    file_id = event.get("pathParameters", {}).get("id")
    item = table().get_item(Key={"fileId": file_id}).get("Item")

    if not item or item.get("ownerId") != owner_id:
        return response(404, {"message": "File not found"})

    s3.delete_object(Bucket=BUCKET_NAME, Key=item["s3Key"])
    table().delete_item(Key={"fileId": file_id})

    return response(200, {"message": "Deleted"})
