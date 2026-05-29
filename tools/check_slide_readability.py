#!/usr/bin/env python3
"""Readable typography and balanced layout at defense viewport (1280×720)."""

from __future__ import annotations

import asyncio
from pathlib import Path

# Minimum computed font sizes (px) at 1280×720
MIN_BULLET_PX = 14
MIN_TABLE_PX = 12
MIN_H2_PX = 20
MAX_TITLE_CENTER_OFFSET_PX = 48
MAX_BULLET_SLIDE_CENTER_OFFSET_RATIO = 0.12

BULLET_SLIDE_IDS = frozenset(
    {
        "problem",
        "objectives",
        "security",
        "validation",
        "conclusions",
        "closing",
    }
)


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
        await page.wait_for_timeout(500)

        report = await page.evaluate(
            f"""() => {{
              const bulletIds = {list(BULLET_SLIDE_IDS)!r};
              const issues = [];
              const slides = [...document.querySelectorAll('.slide')];
              slides.forEach((slide) => {{
                slide.classList.add('visible');
                const id = slide.dataset.id || '';
                const h2 = slide.querySelector('h2');
                if (h2) {{
                  const fs = parseFloat(getComputedStyle(h2).fontSize);
                  if (fs < {MIN_H2_PX}) issues.push(`${{id}}: h2 ${{fs}}px`);
                }}
                const li = slide.querySelector('.bullet-list li');
                if (li) {{
                  const fs = parseFloat(getComputedStyle(li).fontSize);
                  if (fs < {MIN_BULLET_PX}) issues.push(`${{id}}: bullet ${{fs}}px`);
                }}
                const td = slide.querySelector('.data-table td');
                if (td) {{
                  const fs = parseFloat(getComputedStyle(td).fontSize);
                  if (fs < {MIN_TABLE_PX}) issues.push(`${{id}}: table ${{fs}}px`);
                }}
                if (bulletIds.includes(id)) {{
                  const content = slide.querySelector('.slide-content');
                  const block = slide.querySelector('.bullet-list');
                  if (content && block) {{
                    const sr = slide.getBoundingClientRect();
                    const br = block.getBoundingClientRect();
                    const blockCenter = br.top + br.height / 2;
                    const slideCenter = sr.top + sr.height / 2;
                    const ratio = Math.abs(blockCenter - slideCenter) / sr.height;
                    if (ratio > {MAX_BULLET_SLIDE_CENTER_OFFSET_RATIO}) {{
                      issues.push(`${{id}}: off-center ratio=${{ratio.toFixed(2)}}`);
                    }}
                  }}
                }}
              }});
              const title = document.querySelector('.title-slide .slide-card');
              if (title) {{
                const slide = document.querySelector('.title-slide');
                const sr = slide.getBoundingClientRect();
                const tr = title.getBoundingClientRect();
                const offset = Math.abs((tr.top + tr.height / 2) - (sr.top + sr.height / 2));
                if (offset > {MAX_TITLE_CENTER_OFFSET_PX}) {{
                  issues.push(`cover: title offset ${{Math.round(offset)}}px`);
                }}
              }}
              return issues;
            }}"""
        )

        await browser.close()

    print(f"Readability issues at 1280x720: {len(report)}")
    for item in report:
        print(f"  - {item}")
    if report:
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
