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

