#!/usr/bin/env python3
"""Inject profiles/docker Mermaid, enlarge diagram CSS, sparse body typography."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "docs" / "presentacion-defensa-pfc" / "index.html"
MERMAID = REPO / "docs" / "mermaid"


def load(name: str) -> str:
    return (MERMAID / name).read_text(encoding="utf-8-sig").strip()


def replace_profiles(html: str) -> str:
    seq = load("pfc-fig03-reserva-sequence.mmd")
    pattern = re.compile(
        r'(<section class="slide" data-id="profiles">[\s\S]*?)'
        r'<figure class="content-split-aside"><img src="data:image[^"]*"[^>]*></figure>',
        re.DOTALL,
    )

    def sub(m: re.Match[str]) -> str:
        return (
            m.group(1)
            + '<figure class="content-split-aside mermaid-wrap content-split-mermaid">'
            + f'<pre class="mermaid">{seq}</pre></figure>'
        )

    new_html, n = pattern.subn(sub, html, count=1)
    if n != 1:
        raise RuntimeError(f"profiles aside replace failed (n={n})")
    return new_html


def replace_docker(html: str) -> str:
    docker_mmd = load("pfc-fig-docker-compose.mmd")
    pattern = re.compile(
        r'<section class="slide" data-id="docker">[\s\S]*?</section>',
        re.DOTALL,
    )
    block = f"""<section class="slide diagram-slide" data-id="docker">
  <div class="slide-content">
    <span class="slide-num reveal">09</span>
    <h2 class="reveal">Implantación con Docker Compose (Tabla 6)</h2>
    <div class="slide-main reveal content-split content-split--docker">
      <div class="content-split-main">
        <div class="table-wrap reveal dense-table">
        <table class="data-table">
        <thead><tr>
        <th>Servicio</th>
        <th>Función en el stack</th>
        </tr></thead><tbody>
        <tr>
        <td>web</td>
        <td>Apache/PHP — espera healthcheck de MySQL en el arranque.</td>
        </tr>
        <tr>
        <td>mysql</td>
        <td>Persistencia — sin publicar puertos al host en producción.</td>
        </tr>
        <tr>
        <td>prometheus + alertmanager</td>
        <td>Scraping, reglas de alerta y notificaciones.</td>
        </tr>
        <tr>
        <td>grafana</td>
        <td>Dashboards preprovisionados desde monitoring/grafana/.</td>
        </tr>
        <tr>
        <td>exportadores</td>
        <td>Node, MySQL, blackbox, cAdvisor, Telegraf.</td>
        </tr>
        <tr>
        <td>simulador (perfil traffic)</td>
        <td>JMeter worker + UI para carga controlada.</td>
        </tr>
        </tbody></table>
        </div>
      </div>
      <figure class="content-split-aside mermaid-wrap content-split-mermaid" aria-label="Stack Docker Compose">
        <pre class="mermaid">{docker_mmd}</pre>
      </figure>
    </div>
  </div>
</section>"""
    new_html, n = pattern.subn(block, html, count=1)
    if n != 1:
        raise RuntimeError(f"docker section replace failed (n={n})")
    return new_html


def set_slide_num(html: str, slide_id: str, num: str) -> str:
    pat = re.compile(
        rf'(<section[^>]*data-id="{re.escape(slide_id)}"[^>]*>[\s\S]*?<span class="slide-num reveal">)\d+(</span>)',
        re.DOTALL,
    )
    new_html, n = pat.subn(rf"\g<1>{num}\g<2>", html, count=1)
    if n != 1:
        raise RuntimeError(f"slide-num for {slide_id} not updated (n={n})")
    return new_html


def bump_slide_numbers(html: str) -> str:
    """Fix duplicate 06/08/09 and align footer slide counter."""
    nums = {
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
    for slide_id, num in nums.items():
        if f'data-id="{slide_id}"' in html:
            html = set_slide_num(html, slide_id, num)
    return html


def patch_css(html: str) -> str:
    html = html.replace(
        "--body-size: clamp(1.0625rem, 2vw, 1.5rem);",
        "--body-size: clamp(1.125rem, 2.35vw, 1.65rem);",
    )
    html = html.replace(
        "--table-size: clamp(1.05rem, 1.65vw, 1.25rem);",
        "--table-size: clamp(1.1rem, 1.75vw, 1.35rem);",
    )
    html = html.replace(
        "fontSize: \"17px\",",
        "fontSize: \"20px\",",
    )
    html = html.replace("useMaxWidth: false,", "useMaxWidth: true,")
    html = html.replace(
        """          if (
            raw &&
            (raw.startsWith("flowchart") || raw.startsWith("erDiagram"))
          ) {""",
        """          if (
            raw &&
            (raw.startsWith("flowchart") ||
              raw.startsWith("erDiagram") ||
              raw.startsWith("sequenceDiagram"))
          ) {""",
    )
    if ".content-split-mermaid" not in html:
        insert_after = ".content-split-aside img {\n"
        extra = """
    .content-split-mermaid {
      width: 100%;
      min-height: min(48vh, 420px);
      max-height: min(58vh, 520px);
      flex: 1 1 auto;
      overflow: visible;
    }

    .content-split-mermaid pre.mermaid {
      width: 100%;
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
    }

    .content-split-mermaid svg {
      max-width: 100%;
      max-height: min(56vh, 500px);
    }

    .content-split--docker {
      max-height: calc(100dvh - 6.5rem);
    }

    .slide-main:has(> .bullet-list:only-child) .bullet-list li {
      font-size: clamp(1.2rem, 2.55vw, 1.85rem);
      line-height: 1.48;
      padding: 0.28em 0;
      max-width: min(88vw, 980px);
      margin-inline: auto;
    }

    .slide-main:has(> .bullet-list:only-child) .bullet-list {
      gap: clamp(0.55rem, 1.2vh, 0.85rem);
    }

"""
        idx = html.find(insert_after)
        if idx == -1:
            raise RuntimeError("CSS anchor for content-split-mermaid not found")
        # insert after the closing brace of content-split-aside img rule block
        end = html.find("@media (max-width: 900px)", idx)
        if end == -1:
            raise RuntimeError("media query anchor not found")
        html = html[:end] + extra + html[end:]

    # Enlarge diagram wraps
    html = html.replace(
        "min-height: min(40vh, 360px);\n      max-height: min(50vh, 440px);",
        "min-height: min(46vh, 400px);\n      max-height: min(58vh, 520px);",
    )
    html = html.replace(
        "max-height: min(48vh, 420px);",
        "max-height: min(56vh, 500px);",
        1,
    )
    html = html.replace(
        ".slide-main.dual-mermaid .mermaid-wrap--half svg {\n      max-height: min(54vh, 480px);\n      font-size: 12px;\n    }",
        ".slide-main.dual-mermaid .mermaid-wrap--half svg {\n      max-height: min(58vh, 520px);\n    }",
    )
    html = html.replace(
        "min-height: min(52vh, 460px);\n      max-height: min(58vh, 500px);",
        "min-height: min(56vh, 480px);\n      max-height: min(62vh, 540px);",
    )
    if '.slide[data-id="data_model"] .slide-main' not in html:
        html = html.replace(
            ".slide-main.dual-mermaid .mermaid-wrap--half svg {",
            """.slide[data-id="data_model"] .slide-main {
      display: flex;
      flex: 1 1 auto;
      min-height: 0;
      align-items: stretch;
    }

    .slide[data-id="data_model"] .dual-mermaid {
      flex: 1 1 auto;
      min-height: min(58vh, 500px);
    }

    .slide-main.dual-mermaid .mermaid-wrap--half svg {
""",
        )
    html = html.replace(
        """    .diagram-slide .mermaid-wrap svg {
      display: block;
      width: auto !important;
      height: auto !important;
      max-width: 100%;
      max-height: min(48vh, 420px);
      overflow: visible;
    }""",
        """    .diagram-slide .mermaid-wrap svg {
      display: block;
      max-width: 100%;
      overflow: visible;
    }""",
    )
    return html


def patch_fit_svg(html: str) -> str:
    old = """      static fitSvg(el) {
        const svg = el.querySelector("svg");
        const wrap = el.closest(".mermaid-wrap");
        if (!svg || !wrap) return;
        const maxW = wrap.clientWidth || wrap.getBoundingClientRect().width;
        const maxH =
          wrap.clientHeight ||
          parseFloat(getComputedStyle(wrap).maxHeight) ||
          400;
        const vb = svg.viewBox?.baseVal;
        if (!vb || !vb.width || !vb.height) return;
        const pad = 8;
        const scale = Math.min(
          (maxW - pad) / vb.width,
          (maxH - pad) / vb.height
        );
        const w = Math.max(1, vb.width * scale);
        const h = Math.max(1, vb.height * scale);
        svg.style.width = w + "px";
        svg.style.height = h + "px";
        svg.style.maxWidth = "100%";
        svg.style.maxHeight = "100%";
        svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      }"""
    new = """      static fitSvg(el) {
        const svg = el.querySelector("svg");
        const wrap = el.closest(".mermaid-wrap");
        if (!svg || !wrap) return;
        const box = wrap.getBoundingClientRect();
        const maxW = box.width || wrap.clientWidth || 640;
        const cs = getComputedStyle(wrap);
        let maxH = box.height || wrap.clientHeight;
        if (!maxH || maxH < 80) {
          const parsed = parseFloat(cs.maxHeight);
          maxH = Number.isFinite(parsed) && parsed > 0 ? parsed : maxH;
        }
        if (!maxH || maxH < 80) {
          maxH = Math.max(320, window.innerHeight * 0.52);
        }
        const vb = svg.viewBox?.baseVal;
        if (!vb || !vb.width || !vb.height) return;
        const pad = 12;
        const fill = 0.94;
        const scale =
          Math.min((maxW - pad) / vb.width, (maxH - pad) / vb.height) * fill;
        const w = Math.max(1, vb.width * scale);
        const h = Math.max(1, vb.height * scale);
        svg.style.width = w + "px";
        svg.style.height = h + "px";
        svg.style.maxWidth = "100%";
        svg.style.maxHeight = maxH + "px";
        svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      }"""
    if old not in html:
        raise RuntimeError("fitSvg block not found")
    return html.replace(old, new)


def patch_mermaid_error(html: str) -> str:
    return html.replace(
        'console.warn("Mermaid render [" + slideId + "]:", err);',
        'console.warn("Mermaid render [" + (el.dataset.mermaidKey || "diagram") + "]:", err);',
    )


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")
    html = replace_profiles(html)
    html = replace_docker(html)
    html = bump_slide_numbers(html)
    html = patch_css(html)
    html = patch_fit_svg(html)
    html = patch_mermaid_error(html)
    INDEX.write_text(html, encoding="utf-8")
    print("Patched", INDEX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
