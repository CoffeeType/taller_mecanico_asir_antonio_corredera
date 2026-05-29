#!/usr/bin/env python3
"""Extrae imágenes clave del COPIAPFC para PPTX y presentación HTML."""

from __future__ import annotations

import zipfile
from pathlib import Path

from defense_slides_manifest import COPIAPFC_NAME, KEY_IMAGES


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def extract_all(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    docx = root / "docs" / COPIAPFC_NAME
    if not docx.is_file():
        raise FileNotFoundError(f"No se encuentra {docx}")

    cache = root / "docs" / ".pptx_gen_media"
    html_assets = root / "docs" / "presentacion-defensa-pfc" / "assets"
    cache.mkdir(parents=True, exist_ok=True)
    html_assets.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    with zipfile.ZipFile(docx) as z:
        for name in KEY_IMAGES:
            inner = f"word/media/{name}"
            if inner not in z.namelist():
                missing.append(name)
                continue
            data = z.read(inner)
            (cache / name).write_bytes(data)
            (html_assets / name).write_bytes(data)

    return missing


def main():
    missing = extract_all()
    root = repo_root()
    print(f"Cache PPTX: {root / 'docs' / '.pptx_gen_media'}")
    print(f"HTML assets: {root / 'docs' / 'presentacion-defensa-pfc' / 'assets'}")
    if missing:
        print("Aviso: imágenes no encontradas en docx:", ", ".join(missing))
    else:
        print(f"Extraídas {len(KEY_IMAGES)} imágenes.")


if __name__ == "__main__":
    main()
