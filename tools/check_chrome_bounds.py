#!/usr/bin/env python3
"""Check fixed chrome/nav stay within viewport."""

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
    viewports = [
        (1280, 720),
        (1366, 768),
        (1920, 1080),
        (800, 600),
        (1280, 500),
        (1280, 550),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(html.as_uri())
        for w, h in viewports:
            await page.set_viewport_size({"width": w, "height": h})
            await page.reload()
            await page.wait_for_timeout(400)
            info = await page.evaluate(
                """() => {
                  const vw = window.innerWidth;
                  const vh = window.innerHeight;
                  const nav = document.querySelector('.nav-dots');
                  const chrome = document.querySelector('.chrome-top');
                  const nr = nav.getBoundingClientRect();
                  const cr = chrome.getBoundingClientRect();
                  const btns = [...nav.querySelectorAll('button')];
                  const first = btns[0]?.getBoundingClientRect();
                  const last = btns[btns.length - 1]?.getBoundingClientRect();
                  return {
                    vw, vh,
                    nav: {left: nr.left, right: nr.right, top: nr.top, bottom: nr.bottom, w: nr.width, h: nr.height},
                    chrome: {left: cr.left, right: cr.right, top: cr.top, bottom: cr.bottom},
                    firstBtn: first ? {top: first.top, bottom: first.bottom} : null,
                    lastBtn: last ? {top: last.top, bottom: last.bottom} : null,
                    navOverflowRight: nr.right > vw + 0.5,
                    navOverflowBottom: nr.bottom > vh + 0.5,
                    navOverflowTop: nr.top < -0.5,
                    chromeOverflowRight: cr.right > vw + 0.5,
                    btnCount: btns.length,
                  };
                }"""
            )
            issues = []
            if info["navOverflowRight"]:
                issues.append("nav-right")
            if info["navOverflowBottom"]:
                issues.append("nav-bottom")
            if info["navOverflowTop"]:
                issues.append("nav-top")
            if info["chromeOverflowRight"]:
                issues.append("chrome-right")
            nav = info["nav"]
            chrome = info["chrome"]
            print(
                f"{w}x{h}: nav H={nav['h']:.0f} issues={issues or 'ok'} "
                f"navR={nav['right']:.0f}/{info['vw']} chromeR={chrome['right']:.0f}"
            )
            if info["firstBtn"] and info["lastBtn"]:
                fb, lb = info["firstBtn"], info["lastBtn"]
                print(
                    f"  btns top={fb['top']:.0f} bottom={lb['bottom']:.0f} vh={info['vh']}"
                )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
