#!/usr/bin/env python3
"""Audit figure numbering and captions in unpacked PFC document.xml."""
import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/_pfc_diagramas_unpacked/word/document.xml"


def main() -> int:
    xml = DOC.read_text(encoding="utf-8")
    # Manual figure index (skip TOC entry at ~line 198)
    idx_marker = xml.find('w:name="_Toc230036830"')
    i_start = xml.find("Índice de figuras", idx_marker)
    i_end = xml.find("Índice de tablas", i_start)
    index_figs = re.findall(r"Figura (\d+)\. ([^<]+)", xml[i_start:i_end])

    body_start = xml.find("4. DISEÑO")
    body = xml[body_start:]

    # Body legends use bold 10pt (sz 20 half-points)
    body_caps = []
    for m in re.finditer(
        r"<w:b/>.*?<w:t>Figura (\d+)\. ([^<]+)</w:t>", body, re.DOTALL
    ):
        n, t = int(m.group(1)), m.group(2).strip()
        body_caps.append((n, t))

    print(f"Index entries: {len(index_figs)}")
    print(f"Body captions: {len(body_caps)}")

    errors = []
    for i, ((in_n, in_t), (bd_n, bd_t)) in enumerate(zip(index_figs, body_caps), 1):
        if int(in_n) != bd_n:
            errors.append(f"#{i}: index Fig {in_n} vs body Fig {bd_n}")
        elif in_t.strip() != bd_t:
            errors.append(f"#{i}: text mismatch Fig {in_n}")

    if len(index_figs) != len(body_caps):
        errors.append(f"Count mismatch index={len(index_figs)} body={len(body_caps)}")

    # Drawings after each caption (image should precede caption)
    drawing_figs = []
    for m in re.finditer(r"<w:drawing>", body):
        chunk = body[m.start() : m.start() + 15000]
        figs = re.findall(r"Figura (\d+)\. ", chunk)
        name_m = re.search(r'wp:docPr[^>]*name="([^"]*)"', chunk[:3000])
        name = name_m.group(1) if name_m else "?"
        if figs:
            drawing_figs.append(int(figs[0]))
        else:
            errors.append(f"Drawing '{name}' without caption after image")

    if drawing_figs:
        expected = list(range(drawing_figs[0], drawing_figs[0] + len(drawing_figs)))
        if drawing_figs != expected:
            for j in range(len(drawing_figs) - 1):
                if drawing_figs[j + 1] != drawing_figs[j] + 1:
                    errors.append(
                        f"Order break after drawing: Fig {drawing_figs[j]} then Fig {drawing_figs[j+1]}"
                    )
        if drawing_figs[0] != 1:
            errors.append(f"First figure in body drawings is {drawing_figs[0]}, not 1")

    print(f"Drawings with post-caption: {len(drawing_figs)} -> {drawing_figs}")
    print(f"Total <w:drawing> in document.xml: {xml.count('<w:drawing>')}")

    # Fig 1: image before first body caption
    pre = body[: body.find("Figura 1. Arquitectura") + 500]
    if "<w:drawing>" not in pre:
        errors.append("Figura 1: no drawing found before its caption")

    # References in prose
    refs = re.findall(r"[Ff]igura\s+(\d+)", body)
    ref_nums = [int(x) for x in refs]
    for r in set(ref_nums):
        if r < 1 or r > 27:
            errors.append(f"Prose references invalid figure number: {r}")

    if errors:
        print("\nISSUES:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nOK: 27 figures, index matches body, sequential order in document.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
