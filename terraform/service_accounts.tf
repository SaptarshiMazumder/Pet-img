# Identities the Cloud Run services will run AS
resource "google_service_account" "backend" {
  account_id   = "pet-app-backend"
  display_name = "Pet App - Backend (Cloud Run)"

  depends_on = [google_project_service.iam]
}

resource "google_service_account" "frontend" {
  account_id   = "pet-app-frontend"
  display_name = "Pet App - Frontend (Cloud Run)"

  depends_on = [google_project_service.iam]
}
