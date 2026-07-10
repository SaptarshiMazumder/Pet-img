resource "google_cloud_run_v2_service" "backend" {
  name     = "pet-app-backend"
  location = "asia-northeast1"

  deletion_protection = false

  template {
    service_account = google_service_account.backend.email

    scaling {
      max_instance_count = 3
    }

    containers {
      # Placeholder image so the service can be created now.
      # Your CI/CD will deploy the REAL backend image on top of this.
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "R2_BUCKET_NAME"
        value = var.r2_bucket_name
      }
      env {
        name  = "R2_ACCOUNT_ID"
        value = var.r2_account_id
      }
      env {
        name  = "R2_PUBLIC_BASE_URL"
        value = var.r2_public_base_url
      }

      env {
        name = "R2_SECRET_ACCESS_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.r2_secret_access_key.secret_id
            version = "latest"
          }
        }
      }


    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }



  depends_on = [
    google_project_service.run,
    google_secret_manager_secret_iam_member.backend_r2_secret,
  ]

}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "pet-app-frontend"
  location = "asia-northeast1"

  deletion_protection = false

  template {
    service_account = google_service_account.frontend.email

    scaling {
      max_instance_count = 1
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      ports {
        container_port = 80
      }

      env {
        name  = "API_BASE"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }



  depends_on = [google_project_service.run]
}

