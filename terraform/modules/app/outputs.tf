output "frontend_url" {
  description = "Public URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "Public URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "autoscaler_url" {
  description = "Public URL of the autoscaler Cloud Run service"
  value       = google_cloud_run_v2_service.autoscaler.uri
}

output "artifact_registry" {
  description = "Artifact Registry base path for pushing images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}
