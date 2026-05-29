#!/usr/bin/env python3
"""Audit unpacked/docx OOXML for Word-open issues."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
DOCX = REPO / "docs" / "PFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells con cambios.docx"
UNPACKED = REPO / "docs" / "_pfc_review"


def audit_zip(docx: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(docx) as z:
        bad = z.testzip()
        if bad:
            issues.append(f"Corrupt zip entry: {bad}")
        names = set(z.namelist())
        for n in sorted(names):
            if n.endswith((".xml", ".rels")):
                try:
                    ET.fromstring(z.read(n))
                except ET.ParseError as e:
                    issues.append(f"Parse error in {n}: {e}")
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        ns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
        for rel in rels.findall(f".//{ns}Relationship"):
            target = rel.get("Target", "")
            if not target or target.startswith("http"):
                continue
            paths = {target, "word/" + target.lstrip("/")}
            if target.startswith("../"):
                paths.add(target[3:])
            if not paths & names:
                issues.append(f"Missing rel {rel.get('Id')}: {target}")
        doc = z.read("word/document.xml").decode("utf-8")
        rels_txt = z.read("word/_rels/document.xml.rels").decode("utf-8")
        checks = [
            (doc, r"</w:drawing><w:t>", "Malformed: text after drawing in same run"),
            (doc, r"commentReference", "Comment references still in document"),
            (doc, r"<w:p>\s*\n\s*<w:pPr>", "Bare w:p without Word attributes"),
            (rels_txt, r'Target="/media/', "Absolute /media path in rels"),
            (rels_txt, "image1b", "Reference to missing image1b"),
        ]
        for text, pat, msg in checks:
            if re.search(pat, text):
                issues.append(msg)
        # unbalanced tags rough check
        for tag in ("w:p", "w:r", "w:tbl"):
            o, c = doc.count(f"<{tag} "), doc.count(f"</{tag}>")
            if o != c:
                issues.append(f"Tag imbalance {tag}: open={o} close={c}")
    return issues


def audit_unpacked(root: Path) -> list[str]:
    issues: list[str] = []
    doc = (root / "word" / "document.xml").read_text(encoding="utf-8")
    media = {p.name for p in (root / "word" / "media").glob("*")}
    rels = (root / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
    for m in re.finditer(r'r:embed="(rId\d+)"', doc):
        rid = m.group(1)
        if f'Id="{rid}"' in rels:
            seg = rels.split(f'Id="{rid}"', 1)[1][:200]
            tm = re.search(r'Target="([^"]+)"', seg)
            if tm:
                t = tm.group(1).replace("media/", "")
                if t.startswith("/") or (t.endswith(".png") and Path(t).name not in media):
                    issues.append(f"Bad embed {rid} -> {tm.group(1)}")
    return issues


def main() -> int:
    target = UNPACKED if UNPACKED.is_dir() else DOCX
    issues = audit_unpacked(UNPACKED) if UNPACKED.is_dir() else []
    issues.extend(audit_zip(DOCX))
    print(f"Audited: {DOCX.name}")
    if issues:
        print(f"Found {len(issues)} issue(s):")
        for i in sorted(set(issues)):
            print(" -", i)
        return 1
    print("No issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
