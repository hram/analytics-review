#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from render_markdown_html import render_html_document


def replace_page_ids(text: str, pages: dict[str, dict[str, str]]) -> str:
    for page_id, page in sorted(pages.items(), key=lambda item: len(item[0]), reverse=True):
        title = page["title"]
        href = f"pages/{page['html_file']}"
        patterns = [
            rf"страницы?\s+{page_id}\b",
            rf"pageId\s*=\s*{page_id}\b",
            rf"\b{page_id}\.md\b",
            rf"\b{page_id}\b",
        ]
        replacements = [
            f"страницы [{title}]({href})",
            f"pageId=[{title}]({href})",
            f"[{title}]({href})",
            f"[{title}]({href})",
        ]
        for pattern, replacement in zip(patterns, replacements):
            text = re.sub(pattern, replacement, text)
    return text


def unwrap_code_wrapped_links(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"`(\[[^`]+?\]\(pages/[^)]+\))`", r"\1", text)
        text = re.sub(r"`(\[[^`]+?\]\([^)]+\))`", r"\1", text)
    return text


def normalize_nested_links(text: str) -> str:
    pattern = re.compile(
        r"\[([^\]]+)\]\(pages/\[[^\]]+\]\((pages/[^)]+)\)[^)]+\)"
    )
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub(r"[\1](\2)", text)
    return text


def normalize_known_page_links(text: str, pages: dict[str, dict[str, str]]) -> str:
    for page in pages.values():
        title = re.escape(page["title"])
        href = f"pages/{page['html_file']}"
        pattern = re.compile(rf"\[{title}\]\(pages/.*?{page['id']}[^)]*\)")
        text = pattern.sub(f"[{page['title']}]({href})", text)
    return text


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"Usage: {Path(sys.argv[0]).name} <pages_dir> <review_md> <review_html>",
            file=sys.stderr,
        )
        return 1

    pages_dir = Path(sys.argv[1])
    review_md = Path(sys.argv[2])
    review_html = Path(sys.argv[3])

    metadata_file = pages_dir / "metadata.json"
    if not metadata_file.is_file():
        print(f"Metadata file not found: {metadata_file}", file=sys.stderr)
        return 1
    if not review_md.is_file():
        print(f"Review markdown not found: {review_md}", file=sys.stderr)
        return 1

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    pages: dict[str, dict[str, str]] = metadata["pages"]
    root_page_id = str(metadata["root_page_id"])

    for page_id, page in pages.items():
        source_md = pages_dir / page["markdown_file"]
        target_html = pages_dir / page["html_file"]
        if not source_md.is_file():
            continue

        body_md = source_md.read_text(encoding="utf-8")
        header = (
            f"# {page['title']}\n\n"
            f"[Открыть в Confluence]({page['confluence_url']})\n\n"
            f"[Вернуться к ревью](../{review_html.name})\n\n"
            "---\n\n"
        )
        html = render_html_document(
            header + body_md,
            page["title"],
        )
        target_html.write_text(html, encoding="utf-8")
        print(f"Saved to {target_html}")

    review_text = review_md.read_text(encoding="utf-8")
    review_text = normalize_nested_links(review_text)
    review_text = normalize_known_page_links(review_text, pages)
    review_text = replace_page_ids(review_text, pages)
    review_text = unwrap_code_wrapped_links(review_text)
    review_text = normalize_nested_links(review_text)
    review_text = normalize_known_page_links(review_text, pages)
    review_md.write_text(review_text, encoding="utf-8")

    root_title = pages.get(root_page_id, {}).get("title", root_page_id)
    review_title = f"Ревью постановки: {root_title}"
    review_html.write_text(
        render_html_document(review_text, review_title),
        encoding="utf-8",
    )
    print(f"Saved to {review_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
