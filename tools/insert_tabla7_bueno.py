#!/usr/bin/env python3
"""Insert missing Tabla 7 XML into BuenoCOPIAPFC document."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs/_pfc_diagramas_unpacked/word/document.xml"
DST = REPO / "docs/_pfc_bueno_unpacked/word/document.xml"

CAPTION = "<w:t>Tabla 7. Servicios y puertos en despliegue AWS</w:t>"


def extract_tabla7(xml: str) -> str:
    idx = xml.find(CAPTION)
    if idx < 0:
        raise SystemExit("Tabla 7 body caption not found in source")
    tbl_start = xml.find("<w:tbl>", idx)
    tbl_end = xml.find("</w:tbl>", tbl_start) + len("</w:tbl>")
    if tbl_end <= tbl_start:
        raise SystemExit("Table XML not found after Tabla 7")
    return xml[tbl_start:tbl_end]


def main() -> None:
    table_xml = extract_tabla7(SRC.read_text(encoding="utf-8"))
    dst_xml = DST.read_text(encoding="utf-8")

    marker = """    </w:p>
    <w:p w:rsidR="76A90D3D" w:rsidP="539269A4" w:rsidRDefault="76A90D3D" w14:paraId="69BA72C3" w14:textId="6A2DA08B">
      <w:pPr>
        <w:spacing w:before="40" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr/>
        <w:t>Fuente: elaboración propia.</w:t>"""

    if table_xml in dst_xml:
        print("Table already present; no change.")
        return

    if marker not in dst_xml:
        raise SystemExit("Insertion marker not found in destination")

    insert_block = f"""    </w:p>
    {table_xml}
    <w:p w:rsidR="76A90D3D" w:rsidP="539269A4" w:rsidRDefault="76A90D3D" w14:paraId="69BA72C3" w14:textId="6A2DA08B">
      <w:pPr>
        <w:spacing w:before="40" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr/>
        <w:t>Fuente: elaboración propia.</w:t>"""

    DST.write_text(dst_xml.replace(marker, insert_block, 1), encoding="utf-8")
    print(f"Inserted Tabla 7 ({len(table_xml)} chars) before Fuente paragraph.")


if __name__ == "__main__":
    main()
