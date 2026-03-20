#!/bin/bash
set -e

ENV=${1:-dev}
TAG=${2:-$(git rev-parse --short HEAD)}

case $ENV in
  dev)     PROJECT=pet-gen-dev ;;
  staging) PROJECT=pet-gen-staging ;;
  prod)    PROJECT=pet-gen-prod ;;
  *) echo "Usage: $0 [dev|staging|prod] [tag]"; exit 1 ;;
esac

REGION=asia-northeast1
REGISTRY=$REGION-docker.pkg.dev/$PROJECT/pet-gen-$ENV

echo "==> Building and pushing to $REGISTRY (tag: $TAG)"

gcloud config set project $PROJECT
gcloud auth configure-docker $REGION-docker.pkg.dev

docker build -t $REGISTRY/backend:$TAG -f backend/Dockerfile .
docker push $REGISTRY/backend:$TAG

docker build -t $REGISTRY/autoscaler:$TAG -f autoscaler/Dockerfile .
docker push $REGISTRY/autoscaler:$TAG

docker build --no-cache -t $REGISTRY/frontend:$TAG ./frontend-ng
docker push $REGISTRY/frontend:$TAG

echo "==> Done. Run: cd terraform/environments/$ENV && terraform apply -var=\"image_tag=$TAG\""
