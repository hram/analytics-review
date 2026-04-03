#!/usr/bin/env python3

from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import markdown


def render_html_document(md_text: str, title: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"],
        output_format="html5",
    )

    escaped_title = escape(title)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f3ee;
      --panel: #fffdf9;
      --text: #1d1b19;
      --muted: #5b544d;
      --border: #d7cfc4;
      --code-bg: #f1ece4;
      --link: #8b3d16;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #efe7db 0%, var(--bg) 240px);
      color: var(--text);
      line-height: 1.6;
    }}
    main {{
      max-width: 980px;
      margin: 32px auto;
      padding: 32px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(56, 43, 26, 0.08);
    }}
    h1, h2, h3, h4 {{ line-height: 1.25; }}
    h1 {{ margin-top: 0; }}
    a {{ color: var(--link); }}
    pre, code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      background: var(--code-bg);
    }}
    code {{ padding: 0.1em 0.3em; border-radius: 4px; }}
    pre {{
      padding: 16px;
      overflow-x: auto;
      border-radius: 10px;
      border: 1px solid var(--border);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 10px 12px;
      vertical-align: top;
    }}
    th {{
      background: #f3ede4;
      text-align: left;
    }}
    blockquote {{
      margin: 16px 0;
      padding: 8px 16px;
      border-left: 4px solid #c67b4d;
      color: var(--muted);
      background: #fbf7f1;
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"Usage: {Path(sys.argv[0]).name} <input_md> <output_html>",
            file=sys.stderr,
        )
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.is_file():
        print(f"Markdown file not found: {input_path}", file=sys.stderr)
        return 1

    md_text = input_path.read_text(encoding="utf-8")
    html = render_html_document(md_text, input_path.stem)
    output_path.write_text(html, encoding="utf-8")
    print(f"Saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
