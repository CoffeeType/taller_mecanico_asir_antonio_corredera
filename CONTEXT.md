# Glosario — Defensa PFC (presentación)

Vocabulario acordado para **entregables de la defensa** (HTML, PPTX, manifiesto). Sin detalles de implementación.

No define el dominio operativo del taller (citación, cita, roles de usuario, etc.); eso está en [docs/GUIA_USUARIO.md](docs/GUIA_USUARIO.md).

## presentacion_html

Deck web Bold Signal en `docs/presentacion-defensa-pfc/index.html`. Fuente de verdad de contenido y diseño para la defensa en vivo. El copy se edita aquí (modo edición con tecla **E**) o vía el manifiesto.

## capa_proyector

Perfil visual para 1280×720: tipografía ampliada (body y listas con poco contenido más grandes), contenido centrado, rejilla Swiss ligera, **9 diagramas Mermaid** en vivo (arquitectura, contexto/flujo reserva, perfiles/secuencia reserva, modelo ER + flujo en `data_model`, Docker Compose, JMeter, monitorización, AWS EC2) con `fitSvg`, diapositiva `asir_modules` con gráfico de barras ECharts del stack y `asir_modules_2` con Tabla 1 ASIR (**20 diapositivas**: portada `00` + contenido `01`–`19`). Capturas Grafana en PNG donde aplica. Validado con `tools/check_slide_count.py`, `tools/check_mermaid_diagrams.py`, `tools/check_asir_pie_chart.py`, `tools/check_slide_overlap.py`, `tools/check_slide_overflow.py`, `tools/check_slide_readability.py`, `tools/check_slide_centering.py` y `tools/check_slide_visual_fill.py`. Restaurar contrato: `python tools/restore_defense_presentation_contract.py`.

## modo_export

Vista `index.html?export=1`: tema claro, sin barra de navegación ni controles, animaciones `reveal` en estado final. Es lo que captura Playwright para generar el PPTX raster.

## manifiesto

`tools/defense_slides_manifest.py`: títulos, viñetas, tablas, notas del orador (~30 min) y metadatos compartidos por la presentación HTML y los dos PPTX.

## entregable_raster

`docs/PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx` (~9 MB): una imagen full-bleed por diapositiva, alineada con `modo_export`. Texto del slide no editable en PowerPoint; notas del orador sí. **Entregable principal para proyectar** si el tribunal acepta slides como imagen.

## entregable_editable

`docs/PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.pptx`: texto y tablas nativos en PowerPoint (diseño Corporate Blue, no Bold Signal). Mismo contenido que el manifiesto. **Usar solo si el centro exige PowerPoint editable** en el slide, no solo en notas.

## Entregable oficial (decisión 2026-05-24)

| Situación | Qué entregar |
|-----------|----------------|
| Defensa oral / proyección | `presentacion_html` (navegador; opcional `entregable_raster` si piden PowerPoint) |
| Copia para tribunal con edición en diapositiva | `entregable_editable` + nota de que la versión visual de referencia es el HTML |
| Cambiar copy o diseño Bold Signal | Editar `presentacion_html` → `python tools/run_defense_html_export.py` |

No se persigue un único PPTX que sea a la vez pixel-fiel al HTML Bold Signal y editable nativo; son dos pipelines distintos.

## digitalizacion_pyme

Modernización de procesos y datos en una pequeña empresa. En este PFC, el taller mecánico es el dominio de ejemplo para ilustrar esa transformación, no un producto comercial genérico.

## caso_taller

Alcance funcional acotado del negocio (citas, perfiles, administración) frente al alcance ASIR del proyecto (infraestructura reproducible, seguridad, cloud y observabilidad).
