#!/usr/bin/env python3
"""Check that docs/presentacion-defensa-pfc/index.html is portable (embedded images)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "docs" / "presentacion-defensa-pfc" / "index.html"
MIN_PORTABLE_BYTES = 400_000
ASSET_REF = re.compile(r'src="assets/', re.I)
DATA_URI = re.compile(r'src="data:image/', re.I)


def main() -> int:
    if not INDEX_HTML.is_file():
        print(f"Missing: {INDEX_HTML}", file=sys.stderr)
        return 1

    html = INDEX_HTML.read_text(encoding="utf-8")
    size = INDEX_HTML.stat().st_size
    asset_refs = len(ASSET_REF.findall(html))
    data_uris = len(DATA_URI.findall(html))

    ok = size >= MIN_PORTABLE_BYTES and asset_refs == 0 and data_uris >= 6
    print(f"File: {INDEX_HTML.relative_to(REPO_ROOT)}")
    print(f"  Size: {size:,} bytes")
    print(f"  assets/ references: {asset_refs}")
    print(f"  data:image/ embeds: {data_uris}")

    if ok:
        print("OK — portable single-file HTML (safe to copy or upload).")
        return 0

    print("FAIL — run: python tools/embed_defense_html_assets.py", file=sys.stderr)
    if size < MIN_PORTABLE_BYTES:
        print(f"  Expected size >= {MIN_PORTABLE_BYTES:,} bytes.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
