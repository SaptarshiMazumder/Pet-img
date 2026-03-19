# Pet Generator

## Local development

```bash
# Start with hot-reload (frontend + backend only)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend backend --no-deps

# Same but force rebuild
docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend backend --no-deps --build

# Full stack
docker compose up
```

---

## Cloud Run deployment (GCP)

Three environments: **dev**, **staging**, **prod** — each maps to a separate GCP project.

| Environment | GCP project | Pricing |
|---|---|---|
| dev | `pet-gen-dev` | 1 yen (test) |
| staging | `pet-gen-staging` | real prices |
| prod | `pet-gen-prod` | real prices |

### Prerequisites

```bash
# Authenticate
gcloud auth login
gcloud auth application-default login

# Install Terraform >= 1.6
brew install terraform   # or https://developer.hashicorp.com/terraform/install
```

### One-time setup per environment

```bash
ENV=dev   # or staging / prod

# Create tfvars from the example
cp terraform/environments/$ENV/terraform.tfvars.example \
   terraform/environments/$ENV/terraform.tfvars
# Then fill in real values — especially firebase_sa_json:
#   firebase_sa_json = file("../../../backend/pet-gen-dev-firebase-adminsdk-fbsvc-81a081d94f.json")
```

### Build and push Docker images

Run from the repo root. Use the convenience script:

```bash
# Dev (latest tag)
bash scripts/build-push.sh dev

# Dev with a specific tag
bash scripts/build-push.sh dev abc1234

# Staging / prod
bash scripts/build-push.sh staging
bash scripts/build-push.sh prod
```

Or manually:

```bash
PROJECT=pet-gen-dev
REGION=asia-northeast1
REGISTRY=$REGION-docker.pkg.dev/$PROJECT/pet-gen-dev
TAG=latest

gcloud config set project $PROJECT
gcloud auth configure-docker $REGION-docker.pkg.dev

docker build -t $REGISTRY/backend:$TAG -f backend/Dockerfile .
docker push $REGISTRY/backend:$TAG

docker build -t $REGISTRY/autoscaler:$TAG -f autoscaler/Dockerfile .
docker push $REGISTRY/autoscaler:$TAG

docker build -t $REGISTRY/frontend:$TAG ./frontend-ng
docker push $REGISTRY/frontend:$TAG
```

> The Artifact Registry repository is created by Terraform on the first `apply`.
> Push images **after** the first apply, then run apply again if needed.

### Deploy with Terraform

```bash
cd terraform/environments/dev   # or staging / prod

terraform init
terraform plan
terraform apply
```

> **First deploy only:** The Artifact Registry repo must exist before you can push images.
> Create it first, push images, then apply the rest:

```bash
# 1. Create the Artifact Registry repo
cd terraform/environments/dev
terraform apply -target=module.app.google_artifact_registry_repository.main

# 2. Push images (from repo root)
cd c:/Users/sapma/OneDrive/Desktop/Projects/Pet-generator
PROJECT=pet-gen-dev
REGION=asia-northeast1
REGISTRY=$REGION-docker.pkg.dev/$PROJECT/pet-gen-dev
TAG=latest

gcloud config set project $PROJECT
gcloud auth configure-docker $REGION-docker.pkg.dev

docker build -t $REGISTRY/backend:$TAG -f backend/Dockerfile .
docker push $REGISTRY/backend:$TAG

docker build -t $REGISTRY/autoscaler:$TAG -f autoscaler/Dockerfile .
docker push $REGISTRY/autoscaler:$TAG

docker build -t $REGISTRY/frontend:$TAG ./frontend-ng
docker push $REGISTRY/frontend:$TAG

# 3. Deploy everything
cd terraform/environments/dev
terraform apply
```

Outputs after apply:

```
frontend_url      = "https://pet-gen-dev-frontend-xxxx.run.app"
backend_url       = "https://pet-gen-dev-backend-xxxx.run.app"
autoscaler_url    = "https://pet-gen-dev-autoscaler-xxxx.run.app"
artifact_registry = "us-central1-docker.pkg.dev/pet-gen-dev/pet-gen-dev"
```

### Update image tag

To roll out a new image without changing infrastructure:

```bash
cd terraform/environments/dev
terraform apply -var="image_tag=abc1234"
```

### Tear down

```bash
cd terraform/environments/dev
terraform destroy
```
