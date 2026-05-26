#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

PORT="${N8N_PORT:-5678}"
HEALTH_URL="http://127.0.0.1:${PORT}/healthz"
APP_URL="http://127.0.0.1:${PORT}"
ATTEMPTS="${ATTEMPTS:-30}"

for ((attempt = 1; attempt <= ATTEMPTS; attempt++)); do
  if curl --fail --silent --show-error "${HEALTH_URL}" >/dev/null; then
    break
  fi
  sleep 2
done

curl --fail --silent --show-error "${HEALTH_URL}" >/dev/null
curl --fail --silent --show-error "${APP_URL}" >/dev/null

echo "n8n is reachable on ${APP_URL}"
