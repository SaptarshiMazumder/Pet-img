terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

locals {
  prefix     = "pet-gen-${var.env}"
  image_base = "${var.region}-docker.pkg.dev/${var.project_id}/${local.prefix}"
}

# ── Enable required APIs ─────────────────────────────────────────────────────

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "ar" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

# ── Artifact Registry ────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = local.prefix
  format        = "DOCKER"
  depends_on    = [google_project_service.ar]
}

# ── Service Accounts ─────────────────────────────────────────────────────────

resource "google_service_account" "backend" {
  account_id   = "${local.prefix}-backend"
  display_name = "Pet Gen ${var.env} - Backend"
}

resource "google_service_account" "autoscaler" {
  account_id   = "${local.prefix}-scaler"
  display_name = "Pet Gen ${var.env} - Autoscaler"
}


# ── Cloud Run: Autoscaler ────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "autoscaler" {
  name     = "${local.prefix}-autoscaler"
  location = var.region

  template {
    service_account = google_service_account.autoscaler.email

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = "${local.image_base}/autoscaler:${var.image_tag}"

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "RUNPOD_ENDPOINT_ID"
        value = var.runpod_endpoint_id
      }
      env {
        name  = "RUNPOD_API_KEY"
        value = var.runpod_api_key
      }
      env {
        name  = "FIREBASE_SERVICE_ACCOUNT_KEY"
        value = var.firebase_sa_path
      }
    }
  }

  depends_on = [google_project_service.run]
}

# ── Cloud Run: Backend ───────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.prefix}-backend"
  location = var.region

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = "${local.image_base}/backend:${var.image_tag}"

      resources {
        cpu_idle = false
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }

      env {
        name  = "FIREBASE_SERVICE_ACCOUNT_KEY"
        value = var.firebase_sa_path
      }
      env {
        name  = "R2_BUCKET_NAME"
        value = var.r2_bucket_name
      }
      env {
        name  = "R2_ACCOUNT_ID"
        value = var.r2_account_id
      }
      env {
        name  = "R2_ACCESS_KEY_ID"
        value = var.r2_access_key_id
      }
      env {
        name  = "R2_SECRET_ACCESS_KEY"
        value = var.r2_secret_access_key
      }
      env {
        name  = "RUNPOD_ENDPOINT_ID"
        value = var.runpod_endpoint_id
      }
      env {
        name  = "RUNPOD_API_KEY"
        value = var.runpod_api_key
      }
      env {
        name  = "AUTOSCALER_URL"
        value = google_cloud_run_v2_service.autoscaler.uri
      }
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
      env {
        name  = "GELATO_API_KEY"
        value = var.gelato_api_key
      }
      env {
        name  = "DEV_PRICE_1YEN"
        value = var.dev_price_1yen
      }
    }
  }

  depends_on = [google_project_service.run]
}

# Frontend is served via Firebase Hosting — no Cloud Run service needed.

# ── IAM: public invoker ──────────────────────────────────────────────────────

resource "google_cloud_run_v2_service_iam_member" "autoscaler_public" {
  location = var.region
  name     = google_cloud_run_v2_service.autoscaler.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

