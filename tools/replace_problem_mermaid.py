#!/usr/bin/env python3
"""Replace problem slide base64 PNG with live Mermaid (Fig. 3)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "presentacion-defensa-pfc" / "index.html"
MMD = ROOT / "docs" / "mermaid" / "pfc-fig03-reserva.mmd"


def main() -> None:
    mmd = MMD.read_text(encoding="utf-8").strip()
    html = HTML.read_text(encoding="utf-8")
    repl = (
        '<figure class="content-split-aside mermaid-wrap content-split-mermaid" '
        'aria-label="Fig. 3 Flujo de reserva">\n'
        f'        <pre class="mermaid">{mmd}</pre></figure>'
    )
    new, n = re.subn(
        r'<figure class="content-split-aside"><img src="data:image[^"]*"[^>]*></figure>',
        repl,
        html,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Expected 1 replacement, got {n}")
    HTML.write_text(new, encoding="utf-8")
    print("OK: problem slide now uses Mermaid")


if __name__ == "__main__":
    main()
