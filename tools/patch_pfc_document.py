#!/usr/bin/env python3
"""Apply planned content updates to unpacked PFC document.xml."""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/_pfc_con_cambios_edit/word/document.xml"

# (old, new) — exact match on full <w:t> text or substring replacements
TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "Se ha desplegado una utilidad para realizar simulaciones en la propia infraestructura, en la red que correspondiente al simulador que se ha separado de la aplicación principal para evitar que una herramienta de pruebas forme parte del panel de administración. Con el perfil traffic, Docker Compose inicia un worker con API HTTP interna y una UI independiente. La UI actúa como proxy server-side y no expone el token de control al navegador ya que cualquiera que tuviera el token podría utilizar el simulador de tráfico a su antojo y podría iniciar pruebas, pararlas y vigilar el tráfico. Las métricas del simulador se escriben en el mismo formato que la aplicación, identificadas con source=simulator, lo que permite diferenciarlas en Grafana. Se ejecuta en la misma infraestructura para reproducir carga realista sobre la misma ruta de red que un cliente, registrar métricas con source=simulator en Grafana y evitar depender de un servicio de pruebas externo.",
        "El proyecto incluye pruebas de carga con Apache JMeter en contenedores Docker (perfil traffic), separadas del panel de administración del taller. Un worker ejecuta JMeter en línea de comandos y una interfaz web independiente (puerto 8890 por defecto) permite lanzar y vigilar cada ejecución de carga sin exponer el token de control al navegador. Las métricas del tráfico simulado se registran en el mismo formato que el tráfico real de la aplicación, con la etiqueta source=simulator, de modo que Grafana y Prometheus pueden distinguir ambos tipos de uso. La guía paso a paso para operadores está en docs/GUIA_JMETER_USUARIO.md; el detalle técnico, en docs/TRAFFIC_SIMULATOR.md.",
    ),
    (
        "1) Acceder a la interfaz web del simulador en el equipo host (puerto 8890 por defecto; variables TRAFFIC_SIMULATOR_UI_PORT en desarrollo local con docker-compose.yml y TRAFFIC_SIMULATOR_UI_HOST_PORT en EC2).",
        "1) Abrir la interfaz web del simulador en el equipo host (puerto 8890 por defecto en local; en EC2, el puerto publicado en el Security Group).",
    ),
    (
        "6) Observabilidad: abrir Grafana (perfil monitoring), el dashboard principal y la fila Simulador para las series con source=simulator. El tráfico sintético utiliza el mismo recorrido que el tráfico real (métricas expuestas vía metrics.php, Prometheus y Grafana), diferenciado por la etiqueta source respecto de source=app.",
        "6) Observabilidad: en Grafana (perfil monitoring), revisar el dashboard principal y la fila Simulador (source=simulator frente a source=app). Cada ejecución de carga queda identificada con un run_id y el sitio probado con target_host, de forma que la propia interfaz y los paneles pueden filtrar solo la prueba en curso o un destino concreto.",
    ),
    (
        "JMeter escribe los resultados en results.jtl. El runner del proyecto lee ese fichero y lo convierte al formato que ya entiende metrics.php: logs/metrics.log recibe líneas como GET 200 /ruta source=simulator y logs/response_time.log recibe tiempos de respuesta. Así Grafana puede separar el tráfico real de la aplicación, source=app, del tráfico de prueba, source=simulator.",
        "JMeter escribe los resultados en results.jtl. El runner del proyecto importa ese fichero a logs/metrics.log (por ejemplo GET 200 /ruta source=simulator target_host=host run_id=identificador) y a logs/response_time.log (tiempos con las mismas etiquetas). Así se separa el tráfico real (source=app) del simulado y, dentro de este, cada ejecución de carga y cada objetivo de prueba.",
    ),
    (
        "La arquitectura se organiza alrededor de una aplicación PHP en Apache, una base de datos MySQL y servicios de observabilidad (Prometheus, Grafana, Alertmanager, exporters y probes). En entorno de desarrollo, Docker Compose local (docker-compose.yml) levanta todos los componentes en la misma máquina Windows o Linux para pruebas en localhost. En entorno de producción, una instancia EC2 ejecuta docker-compose.aws.yml con Security Groups, bootstrap automatizado y, opcionalmente, una AMI generada con Packer. Las interfaces de monitorización accesibles desde navegador dependen de MONITORING_UI_HOST_BIND (por ejemplo 0.0.0.0 en laboratorio), EXPORTER_HOST_BIND (127.0.0.1 para cAdvisor y Telegraf) y MONITORING_SG_CIDR para limitar el acceso en AWS.",
        "La arquitectura se organiza alrededor de una aplicación PHP en Apache, una base de datos MySQL y servicios de observabilidad (Prometheus, Grafana, Alertmanager, exporters y probes). En desarrollo, Docker Compose local (docker-compose.yml) levanta todos los componentes en la misma máquina para pruebas en localhost. En producción, una instancia EC2 ejecuta docker-compose.aws.yml con Security Groups, bootstrap automatizado y, opcionalmente, una AMI generada con Packer. Las pantallas de monitorización (Grafana, Prometheus, Alertmanager y la UI de JMeter) se publican para acceso desde navegador en laboratorio; en AWS, el acceso debe limitarse con el Security Group a la IP del administrador, no abrir los puertos a todo Internet.",
    ),
    (
        "Para producción se propone usar una instancia EC2 con Docker Compose y volúmenes persistentes. El fichero docker-compose.aws.yml evita montar todo el código como bind-mount, como se nombró anteriormente no publica MySQL y separa los servicios por perfiles: web y mysql como base, monitoring para Prometheus/Grafana/Alertmanager/exporters, y traffic para Apache JMeter y su UI. En la configuración AWS actual, las UIs de monitorización se publican para navegador mediante MONITORING_UI_HOST_BIND=0.0.0.0; por eso la protección real debe estar en el Security Group, usando MONITORING_SG_CIDR con la IP administrativa en vez de abrir 0.0.0.0/0 en producción.",
        "Para producción se propone una instancia EC2 con Docker Compose y volúmenes persistentes. El fichero docker-compose.aws.yml no monta todo el código como en desarrollo, no publica MySQL hacia Internet y agrupa servicios por perfiles: web y mysql (aplicación), monitoring (observabilidad) y traffic (JMeter y su interfaz). Las pantallas de monitorización quedan accesibles desde el navegador en el laboratorio; en producción, la protección efectiva debe estar en el Security Group (solo la IP del administrador), no en abrir los puertos a cualquier origen.",
    ),
    (
        "El despliegue en AWS está totalmente automatizado apoyándose en Packer. Este se encarga de construir una imagen de máquina de amazon (AMI) para base con Docker Engine y plugin Compose, y en &#x201C;scripts/ec2-user-data-bootstrap.sh&#x201D; para Amazon Linux 2023. El bootstrap instala Docker, Compose y Buildx, crea swap, clona el repositorio en &#x201C;/opt/taller_mecanico_asir&#x201D;, genera secretos cuando detecta valores de ejemplo y ejecuta scripts/deploy_aws_docker.sh. El script de despliegue realiza preflight de rutas, memoria y disco, backup opcional de MySQL, build/pull/up del compose, comprobaciones de salud y smoke tests de HTTP, Grafana, Prometheus, Alertmanager y JMeter cuando el perfil traffic está activo.",
        "El despliegue en AWS está automatizado. Packer puede generar una AMI base con Docker Engine y el plugin de Compose. En Amazon Linux 2023, el script ec2-user-data-bootstrap.sh instala Docker, Compose y Buildx, crea memoria de intercambio (swap), clona el repositorio en /opt/taller_mecanico_asir y lanza deploy_aws_docker.sh. Ese script comprueba disco y memoria, hace copia de seguridad opcional de MySQL, construye y levanta el stack, y valida la salud de la web, Grafana, Prometheus, Alertmanager y la UI de JMeter cuando el perfil de carga está activo.",
    ),
    (
        "La observabilidad combina métricas generadas por la aplicación, exporters del sistema y probes sintéticos que sirven para validar errores HTTP, disponibilidad de rutas, latencia y comportamiento bajo carga.. El endpoint metrics.php expone métricas de negocio, salud de la base de datos, peticiones HTTP y tiempos de respuesta. Prometheus las recoge periódicamente, evalúa reglas de alerta y Grafana las presenta en paneles.",
        "La observabilidad combina métricas de la aplicación, exporters del sistema (Node, MySQL, contenedores) y comprobaciones HTTP externas (blackbox). El endpoint metrics.php expone métricas de negocio, salud de la base de datos, peticiones HTTP y tiempos de respuesta. Prometheus las recoge periódicamente, evalúa reglas de alerta y Grafana las presenta en paneles. En el stack local se usan, entre otras, Prometheus v3.11.3, Grafana 13.0.1, Alertmanager v0.32.0, Node Exporter, MySQL Exporter, cAdvisor y Telegraf.",
    ),
    (
        "El simulador de tráfico se prueba con cargas breves, verificando que las líneas aparecen en logs/metrics.log y que Grafana diferencia source=app de ",
        "Las pruebas de carga se validan con ejecuciones breves: deben aparecer líneas con source=simulator en logs/metrics.log (con run_id y target_host cuando corresponda), el volumen logs compartido entre web y simulador, y en Grafana la fila Simulador filtrando source=simulator frente a ",
    ),
    (
        "source=simulator. Este punto es relevante porque permite demostrar observabilidad bajo tráfico generado sin alterar el código de la aplicación.",
        "source=app. Así se demuestra observabilidad bajo tráfico generado sin modificar la lógica de negocio de la aplicación.",
    ),
    (
        "Respecto al CI/CD con GitHub Actions, los workflows de verificación de builds añadían coste de mantenimiento (imágenes base, Buildx en runners, secretos para despliegue) y fallos intermitentes por red o límites de tiempo. Se ha ",
        "En cuanto a integración continua, los workflows de GitHub Actions que existieron en el repositorio añadían coste de mantenimiento (imágenes base, Buildx en runners, secretos) y fallos intermitentes. Se ",
    ),
    (
        "retirado la integración con GitHub Actions; la comprobación de imágenes pasa a hacerse en local con docker compose build.",
        "retiró esa integración; la comprobación de imágenes y del stack se hace en local con docker compose build y los scripts de verificación del repositorio.",
    ),
    (
        "Automatizar CI/CD con GitHub Actions",
        "Automatizar comprobaciones de build (pipeline externo o runner propio)",
    ),
    (
        "En AWS, con MONITORING_UI_HOST_BIND=0.0.0.0 del compose de ejemplo, las UIs quedan accesibles por IP pública y deben protegerse con Security Group (MONITORING_SG_CIDR) o proxy; con 127.0.0.1 solo loopback y túnel SSH.",
        "En AWS, si las UIs de monitorización se publican en todas las interfaces de red del servidor, quedan alcanzables por IP pública y deben protegerse con Security Group (solo la IP del administrador) o con un proxy y túnel SSH.",
    ),
    (
        "La documentación se reparte en README.md y docs. Las guías más importantes para operación son DOCKER_DEPLOYMENT.md para local, AWS_DOCKER_DEPLOYMENT.md para EC2, MONITORING_SETUP_GUIDE.md para observabilidad y TRAFFIC_SIMULATOR.md para JMeter. Los ficheros docker-",
        "La documentación se reparte en README.md y docs. Las guías principales son DOCKER_DEPLOYMENT.md (local), AWS_DOCKER_DEPLOYMENT.md (EC2), MONITORING_SETUP_GUIDE.md (observabilidad), GUIA_JMETER_USUARIO.md (operador de pruebas de carga) y TRAFFIC_SIMULATOR.md (referencia técnica JMeter). Los ficheros docker-",
    ),
    (
        "Documentación interna: README.md, docs/DOCKER_DEPLOYMENT.md, docs/AWS_DOCKER_DEPLOYMENT.md, docs/MONITORING_SETUP_GUIDE.md y docs/TRAFFIC_SIMULATOR.md.",
        "Documentación interna: README.md, docs/DOCKER_DEPLOYMENT.md, docs/AWS_DOCKER_DEPLOYMENT.md, docs/MONITORING_SETUP_GUIDE.md, docs/GUIA_JMETER_USUARIO.md, docs/TRAFFIC_SIMULATOR.md y decisiones de arquitectura en docs/adr/ (0001–0003: métricas JMeter, etiqueta source y run_id/target_host).",
    ),
    (
        "Documentación del simulador de tráfico y su UI separada.",
        "Referencia técnica del simulador JMeter y su API interna.",
    ),
    (
        "4.3. Flujo de reserva de cita",
        "4.3. Flujo de citación",
    ),
    (
        "4.3. Caso de uso: reserva de cita",
        "4.3. Caso de uso: citación",
    ),
    (
        "Figura 3. Flujo de reserva de cita desde la interfaz web.",
        "Figura 3. Flujo de citación desde la interfaz web.",
    ),
    (
        "La reserva de citas se puede validar de diferentes formas:",
        "La citación (solicitud de cita) se puede validar de diferentes formas:",
    ),
    (
        "5.6. Simulador de tráfico",
        "5.6. Pruebas de carga (Apache JMeter)",
    ),
    (
        "Cuando el operador inicia una prueba desde la UI, la UI no llama directamente a JMeter. Primero envía la petición al API interno del worker, protegido por SIMULATOR_CONTROL_TOKEN. El worker genera un plan traffic-test.jmx, un fichero routes.csv con las rutas y pesos, ejecuta jmeter -n -t traffic-test.jmx -l results.jtl -j jmeter.log, y guarda también stdout.log para diagnóstico.",
        "Cuando el operador pulsa iniciar prueba, la interfaz no ejecuta JMeter directamente: llama al API interno del worker, protegido por un token de control en el servidor. El worker genera el plan de prueba, las rutas con sus pesos, ejecuta JMeter en modo no gráfico y guarda los registros de salida para diagnóstico.",
    ),
    (
        "Figura 24. Funcionamiento del simulador Apache JMeter dentro del proyecto.",
        "Figura 24. Funcionamiento de las pruebas de carga con Apache JMeter.",
    ),
    (
        "Fuente: elaboración propia a partir del flujo de pruebas con Apache JMeter.",
        "Fuente: elaboración propia. Incluye importación de resultados JTL a logs compartidos (metrics.log y response_time.log) con etiquetas source, run_id y target_host.",
    ),
]

ANNEX_ROWS = """
      <w:tr w:rsidR="00E6580A" w14:paraId="PFCJM01" w14:textId="77777777">
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="3300" w:type="dxa"/>
            <w:tcBorders>
              <w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
            <w:tcMar>
              <w:top w:w="90" w:type="dxa"/>
              <w:left w:w="120" w:type="dxa"/>
              <w:bottom w:w="90" w:type="dxa"/>
              <w:right w:w="120" w:type="dxa"/>
            </w:tcMar>
          </w:tcPr>
          <w:p w14:paraId="PFCJM02" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
            <w:pPr><w:spacing w:before="40" w:after="80"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>docs/GUIA_JMETER_USUARIO.md</w:t></w:r>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="5204" w:type="dxa"/>
            <w:tcBorders>
              <w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
            <w:tcMar>
              <w:top w:w="90" w:type="dxa"/>
              <w:left w:w="120" w:type="dxa"/>
              <w:bottom w:w="90" w:type="dxa"/>
              <w:right w:w="120" w:type="dxa"/>
            </w:tcMar>
          </w:tcPr>
          <w:p w14:paraId="PFCJM03" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
            <w:pPr><w:spacing w:before="40" w:after="80"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>Guía de usuario para operadores de pruebas de carga (interfaz web JMeter).</w:t></w:r>
          </w:p>
        </w:tc>
      </w:tr>
      <w:tr w:rsidR="00E6580A" w14:paraId="PFCADR1" w14:textId="77777777">
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="3300" w:type="dxa"/>
            <w:tcBorders>
              <w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
            <w:tcMar>
              <w:top w:w="90" w:type="dxa"/>
              <w:left w:w="120" w:type="dxa"/>
              <w:bottom w:w="90" w:type="dxa"/>
              <w:right w:w="120" w:type="dxa"/>
            </w:tcMar>
          </w:tcPr>
          <w:p w14:paraId="PFCADR2" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
            <w:pPr><w:spacing w:before="40" w:after="80"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>docs/adr/0001–0003</w:t></w:r>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="5204" w:type="dxa"/>
            <w:tcBorders>
              <w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
              <w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
            <w:tcMar>
              <w:top w:w="90" w:type="dxa"/>
              <w:left w:w="120" w:type="dxa"/>
              <w:bottom w:w="90" w:type="dxa"/>
              <w:right w:w="120" w:type="dxa"/>
            </w:tcMar>
          </w:tcPr>
          <w:p w14:paraId="PFCADR3" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
            <w:pPr><w:spacing w:before="40" w:after="80"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>Decisiones de arquitectura: pipeline de logs JMeter, etiqueta source y run_id/target_host.</w:t></w:r>
          </w:p>
        </w:tc>
      </w:tr>
"""

COVER_REPO_PARA = """
    <w:p w14:paraId="PFCCOVER01" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
      <w:pPr>
        <w:spacing w:before="200" w:after="280"/>
        <w:jc w:val="center"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:sz w:val="22"/>
          <w:szCs w:val="22"/>
        </w:rPr>
        <w:t>Repositorio público (Git / GitHub):</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="PFCCOVER02" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
      <w:pPr>
        <w:spacing w:before="0" w:after="400"/>
        <w:jc w:val="center"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:color w:val="0563C1"/>
          <w:sz w:val="22"/>
          <w:szCs w:val="22"/>
        </w:rPr>
        <w:t>https://github.com/CoffeeType/taller_mecanico_asir</w:t>
      </w:r>
    </w:p>
"""

FIGURE_LEGEND_NOTE = (
    "Nota: en los diagramas de arquitectura, los actores (visitante, usuario registrado, administrador) "
    "se representan a la izquierda y la base de datos a la derecha, siguiendo el flujo de peticiones HTTP."
)


def add_spacing_to_body_paragraphs(xml: str) -> str:
    """Add spacing to body paragraphs with text but no w:spacing in pPr."""

    def fix_para(match: re.Match[str]) -> str:
        full = match.group(0)
        if "w:spacing" in full[:400]:
            return full
        if "<w:pStyle" in full and any(
            s in full for s in ("Ttulo", "TDC", "TOC", "Title", "Heading")
        ):
            return full
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)", full))
        if len(text) < 60:
            return full
        if "<w:tbl>" in full or "</w:tc>" in full:
            return full
        # insert spacing after <w:pPr> or create pPr
        if "<w:pPr>" in full:
            return full.replace(
                "<w:pPr>",
                '<w:pPr><w:spacing w:before="80" w:after="120"/>',
                1,
            )
        return full.replace(
            "<w:p ",
            '<w:p w:spacingFix="1" ',
            1,
        ).replace(
            "<w:p w:spacingFix=",
            "<w:p ",
            1,
        ).replace(
            ">",
            "><w:pPr><w:spacing w:before=\"80\" w:after=\"120\"/></w:pPr>",
            1,
        )

    # Only fix paragraphs in body section (after first RESUMEN block) — conservative: fix known paraIds without spacing
    para_ids_no_spacing = [
        "62B00641",
        "15ECD38B",
        "397C2C80",
    ]
    for pid in para_ids_no_spacing:
        pattern = rf'(<w:p w14:paraId="{pid}"[^>]*>)(\s*<w:r>)'
        xml = re.sub(
            pattern,
            r'\1<w:pPr><w:spacing w:before="80" w:after="120"/></w:pPr>\2',
            xml,
            count=1,
        )
    return xml


def main() -> int:
    xml = DOC.read_text(encoding="utf-8")
    original_len = len(xml)
    missing: list[str] = []

    for old, new in TEXT_REPLACEMENTS:
        if old not in xml:
            missing.append(old[:80] + "...")
        else:
            xml = xml.replace(old, new, 1)

    if missing:
        print("WARNING: missing replacements:", len(missing))
        for m in missing[:10]:
            print(" -", m)

    # Insert annex rows after TRAFFIC_SIMULATOR row (first occurrence in annex table)
    marker = "<w:t>docs/TRAFFIC_SIMULATOR.md</w:t>"
    if marker in xml and "docs/GUIA_JMETER_USUARIO.md" not in xml:
        idx = xml.find(marker)
        end_tr = xml.find("</w:tr>", idx)
        if end_tr > 0:
            xml = xml[: end_tr + len("</w:tr>")] + ANNEX_ROWS + xml[end_tr + len("</w:tr>") :]

    # Cover: repo link before page break to RESUMEN (after tutor line)
    tutor_marker = "<w:t>Tutor/a individual: Hueso Pastor, Francisco Alfonso</w:t>"
    if tutor_marker in xml and "PFCCOVER01" not in xml:
        pos = xml.find(tutor_marker)
        close_p = xml.find("</w:p>", pos)
        if close_p > 0:
            xml = xml[: close_p + len("</w:p>")] + COVER_REPO_PARA + xml[close_p + len("</w:p>") :]

    # Figure note after Figura 1 caption (first body occurrence after index)
    fig1 = "Figura 1. Arquitectura general del sistema web y servicios de observabilidad."
    if fig1 in xml and FIGURE_LEGEND_NOTE[:30] not in xml:
        idx = xml.find(fig1, 50000)  # skip TOC
        if idx < 0:
            idx = xml.find(fig1)
        close_p = xml.find("</w:p>", idx)
        note_para = f"""
    <w:p w14:paraId="PFCFIGNOTE" w14:textId="77777777" w:rsidR="00E6580A" w:rsidRDefault="00000000" w:rsidP="004A512A">
      <w:pPr><w:spacing w:before="40" w:after="120"/><w:rPr><w:i/></w:rPr></w:pPr>
      <w:r><w:rPr><w:i/></w:rPr><w:t>{FIGURE_LEGEND_NOTE}</w:t></w:r>
    </w:p>"""
        if close_p > 0:
            xml = xml[: close_p + len("</w:p>")] + note_para + xml[close_p + len("</w:p>") :]

    xml = add_spacing_to_body_paragraphs(xml)

    DOC.write_text(xml, encoding="utf-8")
    print(f"Patched {DOC.name}: {original_len} -> {len(xml)} bytes")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
