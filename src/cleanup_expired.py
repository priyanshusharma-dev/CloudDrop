import logging

from common import BUCKET_NAME, now_epoch, s3, table

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    now = now_epoch()
    removed = 0
    scan_kwargs = {}

    while True:
        result = table().scan(**scan_kwargs)
        for item in result.get("Items", []):
            if int(item["expiresAt"]) < now:
                s3.delete_object(Bucket=BUCKET_NAME, Key=item["s3Key"])
                table().delete_item(Key={"fileId": item["fileId"]})
                removed += 1

        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    logger.info("Cleanup finished: removed=%d", removed)
    return {"removed": removed}
