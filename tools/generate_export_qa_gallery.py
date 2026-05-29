#!/usr/bin/env python3
"""Genera galería HTML golden vs PPTX para revisión visual (agent-browser)."""

from __future__ import annotations

import html as html_mod
from pathlib import Path

from defense_slides_manifest import SLIDES


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base = root / "docs" / "presentacion-defensa-pfc"
    golden = base / "_export_golden"
    pptx = base / "_pptx_check"
    out = base / "export_qa_gallery.html"

    rows = []
    for spec in SLIDES:
        sid = spec.id
        g = golden / f"{sid}.png"
        p = pptx / f"{sid}.png"
        if not g.is_file() or not p.is_file():
            continue
        rows.append(
            f"""
    <section class="pair">
      <h2>{html_mod.escape(sid)}</h2>
      <div class="imgs">
        <figure><figcaption>HTML golden</figcaption><img src="_export_golden/{html_mod.escape(sid)}.png" alt="golden {html_mod.escape(sid)}"></figure>
        <figure><figcaption>PPTX render</figcaption><img src="_pptx_check/{html_mod.escape(sid)}.png" alt="pptx {html_mod.escape(sid)}"></figure>
      </div>
    </section>"""
        )

    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Export QA — HTML vs PPTX</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem; background: #1a1a1a; color: #eee; }}
    h1 {{ font-size: 1.25rem; }}
    .pair {{ margin-bottom: 2rem; border-bottom: 1px solid #333; padding-bottom: 1rem; }}
    .imgs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    figure {{ margin: 0; }}
    figcaption {{ font-size: 0.85rem; color: #aaa; margin-bottom: 0.35rem; }}
    img {{ width: 100%; border: 1px solid #444; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Export QA — golden HTML vs PPTX (dom-to-pptx)</h1>
  <p>Ver también <a href="EXPORT_QA.md" style="color:#e85d2c">EXPORT_QA.md</a></p>
{"".join(rows)}
</body>
</html>
"""
    out.write_text(doc, encoding="utf-8")
    print(f"Galería: {out}")


if __name__ == "__main__":
    main()
