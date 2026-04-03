#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from markdownify import markdownify as md


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ[key] = value


def env_flag(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def build_ssl_context() -> ssl.SSLContext:
    ca_file = os.environ.get("CONF_CA_FILE", "").strip()
    if ca_file:
        return ssl.create_default_context(cafile=ca_file)

    if env_flag("CONF_INSECURE_SKIP_VERIFY"):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    return ssl.create_default_context()


def fetch_json(url: str, auth: str, ssl_context: ssl.SSLContext) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": auth})

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        return json.load(resp)


def slugify(text: str) -> str:
    translit = str.maketrans(
        {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }
    )
    slug = text.lower().translate(translit)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "page"


def build_confluence_url(base_url: str, data: dict, page_id: str) -> str:
    links = data.get("_links", {})
    webui = links.get("webui")
    base = links.get("base")
    if webui:
        if base:
            return urllib.parse.urljoin(f"{base.rstrip('/')}/", webui.lstrip("/"))
        return urllib.parse.urljoin(
            f"{base_url.rstrip('/')}/", webui.lstrip("/")
        )
    return f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={page_id}"


def fetch_page(
    base_url: str,
    auth: str,
    page_id: str,
    ssl_context: ssl.SSLContext,
) -> dict:
    url = f"{base_url.rstrip('/')}/rest/api/content/{page_id}?expand=body.storage"
    data = fetch_json(url, auth, ssl_context)

    try:
        html = data["body"]["storage"]["value"]
    except KeyError as exc:
        raise KeyError("body.storage.value is missing") from exc

    title = str(data.get("title") or page_id)
    slug = slugify(title)
    return {
        "id": page_id,
        "title": title,
        "slug": slug,
        "confluence_url": build_confluence_url(base_url, data, page_id),
        "markdown": md(html, heading_style="ATX"),
    }


def fetch_child_page_ids(
    base_url: str,
    auth: str,
    page_id: str,
    ssl_context: ssl.SSLContext,
) -> list[str]:
    next_url = (
        f"{base_url.rstrip('/')}/rest/api/content/"
        f"{page_id}/child/page?limit=200"
    )
    child_ids: list[str] = []

    while next_url:
        data = fetch_json(next_url, auth, ssl_context)
        for item in data.get("results", []):
            child_id = item.get("id")
            if child_id is not None:
                child_ids.append(str(child_id))

        relative_next = data.get("_links", {}).get("next")
        if relative_next:
            next_url = urllib.parse.urljoin(f"{base_url.rstrip('/')}/", relative_next)
        else:
            next_url = ""

    return child_ids


def save_page_tree(
    base_url: str,
    auth: str,
    page_id: str,
    output_dir: Path,
    visited: set[str],
    metadata: dict[str, dict[str, str]],
    ssl_context: ssl.SSLContext,
) -> int:
    if page_id in visited:
        return 0
    visited.add(page_id)

    page = fetch_page(base_url, auth, page_id, ssl_context)
    markdown = page["markdown"]
    output_file = output_dir / f"{page_id}.md"
    output_file.write_text(markdown, encoding="utf-8")
    print(f"Saved to {output_file}")
    metadata[page_id] = {
        "id": page_id,
        "title": page["title"],
        "slug": page["slug"],
        "confluence_url": page["confluence_url"],
        "markdown_file": output_file.name,
        "html_file": f"{page_id}-{page['slug']}.html",
    }

    saved_count = 1
    for child_id in fetch_child_page_ids(base_url, auth, page_id, ssl_context):
        saved_count += save_page_tree(
            base_url, auth, child_id, output_dir, visited, metadata, ssl_context
        )

    return saved_count


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    env_file = Path(os.environ.get("CONF_ENV_FILE", script_dir / ".env"))
    load_env(env_file)

    if len(sys.argv) not in {2, 3}:
        print(
            f"Usage: {Path(sys.argv[0]).name} <page_id> [output_dir]",
            file=sys.stderr,
        )
        print(
            f"Example: {Path(sys.argv[0]).name} 244908187 ./pages",
            file=sys.stderr,
        )
        return 1

    page_id = sys.argv[1]
    output_dir = Path(sys.argv[2] if len(sys.argv) == 3 else ".").resolve()

    base_url = os.environ.get("CONF_BASE_URL", "http://confluence.kifr-ru.local:8090")
    auth = os.environ.get("CONF_AUTH")
    if not auth:
        print("CONF_AUTH is required in .env", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    ssl_context = build_ssl_context()

    try:
        metadata: dict[str, dict[str, str]] = {}
        saved_count = save_page_tree(
            base_url, auth, page_id, output_dir, set(), metadata, ssl_context
        )
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1
    except KeyError:
        print("Unexpected API response: body.storage.value is missing", file=sys.stderr)
        return 1

    metadata_file = output_dir / "metadata.json"
    metadata_file.write_text(
        json.dumps(
            {
                "root_page_id": page_id,
                "pages": metadata,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved to {metadata_file}")
    print(f"Total pages saved: {saved_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
