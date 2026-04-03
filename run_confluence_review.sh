#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 <page_id> [output_dir] [prompt_file]" >&2
  echo "Example: $0 244908187 /home/hram/review/out /home/hram/review/prompt_pragmatic.md" >&2
  exit 1
fi

PAGE_ID="$1"
BASE_OUTPUT_DIR="${2:-/home/hram/review/out}"
PROMPT_FILE="${3:-/home/hram/review/prompt.md}"
RUN_DIR="${BASE_OUTPUT_DIR%/}/${PAGE_ID}"
PAGES_DIR="${RUN_DIR}/pages"
REVIEW_FILE="${RUN_DIR}/review_${PAGE_ID}.md"
REVIEW_HTML_FILE="${RUN_DIR}/review_${PAGE_ID}.html"

mkdir -p "$RUN_DIR"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

/home/hram/review/.venv/bin/python \
  /home/hram/review/fetch_confluence_page_md.py \
  "$PAGE_ID" \
  "$PAGES_DIR"

/home/hram/review/review_confluence_pages.sh \
  "$PAGES_DIR" \
  "$REVIEW_FILE" \
  "$PROMPT_FILE"

/home/hram/review/.venv/bin/python \
  /home/hram/review/decorate_review_bundle.py \
  "$PAGES_DIR" \
  "$REVIEW_FILE" \
  "$REVIEW_HTML_FILE"

echo "Pages saved to $PAGES_DIR"
echo "Review saved to $REVIEW_FILE"
echo "HTML review saved to $REVIEW_HTML_FILE"
