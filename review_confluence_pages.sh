#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <pages_dir> <output_file> [prompt_file]" >&2
  echo "Example: $0 /home/hram/review/pages_244908187_1774354653 /home/hram/review/review_244908187.md /home/hram/review/prompt.md" >&2
  exit 1
fi

PAGES_DIR="$1"
OUTPUT_FILE="$2"
PROMPT_FILE="${3:-/home/hram/review/prompt.md}"

if [[ ! -d "$PAGES_DIR" ]]; then
  echo "Pages directory not found: $PAGES_DIR" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

mapfile -t PAGE_FILES < <(find "$PAGES_DIR" -maxdepth 1 -type f -name '*.md' | sort)

if [[ ${#PAGE_FILES[@]} -eq 0 ]]; then
  echo "No .md files found in: $PAGES_DIR" >&2
  exit 1
fi

TMP_INPUT="$(mktemp)"
trap 'rm -f "$TMP_INPUT"' EXIT

{
  cat "$PROMPT_FILE"
  printf '\n\n'
  printf 'Проведи единое ревью по всем приложенным страницам как по одной связанной постановке.\n'
  printf 'Считай, что дочерние страницы являются частью общей спецификации и должны анализироваться вместе.\n'
  printf 'В ответе дай один цельный review-документ на русском языке.\n'
  printf 'Обязательно ссылайся на конкретные page id, когда проблема относится к отдельной странице.\n'
  printf 'Если проблема возникает из-за противоречий между страницами, явно укажи обе страницы.\n'
  printf '\n'
  for page_file in "${PAGE_FILES[@]}"; do
    printf '\n===== FILE: %s =====\n\n' "$(basename "$page_file")"
    cat "$page_file"
    printf '\n'
  done
} > "$TMP_INPUT"

timeout 20m \
  codex \
    --dangerously-bypass-approvals-and-sandbox \
    exec \
    --skip-git-repo-check \
    -C "$PAGES_DIR" \
    -o "$OUTPUT_FILE" \
    - < "$TMP_INPUT"

echo "Saved review to $OUTPUT_FILE"
