#!/usr/bin/env node
/**
 * DEPRECATED — dom-to-pptx rompe tablas/imágenes con file:// en este deck.
 * Usar: python tools/export_defense_html_to_pptx.py
 *
 * Export docs/presentacion-defensa-pfc/index.html → PPTX via dom-to-pptx.
 */

import { chromium } from "playwright";
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const repoRoot = path.resolve(__dirname, "..");
const htmlPath = path.join(
  repoRoot,
  "docs",
  "presentacion-defensa-pfc",
  "index.html"
);
const bundlePath = path.join(
  repoRoot,
  "node_modules",
  "dom-to-pptx",
  "dist",
  "dom-to-pptx.bundle.js"
);
const outPptx = path.join(
  repoRoot,
  "docs",
  "PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx"
);

if (!fs.existsSync(htmlPath)) {
  console.error(`No encontrado: ${htmlPath}`);
  console.error("Ejecuta: python tools/generate_defense_html.py");
  process.exit(1);
}
if (!fs.existsSync(bundlePath)) {
  console.error(`No encontrado: ${bundlePath}`);
  console.error("Ejecuta: npm install dom-to-pptx --save-dev");
  process.exit(1);
}

const htmlUrl = `${htmlPath.replace(/\\/g, "/")}?export=1`;
const fileUrl = htmlUrl.startsWith("/")
  ? `file://${htmlUrl}`
  : `file:///${htmlUrl}`;

async function main() {
  console.log(`Abriendo ${fileUrl}`);
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
  });

  await page.goto(fileUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__PFC_EXPORT_READY__ === true, {
    timeout: 60000,
  });
  await page.evaluate(async () => {
    await Promise.all(
      Array.from(document.images).map(
        (img) =>
          new Promise((resolve) => {
            if (img.complete) {
              resolve();
              return;
            }
            const done = () => resolve();
            img.addEventListener("load", done, { once: true });
            img.addEventListener("error", done, { once: true });
            setTimeout(done, 5000);
          })
      )
    );
  });

  await page.addScriptTag({ path: bundlePath });

  const slideCount = await page.evaluate(
    () => document.querySelectorAll(".slide").length
  );
  console.log(`Exportando ${slideCount} diapositivas con dom-to-pptx…`);

  const base64 = await page.evaluate(async () => {
    const slides = Array.from(document.querySelectorAll(".slide"));
    if (!slides.length) {
      throw new Error("No .slide elements found");
    }
    const lib = window.domToPptx || window.dom_to_pptx;
    if (!lib || typeof lib.exportToPptx !== "function") {
      throw new Error("dom-to-pptx bundle not loaded");
    }
    const blob = await lib.exportToPptx(slides, {
      fileName: "defense.pptx",
      layout: "LAYOUT_16x9",
      autoEmbedFonts: true,
    });
    const buf = await blob.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  });

  await browser.close();

  const buffer = Buffer.from(base64, "base64");
  fs.mkdirSync(path.dirname(outPptx), { recursive: true });
  fs.writeFileSync(outPptx, buffer);
  console.log(`Guardado: ${outPptx} (${(buffer.length / 1024).toFixed(1)} KB)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
