# Auditoría de fidelidad — PPTX desde HTML (captura raster)

## Resumen

| Campo | Valor |
|-------|-------|
| Fuente HTML | `index.html` (Bold Signal, `?export=1`) |
| PPTX | `../PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx` |
| Motor | Playwright PNG 1920×1080 + `python-pptx` (1 imagen full-bleed por slide) |
| Lienzo | **13.333" × 7.5"** (widescreen) |
| Diapositivas | 20 |
| Texto editable en slide | No (cada slide es una imagen); notas del orador sí editables |
| Notas del orador | Sí (`tools/defense_slides_manifest.py`) |
| Verificación entrega | `python tools/verify_pptx_delivery.py` → OK (~9 MB) |

> **Histórico:** `dom-to-pptx` (`export_defense_html_to_pptx.mjs`) se retiró: ~69 KB, tablas rotas, sin imágenes `file://`. No usar.

## Dump estructural (2026-05-24)

Extracción con skill `pptx-html-fidelity-audit`:

```powershell
python $env:USERPROFILE\.agents\skills\pptx-html-fidelity-audit\scripts\extract_pptx.py `
  docs\PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx `
  -o docs\presentacion-defensa-pfc\pptx_dump.json
```

**Resultado esperado:** 20 slides × 1 `PICTURE (13)` a (0, 0), 13.333×7.5 in, sin cajas de texto en el lienzo.

## Verificación geométrica (rails raster)

```powershell
python $env:USERPROFILE\.agents\skills\pptx-html-fidelity-audit\scripts\verify_layout.py `
  docs\PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx `
  --canvas-w 13.333 --canvas-h 7.5 --content-max-y 7.5
```

**Última ejecución:** 0 violations (20/20 imágenes a pantalla completa).

## Tabla de auditoría (contenido / percepción)

| Slide | Issue | Severity |
|-------|-------|----------|
| — | Estructura raster correcta (1 imagen/slide, 0 rail violations) | — |
| `asir_modules`, `asir_modules_2`, `budget` | Mucho espacio vacío bajo tablas en export antiguo (`justify-content: center`) | 🟠 → corregido en CSS `export-mode` |
| Global | Texto del slide no editable en PowerPoint | 🟢 (limitación documentada; ver `REVISION_ENTREGA.md`) |
| Global | PPTX editable alternativo: `generate_defense_pptx.py` (Corporate Blue) | 🟢 |

**Causas sistémicas (resueltas o documentadas):**

1. Confusión entre export dom-to-pptx (~69 KB) y raster (~9 MB) → `verify_pptx_delivery.py`.
2. Modo `?export=1` centraba verticalmente el bloque principal → tablas pequeñas con hueco inferior → `flex-start` + `max-height` mayor en tablas/diagramas.
3. Edición de copy en slide → solo vía `index.html` o generador Corporate Blue.

## Comparación visual pixel (HTML golden vs PowerPoint)

Ver [EXPORT_QA.md](EXPORT_QA.md) y [export_qa_gallery.html](export_qa_gallery.html).

Umbrales (antialiasing Chrome vs PowerPoint):

- Texto: ≥93.5%
- Portada/cierre: ≥91%
- Diagramas: ≥88%
- `evidence`: ≥82%

## Limitaciones conocidas

1. **Animaciones `reveal`**: solo estado final exportado.
2. **`evidence`**: mayor deriva por `dual-images--stack`.
3. **Fuentes Fontshare**: si falla la red en captura, sustitución en PowerPoint.
4. **Corporate Blue** (`PFC_Defensa_...pptx` sin `_html`): texto/tablas nativos, otro diseño.

## Regenerar

```powershell
python tools/run_defense_html_export.py
python tools/verify_pptx_delivery.py
```

Solo PPTX + notas:

```powershell
python tools/generate_defense_html.py
python tools/export_defense_html_to_pptx.py
python tools/attach_defense_speaker_notes.py
```
