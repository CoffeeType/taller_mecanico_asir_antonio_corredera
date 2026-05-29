#!/usr/bin/env python3
"""Exhaustive OOXML audit for PFC docx (unpacked or zipped)."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REPO = Path(__file__).resolve().parents[1]
DOCX = REPO / "docs" / "PFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells con cambios.docx"


def load_document_xml(source: Path) -> str:
    if source.is_dir():
        return (source / "word" / "document.xml").read_text(encoding="utf-8")
    with zipfile.ZipFile(source) as z:
        return z.read("word/document.xml").decode("utf-8")


def audit_xml(doc: str, rels: str, media: set[str], label: str) -> list[str]:
    issues: list[str] = []

    try:
        ET.fromstring(doc)
    except ET.ParseError as e:
        issues.append(f"FATAL: document.xml no parsea: {e}")

    # Nested paragraphs (invalid)
    for m in re.finditer(
        r"(<w:p w:[^>]+>)(?:(?!</w:p>).)*?<w:p(?:\s|>)",
        doc,
        re.DOTALL,
    ):
        snippet = doc[m.start() : m.start() + 120].replace("\n", " ")
        issues.append(f"Párrafo anidado inválido (~pos {m.start()}): {snippet}...")
        if len([i for i in issues if "anidado" in i]) >= 5:
            issues.append("... (más párrafos anidados omitidos)")
            break

    # Bare <w:p> without Word attributes (from apply script para_text)
    bare = list(re.finditer(r"<w:p>\s*<w:pPr>", doc))
    if bare:
        issues.append(f"Párrafos sin atributos Word (bare <w:p>): {len(bare)} casos")

    # Text glued after drawing in same malformed pattern
    if re.search(r"</w:drawing>\s*<w:t>", doc):
        issues.append("Texto <w:t> pegado tras </w:drawing> fuera de estructura")

    # Unclosed w:r before sibling w:drawing at paragraph level (broken structure)
    for m in re.finditer(
        r"<w:p[^>]*>(?:(?!</w:p>).)*?<w:r>(?:(?!</w:r>).)*?<w:t[^>]*>[^<]*</w:t>\s*<w:drawing>",
        doc,
        re.DOTALL,
    ):
        # Valid if </w:r> appears between </w:t> and <w:drawing>
        block = m.group(0)
        if not re.search(r"</w:t>\s*</w:r>\s*<w:r", block) and "</w:t>\s*<w:drawing>" in block.replace(
            "\n", " "
        ):
            pass
        inner = block[block.rfind("<w:r>") :]
        if re.search(r"</w:t>\s*<w:drawing>", inner) and "</w:t>\s*</w:r>" not in re.sub(
            r"\s+", " ", inner
        ):
            issues.append(
                f"Run sin cerrar antes de drawing (~pos {m.start()}): revisar Figura/captura"
            )
            if len([i for i in issues if "Run sin cerrar" in i]) >= 3:
                break

    # Simpler: find </w:t> followed by <w:drawing> without </w:r> between
    for m in re.finditer(r"</w:t>(\s*)<w:drawing>", doc):
        between = doc[max(0, m.start() - 200) : m.start()]
        last_r_open = between.rfind("<w:r")
        last_r_close = between.rfind("</w:r>")
        if last_r_open > last_r_close:
            issues.append(f"</w:t> seguido de <w:drawing> sin cerrar </w:r> (~pos {m.start()})")
            if len([i for i in issues if "seguido de <w:drawing>" in i]) >= 5:
                issues.append("... (más casos omitidos)")
                break

    # Comment orphans
    if "commentReference" in doc or "commentRangeStart" in doc:
        issues.append("Referencias a comentarios en document.xml sin contenido")

    # Duplicate section numbers / scrambled order
    eip_positions = [m.start() for m in re.finditer(r"5\.4\.2\. Dirección IP", doc)]
    ec2_positions = [m.start() for m in re.finditer(r"5\.4\.1\. Lanzamiento", doc)]
    if len(eip_positions) > 1:
        issues.append(f"Texto 5.4.2 duplicado ({len(eip_positions)} veces)")
    if eip_positions and ec2_positions and eip_positions[0] < ec2_positions[0]:
        issues.append("Orden incorrecto: 5.4.2 aparece antes de 5.4.1 en el XML")

    # para_text() bare paragraphs in body
    if '<w:p><w:pPr>' in doc:
        issues.append("Bloques <w:p><w:pPr> generados por script (sin rsid/paraId)")

    # Relationships
    if 'Target="/media/' in rels:
        issues.append('Ruta absoluta Target="/media/..." en document.xml.rels')
    if "image1b" in rels:
        issues.append("Relación a image1b inexistente")

    for m in re.finditer(r'r:embed="(rId\d+)"', doc):
        rid = m.group(1)
        if f'Id="{rid}"' not in rels:
            issues.append(f"Embed {rid} sin relación en .rels")
            continue
        seg = rels.split(f'Id="{rid}"', 1)[1][:250]
        tm = re.search(r'Target="([^"]+)"', seg)
        if not tm:
            continue
        target = tm.group(1).replace("media/", "")
        if target.startswith("/"):
            issues.append(f"Embed {rid} -> ruta absoluta {tm.group(1)}")
        elif target.endswith((".png", ".jpg", ".jpeg", ".gif")):
            name = Path(target).name
            if name not in media:
                issues.append(f"Embed {rid} -> {tm.group(1)} (fichero no en word/media/)")

    # Empty broken paragraphs from bad repair
    empty_with_attrs = len(
        re.findall(r"<w:p w:[^>]+>\s*<w:pPr>[^<]*</w:pPr>\s*</w:p>", doc)
    )
    self_close = len(re.findall(r"<w:p w:[^>]+/>", doc))
    if empty_with_attrs > 3:
        issues.append(f"Párrafos vacíos sospechosos: {empty_with_attrs}")

    return issues


def audit_package(root: Path) -> list[str]:
    issues: list[str] = []
    doc = load_document_xml(root)
    if root.is_dir():
        rels = (root / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
        media_dir = root / "word" / "media"
        media = {p.name for p in media_dir.glob("*")} if media_dir.is_dir() else set()
        label = str(root)
    else:
        with zipfile.ZipFile(root) as z:
            rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
            media = {n.split("/")[-1] for n in z.namelist() if n.startswith("word/media/")}
            bad = z.testzip()
            if bad:
                issues.append(f"ZIP corrupto: {bad}")
            for n in z.namelist():
                if n.endswith((".xml", ".rels")):
                    try:
                        ET.fromstring(z.read(n))
                    except ET.ParseError as e:
                        issues.append(f"Parse error {n}: {e}")
        label = root.name

    issues.extend(audit_xml(doc, rels, media, label))
    return issues


def main() -> int:
    unpacked = REPO / "docs" / "_pfc_audit"
    targets = []
    if unpacked.is_dir():
        targets.append(unpacked)
    if DOCX.is_file():
        targets.append(DOCX)

    all_issues: list[str] = []
    for t in targets:
        print(f"\n=== {t} ===")
        issues = audit_package(t)
        if issues:
            print(f"Encontrados {len(issues)} problema(s):")
            for i in issues:
                print(f"  - {i}")
            all_issues.extend(issues)
        else:
            print("Sin problemas detectados.")

    return 1 if all_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
