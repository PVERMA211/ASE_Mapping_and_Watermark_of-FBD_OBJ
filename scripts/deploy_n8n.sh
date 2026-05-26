#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
PYTHON_BIN="${PYTHON_BIN:-python3.14}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Required interpreter not found: ${PYTHON_BIN}" >&2
  exit 1
fi

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate_requirements.py" --project-root "${ROOT_DIR}"
docker compose --project-directory "${ROOT_DIR}" up -d
"${ROOT_DIR}/scripts/smoke_test_n8n.sh"
