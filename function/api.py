"""
API Lambda: HTTP API (API Gateway v2) handler for querying document results from DynamoDB.
Routes: GET /results, GET /results/{document_id}, POST /demo/upload-url.
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESULTS_TABLE = os.environ.get("RESULTS_TABLE", "")
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "").strip()
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET", "")
DEMO_QUOTA_TABLE = os.environ.get("DEMO_QUOTA_TABLE", "")
DEMO_UPLOAD_LIMIT_PER_HOUR = int(os.environ.get("DEMO_UPLOAD_LIMIT_PER_HOUR", "3") or "3")
PRESIGN_EXPIRY_SECONDS = 300
QUOTA_TTL_SECONDS = 7200


def _cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN if ALLOWED_ORIGIN else "*",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def lambda_handler(event, context):
    """
    Handle API Gateway HTTP API v2 events.
    requestContext.http.method, rawPath, pathParameters, queryStringParameters.
    """
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = (event.get("rawPath") or "").rstrip("/") or "/"
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    if method == "POST" and path == "/demo/upload-url":
        try:
            return handle_demo_upload_url(event)
        except Exception as e:
            logger.exception("Demo upload-url error: %s", e)
            return response(500, {"error": "Internal server error"})

    if method != "GET":
        return response(405, {"error": "Method not allowed"})

    if not RESULTS_TABLE:
        return response(500, {"error": "RESULTS_TABLE not configured"})

    try:
        if path == "/results":
            limit = _parse_limit(query_params.get("limit"))
            prefix = (query_params.get("prefix") or "").strip() or None
            return list_results(limit, prefix)
        if path.startswith("/results/"):
            document_id = path_params.get("document_id") or path.split("/results/", 1)[-1].split("/")[0]
            if document_id:
                return get_result(document_id)
        return response(404, {"error": "Not found"})
    except Exception as e:
        logger.exception("API error: %s", e)
        return response(500, {"error": "Internal server error"})


def list_results(limit=None, prefix=None):
    """Scan DynamoDB and return items (optional limit, optional prefix filter on document_id)."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(RESULTS_TABLE)
    scan_kw = {}
    if limit is not None and limit > 0:
        scan_kw["Limit"] = min(limit, 100)
    if prefix:
        scan_kw["FilterExpression"] = "begins_with(document_id, :p)"
        scan_kw["ExpressionAttributeValues"] = {":p": prefix}
        if limit is not None and limit > 0:
            scan_kw["Limit"] = min(50, 100)  # scan more when filtering to get enough matches
    resp = table.scan(**scan_kw)
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp and (limit is None or len(items) < limit):
        scan_kw["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        if limit is not None and limit > 0:
            scan_kw["Limit"] = min(50 if prefix else limit - len(items), 100)
        resp = table.scan(**scan_kw)
        items.extend(resp.get("Items", []))
        if limit is not None and limit > 0 and len(items) >= limit:
            break
    if limit is not None and limit > 0:
        items = items[:limit]
    return response(200, {"items": items})


def get_result(document_id):
    """Get a single item by document_id."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(RESULTS_TABLE)
    resp = table.get_item(Key={"document_id": document_id})
    item = resp.get("Item")
    if not item:
        return response(404, {"error": "Document not found", "document_id": document_id})
    return response(200, item)


def _sanitize_filename(name):
    """Keep only safe characters for S3 key; limit length."""
    if not name or not isinstance(name, str):
        return "document"
    base = os.path.basename(name)
    safe = re.sub(r"[^\w.\-]", "_", base)[:128]
    return safe or "document"


def _allowed_content_type(ct):
    """Allow common document/image types for demo upload."""
    if not ct or not isinstance(ct, str):
        return False
    ct = ct.lower().strip()
    return (
        ct.startswith("image/")
        or ct == "application/pdf"
        or ct == "application/octet-stream"
    )


def handle_demo_upload_url(event):
    """
    POST /demo/upload-url: check quota, then return presigned S3 PUT URL and document_id.
    Body (optional): { "filename": "example.pdf" }.
    """
    if not UPLOAD_BUCKET or not DEMO_QUOTA_TABLE:
        return response(503, {"error": "Demo upload not configured"})

    try:
        body = {}
        if event.get("body"):
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
    except json.JSONDecodeError:
        body = {}

    filename = (body.get("filename") or "").strip() or "document"
    filename = _sanitize_filename(filename)
    content_type = (body.get("content_type") or "").strip() or "application/octet-stream"
    if not _allowed_content_type(content_type):
        content_type = "application/octet-stream"

    request_ctx = event.get("requestContext", {}).get("http", {})
    client_ip = request_ctx.get("sourceIp") or request_ctx.get("sourceip") or "unknown"
    # Normalize for DynamoDB key (no # in IP; use hash for separator)
    client_ip = client_ip.replace(":", "_").strip() or "unknown"

    now = datetime.now(timezone.utc)
    hour_slot = now.strftime("%Y-%m-%dT%H")
    quota_id = f"{client_ip}#{hour_slot}"
    ttl_ts = int(now.timestamp()) + QUOTA_TTL_SECONDS

    dynamodb = boto3.resource("dynamodb")
    quota_table = dynamodb.Table(DEMO_QUOTA_TABLE)

    try:
        quota_table.update_item(
            Key={"id": quota_id},
            UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one, #ttl = :ttl",
            ConditionExpression="attribute_not_exists(id) OR #c < :max",
            ExpressionAttributeNames={"#c": "count", "#ttl": "ttl"},
            ExpressionAttributeValues={
                ":max": DEMO_UPLOAD_LIMIT_PER_HOUR,
                ":zero": 0,
                ":one": 1,
                ":ttl": ttl_ts,
            },
        )
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return response(429, {"error": "Demo upload limit reached", "message": "Try again later (hourly limit)."})
        logger.exception("Quota table error: %s", e)
        return response(500, {"error": "Internal server error"})

    date_prefix = now.strftime("%Y-%m-%d")
    unique = f"demo_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    object_key = f"demo/{date_prefix}/{unique}_{filename}"
    # Processor derives document_id from S3 key: key.replace("/", "_").strip("_")
    document_id = object_key.replace("/", "_").strip("_")

    s3 = boto3.client("s3")
    put_params = {"Bucket": UPLOAD_BUCKET, "Key": object_key, "ContentType": content_type}
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params=put_params,
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )

    return response(200, {
        "upload_url": upload_url,
        "document_id": document_id,
        "content_type": content_type,
    })


def _parse_limit(value):
    if value is None:
        return None
    try:
        n = int(value)
        return max(0, min(n, 100)) if n > 0 else None
    except (TypeError, ValueError):
        return None


def response(status_code, body):
    """Return API Gateway HTTP API v2 response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body, default=str),
    }
