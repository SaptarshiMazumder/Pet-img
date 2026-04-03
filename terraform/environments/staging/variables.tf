# ── Static per-environment config (set in terraform.tfvars) ──────────────────
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "r2_bucket_name" {
  type = string
}

variable "r2_account_id" {
  type = string
}

variable "firebase_sa_path" {
  type = string
}

variable "r2_public_base_url" {
  type    = string
  default = ""
}

variable "frontend_public_url" {
  type    = string
  default = ""
}

variable "dev_price_1yen" {
  type    = string
  default = "0"
}

# ── Credentials (exported as TF_VAR_* by scripts/deploy.sh) ──────────────────
# Do NOT set these in terraform.tfvars — read from backend/.env and autoscaler/.env.
variable "r2_access_key_id" {
  type      = string
  sensitive = true
}

variable "r2_secret_access_key" {
  type      = string
  sensitive = true
}

variable "runpod_endpoint_id" {
  type = string
}

variable "runpod_api_key" {
  type      = string
  sensitive = true
}

variable "autoscaler_runpod_api_key" {
  type      = string
  sensitive = true
}

variable "gemini_api_key" {
  type      = string
  sensitive = true
}

variable "sendgrid_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "stripe_secret_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "stripe_webhook_secret" {
  type      = string
  sensitive = true
  default   = ""
}
