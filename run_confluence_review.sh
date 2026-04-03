#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 <page_id> [output_dir] [prompt_file]" >&2
  echo "Example: $0 244908187 ${SCRIPT_DIR}/out ${SCRIPT_DIR}/prompt_pragmatic.md" >&2
  exit 1
fi

PAGE_ID="$1"
BASE_OUTPUT_DIR="${2:-${SCRIPT_DIR}/out}"
PROMPT_FILE="${3:-${SCRIPT_DIR}/prompt.md}"
RUN_DIR="${BASE_OUTPUT_DIR%/}/${PAGE_ID}"
PAGES_DIR="${RUN_DIR}/pages"
REVIEW_RAW_FILE="${RUN_DIR}/review_${PAGE_ID}.raw.md"
REVIEW_FILE="${RUN_DIR}/review_${PAGE_ID}.md"
REVIEW_HTML_FILE="${RUN_DIR}/review_${PAGE_ID}.html"

mkdir -p "$RUN_DIR"
rm -rf "$PAGES_DIR"
mkdir -p "$PAGES_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found or not executable: $PYTHON_BIN" >&2
  echo "Create the virtual environment and install dependencies first." >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI is not installed or not available in PATH" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

"$PYTHON_BIN" \
  "${SCRIPT_DIR}/fetch_confluence_page_md.py" \
  "$PAGE_ID" \
  "$PAGES_DIR"

"${SCRIPT_DIR}/review_confluence_pages.sh" \
  "$PAGES_DIR" \
  "$REVIEW_RAW_FILE" \
  "$PROMPT_FILE"

"$PYTHON_BIN" \
  "${SCRIPT_DIR}/decorate_review_bundle.py" \
  "$PAGES_DIR" \
  "$REVIEW_RAW_FILE" \
  "$REVIEW_FILE" \
  "$REVIEW_HTML_FILE"

echo "Pages saved to $PAGES_DIR"
echo "Raw review saved to $REVIEW_RAW_FILE"
echo "Review saved to $REVIEW_FILE"
echo "HTML review saved to $REVIEW_HTML_FILE"
