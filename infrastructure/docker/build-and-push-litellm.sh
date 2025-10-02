#!/usr/bin/env bash
set -euo pipefail

# Builds the LiteLLM image and pushes it to ECR using Docker Buildx for linux/amd64.

REGION="${AWS_REGION:-ap-southeast-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-084828573819}"
REPO_NAME="${LITELLM_REPO_NAME:-resume-genius/litellm}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

REPO_ROOT="$(git rev-parse --show-toplevel)"

DOCKERFILE="${DOCKERFILE:-${REPO_ROOT}/infrastructure/docker/Dockerfile.litellm}"
DOCKERFILE_DIR="$(cd "$(dirname "${DOCKERFILE}")" && pwd)"
CONTEXT="${BUILD_CONTEXT:-${DOCKERFILE_DIR}}"
PLATFORM="${PLATFORM:-linux/amd64}"

echo "Logging into ECR (${REGION})..."
aws ecr get-login-password --region "${REGION}" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Ensuring Buildx builder exists..."
if ! docker buildx inspect resume-genius-builder >/dev/null 2>&1; then
  docker buildx create --name resume-genius-builder --use
else
  docker buildx use resume-genius-builder
fi

echo "Building and pushing ${IMAGE_URI} for platform ${PLATFORM}..."
docker buildx build \
  --file "${DOCKERFILE}" \
  --platform "${PLATFORM}" \
  --tag "${IMAGE_URI}" \
  --push \
  "${CONTEXT}"

echo "Image pushed: ${IMAGE_URI}"
