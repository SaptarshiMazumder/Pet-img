# A Docker image repository, Terraform-managed
resource "google_artifact_registry_repository" "images" {
  location      = "asia-northeast1"
  repository_id = "pet-app-images"
  description   = "Docker images for the pet app (Terraform-managed)"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry]
}
