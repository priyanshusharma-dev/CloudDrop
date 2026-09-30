from common import get_owner_id, response, table


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

    request_context = event.get("requestContext", {})
    domain_name = request_context.get("domainName")
    stage = request_context.get("stage")

    if domain_name and stage:
        base_url = f"https://{domain_name}/{stage}"
    else:
        base_url = ""

    share_url = f"{base_url}/share/{file_id}"

    return response(200, {"shareUrl": share_url, "fileId": file_id})
