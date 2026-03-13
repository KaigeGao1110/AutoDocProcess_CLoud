"""
Document processing Lambda: triggered by S3 upload, calls Textract (FORMS),
extracts key-value pairs, and writes results to DynamoDB.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (injected by Terraform)
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET", "")
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "")
RESULTS_TABLE = os.environ.get("RESULTS_TABLE", "")


def lambda_handler(event, context):
    """
    Handle S3 ObjectCreated event: run Textract AnalyzeDocument (FORMS),
    parse key-value pairs, and write to DynamoDB (and optionally to processed bucket).
    """
    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3":
            continue
        try:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            # Normalize key for document_id (replace path separators)
            document_id = key.replace("/", "_").strip("_") or str(uuid.uuid4())
            process_one(bucket, key, document_id)
        except Exception as e:
            logger.exception("Failed to process S3 record: %s", e)
            # Optionally write a failed item; for now we log and continue
            raise
    return {"statusCode": 200}


def process_one(bucket, key, document_id):
    """Process a single S3 object: Textract -> DynamoDB (and optional S3 JSON)."""
    textract = boto3.client("textract")
    dynamodb = boto3.resource("dynamodb")
    s3 = boto3.client("s3")

    upload_time = datetime.now(timezone.utc).isoformat()
    table = dynamodb.Table(RESULTS_TABLE)

    try:
        response = textract.analyze_document(
            Document={"S3Object": {"Bucket": bucket, "Name": key}},
            FeatureTypes=["FORMS"],
        )
        extracted_data = parse_key_value_blocks(response.get("Blocks", []))
        status = "processed"
        error_message = None
    except Exception as e:
        logger.exception("Textract or parse failed for s3://%s/%s", bucket, key)
        extracted_data = {}
        status = "failed"
        error_message = str(e)

    item = {
        "document_id": document_id,
        "upload_time": upload_time,
        "extracted_data": extracted_data,
        "status": status,
    }
    if error_message:
        item["error_message"] = error_message

    table.put_item(Item=serialize_dynamo_item(item))

    # Optional: write JSON artifact to processed bucket for audit
    if PROCESSED_BUCKET and status == "processed":
        try:
            payload = json.dumps(
                {
                    "document_id": document_id,
                    "upload_time": upload_time,
                    "extracted_data": extracted_data,
                    "status": status,
                },
                indent=2,
            )
            s3.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=f"results/{document_id}.json",
                Body=payload.encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as e:
            logger.warning("Failed to write JSON to processed bucket: %s", e)


def parse_key_value_blocks(blocks):
    """
    Build a key -> value map from Textract Blocks with BlockType KEY_VALUE_SET.
    Keys and values are linked via Relationships; text comes from WORD/LINE children.
    """
    by_id = {b["Id"]: b for b in blocks}
    result = {}

    for block in blocks:
        if block.get("BlockType") != "KEY_VALUE_SET":
            continue
        if block.get("EntityTypes") and "KEY" in block.get("EntityTypes", []):
            value_block_id = None
            for rel in block.get("Relationships", []):
                if rel.get("Type") == "VALUE":
                    for ref in rel.get("Ids", []):
                        value_block_id = ref
                        break
                    break
            key_text = get_text_from_block(block, by_id)
            value_text = ""
            if value_block_id and value_block_id in by_id:
                value_text = get_text_from_block(by_id[value_block_id], by_id)
            if key_text:
                result[key_text.strip()] = value_text.strip()

    return result


def get_text_from_block(block, by_id):
    """Extract concatenated text from a block and its WORD/LINE children."""
    parts = []
    for rel in block.get("Relationships", []):
        if rel.get("Type") != "CHILD":
            continue
        for ref in rel.get("Ids", []):
            child = by_id.get(ref, {})
            if child.get("BlockType") in ("WORD", "LINE"):
                parts.append(child.get("Text", ""))
    return " ".join(parts) if parts else ""


def serialize_dynamo_item(item):
    """Ensure item is suitable for DynamoDB PutItem (maps and strings)."""
    out = {}
    for k, v in item.items():
        if isinstance(v, dict):
            out[k] = {str(kk): str(vv) for kk, vv in v.items()}
        else:
            out[k] = str(v)
    return out
