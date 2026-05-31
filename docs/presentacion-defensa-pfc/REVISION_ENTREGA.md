# Revisión de entrega — Presentación HTML (defensa en vivo)

**Fecha de revisión:** 2026-05-28 — contrato restaurado (20 diapositivas: portada `00` + contenido `01`–`19`; `asir_modules` con gráfico de barras + `asir_modules_2` con Tabla 1).

**Entregable principal:** abrir [`index.html`](index.html) en el navegador (proyector). No hace falta generar PPTX salvo que el tribunal lo exija por escrito.

## Cómo saber que tienes el fichero correcto

| Señal | PPTX válido (`*_html.pptx`) | PPTX roto (dom-to-pptx, obsoleto) |
|--------|-----------------------------|-----------------------------------|
| Tamaño | **~9 MB** (9000+ KB) | **~69 KB** |
| Contenido en PowerPoint | Una **imagen** por diapositiva, texto legible | Cajas sueltas, **sin diagramas**, tablas rotas |
| Verificación | `python tools/verify_pptx_delivery.py` → OK | Falla por tamaño < 2 MB |

**Ruta:** `docs/PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx`

## Qué contiene (revisión manual + automática)

- **20/20** diapositivas con imagen 1920×1080 embebida a pantalla completa.
- **20/20** notas del orador (guion ~30 min del manifiesto).
- Capturas revisadas: portada, timeline, tablas ASIR, arquitectura, evidencias (Fig. 22 + docker ps), etc.
- Comparación golden HTML vs export PowerPoint: ver [EXPORT_QA.md](EXPORT_QA.md).

## Limitaciones (importante para el tribunal)

1. **No es editable el texto del slide** — cada diapositiva es una imagen. Para cambiar copy o diseño, edita `index.html` y vuelve a ejecutar `python tools/run_defense_html_export.py`.
2. **No es pixel-idéntico al navegador en vivo** — es la vista `?export=1` (tema claro, sin barra de navegación).
3. Si el tribunal exige **PowerPoint editable** con tablas nativas, usa `PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.pptx` (Corporate Blue, generado con `tools/generate_defense_pptx.py`). Regenerar:
   ```powershell
   python tools/extract_defense_assets.py
   python tools/generate_defense_pptx.py
   ```
   Glosario y criterio de entrega: [`CONTEXT.md`](../../CONTEXT.md) en la raíz del repo.

## Presentación HTML en un solo fichero

`index.html` lleva las figuras (`assets/*.png`) incrustadas en **data URI** para poder copiarlo al escritorio o a un USB sin la carpeta `assets/`. Si sustituyes imágenes en `assets/`, vuelve a incrustar:

```powershell
python tools/embed_defense_html_assets.py
```

### Descargar desde GitHub (icono “Download raw file”)

Antes de descargar, comprueba en GitHub el **tamaño** del fichero en la vista del archivo:

| Tamaño en GitHub | ¿Vale para un solo `.html`? |
|------------------|----------------------------|
| **~800 KB** (819 000 bytes aprox.) | Sí — imágenes incrustadas |
| **~60 KB** (61 000 bytes aprox.) | No — sigue pidiendo la carpeta `assets/` y las fotos no se verán |

Si en GitHub sigue saliendo ~60 KB, el commit con las imágenes dentro **aún no está en el remoto**. Sube los cambios y vuelve a descargar:

```powershell
git push origin main
```

En tu PC, la copia buena está en `docs/presentacion-defensa-pfc/index.html` (~800 KB) aunque GitHub aún muestre la antigua.

## Regenerar y comprobar

```powershell
python tools/run_defense_html_export.py
python tools/verify_pptx_delivery.py
```

Galería visual lado a lado: abre [export_qa_gallery.html](export_qa_gallery.html) en el navegador.

## Conclusión de la revisión

El pipeline **dom-to-pptx** se retiró: no incrustaba imágenes locales y destruía tablas. El entregable actual por **captura raster** es coherente con el HTML en modo exportación. Si al abrir en PowerPoint sigues viendo diapositivas vacías, casi seguro es el fichero pequeño (~69 KB) o una copia en caché — cierra PowerPoint, vuelve a generar y abre el de **~9 MB**.
