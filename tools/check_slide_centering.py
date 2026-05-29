#!/usr/bin/env python3
"""Assert slide-main blocks are horizontally centered within slide-content."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

MAX_MARGIN_DELTA_RATIO = 0.08
SKIP_IDS = frozenset({"cover"})


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
        await page.wait_for_timeout(600)
        failures = await page.evaluate(
            f"""() => {{
              const maxRatio = {MAX_MARGIN_DELTA_RATIO};
              const skip = new Set({list(SKIP_IDS)!r});
              const bad = [];
              for (const slide of document.querySelectorAll('.slide')) {{
                const id = slide.dataset.id || '?';
                if (skip.has(id)) continue;
                slide.classList.add('visible');
                const content = slide.querySelector('.slide-content');
                const main = slide.querySelector('.slide-main');
                if (!content || !main) continue;
                const cr = content.getBoundingClientRect();
                const mr = main.getBoundingClientRect();
                const left = mr.left - cr.left;
                const right = cr.right - mr.right;
                const delta = Math.abs(left - right);
                const base = Math.max(cr.width, 1);
                if (delta / base > maxRatio) {{
                  bad.push({{ id, left: Math.round(left), right: Math.round(right), ratio: delta / base }});
                }}
              }}
              return bad;
            }}"""
        )
        await browser.close()

    if not failures:
        print(f"OK — slide-main centered (margin delta <={MAX_MARGIN_DELTA_RATIO * 100:.0f}%)")
        return 0

    print("FAIL — off-center slide-main:", file=sys.stderr)
    for item in failures:
        print(
            f"  [{item['id']}] L={item['left']}px R={item['right']}px "
            f"delta={item['ratio']:.2%}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
