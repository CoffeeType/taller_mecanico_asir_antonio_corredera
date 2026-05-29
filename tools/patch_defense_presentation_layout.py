#!/usr/bin/env python3
"""OBSOLETO: fusionaba ASIR en una sola diapositiva. Usar restore_defense_presentation_contract.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "docs" / "presentacion-defensa-pfc" / "index.html"
MERMAID_DIR = REPO / "docs" / "mermaid"

MERGED_ASIR_SECTION = """<!-- NOTE: 3:00–5:00. Stack + Tabla 1. Gráfico interactivo y mapa de competencias antes de arquitectura. -->
<section class="slide" data-id="asir_modules">
  <div class="slide-content">
    <span class="slide-num reveal">05</span>
    <h2 class="reveal">Stack tecnológico y competencias ASIR</h2>
    <div class="slide-main reveal asir-combo">
      <div class="asir-combo-chart tech-chart-panel reveal">
        <div class="tech-chart-wrap" id="techChart" role="img" aria-label="Gráfico circular del stack tecnológico del PFC. Pulsa un segmento o la leyenda para ver el rol de cada tecnología."></div>
        <div class="tech-legend" id="techLegend" role="list" aria-label="Leyenda del stack tecnológico"></div>
        <p class="tech-chart-hint">Pulsa un segmento o la leyenda para ver el rol en el proyecto.</p>
      </div>
      <div class="asir-combo-table table-wrap reveal dense-table">
      <table class="data-table">
      <thead><tr>
      <th>Módulo</th>
      <th>Contenidos aplicados en el PFC</th>
      </tr></thead><tbody>
      <tr>
      <td>Implantación de Aplicaciones Web</td>
      <td>PHP, Apache, sesiones, formularios, panel admin, API de citas.</td>
      </tr>
      <tr>
      <td>Gestión de Bases de Datos</td>
      <td>MySQL 8, relaciones, índices, unicidad en citas y usuarios.</td>
      </tr>
      <tr>
      <td>Administración de SGBD</td>
      <td>Inicialización SQL, usuarios de aplicación, backups, migración futura a RDS.</td>
      </tr>
      <tr>
      <td>Servicios de Red e Internet</td>
      <td>HTTP, puertos, redes Docker, monitorización.</td>
      </tr>
      <tr>
      <td>Administración de Sistemas Operativos</td>
      <td>Contenedores, volúmenes, logs, healthchecks, scripts de despliegue.</td>
      </tr>
      <tr>
      <td>Seguridad y Alta Disponibilidad</td>
      <td>Roles, contraseñas cifradas, CSRF, consultas preparadas, alertas.</td>
      </tr>
      <tr>
      <td>Planificación y Administración de Redes</td>
      <td>Docker Compose, redes, volúmenes, Security Groups en AWS.</td>
      </tr>
      <tr>
      <td>LMSGI</td>
      <td>HTML/CSS/JS, Markdown, YAML Compose, JSON de dashboards Grafana.</td>
      </tr>
      <tr>
      <td>Empresa e Iniciativa Emprendedora</td>
      <td>Digitalización del taller, presupuesto y costes de explotación.</td>
      </tr>
      <tr>
      <td>Proyecto de administración de sistemas</td>
      <td>Planificación, documentación, despliegue EC2, observabilidad y pruebas.</td>
      </tr>
      </tbody></table>
      </div>
    </div>
  </div>
</section>
"""


def load_mermaid(name: str) -> str:
    path = MERMAID_DIR / name
    text = path.read_text(encoding="utf-8-sig").strip()
    return text


def replace_diagram_img(html: str, slide_id: str, mermaid_body: str) -> str:
    """Replace base64 img inside diagram-figure for a given slide id."""
    section_re = re.compile(
        rf'(<section class="slide diagram-slide" data-id="{re.escape(slide_id)}">.*?)'
        r'<figure class="diagram-figure(?: mermaid-wrap)?">'
        r'(?:<img[^>]+>|<pre class="mermaid">.*?</pre>)'
        r"</figure>",
        re.DOTALL,
    )
    inner = mermaid_body.strip()

    def subfn(m: re.Match[str]) -> str:
        return (
            m.group(1)
            + f'<figure class="diagram-figure mermaid-wrap"><pre class="mermaid">{inner}</pre></figure>'
        )

    new_html, n = section_re.subn(subfn, html, count=1)
    if n != 1:
        raise RuntimeError(f"diagram replace failed for {slide_id} (count={n})")
    return new_html


def fix_broken_figure_tags(html: str) -> str:
    """Repair prior bad replacement: diagram-figure\"> mermaid-wrap\">."""
    return html.replace(
        '<figure class="diagram-figure"> mermaid-wrap">',
        '<figure class="diagram-figure mermaid-wrap">',
    )


def merge_asir_slides(html: str) -> str:
    start = html.index("<!-- NOTE: 3:00")
    end = html.index("<!-- NOTE: 5:00–5:45.")
    return html[:start] + MERGED_ASIR_SECTION + "\n" + html[end:]


def renumber_slide_nums(html: str) -> str:
    """After removing slide 06, decrement slide-num labels 07..20 -> 06..19."""

    def repl(m: re.Match[str]) -> str:
        n = int(m.group(1))
        if n > 6:
            return f'<span class="slide-num reveal">{n - 1:02d}'
        return m.group(0)

    return re.sub(r'<span class="slide-num reveal">(\d{2})', repl, html)


def main() -> int:
    if not INDEX.is_file():
        print(f"Missing {INDEX}", file=sys.stderr)
        return 1

    html = INDEX.read_text(encoding="utf-8")
    html = fix_broken_figure_tags(html)

    # Typography tokens
    html = html.replace(
        "--title-size: clamp(1.65rem, 5.2vw, 3.5rem);\n"
        "      --h2-size: clamp(1.45rem, 3.8vw, 2.75rem);\n"
        "      --body-size: clamp(1rem, 1.85vw, 1.35rem);\n"
        "      --table-size: clamp(0.95rem, 1.45vw, 1.125rem);\n"
        "      --small-size: clamp(0.85rem, 1.2vw, 1rem);",
        "--title-size: clamp(1.85rem, 5.5vw, 3.75rem);\n"
        "      --h2-size: clamp(1.65rem, 4.2vw, 3rem);\n"
        "      --body-size: clamp(1.1rem, 2vw, 1.5rem);\n"
        "      --table-size: clamp(1.05rem, 1.65vw, 1.25rem);\n"
        "      --small-size: clamp(0.9rem, 1.35vw, 1.1rem);",
    )

    html = merge_asir_slides(html)
    html = renumber_slide_nums(html)
    html = html.replace("01 / 20", "01 / 19")

    diagrams = {
        "architecture": load_mermaid("pfc-fig01-arquitectura.mmd"),
        "traffic_source": load_mermaid("pfc-fig24-jmeter.mmd"),
        "monitoring": load_mermaid("pfc-fig-monitoring.mmd"),
        "aws": load_mermaid("pfc-fig23-ec2.mmd"),
    }
    for sid, body in diagrams.items():
        html = replace_diagram_img(html, sid, body)

    INDEX.write_text(html, encoding="utf-8")
    print(f"Patched {INDEX.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
