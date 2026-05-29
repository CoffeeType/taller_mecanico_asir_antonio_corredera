#!/usr/bin/env python3
"""
Restore defense deck contract: 20 slides (cover + 19 numbered), asir_modules_2,
chart-only ASIR slide (horizontal bar), dual-mermaid data_model, slide nums 01-19.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "docs" / "presentacion-defensa-pfc" / "index.html"
MERMAID_DIR = REPO / "docs" / "mermaid"

ASIR_TABLE_ROWS = """
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
"""

ASIR_CHART_SECTION = """<!-- NOTE: 3:00–4:15. Gráfico del stack tecnológico (pesos relativos). Tabla 1 en la diapositiva siguiente. -->
<section class="slide" data-id="asir_modules">
  <div class="slide-content">
    <span class="slide-num reveal">04</span>
    <h2 class="reveal">Stack tecnológico del PFC</h2>
    <div class="slide-main reveal tech-chart-slide">
      <div class="tech-chart-panel tech-chart-panel--solo reveal">
        <div class="tech-chart-wrap" id="techChart" role="img" aria-label="Gráfico de barras del stack tecnológico. Pulsa una barra o la leyenda para ver el rol de cada tecnología."></div>
        <div class="tech-legend" id="techLegend" role="list" aria-label="Leyenda del stack tecnológico"></div>
        <p class="tech-chart-hint">Pulsa una barra o la leyenda para ver el rol en el proyecto.</p>
      </div>
    </div>
  </div>
</section>
"""

ASIR_TABLE_SECTION = f"""<!-- NOTE: 4:15–5:00. Tabla 1 de competencias ASIR. Cierra el mapa antes de arquitectura y demo. -->
<section class="slide" data-id="asir_modules_2">
  <div class="slide-content">
    <span class="slide-num reveal">05</span>
    <h2 class="reveal">Mapa de competencias ASIR (Tabla 1)</h2>
    <div class="slide-main reveal">
      <div class="table-wrap reveal dense-table asir-table-only">
      <table class="data-table">
      <thead><tr>
      <th>Módulo</th>
      <th>Contenidos aplicados en el PFC</th>
      </tr></thead><tbody>
{ASIR_TABLE_ROWS}
      </tbody></table>
      </div>
    </div>
  </div>
</section>
"""

SLIDE_NUMBERS = {
    "timeline": "01",
    "problem": "02",
    "objectives": "03",
    "asir_modules": "04",
    "asir_modules_2": "05",
    "architecture": "06",
    "profiles": "07",
    "data_model": "08",
    "docker": "09",
    "traffic_source": "10",
    "monitoring": "11",
    "evidence": "12",
    "security": "13",
    "aws": "14",
    "validation": "15",
    "budget": "16",
    "conclusions": "17",
    "objectives_grade": "18",
    "closing": "19",
}

BAR_CHART_OPTION = """
      buildOption(animate) {
        const { text, muted } = this.getThemeColors();
        const names = TECH_STACK_DATA.map((d) => d.name);
        return {
          animation: animate && !this.reducedMotion,
          animationDuration: 500,
          grid: { left: "4%", right: "8%", top: "4%", bottom: "4%", containLabel: true },
          tooltip: {
            trigger: "axis",
            axisPointer: { type: "shadow" },
            formatter: (params) => {
              const p = Array.isArray(params) ? params[0] : params;
              const item = TECH_STACK_DATA.find((d) => d.name === p.name);
              return item
                ? `<strong>${item.name}</strong><br/>${item.role}<br/>Peso relativo: ${item.value}%`
                : "";
            },
          },
          xAxis: {
            type: "value",
            max: 30,
            axisLabel: { color: muted, formatter: "{value}%" },
            splitLine: { lineStyle: { color: "rgba(128,128,128,0.2)" } },
          },
          yAxis: {
            type: "category",
            data: names,
            inverse: true,
            axisLabel: { color: text, fontSize: 13, fontWeight: 600 },
            axisTick: { show: false },
          },
          series: [
            {
              name: "Stack",
              type: "bar",
              barMaxWidth: 28,
              data: TECH_STACK_DATA.map((d) => ({
                name: d.name,
                value: d.value,
                itemStyle: { color: d.color, borderRadius: [0, 4, 4, 0] },
              })),
              label: {
                show: true,
                position: "right",
                color: text,
                fontWeight: 700,
                formatter: "{c}%",
              },
              emphasis: {
                focus: "series",
                itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,0.15)" },
              },
            },
          ],
        };
      }
"""

CSS_APPEND = """
    /* === RESTORED CONTRACT: ASIR chart + table split === */
    .tech-chart-panel--solo {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: min(96vw, 1180px);
      margin-inline: auto;
      gap: clamp(0.35rem, 1vh, 0.65rem);
      flex: 1 1 auto;
      min-height: 0;
      max-height: calc(100dvh - 5rem);
    }

    .slide[data-id="asir_modules"] .tech-chart-slide {
      display: flex;
      flex-direction: column;
      align-items: stretch;
      justify-content: center;
      flex: 1 1 auto;
      width: 100%;
    }

    .slide[data-id="asir_modules"] .tech-chart-wrap {
      width: 100%;
      height: min(58vh, 480px);
      max-height: min(58vh, 480px);
      min-height: clamp(280px, 48vh, 420px);
      flex: 1 1 auto;
    }

    .slide[data-id="asir_modules"] .tech-legend {
      max-height: min(22vh, 180px);
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: center;
      gap: clamp(0.25rem, 0.6vw, 0.45rem);
    }

    .slide[data-id="asir_modules_2"] .asir-table-only {
      max-height: min(82vh, 640px);
      width: 100%;
      max-width: min(96vw, 1180px);
      margin-inline: auto;
    }

    .slide[data-id="asir_modules_2"] .data-table {
      font-size: clamp(0.88rem, 1.35vw, 1.05rem);
    }

    @media (max-height: 800px) {
      .slide[data-id="asir_modules"] .tech-chart-wrap {
        height: min(52vh, 400px);
        max-height: min(52vh, 400px);
        min-height: clamp(240px, 44vh, 360px);
      }
    }

    body.export-mode .slide[data-id="asir_modules"] .tech-chart-wrap {
      height: min(62vh, 520px);
      max-height: min(62vh, 520px);
    }

    .slide[data-id="data_model"] .dual-mermaid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      grid-template-rows: minmax(0, 1fr);
      gap: clamp(0.45rem, 1.1vw, 0.75rem);
      width: 100%;
      max-width: min(96vw, 1180px);
      max-height: calc(100dvh - 6.25rem);
      align-items: stretch;
      justify-items: stretch;
    }

    .slide[data-id="data_model"] .mermaid-wrap--half {
      min-height: min(38vh, 320px);
      max-height: min(44vh, 380px);
      width: 100%;
      overflow: hidden;
    }

    @media (max-width: 899px) {
      .slide[data-id="data_model"] .dual-mermaid {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
      }
    }
"""


def load_mermaid(name: str) -> str:
    return (MERMAID_DIR / name).read_text(encoding="utf-8-sig").strip()


def replace_asir_combo(html: str) -> str:
    start = html.find("<!-- NOTE: 3:00")
    if start < 0:
        raise RuntimeError("asir_modules NOTE anchor not found")
    end = html.find("<!-- NOTE: 5:00–5:45.")
    if end < 0:
        raise RuntimeError("architecture NOTE anchor not found")
    return html[:start] + ASIR_CHART_SECTION + "\n" + ASIR_TABLE_SECTION + "\n" + html[end:]


def set_slide_numbers(html: str) -> str:
    for slide_id, num in SLIDE_NUMBERS.items():
        pattern = re.compile(
            rf'(<section[^>]*data-id="{re.escape(slide_id)}"[^>]*>[\s\S]*?)'
            r'<span class="slide-num reveal">\d{2}</span>',
            re.DOTALL,
        )
        html, n = pattern.subn(
            rf'\g<1><span class="slide-num reveal">{num}</span>', html, count=1
        )
        if n != 1:
            raise RuntimeError(f"slide-num not updated for {slide_id} (n={n})")
    return html


def replace_data_model(html: str) -> str:
    er = load_mermaid("pfc-fig02-data-model.mmd")
    flow = load_mermaid("pfc-fig03-reserva.mmd")
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
        raise RuntimeError(f"data_model replace failed (n={n})")
    return new_html


def patch_bar_chart(html: str) -> str:
    old = re.search(
        r"buildOption\(animate\) \{[\s\S]*?\n      \}\n\n      ensureChart",
        html,
    )
    if not old:
        raise RuntimeError("TechStackChart.buildOption block not found")
    return html[: old.start()] + BAR_CHART_OPTION.strip() + "\n\n      ensureChart" + html[old.end() :]


def patch_css(html: str) -> str:
    marker = "/* === INLINE EDITING === */"
    if marker not in html:
        raise RuntimeError("CSS marker not found")
    if ".tech-chart-panel--solo {" in html:
        return html
    return html.replace(marker, CSS_APPEND + "\n\n    " + marker)


def patch_cover_num(html: str) -> str:
    """Optional visible 00 on cover for export consistency."""
    needle = '<section class="slide title-slide title-slide--cover-image" data-id="cover">'
    if "data-id=\"cover\"" in html and 'slide-num reveal">00' in html:
        return html
    insert = (
        needle
        + "\n      <div class=\"slide-content\">\n        "
        '<span class="slide-num reveal" aria-hidden="true">00</span>'
    )
    if needle not in html:
        return html
    # Cover already has slide-content; add 00 after opening slide-content
    pattern = re.compile(
        r'(<section class="slide title-slide title-slide--cover-image" data-id="cover">\s*'
        r'<div class="slide-content">)',
        re.DOTALL,
    )
    return pattern.sub(
        r'\1\n        <span class="slide-num reveal" aria-hidden="true">00</span>',
        html,
        count=1,
    )


def main() -> int:
    if not INDEX.is_file():
        print(f"Missing {INDEX}", file=sys.stderr)
        return 1

    html = INDEX.read_text(encoding="utf-8")
    html = replace_asir_combo(html)
    html = replace_data_model(html)
    html = set_slide_numbers(html)
    html = patch_bar_chart(html)
    html = patch_css(html)
    html = patch_cover_num(html)
    INDEX.write_text(html, encoding="utf-8")
    print(f"Restored contract in {INDEX.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
