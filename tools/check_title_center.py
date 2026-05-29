#!/usr/bin/env python3
"""Check title slide vertical centering."""

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

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(400)
        info = await page.evaluate(
            """() => {
              const slide = document.querySelector('.title-slide');
              const card = slide.querySelector('.slide-card');
              const sr = slide.getBoundingClientRect();
              const cr = card.getBoundingClientRect();
              const cardCenterY = cr.top + cr.height / 2;
              const slideCenterY = sr.top + sr.height / 2;
              return {
                slideH: Math.round(sr.height),
                cardTop: Math.round(cr.top),
                cardBottom: Math.round(cr.bottom),
                cardH: Math.round(cr.height),
                offsetFromCenter: Math.round(cardCenterY - slideCenterY),
                cardLeft: Math.round(cr.left),
                cardWidth: Math.round(cr.width),
              };
            }"""
        )
        print(info)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
