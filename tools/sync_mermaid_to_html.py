#!/usr/bin/env python3
"""Inject docs/mermaid/*.mmd into index.html pre.mermaid blocks by slide id."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "docs" / "presentacion-defensa-pfc" / "index.html"
MERMAID = REPO / "docs" / "mermaid"

# slide data-id -> mermaid file
DIAGRAM_SLIDES = {
    "architecture": "pfc-fig01-arquitectura.mmd",
    "traffic_source": "pfc-fig24-jmeter.mmd",
    "monitoring": "pfc-fig-monitoring.mmd",
    "aws": "pfc-fig23-ec2.mmd",
}

CONTENT_SPLIT_MERMAID = {
    "profiles": "pfc-fig03-reserva-sequence.mmd",
    "docker": "pfc-fig-docker-compose.mmd",
}

DATA_MODEL_ER = "pfc-fig02-data-model.mmd"
DATA_MODEL_FLOW = "pfc-fig03-reserva.mmd"


def load(name: str) -> str:
    return (MERMAID / name).read_text(encoding="utf-8-sig").strip()


def replace_slide_diagram(html: str, slide_id: str, body: str) -> str:
    pattern = re.compile(
        rf'(<section[^>]*data-id="{re.escape(slide_id)}"[^>]*>.*?)'
        r'<figure class="diagram-figure mermaid-wrap"><pre class="mermaid">'
        r"[\s\S]*?"
        r"</pre></figure>",
        re.DOTALL,
    )

    def sub(m: re.Match[str]) -> str:
        return (
            m.group(1)
            + f'<figure class="diagram-figure mermaid-wrap"><pre class="mermaid">{body}</pre></figure>'
        )

    new_html, n = pattern.subn(sub, html, count=1)
    if n != 1:
        raise RuntimeError(f"Could not update diagram for slide {slide_id} (n={n})")
    return new_html


def replace_content_split_mermaid(html: str, slide_id: str, body: str) -> str:
    pattern = re.compile(
        rf'(<section[^>]*data-id="{re.escape(slide_id)}"[^>]*>.*?)'
        r'<figure class="content-split-aside mermaid-wrap content-split-mermaid"[^>]*>\s*'
        r'<pre class="mermaid">[\s\S]*?</pre>\s*</figure>',
        re.DOTALL,
    )

    def sub(m: re.Match[str]) -> str:
        return (
            m.group(1)
            + '<figure class="content-split-aside mermaid-wrap content-split-mermaid">'
            + f'<pre class="mermaid">{body}</pre></figure>'
        )

    new_html, n = pattern.subn(sub, html, count=1)
    if n != 1:
        raise RuntimeError(f"content-split mermaid for {slide_id} failed (n={n})")
    return new_html


def replace_data_model(html: str) -> str:
    er = load(DATA_MODEL_ER)
    flow = load(DATA_MODEL_FLOW)
    block = f"""<section class="slide diagram-slide" data-id="data_model">
  <div class="slide-content">
    <span class="slide-num reveal">08</span>
    <h2 class="reveal">Modelo de datos y flujo de reserva (Fig. 2 y 3)</h2>
    <div class="slide-main reveal dual-mermaid">
      <figure class="diagram-figure mermaid-wrap mermaid-wrap--half" aria-label="Fig. 2 Modelo de datos">
        <pre class="mermaid">{er}</pre>
      </figure>
      <figure class="diagram-figure mermaid-wrap mermaid-wrap--half" aria-label="Fig. 3 Flujo de reserva">
        <pre class="mermaid">{flow}</pre>
      </figure>
    </div>
  </div>
</section>"""
    pattern = re.compile(
        r'<section class="slide(?: diagram-slide)?" data-id="data_model">[\s\S]*?</section>',
        re.DOTALL,
    )
    new_html, n = pattern.subn(block, html, count=1)
    if n != 1:
        raise RuntimeError(f"data_model section replace failed (n={n})")
    return new_html


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")
    for sid, fname in DIAGRAM_SLIDES.items():
        html = replace_slide_diagram(html, sid, load(fname))
    for sid, fname in CONTENT_SPLIT_MERMAID.items():
        html = replace_content_split_mermaid(html, sid, load(fname))
    html = replace_data_model(html)
    INDEX.write_text(html, encoding="utf-8")
    print(f"Synced mermaid sources into {INDEX.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
