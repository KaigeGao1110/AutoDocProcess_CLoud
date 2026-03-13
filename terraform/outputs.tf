output "upload_bucket" {
  description = "Name of the S3 bucket used for document uploads."
  value       = aws_s3_bucket.upload_bucket.bucket
}

output "processed_bucket" {
  description = "Name of the S3 bucket used for processed documents."
  value       = aws_s3_bucket.processed_bucket.bucket
}

output "dynamodb_table" {
  description = "Name of the DynamoDB table storing document results."
  value       = aws_dynamodb_table.document_results.name
}

output "lambda_role_arn" {
  description = "IAM role ARN to be used by the document processing Lambda."
  value       = aws_iam_role.lambda_role.arn
}

