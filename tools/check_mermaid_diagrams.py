#!/usr/bin/env python3
"""Assert Mermaid diagrams render SVG on key diagram slides at 1280x720."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

SLIDE_IDS = (
    "architecture",
    "profiles",
    "problem",
    "data_model",
    "docker",
    "traffic_source",
    "monitoring",
    "aws",
)
MIN_DIAGRAMS = 9
MIN_WRAP_W = 280
MIN_WRAP_H = 200


async def main() -> int:
    from playwright.async_api import async_playwright

    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()
    if not html.is_file():
        print(f"Missing: {html}", file=sys.stderr)
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(1200)
        failures = await page.evaluate(
            f"""async () => {{
              const minW = {MIN_WRAP_W};
              const minH = {MIN_WRAP_H};
              const minDiagrams = {MIN_DIAGRAMS};
              const ids = {list(SLIDE_IDS)!r};
              const bad = [];
              if (document.querySelectorAll('pre.mermaid').length < minDiagrams) {{
                bad.push({{ id: 'all', reason: 'expected ' + minDiagrams + ' mermaid blocks' }});
              }}
              const deadline = Date.now() + 12000;
              while (typeof mermaid === 'undefined' && Date.now() < deadline) {{
                await new Promise((r) => requestAnimationFrame(r));
              }}
              if (typeof MermaidRenderer !== 'undefined') {{
                await MermaidRenderer.init();
              }} else if (typeof mermaid !== 'undefined') {{
                await mermaid.run({{ querySelector: '.mermaid' }});
              }}
              for (const id of ids) {{
                const slide = document.querySelector(`[data-id="${{id}}"]`);
                if (!slide) {{
                  bad.push({{ id, reason: 'slide missing' }});
                  continue;
                }}
                slide.classList.add('visible');
                slide.scrollIntoView({{ block: 'center', behavior: 'instant' }});
                await new Promise((r) => setTimeout(r, 300));
                const pres = slide.querySelectorAll('pre.mermaid');
                if (!pres.length) {{
                  bad.push({{ id, reason: 'no mermaid block' }});
                  continue;
                }}
                pres.forEach((pre, idx) => {{
                  const wrap = pre.closest('.mermaid-wrap');
                  const svg = pre.querySelector('svg');
                  const label = id + (pres.length > 1 ? '[' + idx + ']' : '');
                  if (!wrap || !svg) {{
                    bad.push({{ id: label, reason: 'no svg' }});
                    return;
                  }}
                  if (pre.getAttribute('data-mermaid-error') === 'true') {{
                    bad.push({{ id: label, reason: 'render error flag' }});
                    return;
                  }}
                  if (pre.querySelector('.error-icon, .mermaid-error')) {{
                    bad.push({{ id: label, reason: 'error icon in svg' }});
                    return;
                  }}
                  const r = (wrap || svg).getBoundingClientRect();
                  if (r.width < minW || r.height < minH) {{
                    bad.push({{ id: label, reason: 'wrap ' + Math.round(r.width) + 'x' + Math.round(r.height) }});
                  }}
                }});
              }}
              return bad;
            }}"""
        )
        await browser.close()

    if not failures:
        print(f"OK — Mermaid on {', '.join(SLIDE_IDS)} (wrap>={MIN_WRAP_W}x{MIN_WRAP_H})")
        return 0

    print("FAIL — Mermaid diagrams:", file=sys.stderr)
    for item in failures:
        print(f"  [{item['id']}] {item['reason']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
