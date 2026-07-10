variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "env" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "max_instances" {
  type    = number
  default = 5
}

variable "r2_bucket_name" {
  type = string
}

variable "r2_account_id" {
  type = string
}

variable "runpod_endpoint_id" {
  type = string
}

variable "firebase_sa_path" {
  description = "Path to Firebase SA JSON inside the container (relative to WORKDIR /app)"
  type        = string
}

variable "dev_price_1yen" {
  type    = string
  default = "0"
}

variable "r2_access_key_id" {
  type      = string
  sensitive = true
}

variable "r2_secret_access_key" {
  type      = string
  sensitive = true
}

variable "runpod_api_key" {
  type      = string
  sensitive = true
}

variable "gemini_api_key" {
  type      = string
  sensitive = true
}

variable "autoscaler_runpod_api_key" {
  description = "RunPod API key used by the autoscaler service (read from autoscaler/.env)"
  type        = string
  sensitive   = true
}

variable "stripe_secret_key" {
  description = "Stripe secret key for credit pack checkout sessions"
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook signing secret (used to verify /credits/stripe-webhook)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "sendgrid_api_key" {
  description = "SendGrid API key for order confirmation emails"
  type        = string
  sensitive   = true
  default     = ""
}

variable "frontend_public_url" {
  description = "Public URL of the frontend (used as Stripe checkout success/cancel redirect base)"
  type        = string
  default     = ""
}

variable "r2_public_base_url" {
  description = "Public base URL for R2 bucket objects (e.g. https://pub-xxx.r2.dev)"
  type        = string
  default     = ""
}
