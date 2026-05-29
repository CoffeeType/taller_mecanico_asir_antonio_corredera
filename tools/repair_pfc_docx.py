#!/usr/bin/env python3
"""Repair OOXML issues that prevent Word from opening the PFC docx."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UNPACKED = REPO / "docs" / "_pfc_audit"
DOC = UNPACKED / "word" / "document.xml"
RELS = UNPACKED / "word" / "_rels" / "document.xml.rels"
OUT_DOCX = REPO / "docs" / "PFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells con cambios.docx"
OUT_DOCX_ALT = REPO / "docs" / "PFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_REPARADO.docx"
PACK_SCRIPT = Path.home() / ".agents/skills/docx/scripts/office/pack.py"


def remove_orphan_package_media() -> None:
    """Remove media/ at package root (left by bad /media/ rel paths). Word flags as corrupt."""
    orphan = UNPACKED / "media"
    if orphan.is_dir():
        import shutil

        shutil.rmtree(orphan)
        print("Removed orphan package-root media/ folder")


def repair_rels() -> None:
    text = RELS.read_text(encoding="utf-8")
    text = text.replace('Target="/media/image19.png"', 'Target="media/image19.png"')
    text = text.replace('Target="/media/image1b.png"', 'Target="media/image5.png"')
    RELS.write_text(text, encoding="utf-8")
    print("Fixed cover image relationship targets (relative to word/)")


def repair_nested_paragraphs(xml: str) -> str:
    """Fix invalid <w:p> nested inside another <w:p> (breaks Word)."""
    while True:
        m = re.search(
            r"(<w:p w:[^>]+>)(?:(?!</w:p>).)*?<w:p>\s*<w:pPr>",
            xml,
            re.DOTALL,
        )
        if not m:
            break
        outer_start = m.start()
        outer_open = m.group(1)
        inner_start = m.end() - len("<w:pPr>")
        # find end of outer paragraph
        outer_end = xml.find("</w:p>", inner_start)
        if outer_end == -1:
            break
        block = xml[outer_start : outer_end + len("</w:p>")]
        # split: outer pPr + runs before inner, then inner paragraphs
        inner_parts = re.findall(
            r"<w:p>\s*(<w:pPr>.*?</w:pPr>\s*.*?)\s*</w:p>",
            block,
            re.DOTALL,
        )
        outer_ppr_m = re.search(r"<w:pPr>.*?</w:pPr>", block, re.DOTALL)
        trailing_run_m = re.search(
            r"</w:p>\s*<w:r>\s*<w:t>([^<]*)</w:t>\s*</w:r>\s*</w:p>\s*$",
            block,
            re.DOTALL,
        )
        if not inner_parts:
            break
        rsid = re.search(r'w:rsidR="([^"]+)"', outer_open)
        rsid_attr = rsid.group(1) if rsid else "00E6580A"
        new_paras = []
        for idx, inner in enumerate(inner_parts):
            new_paras.append(
                f'<w:p w:rsidR="{rsid_attr}" w:rsidP="004A512A" w:rsidRDefault="00000000" '
                f'w14:paraId="FIX{idx:04d}" w14:textId="77777777">\n      {inner}\n    </w:p>'
            )
        if trailing_run_m and outer_ppr_m:
            title = trailing_run_m.group(1)
            new_paras.append(
                f'<w:p w:rsidR="{rsid_attr}" w:rsidP="004A512A" w:rsidRDefault="0081761B" '
                f'w14:paraId="FIXHEAD" w14:textId="77777777">\n      {outer_ppr_m.group(0)}\n      '
                f"<w:r><w:t>{title}</w:t></w:r>\n    </w:p>"
            )
        xml = xml[:outer_start] + "\n".join(new_paras) + xml[outer_end + len("</w:p>") :]
        print("Fixed nested paragraph block")
    return xml


def repair_document() -> None:
    xml = DOC.read_text(encoding="utf-8")
    xml = repair_nested_paragraphs(xml)

    # Stray text run glued after drawing
    xml = xml.replace("</w:drawing><w:t>.</w:t></w:r>", "</w:drawing></w:r>")

    # Close w:r before w:drawing when text run was left open (Fig 21 paragraph)
    xml = re.sub(
        r"(<w:t xml:space=\"preserve\">Seleccionaremos la instancia[^<]*</w:t>)\s*<w:drawing>",
        r"\1\n      </w:r>\n      <w:r>\n        <w:rPr>\n          <w:noProof/>\n        </w:rPr>\n        <w:drawing>",
        xml,
        count=1,
    )

    # Bare <w:p> from script inserts -> valid paragraph shell
    bare_p = (
        '<w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="77777777" w14:textId="77777777">'
    )
    xml = xml.replace("<w:p>\n      <w:pPr>", f"{bare_p}\n      <w:pPr>")

    DOC.write_text(xml, encoding="utf-8")
    print("Fixed document.xml structure")


def repair_comments() -> None:
    empty_comments = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
    )
    empty_extended = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<w15:commentsEx xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"/>'
    )
    (UNPACKED / "word" / "comments.xml").write_text(empty_comments, encoding="utf-8")
    (UNPACKED / "word" / "commentsExtended.xml").write_text(empty_extended, encoding="utf-8")
    ids = UNPACKED / "word" / "commentsIds.xml"
    if ids.is_file():
        ids.write_text(
            '<?xml version="1.0" encoding="utf-8"?>'
            '<w16cid:commentsIds xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid"/>',
            encoding="utf-8",
        )
    print("Cleared comment sidecar files")


def validate_png() -> None:
    try:
        from PIL import Image
    except ImportError:
        print("PIL not installed; skipping PNG check")
        return
    media = UNPACKED / "word" / "media"
    for png in media.glob("*.png"):
        try:
            Image.open(png).verify()
        except Exception as e:
            print(f"WARN corrupt PNG {png.name}: {e}")


def pack() -> None:
    import subprocess
    import sys
    import shutil

    original = OUT_DOCX if OUT_DOCX.is_file() else OUT_DOCX_ALT
    targets = [OUT_DOCX, OUT_DOCX_ALT]
    packed = False
    for target in targets:
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(PACK_SCRIPT),
                    str(UNPACKED),
                    str(target),
                    "--original",
                    str(original),
                    "--validate",
                    "false",
                ],
                check=True,
            )
            print(f"Packed: {target}")
            packed = True
            if target == OUT_DOCX_ALT and OUT_DOCX.exists():
                print("Nota: el .docx original estaba abierto; usa el fichero _REPARADO.docx")
            break
        except (PermissionError, subprocess.CalledProcessError):
            continue
    if not packed:
        raise SystemExit("No se pudo escribir el docx (cierra Word y vuelve a ejecutar repair_pfc_docx.py)")


def main() -> None:
    if not UNPACKED.is_dir():
        raise SystemExit(f"Run unpack first: {UNPACKED}")
    remove_orphan_package_media()
    repair_rels()
    repair_document()
    repair_comments()
    validate_png()
    pack()


if __name__ == "__main__":
    main()
