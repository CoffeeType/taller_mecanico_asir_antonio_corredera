#!/usr/bin/env python3
"""
Genera la presentación de defensa del PFC (castellano, ~30 min) con diseño ppt-visual.
Requisitos: python -m pip install python-pptx pillow

Uso (desde la raíz del repo):
    python tools/extract_defense_assets.py
    python tools/generate_defense_pptx.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from pptx import Presentation

from defense_pptx_visual import render_slide
from defense_slides_manifest import (
    COPIAPFC_NAME,
    KEY_IMAGES,
    OUTPUT_PPTX,
    SLIDES,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_image(root: Path, filename: str) -> Path | None:
    """Busca PNG en cache, carpetas descomprimidas o extrae del .docx."""
    dirs = [
        root / "docs" / ".pptx_gen_media",
        root / "docs" / "_copiapfc_work" / "word" / "media",
        root / "docs" / "_reaudit" / "word" / "media",
        root / "docs" / "_copiapfc_unzip" / "word" / "media",
    ]
    for d in dirs:
        p = d / filename
        if p.is_file():
            return p
    docx = root / "docs" / COPIAPFC_NAME
    if not docx.is_file():
        return None
    inner = f"word/media/{filename}"
    cache = root / "docs" / ".pptx_gen_media"
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / filename
    with zipfile.ZipFile(docx) as z:
        if inner not in z.namelist():
            return None
        out.write_bytes(z.read(inner))
    return out


def build_presentation(root: Path) -> Presentation:
    prs = Presentation()
    prs.core_properties.title = "Defensa PFC — Taller mecánico (ASIR)"
    prs.core_properties.author = "Antonio Corredera Cubells"

    def img(name: str | None) -> Path | None:
        return resolve_image(root, name) if name else None

    for idx, spec in enumerate(SLIDES, start=1):
        render_slide(prs, spec, img(spec.image), img(spec.image_right), slide_index=idx)

    return prs


def main():
    root = repo_root()
    out = root / "docs" / OUTPUT_PPTX
    prs = build_presentation(root)
    prs.save(str(out))
    print(f"Guardado: {out} ({len(SLIDES)} diapositivas, diseño ppt-visual)")
    missing = [n for n in KEY_IMAGES if resolve_image(root, n) is None]
    if missing:
        print("Aviso: imágenes no encontradas:", ", ".join(missing))


if __name__ == "__main__":
    main()
