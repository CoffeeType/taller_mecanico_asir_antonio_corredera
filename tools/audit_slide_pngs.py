#!/usr/bin/env python3
"""Detecta PNG vacíos, casi en blanco o con poco contenido."""

from __future__ import annotations

import sys
from pathlib import Path

from defense_slides_manifest import SLIDES


def analyze(path: Path) -> dict:
    from PIL import Image, ImageStat

    im = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(im)
    # varianza media de canales
    var = sum(stat.var) / 3
    # % píxeles casi blancos (fondo típico #f4f1ec ~ 244,241,236)
    pixels = list(im.getdata())
    n = len(pixels)
    whiteish = sum(
        1 for r, g, b in pixels if r > 235 and g > 230 and b > 225
    )
    white_pct = 100 * whiteish / n if n else 0
    return {
        "size_kb": path.stat().st_size // 1024,
        "w": im.width,
        "h": im.height,
        "var": round(var, 1),
        "white_pct": round(white_pct, 1),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dirs = {
        "golden": root / "docs" / "presentacion-defensa-pfc" / "_export_golden",
        "pptx": root / "docs" / "presentacion-defensa-pfc" / "_pptx_check",
    }
    bad = []
    print(f"{'id':<18} {'src':<8} {'kb':>5} {'dim':>12} {'var':>8} {'white%':>7} flag")
    print("-" * 70)
    for spec in SLIDES:
        sid = spec.id
        for name, d in dirs.items():
            p = d / f"{sid}.png"
            if not p.is_file():
                print(f"{sid:<18} {name:<8} MISSING")
                bad.append((sid, name, "missing"))
                continue
            m = analyze(p)
            flags = []
            if m["size_kb"] < 8:
                flags.append("tiny")
            if m["var"] < 80:
                flags.append("low-var")
            if m["white_pct"] > 97:
                flags.append("blank?")
            flag = ",".join(flags) or "ok"
            if flags:
                bad.append((sid, name, flag))
            print(
                f"{sid:<18} {name:<8} {m['size_kb']:>5} "
                f"{m['w']}x{m['h']:>4} {m['var']:>8} {m['white_pct']:>6}% {flag}"
            )
    if bad:
        print(f"\n{len(bad)} aviso(s)")
        raise SystemExit(1)
    print("\nOK — sin PNG sospechosos")


if __name__ == "__main__":
    main()
