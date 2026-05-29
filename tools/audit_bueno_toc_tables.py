#!/usr/bin/env python3
"""Audit main TOC and table presence in Bueno PFC document."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
BUENO = REPO / "docs/_pfc_bueno_unpacked/word/document.xml"
SRC = REPO / "docs/_pfc_diagramas_unpacked/word/document.xml"


def main() -> None:
    bueno = BUENO.read_text(encoding="utf-8")
    src = SRC.read_text(encoding="utf-8")

    i0 = bueno.find('w:name="_Toc230036828"')
    i1 = bueno.find("ÍNDICE DE FIGURAS", i0)
    toc = bueno[i0:i1]
    body = bueno[i1:]

    print("=== MAIN TOC (top-level N. TITLE) ===")
    for m in re.finditer(
        r"<w:t[^>]*>(\d+\.\s+[A-ZÁÉÍÓÚÑ][^<]{8,70})</w:t>", toc
    ):
        print(" ", m.group(1).strip())

    print("\n=== BODY top-level sections ===")
    for m in re.finditer(
        r"<w:t[^>]*>(\d+\.\s+[A-ZÁÉÍÓÚÑ][^<]{8,70})</w:t>", body
    ):
        t = m.group(1).strip()
        if re.match(r"^\d+\.\s", t) and not t.startswith("Tabla"):
            print(" ", t[:75])

    print("\n=== TABLES (body captions, w:tbl within 12k chars) ===")
    for n in range(1, 21):
        for suffix in ("", "."):
            cap = f"Tabla {n}."
            idx = body.find(f"<w:t>Tabla {n}.")
            if idx < 0:
                idx = body.find(f"Tabla {n}.", body.find("Índice de tablas") if n > 1 else 0)
            break
        # body captions without trailing dot in index
        pat = f"Tabla {n}."
        positions = [m.start() for m in re.finditer(re.escape(pat), body)]
        body_caps = [p for p in positions if body[p : p + 20].startswith("<w:t>") or "<w:t>" in body[max(0, p - 50) : p + 5]]
        if not positions:
            print(f"  {n}: missing")
            continue
        # use last occurrence in body (after index)
        idx_fig = body.find("Índice de tablas")
        body_pos = max(p for p in positions if p > idx_fig + 100) if idx_fig >= 0 else positions[-1]
        snippet = body[body_pos : body_pos + 12000]
        tbl = snippet.find("<w:tbl>")
        fuente = snippet.find("Fuente:")
        has = tbl >= 0 and (fuente < 0 or tbl < fuente)
        title = re.search(rf"Tabla {n}\.([^<]+)", snippet)
        tit = title.group(0)[:55] if title else "?"
        print(f"  {n}: {'OK' if has else 'MISSING w:tbl'} — {tit}")

    print("\n=== Compare table XML sizes src vs bueno (sec 8 tables 17-20) ===")
    for n in (17, 18, 19, 20):
        for label, xml in [("src", src), ("bueno", bueno)]:
            cap = f"Tabla {n}."
            idx = xml.find(f"<w:t>Tabla {n}.")
            if idx < 0:
                print(f"  {label} Tabla {n}: caption not found")
                continue
            snip = xml[idx : idx + 15000]
            t0 = snip.find("<w:tbl>")
            t1 = snip.find("</w:tbl>")
            print(f"  {label} Tabla {n}: tbl_len={t1 - t0 if t0 >= 0 else 0}")


if __name__ == "__main__":
    main()
