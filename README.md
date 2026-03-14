## AI Document Processing

Upload a PDF or image and get structured text and form data extracted automatically. This repo provides Terraform for AWS (S3, DynamoDB, Lambda, API Gateway, CloudFront) and a static frontend with **product assistant** (chat + upload in one bar).

**This branch (`terraform`)** contains infrastructure and a copy of `function/` used to package the Lambda. For Lambda-only changes, use the `function` branch; merge into `main` to keep both in sync.

---

Phase 1 + Phase 2: S3, DynamoDB, IAM, and the document-processing Lambda (S3 trigger → Textract → DynamoDB). Phase 3 adds API Gateway (HTTP API), an API Lambda for querying results and **product assistant chat** (AWS Bedrock), a static frontend (S3 + CloudFront, HTTPS), and a **demo upload** flow (presigned URL + per-IP hourly quota) with rate limiting.

**Demo & abuse prevention (public repo):** This repository contains only code and examples. Deployed demo URLs and API endpoints are not committed. The demo enforces rate limits (API Gateway throttling), per-IP hourly upload quotas, and CORS restricted to the frontend origin. Do not abuse demo endpoints.

**Try the demo (customer testing):**  
→ **kaigegao666.com** — Ask the product assistant or upload a PDF/image to see document processing results (up to 20 uploads per IP per hour).

### Prerequisites

- AWS account with permissions to create S3, DynamoDB, IAM, Lambda, API Gateway, and CloudFront resources
- Terraform version **1.5 or later**
- Configured AWS credentials (for example via `aws configure`, environment variables, or an assumed role)

### Project Structure (on this branch)

- `terraform/` – Terraform configuration (Phase 1 + Phase 2 + Phase 3)
  - `provider.tf` – Terraform, AWS, and archive provider
  - `variables.tf`, `s3.tf`, `dynamodb.tf` (results + `demo_upload_quota` with TTL), `iam.tf` – Phase 1
  - `lambda.tf` – Processor Lambda, S3 event trigger, permission (packages `../function`)
  - `api_lambda.tf` – API Lambda (Phase 3), IAM (includes Bedrock for assistant), same `../function` package, handler `api.lambda_handler`
  - `api_gateway.tf` – HTTP API, routes `GET /results`, `GET /results/{document_id}`, `POST /demo/upload-url`, `POST /chat` (product assistant); stage throttling and CORS for frontend only
  - `frontend.tf` – Static frontend: S3 bucket, CloudFront distribution (HTTPS only), uploads `frontend/`
  - `outputs.tf` – Bucket names, table name, Lambda ARNs, **api_endpoint**, **frontend_url** (Phase 3)
  - `terraform.tfvars.example` – Example variable values
- `frontend/` – Static site (Phase 3): `index.html` (product intro, assistant bar: chat + upload, recent results), `config.js.tpl` (API URL injected by Terraform)
- `function/` – Lambda source (processor + API handler)
  - `processor.py` – S3-triggered document processing (Phase 2)
  - `api.py` – HTTP API handler: list/get results, `POST /demo/upload-url` (presigned S3 URL + quota check), `POST /chat` (product assistant via AWS Bedrock, product-only answers)

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

The page includes a short **product intro**, a **Product assistant** bar (main: chat; secondary: upload), and a list of recent results. In the assistant bar you can type a question about the product (e.g. how to upload, limits, supported formats) and get answers from an in-product assistant (AWS Bedrock); or drag/choose a file and click Upload to process a document. The app requests a presigned URL (subject to per-IP hourly quota), uploads to S3, then polls until processing completes and shows the result. Demo upload is limited (20 per IP per hour) and the API is throttled. The API base URL is injected into `config.js` at apply time from `api_endpoint`.

**Product assistant (Bedrock):** The `POST /chat` endpoint uses AWS Bedrock (configurable model ID, e.g. `zai.glm-4.7-flash`). The assistant is constrained to answer only questions about this product (upload, limits, results, usage). Enable the model in your AWS account and ensure the API Lambda role has `bedrock:InvokeModel` on the foundation model.

### Customer test steps (how to try the demo)

1. **Open the demo**  
   **Live demo:** kaigegao666.com  
   Or, if you deploy yourself, run `terraform output -raw frontend_url` in the `terraform/` directory and open that URL in a browser.

2. **Use the assistant or upload**  
   - **Chat:** Type a question in the Product assistant bar (e.g. “How do I upload?” or “What are the limits?”) and click **Send**. Replies appear below the bar.  
   - **Upload:** Click **Upload file** or drag a file into the same bar. Supported: PDF or images (e.g. .jpg, .png). When a file is selected, click **Upload**; the page shows: requesting upload URL → uploading → waiting for processing → done.

3. **View the list and results**  
   The page lists processed documents. If there is no data yet, it shows “No results yet. Upload a document above to try.” When processing finishes, the parsed result appears; the list refreshes and you can click an item to view details again.

4. **Limits**  
   - Each IP can upload at most **20** times per hour. Beyond that you’ll see “Upload limit reached for this hour. Try again later.”  
   - If you send too many requests, the API may throttle; wait a moment and retry.

### Cleaning Up

To destroy all infrastructure (Phases 1–3):

```bash
cd terraform
terraform destroy
```

