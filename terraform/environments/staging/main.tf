terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "app" {
  source = "../../modules/app"

  project_id         = var.project_id
  env                = "staging"
  region             = var.region
  image_tag          = var.image_tag
  max_instances      = 5
  dev_price_1yen     = "0"

  r2_bucket_name     = var.r2_bucket_name
  r2_account_id      = var.r2_account_id
  runpod_endpoint_id = var.runpod_endpoint_id
  firebase_sa_path   = var.firebase_sa_path

  r2_access_key_id     = var.r2_access_key_id
  r2_secret_access_key = var.r2_secret_access_key
  runpod_api_key       = var.runpod_api_key
  gemini_api_key       = var.gemini_api_key
  gelato_api_key       = var.gelato_api_key
}

output "frontend_url"      { value = module.app.frontend_url }
output "backend_url"       { value = module.app.backend_url }
output "autoscaler_url"    { value = module.app.autoscaler_url }
output "artifact_registry" { value = module.app.artifact_registry }
