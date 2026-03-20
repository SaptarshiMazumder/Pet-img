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

# Razorpay (disabled — kept for reference)
# variable "razorpay_key_id" {
#   type      = string
#   sensitive = true
# }
#
# variable "razorpay_key_secret" {
#   type      = string
#   sensitive = true
# }

variable "komoju_secret_key" {
  type      = string
  sensitive = true
}

variable "komoju_publishable_key" {
  type      = string
  sensitive = true
}

variable "komoju_merchant_id" {
  type = string
}

variable "gelato_api_key" {
  type      = string
  sensitive = true
}
