# The secret "container"
resource "google_secret_manager_secret" "r2_secret_access_key" {
  secret_id = "r2-secret-access-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

# The secret's value (a "version")
resource "google_secret_manager_secret_version" "r2_secret_access_key" {
  secret      = google_secret_manager_secret.r2_secret_access_key.id
  secret_data = var.r2_secret_access_key
}

# Let ONLY the backend's identity read it
resource "google_secret_manager_secret_iam_member" "backend_r2_secret" {
  secret_id = google_secret_manager_secret.r2_secret_access_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}
