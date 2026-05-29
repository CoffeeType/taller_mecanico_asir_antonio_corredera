#!/usr/bin/env python3
"""Fail if main visuals use less than 35% of slide-main area (1280x720)."""

from __future__ import annotations

import asyncio
from pathlib import Path

MIN_VISUAL_FILL_RATIO = 0.35


async def main() -> None:
    from playwright.async_api import async_playwright

    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(600)

        report = await page.evaluate(
            f"""() => {{
              const minRatio = {MIN_VISUAL_FILL_RATIO};
              const bad = [];
              for (const slide of document.querySelectorAll('.slide')) {{
                slide.classList.add('visible');
                const id = slide.dataset.id || '?';
                const main = slide.querySelector('.slide-main');
                if (!main) continue;
                const hasVisualBlock = main.querySelector(
                  '.dual-images, .diagram-figure, .mermaid-wrap, .content-split, .asir-combo'
                );
                if (!hasVisualBlock) continue;
                const mr = main.getBoundingClientRect();
                const mainArea = mr.width * mr.height;
                if (mainArea < 1000) continue;
                let minTop = Infinity;
                let maxBottom = -Infinity;
                let minLeft = Infinity;
                let maxRight = -Infinity;
                for (const child of main.children) {{
                  const r = child.getBoundingClientRect();
                  if (r.height < 8) continue;
                  minTop = Math.min(minTop, r.top);
                  maxBottom = Math.max(maxBottom, r.bottom);
                  minLeft = Math.min(minLeft, r.left);
                  maxRight = Math.max(maxRight, r.right);
                }}
                if (!Number.isFinite(minTop)) continue;
                const usedArea = (maxRight - minLeft) * (maxBottom - minTop);
                const ratio = usedArea / mainArea;
                if (ratio < minRatio) {{
                  bad.push({{
                    id,
                    ratio: Math.round(ratio * 100),
                    mainH: Math.round(mr.height),
                    mainW: Math.round(mr.width),
                  }});
                }}
              }}
              return bad;
            }}"""
        )
        await browser.close()

    print(f"Slides below {int(MIN_VISUAL_FILL_RATIO * 100)}% visual fill in slide-main:")
    for item in report:
        print(
            f"  {item['id']}: {item['ratio']}% "
            f"(slide-main {item['mainW']}x{item['mainH']})"
        )
    if report:
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
