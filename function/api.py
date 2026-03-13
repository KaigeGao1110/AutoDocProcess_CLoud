"""
API Lambda: HTTP API (API Gateway v2) handler for querying document results from DynamoDB.
Routes: GET /results (list), GET /results/{document_id} (single item).
"""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESULTS_TABLE = os.environ.get("RESULTS_TABLE", "")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
}


def lambda_handler(event, context):
    """
    Handle API Gateway HTTP API v2 events.
    requestContext.http.method, rawPath, pathParameters, queryStringParameters.
    """
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    if method != "GET":
        return response(405, {"error": "Method not allowed"})

    if not RESULTS_TABLE:
        return response(500, {"error": "RESULTS_TABLE not configured"})

    try:
        if path == "/results" or path.rstrip("/") == "/results":
            limit = _parse_limit(query_params.get("limit"))
            return list_results(limit)
        if path.startswith("/results/"):
            document_id = path_params.get("document_id") or path.split("/results/", 1)[-1].split("/")[0]
            if document_id:
                return get_result(document_id)
        return response(404, {"error": "Not found"})
    except Exception as e:
        logger.exception("API error: %s", e)
        return response(500, {"error": "Internal server error"})


def list_results(limit=None):
    """Scan DynamoDB and return items (optional limit)."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(RESULTS_TABLE)
    scan_kw = {}
    if limit is not None and limit > 0:
        scan_kw["Limit"] = min(limit, 100)
    resp = table.scan(**scan_kw)
    items = resp.get("Items", [])
    # Handle pagination: optional, return first page only for simplicity
    while "LastEvaluatedKey" in resp and (limit is None or len(items) < limit):
        scan_kw["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        if limit is not None:
            scan_kw["Limit"] = min(limit - len(items), 100)
        resp = table.scan(**scan_kw)
        items.extend(resp.get("Items", []))
        if limit is not None and len(items) >= limit:
            items = items[:limit]
            break
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
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }
