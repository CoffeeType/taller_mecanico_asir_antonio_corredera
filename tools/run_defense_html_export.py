#!/usr/bin/env python3
"""
Pipeline completo: HTML (?export=1) -> PPTX raster (Playwright PNG) -> notas -> QA PNG.

Uso (raíz del repo):
    python tools/run_defense_html_export.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=repo_root(), check=True)


def main() -> None:
    root = repo_root()
    py = sys.executable
    # No regenerar index.html aquí: el deck usa assets incrustados y restore_defense_presentation_contract.py
    steps = [
        [py, "tools/export_defense_html_to_pptx.py"],
        [py, "tools/attach_defense_speaker_notes.py"],
        [py, "tools/screenshot_all_slides.py", "--export"],
        [py, "tools/screenshot_pptx_slides.py"],
        [py, "tools/compare_slide_pngs.py"],
        [py, "tools/generate_export_qa_gallery.py"],
        [py, "tools/verify_pptx_delivery.py"],
    ]
    for cmd in steps:
        run(cmd)
    pptx = root / "docs" / "PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx"
    print(f"\nListo: {pptx}")


if __name__ == "__main__":
    main()
