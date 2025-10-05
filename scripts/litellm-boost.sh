#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${TERRAFORM_ENVIRONMENT:-dev}"
ARG="${1:-}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${BASE_DIR}/infrastructure/terraform/environments/${ENVIRONMENT}"

if [ ! -d "${TF_DIR}" ]; then
  echo "Terraform environment directory not found: ${TF_DIR}" >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI v2 is required" >&2
  exit 1
fi

DESIRED_COUNT=1
if [ "${ARG}" = "--off" ] || [ "${ARG}" = "off" ]; then
  DESIRED_COUNT=0
elif [ -n "${ARG}" ]; then
  if [[ "${ARG}" =~ ^[0-9]+$ ]]; then
    DESIRED_COUNT="${ARG}"
  else
    echo "Unrecognised argument: ${ARG}" >&2
    echo "Usage: $0 [desired-count|--off]" >&2
    exit 1
  fi
fi

CLUSTER="${LITELLM_CLUSTER_NAME:-}"
SERVICE="${LITELLM_SERVICE_NAME:-}"
if [ -z "${CLUSTER}" ] && command -v terraform >/dev/null 2>&1; then
  CLUSTER=$(terraform -chdir "${TF_DIR}" output -raw litellm_cluster_name 2>/dev/null || true)
fi
if [ -z "${SERVICE}" ] && command -v terraform >/dev/null 2>&1; then
  SERVICE=$(terraform -chdir "${TF_DIR}" output -raw litellm_service_name 2>/dev/null || true)
fi
if [ -z "${CLUSTER}" ] || [ -z "${SERVICE}" ]; then
  # Fall back to naming convention used in Terraform
  CLUSTER="resume-genius-${ENVIRONMENT}-litellm-cluster"
  SERVICE="resume-genius-${ENVIRONMENT}-litellm-svc"
fi

echo "Updating LiteLLM service ${SERVICE} in cluster ${CLUSTER} to desired count ${DESIRED_COUNT}" >&2
aws ecs update-service \
  --cluster "${CLUSTER}" \
  --service "${SERVICE}" \
  --desired-count "${DESIRED_COUNT}" >/dev/null

echo "Update submitted." >&2

if [ "${DESIRED_COUNT}" -gt 0 ]; then
  echo "Waiting for a task to reach RUNNING state..." >&2
  for attempt in {1..30}; do
    TASK_ARN=$(aws ecs list-tasks \
      --cluster "${CLUSTER}" \
      --service-name "${SERVICE}" \
      --desired-status RUNNING \
      --query 'taskArns[0]' \
      --output text 2>/dev/null || true)
    if [ -n "${TASK_ARN}" ] && [ "${TASK_ARN}" != "None" ]; then
      echo "LiteLLM task is running (${TASK_ARN})." >&2
      exit 0
    fi
    sleep 5
  done
  echo "No running task detected after waiting; check ECS console for details." >&2
else
  echo "LiteLLM will scale down to zero shortly." >&2
fi
