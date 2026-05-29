#!/usr/bin/env python3
"""Assert slide asir_modules uses a legible ECharts horizontal bar chart at 1280x720."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

MIN_CANVAS_W = 520
MIN_CANVAS_H = 280
SLIDE_ID = "asir_modules"


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
        await page.wait_for_timeout(800)

        ok = await page.evaluate(
            f"""async () => {{
              const slide = document.querySelector('[data-id="{SLIDE_ID}"]');
              if (!slide) return {{ ok: false, reason: "slide missing" }};
              slide.classList.add("visible");
              slide.scrollIntoView({{ block: "center" }});
              const deadline = Date.now() + 8000;
              while (typeof echarts === "undefined" && Date.now() < deadline) {{
                await new Promise((r) => requestAnimationFrame(r));
              }}
              if (typeof echarts === "undefined") {{
                return {{ ok: false, reason: "echarts not loaded" }};
              }}
              const el = document.getElementById("techChart");
              if (!el) return {{ ok: false, reason: "techChart missing" }};
              let chart = echarts.getInstanceByDom(el);
              if (!chart) {{
                if (typeof TechStackChart !== "undefined") {{
                  const inst = new TechStackChart();
                  inst.ensureChart(false);
                  chart = inst.chart;
                }}
              }}
              if (!chart) return {{ ok: false, reason: "chart not initialized" }};
              const opt = chart.getOption();
              const series = opt && opt.series && opt.series[0];
              const type = series && series.type;
              const canvas = el.querySelector("canvas");
              const cw = canvas ? canvas.width : 0;
              const ch = canvas ? canvas.height : 0;
              if (type !== "bar") {{
                return {{ ok: false, reason: `series type is ${{type}}, expected bar`, cw, ch }};
              }}
              if (cw < {MIN_CANVAS_W} || ch < {MIN_CANVAS_H}) {{
                return {{ ok: false, reason: `canvas too small (${{cw}}x${{ch}})`, cw, ch }};
              }}
              return {{ ok: true, type, cw, ch }};
            }}"""
        )
        await browser.close()

    if ok.get("ok"):
        print(
            f"OK — {SLIDE_ID}: bar chart {ok.get('cw')}x{ok.get('ch')} px at 1280x720"
        )
        return 0

    print(f"FAIL — {SLIDE_ID}: {ok.get('reason')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
