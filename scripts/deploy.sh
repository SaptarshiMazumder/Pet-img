#!/usr/bin/env bash
# scripts/deploy.sh — Build, push, and deploy to a target environment.
#
# Credentials are read directly from the service .env files and exported as
# TF_VAR_* so Terraform picks them up automatically.
# terraform.tfvars holds only static per-environment config (project, region,
# paths) — nothing that can drift between local and cloud.
#
# Usage:
#   ./scripts/deploy.sh [dev|staging|prod] [image-tag]
#   ./scripts/deploy.sh dev              # uses current git short SHA as tag
#   ./scripts/deploy.sh prod v2.1.0      # explicit tag

set -euo pipefail

ENV=${1:-dev}
TAG=${2:-$(git rev-parse --short HEAD)}

case $ENV in
  dev)
    PROJECT=pet-gen-dev
    BACKEND_ENV=backend/.env
    AUTOSCALER_ENV=autoscaler/.env
    ;;
  staging)
    PROJECT=pet-gen-staging
    BACKEND_ENV=backend/.env.staging
    AUTOSCALER_ENV=autoscaler/.env.staging
    ;;
  prod)
    PROJECT=pet-gen-prod
    BACKEND_ENV=backend/.env.prod
    AUTOSCALER_ENV=autoscaler/.env.prod
    ;;
  *)
    echo "Usage: $0 [dev|staging|prod] [image-tag]"
    exit 1
    ;;
esac

# ── Read a single value from a .env file ──────────────────────────────────────
env_get() { grep -E "^${2}=" "${1}" 2>/dev/null | head -1 | cut -d= -f2-; }

for f in "$BACKEND_ENV" "$AUTOSCALER_ENV"; do
  [[ -f "$f" ]] || { echo "ERROR: env file not found: $f"; exit 1; }
done

# ── Export secrets as TF_VAR_* (read from .env files, never from tfvars) ──────
export TF_VAR_r2_access_key_id=$(env_get "$BACKEND_ENV" R2_ACCESS_KEY_ID)
export TF_VAR_r2_secret_access_key=$(env_get "$BACKEND_ENV" R2_SECRET_ACCESS_KEY)
export TF_VAR_runpod_endpoint_id=$(env_get "$BACKEND_ENV" RUNPOD_ENDPOINT_ID)
export TF_VAR_runpod_api_key=$(env_get "$BACKEND_ENV" RUNPOD_API_KEY)
export TF_VAR_autoscaler_runpod_api_key=$(env_get "$AUTOSCALER_ENV" RUNPOD_API_KEY)
export TF_VAR_gemini_api_key=$(env_get "$BACKEND_ENV" GEMINI_API_KEY)
export TF_VAR_sendgrid_api_key=$(env_get "$BACKEND_ENV" SEND_GRID_API_KEY)

# Optional — only exported when present in the env file
_stripe_sk=$(env_get "$BACKEND_ENV" STRIPE_SECRET_KEY || true)
_stripe_wh=$(env_get "$BACKEND_ENV" STRIPE_WEBHOOK_SECRET || true)
[[ -n "$_stripe_sk" ]] && export TF_VAR_stripe_secret_key="$_stripe_sk"
[[ -n "$_stripe_wh" ]] && export TF_VAR_stripe_webhook_secret="$_stripe_wh"

echo "==> Credentials loaded"
printf "    %-28s %s\n" "RunPod endpoint:"         "$(env_get "$BACKEND_ENV" RUNPOD_ENDPOINT_ID)"
printf "    %-28s %s...\n" "Backend RunPod key:"   "$(env_get "$BACKEND_ENV" RUNPOD_API_KEY | cut -c1-16)"
printf "    %-28s %s...\n" "Autoscaler RunPod key:" "$(env_get "$AUTOSCALER_ENV" RUNPOD_API_KEY | cut -c1-16)"

# ── Docker build + push ────────────────────────────────────────────────────────
REGION=asia-northeast1
REGISTRY=$REGION-docker.pkg.dev/$PROJECT/pet-gen-$ENV

echo ""
echo "==> Building and pushing to $REGISTRY  (tag: $TAG)"

gcloud config set project "$PROJECT"
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

docker build -t "$REGISTRY/backend:$TAG"    -f backend/Dockerfile .
docker push "$REGISTRY/backend:$TAG"

docker build -t "$REGISTRY/autoscaler:$TAG" -f autoscaler/Dockerfile .
docker push "$REGISTRY/autoscaler:$TAG"

docker build --no-cache -t "$REGISTRY/frontend:$TAG" ./frontend-ng
docker push "$REGISTRY/frontend:$TAG"

# ── Terraform apply ────────────────────────────────────────────────────────────
echo ""
echo "==> Applying Terraform for: $ENV"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../terraform/environments/$ENV"

terraform init -input=false -upgrade
terraform apply -auto-approve -var="image_tag=$TAG"

echo ""
echo "==> Done"
terraform output
