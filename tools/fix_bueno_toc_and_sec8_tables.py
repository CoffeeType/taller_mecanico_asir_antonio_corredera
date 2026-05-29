#!/usr/bin/env python3
"""Extend main TOC (7.1–10) and insert missing tables 17–20 in Bueno PFC."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs/_pfc_diagramas_unpacked/word/document.xml"
DST = REPO / "docs/_pfc_bueno_unpacked/word/document.xml"

TOC_START = '<w:p w14:paraId="30F2A4D8"'
TOC_END = '<w:p w14:paraId="46644ABC"'

TOC_INSERT_AFTER = (
    '          </w:hyperlink>\n'
    "        </w:p>\n"
    "      </w:sdtContent>\n"
    "    </w:sdt>\n"
    '    <w:p w14:paraId="1093ECA3"'
)

TABLE_SPECS = [
    ("Tabla 17. Grado de consecución de objetivos", "<w:t>Fuente: elaboración propia.</w:t>"),
    ("Tabla 18. Problemas encontrados y resolución", "<w:t>8.2.1. Dificultades técnicas"),
    ("Tabla 19. Propuestas de mejora", "<w:t>Fuente: elaboración propia.</w:t>"),
    ("Tabla 20. Inventario de artefactos del repositorio", "<w:t>Fuente: elaboración propia.</w:t>"),
    ("Tabla 21. Variables principales de configuración", "<w:t>Fuente: elaboración propia.</w:t>"),
]


def extract_toc_block(src: str) -> str:
    start = src.find(TOC_START)
    end = src.find(TOC_END, start)
    if start < 0 or end < 0:
        raise SystemExit("TOC block not found in source")
    return src[start:end]


def extract_table_after_caption(src: str, caption: str) -> str:
    needle = f"<w:t>{caption}</w:t>"
    idx = src.find(needle)
    if idx < 0:
        raise SystemExit(f"Caption not found in source: {caption}")
    tbl_start = src.find("<w:tbl>", idx)
    tbl_end = src.find("</w:tbl>", tbl_start) + len("</w:tbl>")
    if tbl_end <= tbl_start:
        raise SystemExit(f"Table XML not found after: {caption}")
    return src[tbl_start:tbl_end]


def insert_table(dst: str, caption: str, next_needle: str, table_xml: str) -> str:
    cap_needle = f"<w:t>{caption}</w:t>"
    cap_idx = dst.find(cap_needle)
    if cap_idx < 0:
        raise SystemExit(f"Caption not in destination: {caption}")
    check = dst[cap_idx : cap_idx + 8000]
    if table_xml[:200] in check:
        print(f"  {caption.split('.')[0]}: already present")
        return dst
    para_end = dst.find("</w:p>", cap_idx) + len("</w:p>")
    nxt = dst.find(next_needle, para_end)
    if nxt < 0:
        raise SystemExit(f"Next marker not found for {caption}")
    return dst[:para_end] + "\n    " + table_xml + "\n    " + dst[para_end:]


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    dst = DST.read_text(encoding="utf-8")
    fig_idx = dst.find("ÍNDICE DE FIGURAS")
    toc_region = dst[:fig_idx]

    changed = False

    if "8. CONCLUSIONES</w:t>" in toc_region and "_Toc230036873" in toc_region:
        print("TOC: sections 8–10 already present")
    else:
        toc_block = extract_toc_block(src)
        if TOC_INSERT_AFTER not in dst:
            raise SystemExit("TOC insert anchor not found")
        dst = dst.replace(
            TOC_INSERT_AFTER,
            "          </w:hyperlink>\n        </w:p>\n" + toc_block + "      </w:sdtContent>\n    </w:sdt>\n    <w:p w14:paraId=\"1093ECA3\"",
            1,
        )
        print(f"TOC: inserted block ({len(toc_block)} chars)")
        changed = True

    for caption, next_needle in TABLE_SPECS:
        table_xml = extract_table_after_caption(src, caption)
        new_dst = insert_table(dst, caption, next_needle, table_xml)
        if new_dst != dst:
            print(f"  Inserted {caption.split('.')[0]} ({len(table_xml)} chars)")
            dst = new_dst
            changed = True

    if changed:
        DST.write_text(dst, encoding="utf-8")
        print("Saved", DST)
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
