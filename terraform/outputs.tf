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

output "lambda_processor_arn" {
  description = "ARN of the document processing Lambda function (Phase 2)."
  value       = aws_lambda_function.processor.arn
}

output "lambda_processor_name" {
  description = "Name of the document processing Lambda function (Phase 2)."
  value       = aws_lambda_function.processor.function_name
}

output "api_endpoint" {
  description = "Base URL of the Phase 3 HTTP API (GET /results, GET /results/{document_id})."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "frontend_url" {
  description = "HTTPS URL of the static frontend (CloudFront)."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "frontend_domain" {
  description = "CloudFront domain name for the frontend."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

