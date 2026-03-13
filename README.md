## AI Document Processing – Function (this branch)

**This branch (`function`)** contains only the Lambda function source. For infrastructure (Terraform), see the `terraform` branch or `main`.

---

This repo provides a serverless AI document processing pipeline on AWS.

### On this branch: `function/` only

- **`function/`** – Document processing Lambda (S3 → Textract FORMS → DynamoDB)
  - `processor.py` – handler, Textract key-value extraction, DynamoDB write, optional S3 results
  - `requirements.txt` – boto3

Deploy via the `terraform` branch (packages this folder and deploys to AWS). Prerequisites, getting started, testing, and full project structure are on `main` or `terraform`.

