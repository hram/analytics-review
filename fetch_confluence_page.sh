#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${CONF_ENV_FILE:-${SCRIPT_DIR}/.env}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <page_id> [output_file]" >&2
  echo "Example: $0 244908187 244908187.html" >&2
  exit 1
fi

PAGE_ID="$1"
OUTPUT_FILE="${2:-${PAGE_ID}.html}"
EXPAND="body.storage"

: "${CONF_BASE_URL:=http://confluence.kifr-ru.local:8090}"
: "${CONF_AUTH:?Set CONF_AUTH with Basic auth header value, e.g. 'Basic xxx'}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required but not installed" >&2
  exit 1
fi

API_URL="${CONF_BASE_URL%/}/rest/api/content/${PAGE_ID}?expand=${EXPAND}"

CURL_ARGS=(
  --silent
  --show-error
  --fail
  --location
  "$API_URL"
  --header "Authorization: ${CONF_AUTH}"
)

if [[ -n "${CONF_CA_FILE:-}" ]]; then
  CURL_ARGS+=(--cacert "$CONF_CA_FILE")
fi

if [[ "${CONF_INSECURE_SKIP_VERIFY:-}" =~ ^(1|true|yes|on)$ ]]; then
  CURL_ARGS+=(--insecure)
fi

curl "${CURL_ARGS[@]}" | jq -r '.body.storage.value' > "$OUTPUT_FILE"

echo "Saved to $OUTPUT_FILE"
