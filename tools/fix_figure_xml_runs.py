#!/usr/bin/env python3
"""Fix invalid OOXML: w:t and w:drawing must not share the same w:r."""
import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/_pfc_diagramas_unpacked/word/document.xml"

DRAWING_RUN = (
    "</w:t>\n      </w:r>\n"
    "      <w:r>\n"
    "        <w:rPr>\n"
    "          <w:noProof/>\n"
    "        </w:rPr>\n"
    "        <w:drawing>"
)

TEXT_RUN = (
    "</w:drawing>\n"
    "      </w:r>\n"
    "      <w:r>\n"
    "        <w:t>"
)


def fix_document(xml: str) -> tuple[str, int]:
    n = 0
    while True:
        m = re.search(
            r"</w:t>(\s*(?:<w:lastRenderedPageBreak/>)?\s*)<w:drawing>",
            xml,
        )
        if not m:
            break
        insert = "</w:t>\n      </w:r>\n      <w:r>\n        <w:rPr>\n          <w:noProof/>\n        </w:rPr>\n"
        if m.group(1).strip():
            insert += m.group(1).strip() + "\n        "
        insert += "<w:drawing>"
        xml = xml[: m.start()] + insert + xml[m.end() :]
        n += 1

    while True:
        m = re.search(r"</w:drawing>\s*<w:t>", xml)
        if not m:
            break
        xml = xml[: m.start()] + TEXT_RUN + xml[m.end() :]
        n += 1

    return xml, n


def main() -> int:
    xml = DOC.read_text(encoding="utf-8")
    fixed, count = fix_document(xml)
    if count == 0:
        print("No fixes needed.")
        return 0
    DOC.write_text(fixed, encoding="utf-8")
    print(f"Applied {count} XML run fix(es) to {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
