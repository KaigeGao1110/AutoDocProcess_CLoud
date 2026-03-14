resource "aws_dynamodb_table" "document_results" {
  name         = "${var.project_name}-results"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "document_id"

  attribute {
    name = "document_id"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "document-results"
  }
}

# Demo upload quota: per-IP hourly limit to prevent abuse (TTL for auto cleanup)
resource "aws_dynamodb_table" "demo_upload_quota" {
  name         = "${var.project_name}-demo-quota-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "demo-upload-quota"
  }
}

