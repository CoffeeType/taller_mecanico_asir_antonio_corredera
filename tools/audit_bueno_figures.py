#!/usr/bin/env python3
"""Audit figures in BuenoCOPIAPFC document.xml."""
import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/_pfc_bueno_unpacked/word/document.xml"


def main() -> None:
    xml = DOC.read_text(encoding="utf-8")

    # Index
    idx_start = xml.find('w:name="_Toc230036830"')
    if idx_start < 0:
        idx_start = xml.find("Índice de figuras")
    i_start = xml.find("Índice de figuras", idx_start)
    i_end = xml.find("Índice de tablas", i_start)
    index = re.findall(r"Figura (\d+)\. ([^<]+)", xml[i_start:i_end])

    body_start = xml.find("4. DISEÑO")
    body = xml[body_start:]

    # Bold captions in body
    body_caps = re.findall(
        r"<w:b[^/]*/>.*?<w:t>Figura (\d+)\. ([^<]+)</w:t>", body, re.DOTALL
    )

    # Drawings with next caption
    drawing_caps = []
    for m in re.finditer(r"<w:drawing>", body):
        chunk = body[m.start() : m.start() + 20000]
        fig = re.search(r"<w:b[^/]*/>.*?<w:t>Figura (\d+)\. ([^<]+)</w:t>", chunk, re.DOTALL)
        if not fig:
            fig = re.search(r"<w:t>Figura (\d+)\. ([^<]+)</w:t>", chunk)
        name = re.search(r'name="([^"]*)"', chunk[:2500])
        drawing_caps.append(
            (
                int(fig.group(1)) if fig else None,
                fig.group(2).strip() if fig else None,
                name.group(1) if name else "?",
                m.start(),
            )
        )

    sec_start = body.find("5.4.1. Lanzamiento")
    sec_end = body.find("5.4.2", sec_start)
    if sec_end < 0:
        sec_end = body.find("Tabla 7.", sec_start)
    if sec_end < 0:
        sec_end = body.find("Reglas de entrada", sec_start)
    section = body[sec_start:sec_end] if sec_end > sec_start else body[sec_start : sec_start + 200000]

    sec_drawings = len(re.findall(r"<w:drawing>", section))
    sec_figs = re.findall(
        r"<w:b[^/]*/>.*?<w:t>Figura (\d+)\. ([^<]+)</w:t>", section, re.DOTALL
    )

    print("=== INDEX ===")
    for n, t in index:
        print(f"  {n}: {t[:70]}")

    print(f"\n=== BODY: {len(body_caps)} bold captions, {len(drawing_caps)} drawings ===")
    nums = [d[0] for d in drawing_caps if d[0]]
    print("Drawing -> caption order:", nums)
    for i in range(len(nums) - 1):
        if nums[i + 1] != nums[i] + 1:
            print(f"  BREAK: Fig {nums[i]} then Fig {nums[i+1]}")

    print(f"\n=== SECTION 5.4.1: {sec_drawings} drawings, {len(sec_figs)} captions ===")
    for n, t in sec_figs:
        print(f"  {n}: {t[:70]}")

    missing = [d for d in drawing_caps if d[0] is None]
    if missing:
        print(f"\n=== DRAWINGS WITHOUT CAPTION ({len(missing)}) ===")
        for _, _, name, pos in missing:
            print(f"  {name} at offset {pos}")

    # Index vs body count
    if len(index) != len([d for d in drawing_caps if d[0]]):
        print(f"\nCOUNT: index={len(index)} drawings_with_cap={len([d for d in drawing_caps if d[0]])}")


if __name__ == "__main__":
    main()
