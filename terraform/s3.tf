locals {
  upload_bucket_name    = "${var.project_name}-upload-${var.environment}"
  processed_bucket_name = "${var.project_name}-processed-${var.environment}"
}

resource "aws_s3_bucket" "upload_bucket" {
  bucket        = local.upload_bucket_name
  force_destroy = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "document-upload"
  }
}

resource "aws_s3_bucket" "processed_bucket" {
  bucket        = local.processed_bucket_name
  force_destroy = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "document-processed"
  }
}

