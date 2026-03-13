## AI Document Processing – Terraform (this branch)

**This branch (`terraform`)** contains infrastructure (Terraform) and a copy of `function/` used to package the Lambda. For Lambda-only changes, use the `function` branch; merge into `main` to keep both in sync.

---

Phase 1 + Phase 2: S3, DynamoDB, IAM, and the document-processing Lambda (S3 trigger → Textract → DynamoDB). Phase 3 adds API Gateway (HTTP API), an API Lambda for querying results, and a static frontend (S3 + CloudFront, HTTPS).

### Prerequisites

- AWS account with permissions to create S3, DynamoDB, IAM, Lambda, API Gateway, and CloudFront resources
- Terraform version **1.5 or later**
- Configured AWS credentials (for example via `aws configure`, environment variables, or an assumed role)

### Project Structure (on this branch)

- `terraform/` – Terraform configuration (Phase 1 + Phase 2 + Phase 3)
  - `provider.tf` – Terraform, AWS, and archive provider
  - `variables.tf`, `s3.tf`, `dynamodb.tf`, `iam.tf` – Phase 1
  - `lambda.tf` – Processor Lambda, S3 event trigger, permission (packages `../function`)
  - `api_lambda.tf` – API Lambda (Phase 3), IAM, same `../function` package, handler `api.lambda_handler`
  - `api_gateway.tf` – HTTP API, routes `GET /results` and `GET /results/{document_id}`
  - `frontend.tf` – Static frontend: S3 bucket, CloudFront distribution (HTTPS only), uploads `frontend/`
  - `outputs.tf` – Bucket names, table name, Lambda ARNs, **api_endpoint**, **frontend_url** (Phase 3)
  - `terraform.tfvars.example` – Example variable values
- `frontend/` – Static site (Phase 3): `index.html`, `config.js.tpl` (API URL injected by Terraform)
- `function/` – Lambda source (processor + API handler)
  - `processor.py` – S3-triggered document processing (Phase 2)
  - `api.py` – HTTP API handler for listing/getting results (Phase 3)

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

After a successful apply, Terraform will output the upload bucket name, processed bucket name, DynamoDB table name, Lambda ARNs, (Phase 3) **api_endpoint**, and **frontend_url** (HTTPS).

### Phase 3: Using the API

Once Phase 3 is applied, you can query document results over HTTP.

**Get the API base URL:**

```bash
cd terraform
terraform output -raw api_endpoint
```

**List results** (optional query: `?limit=10`):

```bash
API=$(terraform output -raw api_endpoint)
curl "${API}/results"
# or with limit:
curl "${API}/results?limit=5"
```

**Get one result by document_id:**

```bash
DOC_ID="your-document-id.pdf"   # e.g. the object key used in upload
curl "${API}/results/${DOC_ID}"
```

Responses are JSON with `Content-Type: application/json` and CORS headers for browser use.

### Phase 3: Static frontend (HTTPS)

The frontend is hosted on S3 and served via CloudFront with **HTTPS only** (HTTP redirects to HTTPS).

**Open the frontend:**

```bash
cd terraform
terraform output -raw frontend_url
# Open that URL in a browser (e.g. https://xxxx.cloudfront.net)
```

The page lists document results from the API and lets you open a single result. The API base URL is injected into `config.js` at apply time from `api_endpoint`.

### Cleaning Up

To destroy all infrastructure (Phases 1–3):

```bash
cd terraform
terraform destroy
```

