#!/usr/bin/env python3
"""Embed docs/presentacion-defensa-pfc/assets/*.png as data URIs in index.html."""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = REPO_ROOT / "docs" / "presentacion-defensa-pfc"
INDEX_HTML = PRESENTATION_DIR / "index.html"
ASSETS_DIR = PRESENTATION_DIR / "assets"

SRC_PATTERN = re.compile(
    r'src="assets/([^"]+\.(?:png|jpe?g|gif|webp|svg))"',
    re.IGNORECASE,
)


def mime_for(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(ext, "application/octet-stream")


def embed(html: str) -> tuple[str, list[str]]:
    embedded: list[str] = []

    def replace(match: re.Match[str]) -> str:
        filename = match.group(1)
        path = ASSETS_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing asset: {path}")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        mime = mime_for(filename)
        embedded.append(filename)
        return f'src="data:{mime};base64,{data}"'

    return SRC_PATTERN.sub(replace, html), embedded


def main() -> int:
    if not INDEX_HTML.is_file():
        print(f"Not found: {INDEX_HTML}", file=sys.stderr)
        return 1

    html = INDEX_HTML.read_text(encoding="utf-8")
    new_html, files = embed(html)
    if not files:
        print("No assets/ references found — nothing to embed.")
        return 0

    unique = sorted(set(files))
    INDEX_HTML.write_text(new_html, encoding="utf-8", newline="\n")
    print(f"Embedded {len(unique)} asset(s) into {INDEX_HTML.relative_to(REPO_ROOT)}:")
    for name in unique:
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
