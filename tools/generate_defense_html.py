#!/usr/bin/env python3
"""
Genera docs/presentacion-defensa-pfc/index.html desde defense_slides_manifest.
Ejecutar tras extract_defense_assets.py.
"""

from __future__ import annotations

import html
from pathlib import Path

from defense_slides_manifest import SLIDES, TITLE_MAIN

IMAGE_SIZES: dict[str, tuple[int, int]] = {
    "image1.png": (1568, 704),
    "image2.png": (1568, 1260),
    "image3.png": (1568, 1092),
    "image4.png": (1568, 392),
    "image19.png": (1568, 524),
    "image20.png": (2114, 279),
}

IMAGE_ALT: dict[str, str] = {
    "image1.png": "Arquitectura general del sistema web y observabilidad (Fig. 1)",
    "image2.png": "Modelo de datos principal de la aplicación (Fig. 2)",
    "image3.png": "Flujo de reserva de cita desde la interfaz web (Fig. 3)",
    "image4.png": "Despliegue recomendado en AWS con EC2 y Docker Compose (Fig. 4)",
    "image19.png": "Flujo de monitorización y simulación de tráfico (Fig. 22)",
    "image20.png": "Estado de contenedores Docker en EC2 (Fig. 20, docker ps)",
}


def img_tag(filename: str, alt: str | None = None) -> str:
    w, h = IMAGE_SIZES.get(filename, (800, 600))
    alt_text = alt or IMAGE_ALT.get(filename, filename)
    return (
        f'<img src="assets/{esc(filename)}" alt="{esc(alt_text)}" '
        f'width="{w}" height="{h}" loading="lazy">'
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_viewport_css() -> str:
    candidates = [
        Path.home() / ".agents" / "skills" / "frontend-slides" / "viewport-base.css",
        repo_root() / "docs" / "presentacion-defensa-pfc" / "viewport-base.css",
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("viewport-base.css no encontrado; copia el skill frontend-slides")


def esc(s: str) -> str:
    return html.escape(s)


def slide_number(idx: int) -> str:
    return f"{idx:02d}"


def indent_lines(lines: list[str], spaces: int) -> list[str]:
    pad = " " * spaces
    return [pad + line.strip() for line in lines if line.strip()]


def dual_images_class(spec) -> str:
    """Stack very wide screenshots (e.g. docker ps) full-width below the diagram."""
    classes = ["dual-images"]
    for name in (spec.image_right, spec.image):
        if not name:
            continue
        w, h = IMAGE_SIZES.get(name, (0, 0))
        if h > 0 and w / h >= 4.5:
            classes.append("dual-images--stack")
            break
    return " ".join(classes)


def render_slide(spec, idx: int) -> str:
    num = slide_number(idx)
    extra_class = spec.html_class.strip() if spec.html_class else ""
    extra = f" {extra_class}" if extra_class and spec.layout != "title" else ""
    if spec.layout == "title" and extra_class and extra_class != "title-slide":
        extra = f" {extra_class}"
    note = f"<!-- NOTE: {esc(spec.notes)} -->" if spec.notes else ""

    if spec.layout == "title":
        lines = "".join(f'<p class="reveal subtitle">{esc(l)}</p>' for l in spec.bullets)
        title_html = esc(spec.title).replace("\n", "<br>")
        return f"""
    {note}
    <section class="slide title-slide" data-id="{esc(spec.id)}">
      <div class="slide-content">
        <div class="slide-card reveal">
          <span class="slide-num">{num}</span>
          <h1 class="reveal">{title_html}</h1>
          {lines}
        </div>
      </div>
    </section>"""

    parts = [
        note,
        f'<section class="slide{extra}" data-id="{esc(spec.id)}">',
        '  <div class="slide-content">',
        f'    <span class="slide-num reveal">{num}</span>',
        f'    <h2 class="reveal">{esc(spec.title)}</h2>',
    ]
    body: list[str] = []

    if spec.layout in ("table", "timeline"):
        dense = " dense-table" if len(spec.table_rows) >= 6 else ""
        table_lines = [
            f'    <div class="table-wrap reveal{dense}">',
            '      <table class="data-table">',
            "        <thead><tr>",
        ]
        for h in spec.table_headers:
            table_lines.append(f"<th>{esc(h)}</th>")
        table_lines.append("</tr></thead><tbody>")
        for row in spec.table_rows:
            table_lines.append("<tr>")
            for cell in row:
                table_lines.append(f"<td>{esc(cell)}</td>")
            table_lines.append("</tr>")
        table_lines.extend(
            [
                "      </tbody></table>",
                "    </div>",
            ]
        )
        if spec.image:
            body.append('      <div class="content-split">')
            body.append('        <div class="content-split-main">')
            body.extend(indent_lines(table_lines, 10))
            body.append("        </div>")
            body.append(
                f'        <figure class="content-split-aside">{img_tag(spec.image)}</figure>'
            )
            body.append("      </div>")
        else:
            body.extend(indent_lines(table_lines, 6))
    elif spec.layout == "two_picture":
        body.append(f'      <div class="{dual_images_class(spec)}">')
        if spec.image:
            body.append(f"        <figure>{img_tag(spec.image)}</figure>")
        if spec.image_right:
            body.append(f"        <figure>{img_tag(spec.image_right)}</figure>")
        body.append("      </div>")
    elif spec.layout == "picture":
        if spec.image:
            body.append(
                f'      <figure class="diagram-figure">{img_tag(spec.image)}</figure>'
            )
        if spec.bullets:
            body.append('      <ul class="bullet-list">')
            for b in spec.bullets:
                body.append(f"        <li>{esc(b)}</li>")
            body.append("      </ul>")
    elif spec.bullets:
        if spec.image:
            body.append('      <div class="content-split">')
            body.append('        <div class="content-split-main">')
            body.append('          <ul class="bullet-list">')
            for b in spec.bullets:
                body.append(f"            <li>{esc(b)}</li>")
            body.append("          </ul>")
            body.append("        </div>")
            body.append(
                f'        <figure class="content-split-aside">{img_tag(spec.image)}</figure>'
            )
            body.append("      </div>")
        else:
            body.append('      <ul class="bullet-list">')
            for b in spec.bullets:
                body.append(f"        <li>{esc(b)}</li>")
            body.append("      </ul>")

    parts.append('    <div class="slide-main reveal">')
    parts.extend(body)
    parts.append("    </div>")
    parts.append("  </div>")
    parts.append("</section>")
    return "\n".join(parts)


def build_html() -> str:
    viewport = load_viewport_css()
    slides_html = "\n".join(render_slide(s, i) for i, s in enumerate(SLIDES))
    title_esc = esc(TITLE_MAIN.split("\n")[0])

    return f"""<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#f4f1ec" id="themeColorMeta">
  <title>Defensa PFC — Taller mecánico ASIR</title>
  <script>
    (function () {{
      var params = new URLSearchParams(window.location.search);
      var exportMode = params.get("export") === "1";
      window.__PFC_EXPORT_MODE__ = exportMode;
      var k = "pfc-defense-theme";
      var t = localStorage.getItem(k);
      var theme = exportMode ? "light" : (t === "dark" ? "dark" : "light");
      document.documentElement.setAttribute("data-theme", theme);
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", theme === "dark" ? "#1a1a1a" : "#f4f1ec");
    }})();
  </script>
  <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&f[]=clash-display@600,700&display=swap">
  <style>
    /* === THEME: Bold Signal (light default + dark) === */
    :root {{
      --font-display: "Clash Display", sans-serif;
      --font-body: "Satoshi", sans-serif;
      --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
      --duration-normal: 0.55s;
      --focus-ring: 0 0 0 3px var(--accent);
      --chrome-edge: max(1.25rem, calc(env(safe-area-inset-right, 0px) + 1rem));
      --chrome-rail-width: 2.75rem;
      --nav-btn-height: 22px;
    }}

    html[data-theme="light"] {{
      color-scheme: light;
      --bg-primary: #f4f1ec;
      --bg-gradient: linear-gradient(135deg, #f4f1ec 0%, #ebe6df 50%, #f4f1ec 100%);
      --card-bg: #ffffff;
      --text-primary: #1a1a1a;
      --text-secondary: #4a4a4a;
      --text-on-card: #1a1a1a;
      --card-border: rgba(232, 93, 44, 0.35);
      --accent: #c94e22;
      --accent-glow: rgba(201, 78, 34, 0.2);
      --surface-muted: rgba(26, 26, 26, 0.06);
      --table-header-bg: rgba(232, 93, 44, 0.12);
      --table-border: rgba(26, 26, 26, 0.1);
      --nav-dot: rgba(26, 26, 26, 0.22);
      --nav-dot-active: var(--accent);
      --chrome-bg: rgba(244, 241, 236, 0.92);
      --chrome-border: rgba(26, 26, 26, 0.08);
      --chrome-text: #1a1a1a;
      --theme-color-meta: #f4f1ec;
    }}

    html[data-theme="dark"] {{
      color-scheme: dark;
      --bg-primary: #1a1a1a;
      --bg-gradient: linear-gradient(135deg, #1a1a1a 0%, #252525 45%, #1a1a1a 100%);
      --card-bg: #e85d2c;
      --text-primary: #ffffff;
      --text-secondary: #b8b8b8;
      --text-on-card: #1a1a1a;
      --card-border: transparent;
      --accent: #e85d2c;
      --accent-glow: rgba(232, 93, 44, 0.35);
      --surface-muted: rgba(255, 255, 255, 0.06);
      --table-header-bg: rgba(232, 93, 44, 0.2);
      --table-border: rgba(255, 255, 255, 0.08);
      --nav-dot: rgba(255, 255, 255, 0.25);
      --nav-dot-active: var(--accent);
      --chrome-bg: rgba(26, 26, 26, 0.88);
      --chrome-border: rgba(255, 255, 255, 0.1);
      --chrome-text: #ffffff;
      --theme-color-meta: #1a1a1a;
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      font-family: var(--font-body);
      background: var(--bg-primary);
      background-image: var(--bg-gradient);
      color: var(--text-primary);
      touch-action: manipulation;
      -webkit-tap-highlight-color: transparent;
      transition: background-color 0.2s ease, color 0.2s ease;
    }}

    /* === VIEWPORT BASE (mandatory) === */
{chr(10).join("    " + line for line in viewport.splitlines())}

    /* === PRESENTATION LAYOUT === */
    /* Anula el tope global de viewport-base (50vh) dentro de diapositivas */
    .slide-content img {{
      max-height: none;
    }}

    /* Legibilidad en proyector (1280×720): por encima del viewport-base embebido */
    :root {{
      --title-size: clamp(1.65rem, 5.2vw, 3.5rem);
      --h2-size: clamp(1.2rem, 3.2vw, 2.25rem);
      --body-size: clamp(0.9rem, 1.55vw, 1.2rem);
      --table-size: clamp(0.8125rem, 1.25vw, 1rem);
      --small-size: clamp(0.75rem, 1.05vw, 0.9rem);
    }}

    /* Evita scroll horizontal: 100vw incluye la barra de scroll y recorta el chrome fijo */
    html {{
      overflow-x: clip;
      width: 100%;
      scrollbar-gutter: stable;
    }}

    body {{
      width: 100%;
      max-width: 100%;
    }}

    .slide {{
      width: 100%;
      max-width: 100%;
    }}

    .progress-bar {{
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: var(--accent);
      width: 0%;
      z-index: 9999;
      transition: width 0.2s ease;
    }}

    .chrome-top {{
      position: fixed;
      top: max(0.65rem, calc(env(safe-area-inset-top, 0px) + 0.25rem));
      right: var(--chrome-edge);
      left: auto;
      display: flex;
      align-items: center;
      gap: clamp(0.35rem, 1vw, 0.65rem);
      z-index: 10001;
      max-width: calc(100% - 1.5rem);
      flex-wrap: nowrap;
    }}

    .slide-counter {{
      font-size: var(--small-size);
      font-weight: 500;
      font-variant-numeric: tabular-nums;
      color: var(--chrome-text);
      background: var(--chrome-bg);
      border: 1px solid var(--chrome-border);
      border-radius: 8px;
      padding: 0.45rem 0.65rem;
      min-height: 44px;
      display: inline-flex;
      align-items: center;
      backdrop-filter: blur(8px);
    }}

    .chrome-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 44px;
      min-height: 44px;
      padding: 0.5rem;
      border: 1px solid var(--chrome-border);
      border-radius: 8px;
      background: var(--chrome-bg);
      color: var(--chrome-text);
      cursor: pointer;
      backdrop-filter: blur(8px);
      transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }}

    .chrome-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}

    .chrome-btn:focus-visible {{
      outline: none;
      box-shadow: var(--focus-ring);
    }}

    .theme-toggle .icon-moon {{ display: none; }}
    html[data-theme="dark"] .theme-toggle .icon-sun {{ display: none; }}
    html[data-theme="dark"] .theme-toggle .icon-moon {{ display: block; }}

    .theme-toggle svg {{
      width: 1.25rem;
      height: 1.25rem;
      fill: currentColor;
    }}

    .nav-dots {{
      position: fixed;
      right: var(--chrome-edge);
      top: max(0.75rem, env(safe-area-inset-top, 0px));
      bottom: max(0.75rem, env(safe-area-inset-bottom, 0px));
      width: var(--chrome-rail-width);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      gap: 0;
      z-index: 100;
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-width: none;
      padding: 0.25rem 0;
      overscroll-behavior: contain;
      pointer-events: auto;
    }}

    .nav-dots::-webkit-scrollbar {{
      display: none;
    }}

    .nav-dots button {{
      width: 100%;
      height: var(--nav-btn-height, 22px);
      min-height: max(var(--nav-btn-height, 22px), 18px);
      flex-shrink: 0;
      border: none;
      background: transparent;
      cursor: pointer;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: background 0.2s ease;
    }}

    .nav-dots button::after {{
      content: "";
      width: clamp(6px, 1vw, 10px);
      height: clamp(6px, 1vw, 10px);
      border-radius: 50%;
      background: var(--nav-dot);
      transition: background 0.2s ease, transform 0.2s ease;
    }}

    .nav-dots button.active::after {{
      background: var(--nav-dot-active);
      transform: scale(1.35);
    }}

    .nav-dots button:focus-visible {{
      outline: none;
      box-shadow: var(--focus-ring);
    }}

    .slide-num {{
      font-family: var(--font-display);
      font-size: clamp(2.5rem, 8vw, 5rem);
      font-weight: 700;
      color: var(--accent);
      opacity: 0.35;
      line-height: 1;
      margin-bottom: var(--element-gap);
      flex-shrink: 0;
    }}

    .slide-content > .slide-num {{
      font-size: clamp(0.9rem, 3.2vh, 1.85rem);
      margin-bottom: clamp(0.15rem, 0.6vh, 0.4rem);
    }}

    .slide:not(.title-slide) .slide-content {{
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      align-items: stretch;
      min-height: 0;
      padding-block: clamp(0.35rem, 1.2vh, 0.75rem);
      padding-left: var(--slide-padding);
      padding-right: calc(var(--slide-padding) + var(--chrome-rail-width) + 0.5rem);
      gap: clamp(0.15rem, 0.4vh, 0.3rem);
    }}

    .title-slide .slide-content {{
      justify-content: center;
      align-items: center;
      padding-block: var(--slide-padding);
      padding-left: var(--slide-padding);
      padding-right: calc(var(--slide-padding) + var(--chrome-rail-width) + 0.5rem);
    }}

    .slide-main {{
      flex: 1 1 auto;
      min-height: 0;
      width: 100%;
      max-width: min(95vw, 1100px);
      margin-inline: auto;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: stretch;
      overflow: hidden;
      gap: clamp(0.25rem, 0.75vh, 0.5rem);
    }}

    .slide-main:has(> .dual-images:only-child) {{
      justify-content: stretch;
    }}

    .slide-card {{
      background: var(--card-bg);
      color: var(--text-on-card);
      border: 1px solid var(--card-border);
      border-radius: clamp(8px, 1.5vw, 20px);
      padding: clamp(1.25rem, 4vw, 3rem);
      width: min(92vw, 1100px);
      max-width: min(92vw, 1100px);
      flex-shrink: 0;
      box-shadow: 0 24px 80px var(--accent-glow);
      transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .title-slide .slide-num {{ color: var(--text-on-card); opacity: 0.5; }}

    .title-slide h1 {{
      font-family: var(--font-display);
      font-size: var(--title-size);
      font-weight: 700;
      line-height: 1.1;
      margin-bottom: var(--content-gap);
      text-wrap: balance;
    }}

    .subtitle {{
      font-size: var(--body-size);
      line-height: 1.5;
      margin-top: 0.35em;
      opacity: 0.9;
    }}

    h2 {{
      font-family: var(--font-display);
      font-size: var(--h2-size);
      font-weight: 600;
      margin-bottom: clamp(0.3rem, 1vh, var(--content-gap));
      color: var(--text-primary);
      text-wrap: balance;
      flex-shrink: 0;
    }}

    .bullet-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: clamp(0.35rem, 1vh, 0.75rem);
      width: 100%;
      max-width: 100%;
      flex-shrink: 0;
    }}

    .slide-main > .bullet-list {{
      max-width: min(88vw, 920px);
      margin-inline: auto;
    }}

    .bullet-list li {{
      font-size: var(--body-size);
      line-height: 1.45;
      padding-left: 1.2em;
      position: relative;
      color: var(--text-secondary);
    }}

    .bullet-list li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 0.55em;
      width: 0.45em;
      height: 0.45em;
      background: var(--accent);
      border-radius: 2px;
    }}

    .content-split {{
      flex: 1 1 auto;
      min-height: 0;
      height: 100%;
      max-height: calc(100dvh - 7.5rem);
      width: 100%;
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
      gap: clamp(0.65rem, 1.5vw, 1.1rem);
      align-items: stretch;
      overflow: hidden;
    }}

    .content-split-main,
    .content-split-aside {{
      min-width: 0;
      min-height: 0;
      overflow: hidden;
    }}

    .content-split-main {{
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    .content-split-aside {{
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .content-split-aside img {{
      display: block;
      width: 100%;
      height: 100%;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      margin-inline: auto;
    }}

    @media (max-width: 900px) {{
      .content-split {{
        grid-template-columns: 1fr;
        max-height: calc(100dvh - 8rem);
      }}
      .content-split-aside img {{ max-height: min(30vh, 240px); }}
    }}

    .diagram-slide .slide-main {{
      display: grid;
      grid-template-rows: minmax(0, 1.12fr) auto;
      gap: clamp(0.35rem, 1vh, 0.55rem);
      align-content: stretch;
      height: 100%;
    }}

    .diagram-slide .diagram-figure {{
      margin: 0;
      min-height: 0;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .diagram-slide .diagram-figure img {{
      max-width: 100%;
      max-height: 100%;
      width: auto;
      height: auto;
      object-fit: contain;
    }}

    .diagram-slide .bullet-list {{
      width: 100%;
      max-width: 100%;
    }}

    .diagram-slide .bullet-list li {{
      line-height: 1.35;
    }}

    .slide-main > .dual-images {{
      flex: 1 1 auto;
      min-height: 0;
      height: 100%;
      max-height: calc(100dvh - 7rem);
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr;
      gap: clamp(0.5rem, 1.2vw, 0.85rem);
      align-items: stretch;
      justify-items: stretch;
      overflow: hidden;
    }}

    .slide-main > .dual-images.dual-images--stack {{
      grid-template-columns: 1fr;
      grid-template-rows: minmax(0, 1.1fr) minmax(0, 0.9fr);
    }}

    .slide-main > .dual-images figure {{
      margin: 0;
      min-height: 0;
      min-width: 0;
      height: 100%;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      background: var(--card-bg);
      border-radius: clamp(6px, 1vw, 12px);
      border: 1px solid var(--table-border);
      padding: clamp(0.25rem, 0.6vw, 0.5rem);
    }}

    .slide-main > .dual-images img {{
      width: 100%;
      height: 100%;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      object-position: center;
    }}

    @media (max-width: 700px) {{
      .slide-main > .dual-images {{
        grid-template-columns: 1fr;
        grid-template-rows: 1fr 1fr;
      }}
    }}

    .slide-main > .table-wrap {{
      flex: 0 1 auto;
      width: 100%;
      min-height: 0;
      max-height: calc(100dvh - 7.5rem);
      overflow: hidden;
    }}

    .table-wrap {{
      overflow: hidden;
      flex-shrink: 1;
      min-height: 0;
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: var(--table-size);
    }}

    .data-table th {{
      text-align: left;
      padding: 0.5em 0.65em;
      background: var(--table-header-bg);
      color: var(--text-primary);
      font-weight: 700;
    }}

    .data-table td {{
      padding: 0.45em 0.65em;
      border-bottom: 1px solid var(--table-border);
      color: var(--text-secondary);
      vertical-align: top;
    }}

    .table-wrap.dense-table .data-table th,
    .table-wrap.dense-table .data-table td {{
      padding: 0.35em 0.5em;
      line-height: 1.35;
    }}

    .table-wrap.dense-table {{
      max-height: min(62vh, 520px);
    }}

    .data-table tbody tr:last-child td {{
      font-weight: 600;
    }}

    html[data-theme="dark"] .data-table tbody tr:last-child td {{
      color: var(--text-primary);
    }}

    /* === 720p / proyector (1280×720) === */
    @media (max-height: 800px) {{
      :root {{
        --slide-padding: clamp(0.65rem, 2.2vw, 1.65rem);
        --content-gap: clamp(0.35rem, 1vh, 0.65rem);
        --h2-size: clamp(1.05rem, 2.8vw, 1.75rem);
        --body-size: clamp(0.875rem, 1.4vw, 1.05rem);
        --table-size: clamp(0.8125rem, 1.15vw, 0.9375rem);
        --small-size: clamp(0.75rem, 1vw, 0.875rem);
      }}

      .slide-content > .slide-num {{
        font-size: clamp(0.8rem, 2.5vh, 1.35rem);
      }}

      .content-split,
      .slide-main > .table-wrap,
      .slide-main > .dual-images {{
        max-height: calc(100dvh - 7rem);
      }}

      .diagram-slide .slide-content > .slide-num {{
        display: none;
      }}

      .diagram-slide .bullet-list {{
        gap: clamp(0.15rem, 0.4vh, 0.3rem);
      }}

      .diagram-slide .bullet-list li {{
        font-size: clamp(0.8rem, 1.2vw, 0.95rem);
        line-height: 1.3;
      }}

      .table-wrap.dense-table .data-table th,
      .table-wrap.dense-table .data-table td {{
        padding: 0.26em 0.42em;
        line-height: 1.22;
      }}
    }}

    @media (max-height: 600px) {{
      .slide-main > .dual-images.dual-images--stack {{
        grid-template-rows: minmax(0, 1fr) minmax(0, 0.85fr);
      }}

      .diagram-slide .bullet-list {{
        gap: 0.2rem;
      }}

      .diagram-slide .bullet-list li {{
        line-height: 1.25;
      }}

      .slide-content > .slide-num {{
        display: none;
      }}
    }}

    @media (max-width: 1024px) {{
      .slide:not(.title-slide) .slide-content,
      .title-slide .slide-content {{
        padding-right: calc(var(--slide-padding) + var(--chrome-rail-width) + 0.75rem);
      }}
    }}

    .reveal {{
      opacity: 0;
      transform: translateY(24px);
      transition: opacity var(--duration-normal) var(--ease-out-expo),
        transform var(--duration-normal) var(--ease-out-expo);
    }}

    .slide.visible .reveal {{
      opacity: 1;
      transform: translateY(0);
    }}

    .slide.visible .reveal:nth-child(2) {{ transition-delay: 0.08s; }}
    .slide.visible .reveal:nth-child(3) {{ transition-delay: 0.14s; }}
    .slide.visible .reveal:nth-child(4) {{ transition-delay: 0.2s; }}
    .slide.visible .reveal:nth-child(5) {{ transition-delay: 0.26s; }}

  /* === INLINE EDITING === */
    .edit-hotzone {{
      position: fixed;
      top: 0;
      left: 0;
      width: 80px;
      height: 80px;
      z-index: 10000;
      cursor: pointer;
    }}
    .edit-toggle {{
      position: fixed;
      top: max(12px, env(safe-area-inset-top, 0px));
      left: max(12px, env(safe-area-inset-left, 0px));
      opacity: 0;
      pointer-events: none;
      z-index: 10001;
      min-width: 44px;
      min-height: 44px;
      background: var(--chrome-bg);
      color: var(--chrome-text);
      border: 1px solid var(--chrome-border);
      border-radius: 8px;
      padding: 0.5rem;
      cursor: pointer;
      transition: opacity 0.3s ease, background 0.2s ease, border-color 0.2s ease;
    }}

    .edit-toggle svg {{
      width: 1.25rem;
      height: 1.25rem;
      stroke: currentColor;
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .edit-toggle:focus-visible {{
      outline: none;
      box-shadow: var(--focus-ring);
    }}
    .edit-toggle.show, .edit-toggle.active {{
      opacity: 1;
      pointer-events: auto;
    }}
    body.edit-active [data-editable] {{
      outline: 2px dashed var(--accent);
      outline-offset: 4px;
      cursor: text;
    }}
    .edit-banner {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      padding-bottom: env(safe-area-inset-bottom, 0px);
      background: var(--accent);
      color: #ffffff;
      text-align: center;
      padding: 0.5rem;
      font-size: var(--small-size);
      transform: translateY(100%);
      transition: transform 0.3s ease;
      z-index: 10002;
    }}
    .edit-banner.active {{ transform: translateY(0); }}

    /* === EXPORT MODE (?export=1) — dom-to-pptx / golden PNG === */
    body.export-mode .progress-bar,
    body.export-mode .chrome-top,
    body.export-mode .nav-dots,
    body.export-mode .edit-hotzone,
    body.export-mode .edit-toggle,
    body.export-mode .edit-banner {{
      display: none !important;
      pointer-events: none !important;
    }}

    html.export-scroll {{
      scroll-snap-type: none;
    }}

    body.export-mode .slide {{
      scroll-snap-align: none;
    }}

    body.export-mode .reveal,
    body.export-mode .slide.visible .reveal {{
      opacity: 1 !important;
      transform: none !important;
      transition: none !important;
    }}

    body.export-mode *,
    body.export-mode *::before,
    body.export-mode *::after {{
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }}

    /* Sin hueco del rail de navegación (1280px activa @media 1024) */
    body.export-mode .slide:not(.title-slide) .slide-content,
    body.export-mode .title-slide .slide-content {{
      padding-right: var(--slide-padding) !important;
    }}

    /* Captura PPTX: portada/cierre centrados; contenido denso arriba (más área útil) */
    body.export-mode .slide.title-slide .slide-content,
    body.export-mode .slide[data-id="closing"] .slide-content {{
      justify-content: center !important;
    }}

    body.export-mode .slide:not(.title-slide):not([data-id="closing"]) .slide-content {{
      justify-content: flex-start !important;
      padding-block: clamp(0.75rem, 2.5vh, 1.5rem) !important;
    }}

    body.export-mode .slide:not(.title-slide) .slide-main {{
      flex: 0 1 auto;
      max-height: min(78vh, 840px);
    }}

    body.export-mode .slide.diagram-slide .slide-main,
    body.export-mode .slide:not(.title-slide) .slide-main:has(.table-wrap) {{
      max-height: min(85vh, 920px);
    }}

    body.export-mode .slide-main > .table-wrap {{
      max-height: min(80vh, 880px);
    }}

    body.export-mode .slide:not(.title-slide) .slide-content > .slide-num {{
      margin-bottom: 0.15rem;
    }}

    body.export-mode .slide:not(.title-slide) h2 {{
      margin-bottom: clamp(0.35rem, 1vh, 0.6rem);
    }}
  </style>
</head>
<body>
  <div class="progress-bar" id="progressBar"></div>
  <div class="chrome-top">
    <span class="slide-counter" id="slideCounter" aria-live="polite">01 / {len(SLIDES)}</span>
    <button type="button" class="chrome-btn theme-toggle" id="themeToggle"
      aria-label="Activar tema oscuro" aria-pressed="false">
      <svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="currentColor"/><g stroke="currentColor" stroke-width="2" fill="none"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></g></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
  </div>
  <nav class="nav-dots" id="navDots" aria-label="Diapositivas"></nav>
  <div class="edit-hotzone" aria-hidden="true"></div>
  <button type="button" class="edit-toggle" id="editToggle" aria-label="Modo edición" title="Modo edición (E)">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
  </button>
  <div class="edit-banner">Modo edición — clic en textos · Ctrl+S exportar · E salir</div>

{slides_html}

  <script>
    /* === THEME === */
    class ThemeController {{
      constructor() {{
        this.storageKey = "pfc-defense-theme";
        this.root = document.documentElement;
        this.toggle = document.getElementById("themeToggle");
        this.meta = document.getElementById("themeColorMeta");
        this.apply(this.getTheme(), false);
        this.toggle?.addEventListener("click", () => this.toggleTheme());
        document.addEventListener("keydown", (e) => {{
          if (e.target.getAttribute("contenteditable") === "true") return;
          if (e.key === "t" || e.key === "T") {{
            e.preventDefault();
            this.toggleTheme();
          }}
        }});
      }}

      getTheme() {{
        const saved = localStorage.getItem(this.storageKey);
        return saved === "dark" ? "dark" : "light";
      }}

      apply(theme, persist) {{
        this.root.setAttribute("data-theme", theme);
        if (persist) localStorage.setItem(this.storageKey, theme);
        const isDark = theme === "dark";
        if (this.meta) {{
          this.meta.setAttribute("content", isDark ? "#1a1a1a" : "#f4f1ec");
        }}
        if (this.toggle) {{
          this.toggle.setAttribute("aria-pressed", isDark ? "true" : "false");
          this.toggle.setAttribute(
            "aria-label",
            isDark ? "Activar tema claro" : "Activar tema oscuro"
          );
        }}
      }}

      toggleTheme() {{
        const next = this.getTheme() === "dark" ? "light" : "dark";
        this.apply(next, true);
      }}
    }}

    /* === SLIDE CONTROLLER === */
    class SlidePresentation {{
      constructor() {{
        this.slides = Array.from(document.querySelectorAll(".slide"));
        this.currentSlide = 0;
        this.navDotsContainer = document.getElementById("navDots");
        this.progressBar = document.getElementById("progressBar");
        this.slideCounter = document.getElementById("slideCounter");
        this.totalSlides = this.slides.length;
        this.setupIntersectionObserver();
        this.setupKeyboardNav();
        this.setupTouchNav();
        this.setupWheelNav();
        this.setupNavDots();
        this.layoutNavRail();
        window.addEventListener("resize", () => this.layoutNavRail());
        this.updateUI(0);
      }}

      setupIntersectionObserver() {{
        const obs = new IntersectionObserver(
          (entries) => {{
            entries.forEach((e) => {{
              if (e.isIntersecting) {{
                e.target.classList.add("visible");
                const i = this.slides.indexOf(e.target);
                if (i >= 0) this.updateUI(i);
              }}
            }});
          }},
          {{ threshold: 0.45 }}
        );
        this.slides.forEach((s) => obs.observe(s));
      }}

      goTo(index) {{
        const i = Math.max(0, Math.min(index, this.slides.length - 1));
        this.slides[i].scrollIntoView({{ behavior: "smooth" }});
        this.updateUI(i);
      }}

      updateUI(index) {{
        this.currentSlide = index;
        const pct = ((index + 1) / this.slides.length) * 100;
        this.progressBar.style.width = pct + "%";
        const num = String(index + 1).padStart(2, "0");
        const total = String(this.totalSlides).padStart(2, "0");
        if (this.slideCounter) {{
          this.slideCounter.textContent = num + " / " + total;
        }}
        this.navDotsContainer.querySelectorAll("button").forEach((btn, j) => {{
          btn.classList.toggle("active", j === index);
          btn.setAttribute("aria-current", j === index ? "true" : "false");
        }});
      }}

      setupNavDots() {{
        this.navDotsContainer.innerHTML = "";
        this.slides.forEach((_, i) => {{
          const btn = document.createElement("button");
          btn.type = "button";
          const label = "Diapositiva " + (i + 1);
          btn.setAttribute("aria-label", label);
          btn.title = label;
          btn.addEventListener("click", () => this.goTo(i));
          this.navDotsContainer.appendChild(btn);
        }});
        this.layoutNavRail();
      }}

      layoutNavRail() {{
        const n = this.slides.length;
        if (!n) return;
        const vh = window.innerHeight;
        const chromePad = 48;
        const available = Math.max(120, vh - chromePad);
        const maxBtnH = 28;
        const minBtnH = 14;
        let btnH = Math.floor((available - Math.max(0, n - 1)) / n);
        btnH = Math.max(minBtnH, Math.min(maxBtnH, btnH));
        document.documentElement.style.setProperty("--nav-btn-height", btnH + "px");
        document.documentElement.style.setProperty("--slide-count", String(n));
      }}

      setupKeyboardNav() {{
        document.addEventListener("keydown", (e) => {{
          if (e.target.getAttribute("contenteditable") === "true") return;
          if (e.key === "ArrowDown" || e.key === "PageDown" || e.key === " ") {{
            e.preventDefault();
            this.goTo(this.currentSlide + 1);
          }} else if (e.key === "ArrowUp" || e.key === "PageUp") {{
            e.preventDefault();
            this.goTo(this.currentSlide - 1);
          }} else if (e.key === "Home") {{
            this.goTo(0);
          }} else if (e.key === "End") {{
            this.goTo(this.slides.length - 1);
          }}
        }});
      }}

      setupTouchNav() {{
        let y0 = 0;
        document.addEventListener(
          "touchstart",
          (e) => {{ y0 = e.touches[0].clientY; }},
          {{ passive: true }}
        );
        document.addEventListener(
          "touchend",
          (e) => {{
            const dy = y0 - e.changedTouches[0].clientY;
            if (Math.abs(dy) > 50) {{
              this.goTo(this.currentSlide + (dy > 0 ? 1 : -1));
            }}
          }},
          {{ passive: true }}
        );
      }}

      setupWheelNav() {{
        let locked = false;
        document.addEventListener(
          "wheel",
          (e) => {{
            if (locked || document.body.classList.contains("edit-active")) return;
            if (Math.abs(e.deltaY) < 30) return;
            locked = true;
            setTimeout(() => {{ locked = false; }}, 600);
            this.goTo(this.currentSlide + (e.deltaY > 0 ? 1 : -1));
          }},
          {{ passive: true }}
        );
      }}
    }}

    /* === INLINE EDITOR === */
    class SlideEditor {{
      constructor() {{
        this.isActive = false;
        this.toggle = document.getElementById("editToggle");
        this.banner = document.querySelector(".edit-banner");
        this.markEditable();
        this.loadFromStorage();
        this.setupSaveShortcut();
      }}

      markEditable() {{
        document.querySelectorAll(
          "h1, h2, p, li, th, td, .slide-num"
        ).forEach((el) => el.setAttribute("data-editable", "true"));
      }}

      toggleEditMode() {{
        this.isActive = !this.isActive;
        document.body.classList.toggle("edit-active", this.isActive);
        this.toggle.classList.toggle("active", this.isActive);
        this.banner.classList.toggle("active", this.isActive);
        document.querySelectorAll("[data-editable]").forEach((el) => {{
          if (this.isActive) el.setAttribute("contenteditable", "true");
          else el.removeAttribute("contenteditable");
        }});
        if (this.isActive) this.saveToStorage();
        else this.saveToStorage();
      }}

      saveToStorage() {{
        const data = {{}};
        document.querySelectorAll("[data-editable]").forEach((el, i) => {{
          data["e" + i] = el.innerHTML;
        }});
        try {{
          localStorage.setItem("pfc-defense-slides-v2", JSON.stringify(data));
        }} catch (_) {{}}
      }}

      loadFromStorage() {{
        try {{
          const raw = localStorage.getItem("pfc-defense-slides-v2");
          if (!raw) return;
          const data = JSON.parse(raw);
          document.querySelectorAll("[data-editable]").forEach((el, i) => {{
            const k = "e" + i;
            if (data[k] != null) el.innerHTML = data[k];
          }});
        }} catch (_) {{}}
      }}

      exportFile() {{
        const editableEls = Array.from(document.querySelectorAll("[contenteditable]"));
        editableEls.forEach((el) => el.removeAttribute("contenteditable"));
        document.body.classList.remove("edit-active");
        const editToggle = document.getElementById("editToggle");
        const editBanner = document.querySelector(".edit-banner");
        editToggle?.classList.remove("active", "show");
        editBanner?.classList.remove("active", "show");
        const out =
          "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
        if (this.isActive) {{
          document.body.classList.add("edit-active");
          editableEls.forEach((el) => el.setAttribute("contenteditable", "true"));
          editToggle?.classList.add("active");
          editBanner?.classList.add("active");
        }}
        const blob = new Blob([out], {{ type: "text/html" }});
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "presentacion-defensa-pfc.html";
        a.click();
        URL.revokeObjectURL(a.href);
      }}

      setupSaveShortcut() {{
        document.addEventListener("keydown", (e) => {{
          if ((e.ctrlKey || e.metaKey) && e.key === "s") {{
            e.preventDefault();
            if (this.isActive) {{
              this.saveToStorage();
              this.exportFile();
            }}
          }}
        }});
        document.querySelectorAll("[data-editable]").forEach((el) => {{
          el.addEventListener("input", () => {{
            if (this.isActive) this.saveToStorage();
          }});
        }});
      }}
    }}

    /* === EXPORT MODE CONTROLLER === */
    class ExportModeController {{
      static isExport() {{
        return window.__PFC_EXPORT_MODE__ === true;
      }}

      static async prepare() {{
        if (!ExportModeController.isExport()) return;
        document.body.classList.add("export-mode");
        document.documentElement.classList.add("export-scroll");
        document.documentElement.setAttribute("data-theme", "light");
        const meta = document.getElementById("themeColorMeta");
        if (meta) meta.setAttribute("content", "#f4f1ec");
        document.querySelectorAll(".slide").forEach((s) => s.classList.add("visible"));
        if (document.fonts && document.fonts.ready) {{
          await document.fonts.ready;
        }}
        await Promise.all(
          Array.from(document.images).map(
            (img) =>
              new Promise((resolve) => {{
                if (img.complete) {{
                  resolve();
                  return;
                }}
                const done = () => resolve();
                img.addEventListener("load", done, {{ once: true }});
                img.addEventListener("error", done, {{ once: true }});
                setTimeout(done, 4000);
              }})
          )
        );
        await new Promise((r) => setTimeout(r, 300));
      }}
    }}

    (async function initPresentation() {{
      await ExportModeController.prepare();
      if (ExportModeController.isExport()) {{
        window.__PFC_EXPORT_READY__ = true;
        return;
      }}
      new ThemeController();
      const editor = new SlideEditor();
      new SlidePresentation();
      wireEditChrome(editor);
    }})();

    function wireEditChrome(editor) {{
    const hotzone = document.querySelector(".edit-hotzone");
    const editToggle = document.getElementById("editToggle");
    let hideTimeout = null;
    hotzone.addEventListener("mouseenter", () => {{
      clearTimeout(hideTimeout);
      editToggle.classList.add("show");
    }});
    hotzone.addEventListener("mouseleave", () => {{
      hideTimeout = setTimeout(() => {{
        if (!editor.isActive) editToggle.classList.remove("show");
      }}, 400);
    }});
    editToggle.addEventListener("mouseenter", () => clearTimeout(hideTimeout));
    editToggle.addEventListener("mouseleave", () => {{
      hideTimeout = setTimeout(() => {{
        if (!editor.isActive) editToggle.classList.remove("show");
      }}, 400);
    }});
    hotzone.addEventListener("click", () => editor.toggleEditMode());
    editToggle.addEventListener("click", () => editor.toggleEditMode());
    document.addEventListener("keydown", (e) => {{
      if ((e.key === "e" || e.key === "E") && !e.target.getAttribute("contenteditable")) {{
        editor.toggleEditMode();
      }}
    }});
    }}
  </script>
</body>
</html>
"""


def main():
    root = repo_root()
    out_dir = root / "docs" / "presentacion-defensa-pfc"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(build_html(), encoding="utf-8")
    print(f"Guardado: {out} ({len(SLIDES)} diapositivas)")


if __name__ == "__main__":
    main()
