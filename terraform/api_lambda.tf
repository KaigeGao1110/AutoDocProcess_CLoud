# API Lambda (Phase 3): HTTP API handler – read-only DynamoDB + CloudWatch Logs

resource "aws_iam_role" "api_lambda_role" {
  name = "${var.project_name}-api-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "api_lambda_policy" {
  name        = "${var.project_name}-api-lambda-policy-${var.environment}"
  description = "Permissions for the API Lambda to read DynamoDB, write logs, demo upload (S3 presign + quota table)."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.document_results.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:ConditionCheckItem"
        ]
        Resource = aws_dynamodb_table.demo_upload_quota.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.upload_bucket.arn}/demo/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_lambda_attach" {
  role       = aws_iam_role.api_lambda_role.name
  policy_arn = aws_iam_policy.api_lambda_policy.arn
}

# API Lambda: same zip as processor, different handler and role
resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name   = "${var.project_name}-api-${var.environment}"
  role            = aws_iam_role.api_lambda_role.arn
  runtime         = "python3.12"
  handler         = "api.lambda_handler"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      RESULTS_TABLE             = aws_dynamodb_table.document_results.name
      ALLOWED_ORIGIN            = "*"
      UPLOAD_BUCKET             = aws_s3_bucket.upload_bucket.id
      DEMO_QUOTA_TABLE          = aws_dynamodb_table.demo_upload_quota.name
      DEMO_UPLOAD_LIMIT_PER_HOUR = "20"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.api_lambda_attach]
}
