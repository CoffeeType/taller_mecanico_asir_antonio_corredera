#!/usr/bin/env python3
"""Compare golden HTML PNGs vs PPTX-exported PNGs; write EXPORT_QA.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from defense_slides_manifest import SLIDES

# Slides with large diagrams tolerate more antialiasing drift
DIAGRAM_SLIDES = frozenset(
    {
        "architecture",
        "data_model",
        "traffic_source",
        "monitoring",
        "aws",
        "docker",
        "evidence",
        "problem",
        "profiles",
    }
)
# Raster export: golden HTML vs PowerPoint PNG export (antialiasing menor).
TEXT_THRESHOLD = 0.935
DIAGRAM_THRESHOLD = 0.88
EVIDENCE_THRESHOLD = 0.82
TITLE_SLIDES = frozenset({"cover", "closing"})
TITLE_THRESHOLD = 0.91


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def similarity(a_path: Path, b_path: Path) -> float | None:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("Requiere pillow: python -m pip install pillow", file=sys.stderr)
        raise SystemExit(1) from None

    if not a_path.is_file() or not b_path.is_file():
        return None
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    # Per-channel sum of squared diffs normalized
    sq = 0
    for i in range(256):
        sq += hist[i] * (i * i)
    max_sq = 255 * 255 * 3 * a.size[0] * a.size[1]
    if max_sq == 0:
        return 1.0
    return 1.0 - (sq / max_sq) ** 0.5


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--golden",
        type=Path,
        default=repo_root() / "docs" / "presentacion-defensa-pfc" / "_export_golden",
    )
    p.add_argument(
        "--pptx",
        type=Path,
        default=repo_root() / "docs" / "presentacion-defensa-pfc" / "_pptx_check",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=repo_root() / "docs" / "presentacion-defensa-pfc" / "EXPORT_QA.md",
    )
    args = p.parse_args()
    golden = args.golden.resolve()
    pptx_dir = args.pptx.resolve()
    report_path = args.report.resolve()

    rows: list[dict] = []
    failures = 0
    for spec in SLIDES:
        sid = spec.id
        g = golden / f"{sid}.png"
        t = pptx_dir / f"{sid}.png"
        if sid == "evidence":
            thresh = EVIDENCE_THRESHOLD
        elif sid in TITLE_SLIDES:
            thresh = TITLE_THRESHOLD
        elif sid in DIAGRAM_SLIDES:
            thresh = DIAGRAM_THRESHOLD
        else:
            thresh = TEXT_THRESHOLD
        sim = similarity(g, t)
        if sim is None:
            status = "MISSING"
            failures += 1
        elif sim >= thresh:
            status = "OK"
        else:
            status = "FAIL"
            failures += 1
        rows.append(
            {
                "id": sid,
                "similarity": round(sim, 4) if sim is not None else None,
                "threshold": thresh,
                "status": status,
            }
        )

    lines = [
        "# Export QA — HTML vs PPTX (captura raster full-bleed)",
        "",
        f"- Golden: `{golden}`",
        f"- PPTX PNG: `{pptx_dir}`",
        f"- Umbrales: texto {TEXT_THRESHOLD:.0%}, portada/cierre {TITLE_THRESHOLD:.0%}, "
        f"diagramas {DIAGRAM_THRESHOLD:.0%}, evidence {EVIDENCE_THRESHOLD:.0%}",
        "",
        "| Slide | Similitud | Umbral | Estado |",
        "|-------|-----------|--------|--------|",
    ]
    for r in rows:
        sim_s = f"{r['similarity']:.1%}" if r["similarity"] is not None else "—"
        lines.append(
            f"| `{r['id']}` | {sim_s} | {r['threshold']:.0%} | {r['status']} |"
        )
    lines.extend(
        [
            "",
            f"**Resumen:** {len(rows) - failures}/{len(rows)} slides OK.",
            "",
        ]
    )
    if failures:
        lines.append("Algunas diapositivas están por debajo del umbral; revisar en PowerPoint.")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    json_path = report_path.with_suffix(".json")
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Informe: {report_path}")
    print(f"JSON: {json_path}")
    for r in rows:
        if r["status"] != "OK":
            print(f"  {r['id']}: {r['status']} ({r.get('similarity')})")
    if failures:
        raise SystemExit(1)
    print("OK — todas las diapositivas dentro del umbral.")


if __name__ == "__main__":
    main()
