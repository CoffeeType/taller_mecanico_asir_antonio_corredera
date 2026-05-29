#!/usr/bin/env python3
"""Screenshot every slide for visual QA (normal or export mode)."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Screenshot all defense slides")
    p.add_argument(
        "--export",
        action="store_true",
        help="Use ?export=1 (golden references for PPTX QA)",
    )
    p.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: _layout_check/slides or _export_golden)",
    )
    return p.parse_args()


async def main() -> None:
    from playwright.async_api import async_playwright

    args = parse_args()
    html = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "presentacion-defensa-pfc"
        / "index.html"
    ).resolve()
    if args.out_dir:
        out_dir = args.out_dir.resolve()
    elif args.export:
        out_dir = html.parent / "_export_golden"
    else:
        out_dir = html.parent / "_layout_check" / "slides"
    out_dir.mkdir(parents=True, exist_ok=True)

    url = html.as_uri()
    if args.export:
        url += "?export=1"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        vw, vh = (1920, 1080) if args.export else (1280, 720)
        page = await browser.new_page(viewport={"width": vw, "height": vh})
        await page.goto(url, wait_until="networkidle")
        if args.export:
            await page.wait_for_function(
                "window.__PFC_EXPORT_READY__ === true", timeout=30000
            )
        else:
            await page.wait_for_timeout(500)
        ids = await page.evaluate(
            """() => [...document.querySelectorAll('.slide')].map(s => s.dataset.id)"""
        )
        for sid in ids:
            await page.evaluate(
                f'document.querySelector("[data-id=\\"{sid}\\"]").scrollIntoView()'
            )
            await page.wait_for_timeout(300)
            path = out_dir / f"{sid}.png"
            await page.screenshot(path=str(path), full_page=False)
        await browser.close()
    print(f"Wrote {len(ids)} screenshots to {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
