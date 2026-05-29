#!/usr/bin/env python3
"""Export PPTX slides to PNG (PowerPoint COM on Windows, else LibreOffice)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from defense_slides_manifest import OUTPUT_PPTX_FROM_HTML, SLIDES


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_pptx() -> Path:
    return repo_root() / "docs" / OUTPUT_PPTX_FROM_HTML


def default_out_dir() -> Path:
    return (
        repo_root()
        / "docs"
        / "presentacion-defensa-pfc"
        / "_pptx_check"
    )


def export_via_com(pptx: Path, out_dir: Path) -> bool:
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    try:
        pres = app.Presentations.Open(str(pptx.resolve()), WithWindow=False)
        n = pres.Slides.Count
        for i in range(1, n + 1):
            sid = SLIDES[i - 1].id if i - 1 < len(SLIDES) else f"slide_{i:02d}"
            out_file = str((out_dir / f"{sid}.png").resolve())
            pres.Slides(i).Export(out_file, "PNG", 1920, 1080)
        pres.Close()
        print(f"COM: exportadas {n} diapositivas -> {out_dir}")
        return True
    finally:
        app.Quit()


def export_via_libreoffice(pptx: Path, out_dir: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_lo_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "png",
            "--outdir",
            str(tmp),
            str(pptx.resolve()),
        ],
        check=True,
        capture_output=True,
    )
    pngs = sorted(tmp.glob("*.png"))
    for i, src in enumerate(pngs):
        sid = SLIDES[i].id if i < len(SLIDES) else f"slide_{i + 1:02d}"
        dest = out_dir / f"{sid}.png"
        src.replace(dest)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"LibreOffice: {len(pngs)} PNG → {out_dir}")
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("pptx", nargs="?", type=Path, default=default_pptx())
    p.add_argument("-o", "--out-dir", type=Path, default=default_out_dir())
    args = p.parse_args()
    pptx = args.pptx.resolve()
    out_dir = args.out_dir.resolve()
    if not pptx.is_file():
        print(f"No encontrado: {pptx}", file=sys.stderr)
        raise SystemExit(1)
    if export_via_com(pptx, out_dir):
        return
    if export_via_libreoffice(pptx, out_dir):
        return
    print(
        "No se pudo exportar PPTX a PNG.\n"
        "Instala Microsoft PowerPoint + pywin32, o LibreOffice en PATH.\n"
        "  pip install pywin32\n"
        "  python tools/screenshot_pptx_slides.py",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
