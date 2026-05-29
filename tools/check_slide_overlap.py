#!/usr/bin/env python3
"""Detect overlapping UI elements per slide at defense viewport."""

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

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(html.as_uri())
        await page.wait_for_timeout(600)

        report = await page.evaluate(
            """() => {
              function intersects(a, b) {
                return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
              }
              function area(r) {
                return Math.max(0, r.width) * Math.max(0, r.height);
              }
              function overlapPx(a, b) {
                const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
                const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
                return x * y;
              }
              const results = [];
              for (const slide of document.querySelectorAll('.slide')) {
                slide.classList.add('visible');
                const id = slide.dataset.id || '?';
                const content = slide.querySelector('.slide-main');
                if (!content) continue;
                const nodes = [...new Set([...content.querySelectorAll(
                  'h2, .slide-num, .bullet-list, .table-wrap, .diagram-figure, .mermaid-wrap, .asir-combo, .dual-images, .content-split, .tech-chart-wrap, .tech-legend, figure img'
                )])].filter(el => {
                  if (el.classList.contains('slide-num')) return false;
                  const r = el.getBoundingClientRect();
                  return r.width > 20 && r.height > 20;
                });
                const pairs = [];
                for (let i = 0; i < nodes.length; i++) {
                  const ri = nodes[i].getBoundingClientRect();
                  for (let j = i + 1; j < nodes.length; j++) {
                    const rj = nodes[j].getBoundingClientRect();
                    if (nodes[i].contains(nodes[j]) || nodes[j].contains(nodes[i])) continue;
                    if (intersects(ri, rj)) {
                      const px = Math.round(overlapPx(ri, rj));
                      const minA = Math.min(area(ri), area(rj));
                      if (px > 80 && px > minA * 0.08) {
                        pairs.push({
                          a: nodes[i].className || nodes[i].tagName,
                          b: nodes[j].className || nodes[j].tagName,
                          px
                        });
                      }
                    }
                  }
                }
                if (pairs.length) results.push({ id, pairs });
              }
              return results;
            }"""
        )

        await browser.close()

    print(f"Slides with significant overlaps at 1280x720: {len(report)}")
    for item in report:
        print(f"\n  [{item['id']}]")
        for p in item["pairs"][:8]:
            print(f"    {p['a']} <-> {p['b']}: {p['px']}px2")
    if report:
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
