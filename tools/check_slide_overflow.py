#!/usr/bin/env python3
"""Detect slide content overflow at 1280x720."""

from __future__ import annotations

import asyncio
from pathlib import Path

# Subpixel/layout tolerance; slides clip with overflow:hidden (frontend-slides contract).
OVERFLOW_TOLERANCE_PX = 16


async def check_viewport(page, width: int, height: int) -> list[dict]:
    await page.set_viewport_size({"width": width, "height": height})
    await page.reload()
    await page.wait_for_timeout(400)
    return await page.evaluate(
        """(tol) => {
          const slides = [...document.querySelectorAll('.slide')];
          return slides.map((slide, i) => {
            slide.classList.add('visible');
            const content = slide.querySelector('.slide-content')
              || slide.querySelector('.slide-card')
              || slide;
            const slideRect = slide.getBoundingClientRect();
            let maxBottom = 0;
            let maxRight = 0;
            content.querySelectorAll('*').forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.height > 0) {
                maxBottom = Math.max(maxBottom, r.bottom - slideRect.top);
                maxRight = Math.max(maxRight, r.right - slideRect.left);
              }
            });
            const id = slide.dataset.id || ('slide-' + (i + 1));
            const overflowY = maxBottom > slideRect.height + tol;
            const overflowX = maxRight > slideRect.width + tol;
            return {
              i: i + 1,
              id,
              overflowY,
              overflowX,
              diffY: Math.round(maxBottom - slideRect.height),
              diffX: Math.round(maxRight - slideRect.width),
            };
          });
        }""",
        OVERFLOW_TOLERANCE_PX,
    )


async def main() -> None:
    from playwright.async_api import async_playwright

    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()
    url = html.as_uri()
    viewports = [(1280, 720), (1366, 768), (1920, 1080), (1024, 768), (1280, 600), (800, 600)]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        for w, h in viewports:
            results = await check_viewport(page, w, h)
            bad = [r for r in results if r["overflowY"] or r["overflowX"]]
            nav = await page.evaluate(
                """() => {
                  const nav = document.querySelector('.nav-dots');
                  const r = nav.getBoundingClientRect();
                  const slide = document.querySelector('.slide[data-id="architecture"]');
                  const content = slide?.querySelector('.slide-content');
                  const cr = content?.getBoundingClientRect();
                  return {
                    navH: Math.round(r.height),
                    navTop: Math.round(r.top),
                    navBottom: Math.round(r.bottom),
                    vh: window.innerHeight,
                    contentRight: cr ? Math.round(cr.right) : null,
                    overlapNav: cr ? cr.right > r.left - 8 : null,
                  };
                }"""
            )
            print(f"\n=== {w}x{h} nav={nav} bad={len(bad)} ===")
            for r in bad:
                print(
                    f"  {r['i']:02d} {r['id']}: Y+{r['diffY']} X+{r['diffX']}"
                )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
