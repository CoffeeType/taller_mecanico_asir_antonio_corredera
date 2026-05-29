#!/usr/bin/env python3
"""Assert defense deck has 20 slides (cover + 19 content) with asir_modules_2."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

EXPECTED_SLIDES = 20


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
        await page.wait_for_timeout(400)
        result = await page.evaluate(
            """() => ({
              count: document.querySelectorAll('.slide').length,
              hasAsir2: !!document.querySelector('[data-id="asir_modules_2"]'),
              chartOnly: !!document.querySelector('[data-id="asir_modules"] #techChart')
                && !document.querySelector('[data-id="asir_modules"] .asir-combo-table'),
              numbered: document.querySelectorAll('.slide:not(.title-slide) .slide-num').length,
            })"""
        )
        await browser.close()

    if (
        result["count"] == EXPECTED_SLIDES
        and result["hasAsir2"]
        and result["chartOnly"]
        and result["numbered"] == 19
    ):
        print(
            f"OK — {EXPECTED_SLIDES} slides, asir_modules chart-only, "
            f"asir_modules_2 present, {result['numbered']} numbered"
        )
        return 0

    print(
        f"FAIL — count={result['count']} (expected {EXPECTED_SLIDES}), "
        f"asir_modules_2={result['hasAsir2']}, chartOnly={result['chartOnly']}, "
        f"numbered={result['numbered']} (expected 19)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
