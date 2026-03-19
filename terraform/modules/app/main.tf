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

resource "google_service_account" "frontend" {
  account_id   = "${local.prefix}-frontend"
  display_name = "Pet Gen ${var.env} - Frontend"
}

# ── Cloud Run: Autoscaler ────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "autoscaler" {
  name     = "${local.prefix}-autoscaler"
  location = var.region

  template {
    service_account = google_service_account.autoscaler.email

    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }

    containers {
      image = "${local.image_base}/autoscaler:${var.image_tag}"

      resources {
        cpu_idle = false
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
      min_instance_count = 1
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
        name  = "RAZORPAY_KEY_ID"
        value = var.razorpay_key_id
      }
      env {
        name  = "RAZORPAY_KEY_SECRET"
        value = var.razorpay_key_secret
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

# ── Cloud Run: Frontend ──────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.prefix}-frontend"
  location = var.region

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = "${local.image_base}/frontend:${var.image_tag}"

      ports {
        container_port = 80
      }

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }

      env {
        name  = "API_BASE"
        value = google_cloud_run_v2_service.backend.uri
      }
      env {
        name  = "BACKEND_UPSTREAM"
        value = trimprefix(google_cloud_run_v2_service.backend.uri, "https://")
      }
    }
  }

  depends_on = [google_project_service.run]
}

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

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
