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

# CORS so browser can send OPTIONS preflight and PUT to presigned URLs (demo upload)
resource "aws_s3_bucket_cors_configuration" "upload_bucket" {
  bucket = aws_s3_bucket.upload_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET", "HEAD"]
    allowed_origins = ["https://${aws_cloudfront_distribution.frontend.domain_name}"]
    expose_headers  = ["ETag"]
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

