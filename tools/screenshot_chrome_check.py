#!/usr/bin/env python3
"""Screenshot slide 1 chrome layout for visual review."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def main() -> None:
    from playwright.async_api import async_playwright

    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()
    out_dir = html.parent / "_layout_check"
    out_dir.mkdir(exist_ok=True)
    targets = [
        ("cover", "slide-cover-1280x720.png"),
        ("problem", "slide-problem-1280x720.png"),
        ("profiles", "slide-profiles-1280x720.png"),
        ("monitoring", "slide-monitoring-1280x720.png"),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(500)
        for slide_id, filename in targets:
            await page.evaluate(
                f'document.querySelector("[data-id=\\"{slide_id}\\"]").scrollIntoView()'
            )
            await page.wait_for_timeout(350)
            path = out_dir / filename
            await page.screenshot(path=str(path), full_page=False)
            print(f"Wrote {path}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
