## AI Document Processing – Terraform (this branch)

**This branch (`terraform`)** contains infrastructure (Terraform) and a copy of `function/` used to package the Lambda. For Lambda-only changes, use the `function` branch; merge into `main` to keep both in sync.

---

Phase 1 + Phase 2: S3, DynamoDB, IAM, and the document-processing Lambda (S3 trigger → Textract → DynamoDB). Phase 3 will add API Gateway and a frontend.

### Prerequisites

- AWS account with permissions to create S3, DynamoDB, IAM, and Lambda resources
- Terraform version **1.5 or later**
- Configured AWS credentials (for example via `aws configure`, environment variables, or an assumed role)

### Project Structure (on this branch)

- `terraform/` – Terraform configuration (Phase 1 + Phase 2)
  - `provider.tf` – Terraform, AWS, and archive provider
  - `variables.tf`, `s3.tf`, `dynamodb.tf`, `iam.tf` – Phase 1
  - `lambda.tf` – Lambda function, S3 event trigger, permission (packages `../function`)
  - `outputs.tf` – Bucket names, table name, Lambda role ARN, Lambda processor ARN/name
  - `terraform.tfvars.example` – Example variable values
- `function/` – Lambda source (packaged by `terraform/lambda.tf`; for edits prefer the `function` branch)

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

