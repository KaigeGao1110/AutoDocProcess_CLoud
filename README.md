## AI Document Processing – Infrastructure (Phase 1)

This repository contains the Phase 1 infrastructure for a serverless AI document processing pipeline on AWS, managed entirely with Terraform.

Phase 1 focuses on foundational resources only:
- S3 upload bucket for raw documents
- S3 processed bucket for future outputs
- DynamoDB table for document processing results
- IAM role and policy for the future Lambda processor

Later phases will add Lambda functions, Textract integration, API Gateway, and a frontend.

### Prerequisites

- AWS account with permissions to create S3, DynamoDB, and IAM resources
- Terraform version **1.5 or later**
- Configured AWS credentials (for example via `aws configure`, environment variables, or an assumed role)

### Project Structure

- `terraform/` – Terraform configuration for Phase 1
  - `provider.tf` – Terraform and AWS provider configuration
  - `variables.tf` – Shared input variables (region, project name, environment)
  - `s3.tf` – S3 buckets for uploads and processed documents
  - `dynamodb.tf` – DynamoDB table for document results
  - `iam.tf` – IAM role and policy for the Lambda processor
  - `outputs.tf` – Useful outputs (bucket names, table name, Lambda role ARN)
  - `terraform.tfvars.example` – Example variable values for local use

### Getting Started

1. Change into the Terraform directory:

   ```bash
   cd terraform
   ```

2. (Optional) Copy the example tfvars and adjust values:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Initialize Terraform:

   ```bash
   terraform init
   ```

4. Format and validate the configuration:

   ```bash
   terraform fmt -recursive
   terraform validate
   ```

5. Review the execution plan:

   ```bash
   terraform plan
   ```

6. Apply the changes:

   ```bash
   terraform apply
   ```

After a successful apply, Terraform will output the upload bucket name, processed bucket name, DynamoDB table name, and Lambda role ARN. These values will be used in later phases for Lambda, Textract, and API Gateway.

### Cleaning Up

To destroy the Phase 1 infrastructure:

```bash
cd terraform
terraform destroy
```

