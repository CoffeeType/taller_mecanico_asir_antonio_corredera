# Documentación del proyecto

Índice de guías operativas en castellano. Glosario de dominio: [CONTEXT.md](../CONTEXT.md). Mapa del repositorio: [ESTRUCTURA_Y_HERRAMIENTAS.md](ESTRUCTURA_Y_HERRAMIENTAS.md).

## Convención Docker

Usa **`docker compose`** (V2) en los ejemplos de las guías. Los manifiestos del proyecto se llaman `docker-compose*.yml`.

## Instalación y despliegue

| Guía | Cuándo usarla |
|------|----------------|
| [INSTALL.md](INSTALL.md) | Instalación rápida sin Docker |
| [GUIA_DESPLIEGUE_LOCAL.md](GUIA_DESPLIEGUE_LOCAL.md) | XAMPP en Windows (paso a paso) |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker en local (recomendado) |
| [AWS_DOCKER_DEPLOYMENT.md](AWS_DOCKER_DEPLOYMENT.md) | EC2 + Docker Compose + `deploy_aws_docker.sh` (incl. JMeter en perfil `traffic`) |
| [COOLIFY_DEPLOYMENT.md](COOLIFY_DEPLOYMENT.md) | Plataforma Coolify |

## Uso y técnica

| Guía | Contenido |
|------|-----------|
| [GUIA_USUARIO.md](GUIA_USUARIO.md) | Visitantes, usuarios y administradores |
| [STACK_TECNOLOGICO.md](STACK_TECNOLOGICO.md) | Stack LAMP, Docker y dependencias |
| [MONITORING_SETUP_GUIDE.md](MONITORING_SETUP_GUIDE.md) | Prometheus, Grafana, Alertmanager |
| [MONITORING_CONTAINER_METRICS_RUNBOOK.md](MONITORING_CONTAINER_METRICS_RUNBOOK.md) | Métricas por contenedor (Telegraf/cAdvisor) |
| [GUIA_JMETER_USUARIO.md](GUIA_JMETER_USUARIO.md) | Pruebas de carga JMeter: interfaz web, controles y variables (nuevos operadores) |
| [TRAFFIC_SIMULATOR.md](TRAFFIC_SIMULATOR.md) | Apache JMeter — referencia técnica (API, CLI, volúmenes) |

## Entregables académicos (PFC)

En esta carpeta, sin versionar artefactos temporales de edición:

- `COPIAPFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_con_diagramas.docx` — memoria en Word (fuente maestra); parches automatizados con [`tools/update-pfc-docx.ps1`](../tools/update-pfc-docx.ps1).
- `COPIAPFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.pdf` — exportación PDF opcional (Word COM: [`tools/export-pfc-pdf.ps1`](../tools/export-pfc-pdf.ps1)).
- `PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.pptx` — presentación de defensa (PowerPoint, ~30 min, notas del orador, diseño **ppt-visual Corporate Blue** generado con `python-pptx`).
- `PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx` — **réplica visual del HTML** (Bold Signal): una imagen por diapositiva + notas del orador; ver [presentacion-defensa-pfc/FIDELITY_AUDIT.md](presentacion-defensa-pfc/FIDELITY_AUDIT.md).
- [`presentacion-defensa-pfc/index.html`](presentacion-defensa-pfc/index.html) — misma exposición en HTML (navegador, flechas/Espacio, tema claro/oscuro con el botón superior derecho o tecla **T**, edición con **E** y exportación **Ctrl+S**).
- `RUBRICA AVALUACIO PFC.xlsx` — criterios de evaluación (formal 20 %, exposición 30 %, contenidos 50 %).
- `Guia PFC 2020_21 revisada Marzo 2024.pdf`

### Regenerar las presentaciones de defensa

Desde la raíz del repositorio:

**PPTX Corporate Blue** (`python -m pip install python-pptx pillow`):

```powershell
cd tools
python extract_defense_assets.py
python generate_defense_pptx.py
python generate_defense_html.py
```

**PPTX fiel al HTML** (captura Playwright + `python-pptx`; requiere `playwright`, `python-pptx`, `pillow` y opcionalmente PowerPoint para QA visual):

```powershell
python tools/run_defense_html_export.py
```

Salida: `docs/PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx`, informe [EXPORT_QA.md](presentacion-defensa-pfc/EXPORT_QA.md), galería [export_qa_gallery.html](presentacion-defensa-pfc/export_qa_gallery.html).

El manifiesto compartido de diapositivas está en [`tools/defense_slides_manifest.py`](../tools/defense_slides_manifest.py) (guion Tabla 16 del COPIAPFC). Las imágenes se extraen del `.docx` a `docs/.pptx_gen_media/` y `docs/presentacion-defensa-pfc/assets/`.

**Abrir el HTML:** doble clic en `index.html` o, si las imágenes no cargan por restricciones del navegador, `python -m http.server 8080` en `docs/presentacion-defensa-pfc/` y visitar `http://localhost:8080/`.

## Histórico

- [CHANGELOG.md](CHANGELOG.md) — versiones del proyecto
- [adr/](adr/) — decisiones de arquitectura
