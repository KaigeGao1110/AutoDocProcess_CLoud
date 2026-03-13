# Package Lambda source from function/ (same repo; when applying from main or terraform branch)
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../function"
  output_path = "${path.module}/lambda.zip"
}

# Document processing Lambda: S3 trigger -> Textract -> DynamoDB
resource "aws_lambda_function" "processor" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name   = "${var.project_name}-processor-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  runtime         = "python3.12"
  handler         = "processor.lambda_handler"
  timeout         = 60
  memory_size     = 256

  environment {
    variables = {
      UPLOAD_BUCKET    = aws_s3_bucket.upload_bucket.id
      PROCESSED_BUCKET = aws_s3_bucket.processed_bucket.id
      RESULTS_TABLE    = aws_dynamodb_table.document_results.name
    }
  }
}

# Allow S3 to invoke the Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_bucket.arn
}

# Notify Lambda on new objects in the upload bucket
resource "aws_s3_bucket_notification" "upload_notify" {
  bucket = aws_s3_bucket.upload_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
