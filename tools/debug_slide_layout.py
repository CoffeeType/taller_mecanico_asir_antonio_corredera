#!/usr/bin/env python3
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
    sid = "evidence"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.evaluate(f'document.querySelector("[data-id={sid}]").scrollIntoView()')
        await page.wait_for_timeout(500)
        info = await page.evaluate(
            f"""() => {{
              const slide = document.querySelector('[data-id={sid}]');
              slide.classList.add('visible');
              const main = slide.querySelector('.slide-main');
              const dual = slide.querySelector('.dual-images');
              const cs = getComputedStyle(dual);
              const figs = [...dual.querySelectorAll('figure')].map((f, i) => {{
                const r = f.getBoundingClientRect();
                const img = f.querySelector('img');
                const ir = img.getBoundingClientRect();
                return {{i, fig: [r.width, r.height], img: [ir.width, ir.height]}};
              }});
              return {{
                gridCols: cs.gridTemplateColumns,
                gridRows: cs.gridTemplateRows,
                dual: [dual.getBoundingClientRect().width, dual.getBoundingClientRect().height],
                main: [main.getBoundingClientRect().width, main.getBoundingClientRect().height],
                figs,
              }};
            }}"""
        )
        print(info)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
