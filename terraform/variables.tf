variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name used for tagging and naming resources."
  type        = string
  default     = "ai-doc-processing"
}

variable "environment" {
  description = "Deployment environment identifier (for example, dev, staging, prod)."
  type        = string
  default     = "dev"
}

