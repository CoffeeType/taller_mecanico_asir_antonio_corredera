#!/usr/bin/env python3
"""Minimum computed font sizes for defense slides at 1280x720 (projector)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

MIN_H2_PX = 24
MIN_BODY_PX = 18
MIN_TABLE_PX = 16


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
              const minH2 = {MIN_H2_PX};
              const minBody = {MIN_BODY_PX};
              const minTable = {MIN_TABLE_PX};
              const bad = [];
              const px = (v) => parseFloat(v) || 0;

              for (const slide of document.querySelectorAll(".slide")) {{
                slide.classList.add("visible");
                const id = slide.dataset.id || "?";
                if (slide.classList.contains("title-slide")) continue;

                const h2 = slide.querySelector("h2");
                if (h2) {{
                  const size = px(getComputedStyle(h2).fontSize);
                  if (size < minH2) bad.push({{ id, el: "h2", size, min: minH2 }});
                }}

                const bullet = slide.querySelector(".bullet-list li");
                if (bullet) {{
                  const size = px(getComputedStyle(bullet).fontSize);
                  if (size < minBody) bad.push({{ id, el: "bullet", size, min: minBody }});
                }}

                const td = slide.querySelector(".data-table td");
                if (td) {{
                  const size = px(getComputedStyle(td).fontSize);
                  if (size < minTable) bad.push({{ id, el: "table", size, min: minTable }});
                }}
              }}
              return bad;
            }}"""
        )
        await browser.close()

    if not failures:
        print(
            f"OK — typography at 1280x720 (h2>={MIN_H2_PX}px, "
            f"body>={MIN_BODY_PX}px, table>={MIN_TABLE_PX}px)"
        )
        return 0

    print("FAIL — slides below minimum font size:", file=sys.stderr)
    for item in failures:
        print(
            f"  [{item['id']}] {item['el']}: {item['size']}px (min {item['min']}px)",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
