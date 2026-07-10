variable "r2_bucket_name" {
  type        = string
  description = "Cloudflare R2 bucket name"
}

variable "r2_account_id" {
  type        = string
  description = "Cloudflare R2 account ID"
}

variable "r2_public_base_url" {
  type        = string
  description = "Public base URL for R2 objects (Cloudflare CDN)"
}

variable "r2_secret_access_key" {
  type        = string
  description = "Cloudflare R2 secret access key"
  sensitive   = true
}
