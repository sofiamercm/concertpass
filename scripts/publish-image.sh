#!/usr/bin/env bash
#Levantar servicios
set -euo pipefail

SERVICE="${1:?Uso: ./publish-image.sh <ticket-api|ticket-checkout>}"
REGION="us-east-1"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE="${REGISTRY}/${SERVICE}:latest"

cd "$(dirname "$0")/../apps/${SERVICE}"

aws ecr describe-repositories --repository-names "$SERVICE" --region "$REGION" \
  >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "$SERVICE" --region "$REGION"

aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$REGISTRY"

docker build -t "$SERVICE" .
docker tag "$SERVICE" "$IMAGE"
docker push "$IMAGE"

echo "Publicada: $IMAGE"