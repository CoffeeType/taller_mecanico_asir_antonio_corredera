#!/usr/bin/env python3
"""Screenshot specific slides for manual QA."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


async def main() -> None:
    from playwright.async_api import async_playwright

    slide_ids = sys.argv[1:] or [
        "evidence",
        "data_model",
        "problem",
        "profiles",
        "architecture",
        "monitoring",
    ]
    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()
    out_dir = html.parent / "_layout_check" / "slides"
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(500)
        for sid in slide_ids:
            await page.evaluate(
                f'document.querySelector("[data-id=\\"{sid}\\"]").scrollIntoView()'
            )
            await page.wait_for_timeout(400)
            path = out_dir / f"{sid}.png"
            await page.screenshot(path=str(path), full_page=False)
            print(f"Wrote {path}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
