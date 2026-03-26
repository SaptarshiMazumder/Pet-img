variable "project_id" { type = string }

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "r2_bucket_name"     { type = string }
variable "r2_account_id"      { type = string }
variable "runpod_endpoint_id" { type = string }
variable "firebase_sa_path"   { type = string }

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
variable "gelato_api_key" {
  type      = string
  sensitive = true
}
