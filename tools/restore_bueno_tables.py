#!/usr/bin/env python3
"""Restore missing w:tbl blocks in Bueno PFC from diagramas source."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs/_pfc_diagramas_unpacked/word/document.xml"
DST = REPO / "docs/_pfc_bueno_unpacked/word/document.xml"

# Body captions in bueno (no trailing dot), tables 1–21
BODY_CAPTIONS = [
    "Tabla 1. Relación entre módulos del CFGS ASIR y contenidos aplicados",
    "Tabla 2. Requisitos funcionales del sistema",
    "Tabla 3. Comparativa de soluciones existentes",
    "Tabla 4. Plan de trabajo y temporalización",
    "Tabla 5. Entidades principales de la base de datos",
    "Tabla 6. Servicios del despliegue Docker local",
    "Tabla 7. Servicios y puertos en despliegue AWS",
    "Tabla 8. Métricas y alertas implantadas",
    "Tabla 9. Requisitos no funcionales",
    "Tabla 10. Checklist de despliegue",
    "Tabla 11. Comparativa de escenarios de despliegue",
    "Tabla 12. Plan de mantenimiento preventivo",
    "Tabla 13. Recursos utilizados",
    "Tabla 14. Presupuesto anual orientativo",
    "Tabla 15. Matriz de pruebas funcionales y técnicas",
    "Tabla 16. Guion de demostración",
    "Tabla 17. Grado de consecución de objetivos",
    "Tabla 18. Problemas encontrados y resolución",
    "Tabla 19. Propuestas de mejora",
    "Tabla 20. Inventario de artefactos del repositorio",
    "Tabla 21. Variables principales de configuración",
]


def body_region(text: str) -> str:
    start = text.find("<w:t>1. INTRODUCCIÓN</w:t>")
    if start < 0:
        raise SystemExit("Section 1 not found")
    return text[start:]


def extract_table(src: str, caption: str) -> str | None:
    for cap in (caption, caption + "."):
        needle = f"<w:t>{cap}</w:t>"
        idx = src.find(needle)
        if idx < 0:
            continue
        # Prefer last match in body (after index)
        positions = [m.start() for m in re.finditer(re.escape(needle), src)]
        idx = positions[-1] if positions else idx
        tbl_start = src.find("<w:tbl>", idx)
        tbl_end = src.find("</w:tbl>", tbl_start)
        if tbl_start >= 0 and tbl_end > tbl_start:
            return src[tbl_start : tbl_end + len("</w:tbl>")]
    return None


def has_table_after(dst: str, cap_idx: int) -> bool:
    snippet = dst[cap_idx : cap_idx + 8000]
    fuente = snippet.find("Fuente:")
    tbl = snippet.find("<w:tbl>")
    return tbl >= 0 and (fuente < 0 or tbl < fuente)


def insert_table(dst: str, caption: str, table_xml: str) -> str:
    needle = f"<w:t>{caption}</w:t>"
    fig = dst.find("Índice de tablas")
    idx = dst.find(needle, fig if fig >= 0 else 0)
    if idx < 0:
        raise SystemExit(f"Caption not in bueno body: {caption}")
    if has_table_after(dst, idx):
        return dst
    para_end = dst.find("</w:p>", idx) + len("</w:p>")
    return dst[:para_end] + "\n    " + table_xml + "\n    " + dst[para_end:]


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    dst = DST.read_text(encoding="utf-8")
    changed = False

    for caption in BODY_CAPTIONS:
        table_xml = extract_table(src, caption)
        if not table_xml:
            print(f"SKIP (no source): {caption[:50]}...")
            continue
        new_dst = insert_table(dst, caption, table_xml)
        if new_dst != dst:
            print(f"Inserted: {caption[:55]}... ({len(table_xml)} chars)")
            dst = new_dst
            changed = True
        else:
            print(f"OK (present): {caption[:55]}...")

    if changed:
        DST.write_text(dst, encoding="utf-8")
        print("Saved", DST)
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
