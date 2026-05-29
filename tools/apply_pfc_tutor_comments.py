#!/usr/bin/env python3
"""Apply tutor review comments to unpacked PFC document.xml."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UNPACKED = REPO / "docs" / "_pfc_unpacked"
DOC_XML = UNPACKED / "word" / "document.xml"
RELS_XML = UNPACKED / "word" / "_rels" / "document.xml.rels"
GITHUB_URL = "https://github.com/CoffeeType/taller_mecanico_asir"

ABSTRACT = (
    "La memoria documenta el análisis, diseño, implantación y validación de una "
    "solución web orientada a la gestión de un taller mecánico. El trabajo se ha "
    "enfocado desde la perspectiva del ciclo de Administración de Sistemas "
    "Informáticos en Red, por lo que no se limita a describir la aplicación, sino "
    "que explica también la infraestructura, la seguridad, la observabilidad, el "
    "despliegue con contenedores y la propuesta de un entorno cloud."
)

DB_PARA = (
    "La base de datos almacena en un modelo relacional la información de usuarios, "
    "citas, noticias y consejos del taller. El modelo ER separa datos personales y "
    "credenciales para no mezclar el perfil y la autenticación; las citas admiten "
    "usuario registrado o invitado; noticias y consejos referencian al autor "
    "administrador por clave foránea. La implementación utiliza MySQL con tablas "
    "InnoDB, charset utf8mb4, integridad referencial y acceso vía PDO con consultas "
    "parametrizadas."
)

ARCH_PARA = (
    "La arquitectura se organiza alrededor de una aplicación PHP en Apache, una base "
    "de datos MySQL y servicios de observabilidad (Prometheus, Grafana, "
    "Alertmanager, exporters y probes). "
    "En entorno de desarrollo, Docker Compose local (docker-compose.yml) levanta "
    "todos los componentes en la misma máquina Windows o Linux para pruebas en "
    "localhost. "
    "En entorno de producción, una instancia EC2 ejecuta docker-compose.aws.yml con "
    "Security Groups, bootstrap automatizado y, opcionalmente, una AMI generada con "
    "Packer. "
    "Las interfaces de monitorización accesibles desde navegador dependen de "
    "MONITORING_UI_HOST_BIND (por ejemplo 0.0.0.0 en laboratorio), "
    "EXPORTER_HOST_BIND (127.0.0.1 para cAdvisor y Telegraf) y "
    "MONITORING_SG_CIDR para limitar el acceso en AWS."
)

TECH_CHOICE = (
    "En particular, dentro de la solución se han elegido las tecnologías descritas "
    "porque son software libre, constituyen estándares de facto en la industria "
    "(LAMP, Prometheus, Docker) y coinciden con el stack habitual en entornos "
    "profesionales de desarrollo. "
    "Como alternativas consideradas: PostgreSQL en lugar de MySQL; Nagios o Zabbix "
    "frente a Prometheus; WordPress con plugins frente a aplicación PHP propia; "
    "XAMPP frente a Docker Compose para reproducir el despliegue."
)

NETWORKS_PARA_EXTRA = (
    " La separación en dos redes Docker (aplicación y monitorización) reduce el "
    "acoplamiento: la red de aplicación concentra web y MySQL; la de monitorización "
    "agrupa Prometheus, Grafana y exporters. El contenedor web participa en ambas "
    "porque publica métricas y atiende peticiones, pero MySQL no queda expuesto a "
    "Internet. El simulador JMeter vive en la red de aplicación para golpear la web "
    "como un cliente real, sin mezclar su tráfico con la capa de administración de "
    "base de datos."
)

TLS_NOTE = (
    " En laboratorio se acepta HTTP en el puerto 80; en producción con "
    "autenticación conviene terminar HTTPS (puerto 443) mediante ALB con ACM, Caddy "
    "o un proxy inverso, porque las credenciales y cookies de sesión no deben "
    "viajar en claro (véase la mejora prioritaria en el apartado 8.3)."
)

    EIP_SECTION = """    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" w14:paraId="EIPHEAD01" w14:textId="77777777">
      <w:pPr><w:pStyle w:val="Ttulo3"/><w:spacing w:before="180" w:after="120"/></w:pPr>
      <w:r><w:t>5.4.2. Dirección IP elástica (Elastic IP)</w:t></w:r>
    </w:p>
    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" w14:paraId="EIPTEXT01" w14:textId="77777777">
      <w:pPr><w:spacing w:before="80" w:after="120"/></w:pPr>
      <w:r><w:t>La IPv4 pública asignada por defecto a una instancia EC2 cambia si se detiene y arranca de nuevo. Para el taller y para la defensa conviene asociar una Elastic IP: en la consola EC2, Elastic IPs → Asignar dirección → Asociar a la instancia. El coste es bajo mientras la IP esté asociada a una instancia en ejecución; si la instancia está parada, revisar la política de facturación de AWS. Así la URL de acceso al taller y a Grafana permanece estable entre reinicios.</w:t></w:r>
    </w:p>"""

VERSIONS_TABLE_ROWS = [
    ("PHP / Apache", "8.2 (imagen construida desde Dockerfile)"),
    ("MySQL", "8.0 (mysql:8.0)"),
    ("Prometheus", "v3.11.3"),
    ("Grafana", "13.0.1"),
    ("Alertmanager", "v0.32.1"),
    ("Node Exporter", "v1.11.1"),
    ("MySQL Exporter", "v0.19.0"),
    ("Blackbox Exporter", "v0.26.0"),
    ("cAdvisor", "0.56.2 (GHCR)"),
    ("Telegraf", "latest (solo desarrollo; fijar tag en producción)"),
]


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def para_text(text: str, style: str | None = None, spacing: bool = True) -> str:
    ppr = "<w:pPr>"
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if spacing:
        ppr += '<w:spacing w:before="80" w:after="120"/>'
    ppr += "</w:pPr>"
    return f"<w:p>{ppr}<w:r><w:t>{esc(text)}</w:t></w:r></w:p>"


def strip_comments(xml: str) -> str:
    xml = re.sub(r"<w:commentRangeStart w:id=\"[^\"]+\"/>\s*", "", xml)
    xml = re.sub(r"<w:commentRangeEnd w:id=\"[^\"]+\"/>\s*", "", xml)
    xml = re.sub(
        r"<w:r>\s*<w:rPr>[\s\S]*?<w:commentReference w:id=\"[^\"]+\"/>[\s\S]*?</w:r>\s*",
        "",
        xml,
    )
    return xml


def replace_once(xml: str, old: str, new: str, label: str) -> str:
    if old not in xml:
        print(f"WARN: not found [{label}]")
        return xml
    return xml.replace(old, new, 1)


def replace_all(xml: str, old: str, new: str, label: str) -> str:
    n = xml.count(old)
    if n == 0:
        print(f"WARN: not found [{label}]")
        return xml
    print(f"OK: {label} ({n}x)")
    return xml.replace(old, new)


def fix_portada_resumen(xml: str) -> str:
    # Remove abstract from cover (before page break to index)
    cover_abstract = (
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="7947CB6B" w14:textId="7A871B95">\n'
        "      <w:pPr>\n"
        '        <w:spacing w:before="80" w:after="120"/>\n'
        "      </w:pPr>\n"
        "      <w:r>\n"
        f"        <w:t>{esc(ABSTRACT)}</w:t>\n"
        "      </w:r>\n"
        "      \n"
        "      \n"
        "    </w:p>\n"
    )
    if cover_abstract not in xml:
        print("WARN: cover abstract block not found")
        return xml

    resumen_block = (
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="A1RESUMEN" w14:textId="77777777">\n'
        "      <w:r><w:br w:type=\"page\"/></w:r>\n"
        "    </w:p>\n"
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="B2RESUMEN" w14:textId="77777777">\n'
        '      <w:pPr><w:pStyle w:val="Ttulo1"/><w:jc w:val="center"/></w:pPr>\n'
        "      <w:r><w:rPr><w:b/><w:sz w:val=\"32\"/><w:szCs w:val=\"32\"/></w:rPr>"
        "<w:t>RESUMEN</w:t></w:r>\n"
        "    </w:p>\n"
        + para_text(ABSTRACT, spacing=True)
        + '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="C3RESUMEN" w14:textId="77777777">\n'
        "      <w:r><w:br w:type=\"page\"/></w:r>\n"
        "    </w:p>\n"
    )

    xml = xml.replace(cover_abstract, "", 1)
    # Insert resumen before ÍNDICE
    marker = (
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="70DF2D4A" w14:textId="77777777">\n'
        '      <w:pPr>\n        <w:pStyle w:val="Ttulo1"/>\n      </w:pPr>\n'
        '      <w:bookmarkStart w:name="_Toc230036828" w:id="1"/>\n'
        "      <w:r>\n        <w:t>ÍNDICE</w:t>\n"
    )
    if marker not in xml:
        print("WARN: ÍNDICE marker not found")
        return xml
    return xml.replace(marker, resumen_block + marker, 1)


def fix_db_paragraph(xml: str) -> str:
    pat = re.compile(
        r"<w:p[^>]*w14:paraId=\"0C50E2C5\"[^>]*>.*?</w:p>",
        re.DOTALL,
    )
    m = pat.search(xml)
    if not m:
        print("WARN: DB paragraph not found")
        return xml
    new_p = (
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="0C50E2C5" w14:textId="0532BA9C">\n'
        '      <w:pPr><w:spacing w:before="80" w:after="120"/></w:pPr>\n'
        f"      <w:r><w:t>{esc(DB_PARA)}</w:t></w:r>\n"
        "    </w:p>"
    )
    return xml[: m.start()] + new_p + xml[m.end() :]


def fix_architecture_paragraph(xml: str) -> str:
    pat = re.compile(
        r"<w:p[^>]*w14:paraId=\"59410B5D\"[^>]*>.*?</w:p>",
        re.DOTALL,
    )
    m = pat.search(xml)
    if not m:
        print("WARN: architecture paragraph not found")
        return xml
    new_p = (
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="59410B5D" w14:textId="2E6B58E4">\n'
        '      <w:pPr><w:spacing w:before="80" w:after="120"/></w:pPr>\n'
        f"      <w:r><w:t>{esc(ARCH_PARA)}</w:t></w:r>\n"
        "    </w:p>"
    )
    return xml[: m.start()] + new_p + xml[m.end() :]


def add_hyperlink_rel() -> None:
    rels = RELS_XML.read_text(encoding="utf-8")
    if "CoffeeType" in rels:
        return
    rels = rels.replace(
        "</Relationships>",
        f'  <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        f'Target="{GITHUB_URL}" TargetMode="External" Id="rId41"/>\n</Relationships>',
    )
    RELS_XML.write_text(rels, encoding="utf-8")


def github_link_xml() -> str:
    return (
        '<w:hyperlink r:id="rId41">'
        '<w:r><w:rPr><w:rStyle w:val="Hipervnculo"/></w:rPr>'
        f"<w:t>{esc(GITHUB_URL)}</w:t></w:r></w:hyperlink>"
    )


def main() -> int:
    if not DOC_XML.is_file():
        print(f"Missing {DOC_XML}", file=sys.stderr)
        return 1

    xml = DOC_XML.read_text(encoding="utf-8")
    print("Stripping comment markers...")
    xml = strip_comments(xml)

    print("Portada y resumen...")
    xml = fix_portada_resumen(xml)

    # Remove comment id 0 from portada title if still present
    xml = re.sub(
        r"<w:commentRangeStart w:id=\"0\"/>\s*",
        "",
        xml,
    )
    xml = re.sub(
        r"<w:commentRangeEnd w:id=\"0\"/>\s*<w:r>\s*<w:rPr>\s*"
        r"<w:rStyle w:val=\"CommentReference\"[^/]*/>\s*</w:rPr>\s*"
        r"<w:commentReference w:id=\"0\"/>\s*</w:r>\s*",
        "",
        xml,
    )

    replacements = [
        ("estimatorias ", "estimativas ", "estimatorias"),
        (
            "mediante PDO y consultas preparadas",
            "mediante PDO (PHP Data Objects) y consultas preparadas",
            "PDO extension",
        ),
        (
            "contraseñas almacenadas con bcrypt",
            "contraseñas almacenadas con el algoritmo bcrypt mediante password_hash y password_verify",
            "bcrypt detail",
        ),
        (
            "repositorio de GitHub en el que se basa nuestro proyecto ",
            "repositorio Git alojado en GitHub (",
            "github intro",
        ),
        (
            "incorpora mecanismos de observabilidad desde el inicio",
            "incorpora mecanismos de observabilidad desde el inicio",
            "observabilidad dup",
        ),
        (
            "El despliegue en AWS está totalmente automatizad ",
            "El despliegue en AWS está totalmente automatizado ",
            "automatizad typo",
        ),
        (
            "apoyandose en Packer",
            "apoyándose en Packer",
            "apoyandose",
        ),
        (
            "PHP ya que incorpora en ella en ella el perfil del usuario autenticado  ",
            "PHP, incorporando en la sesión el perfil del usuario autenticado (identificador, nombre de usuario y rol). ",
            "sesiones duplicado",
        ),
        (
            "En la instancia EC2 hay dos cosas distintas: Docker debe publicar el puerto",
            "Para acceder desde un navegador web a la aplicación desplegada en EC2, Docker debe publicar el puerto en el host (sección ports del compose) y, en paralelo,",
            "EC2 browser intro",
        ),
        (
            "Fuente: elaboración propia a partir del funcionamiento del contenedor traffic-simulator.",
            "Fuente: elaboración propia a partir del flujo de pruebas con Apache JMeter.",
            "fig24 source",
        ),
        (
            "En AWS se publican solo en loopback y se accede por túnel o proxy seguro.",
            "En AWS, con MONITORING_UI_HOST_BIND=0.0.0.0 del compose de ejemplo, las UIs quedan accesibles por IP pública y deben protegerse con Security Group (MONITORING_SG_CIDR) o proxy; con 127.0.0.1 solo loopback y túnel SSH.",
            "loopback 8.2",
        ),
        (
            "dentro del contenedor traffic-simulator.",
            "mediante el worker del perfil traffic de Docker Compose.",
            "jmeter container",
        ),
        (
            "primera version",
            "primera versión",
            "version tilde",
        ),
        (
            "unicamente",
            "únicamente",
            "unicamente",
        ),
        (
            "podria",
            "podría",
            "podria",
        ),
        (
            "inicar",
            "iniciar",
            "inicar",
        ),
        (
            "trafico",
            "tráfico",
            "trafico",
        ),
        (
            "La política de d",
            "La política de actualización de versiones fijadas en el proyecto contempla, entre otras, ",
            "version policy",
        ),
        (
            "e las nuevas versiones de la aplicación ",
            "",
            "version policy part2",
        ),
    ]
    for old, new, label in replacements:
        if old == new:
            continue
        xml = replace_all(xml, old, new, label)

    # Fix observabilidad duplicate (mecanismos de + observabilidad)
    xml = xml.replace(
        "incorpora mecanismos de observabilidad desde el inicio",
        "incorpora mecanismos de observabilidad desde el inicio",
    )
    # Was: mecanismos de observabilidad observabilidad - check
    xml = xml.replace(
        "mecanismos de observabilidad observabilidad ",
        "mecanismos de observabilidad ",
    )

    xml = replace_once(
        xml,
        "repositorio Git alojado en GitHub (",
        f"repositorio Git alojado en GitHub ({GITHUB_URL}) ",
        "github url",
    )

    # Tech choice paragraph after 2.3
    insert_after = (
        '      <w:r>\n        <w:t>.</w:t>\n      </w:r>\n    </w:p>\n'
        '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="1537F953"'
    )
    if insert_after in xml and "estándares de facto" not in xml:
        xml = xml.replace(
            insert_after,
            '      <w:r>\n        <w:t>.</w:t>\n      </w:r>\n    </w:p>\n'
            + para_text(TECH_CHOICE)
            + '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
            'w14:paraId="1537F953"',
            1,
        )

    print("Architecture & DB paragraphs...")
    xml = fix_architecture_paragraph(xml)
    xml = fix_db_paragraph(xml)

    # Networks 4.4 - append to paragraph before Figura 4 if not present
    if "red de monitorización) reduce" not in xml:
        xml = replace_once(
            xml,
            "funcionan unicamente a través de 127.0.0.1",
            "funcionan únicamente a través de 127.0.0.1",
            "unicamente networks",
        )
        xml = replace_once(
            xml,
            "porque solo los debe consultar Prometheus.</w:t>",
            "porque solo los debe consultar Prometheus."
            + esc(NETWORKS_PARA_EXTRA)
            + "</w:t>",
            "networks why",
        )

    if "mejora prioritaria en el apartado 8.3" not in xml:
        xml = replace_once(
            xml,
            "sin mezclar su tráfico con la capa de administración de base de datos.</w:t>",
            "sin mezclar su tráfico con la capa de administración de base de datos."
            + esc(TLS_NOTE)
            + "</w:t>",
            "tls note",
        )

    # EIP section before 5.5 (never inside an existing <w:p> — breaks Word)
    if "5.4.2. Dirección IP elástica" not in xml:
        marker = (
            '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
            'w14:paraId="380E75FF" w14:textId="77777777">\n'
            '      <w:pPr>\n        <w:pStyle w:val="Ttulo2"/>'
        )
        xml = replace_once(xml, marker, EIP_SECTION + "\n" + marker, "eip section")

    # Simulator why paragraph
    why_sim = (
        " Se ejecuta en la misma infraestructura para reproducir carga realista sobre la "
        "misma ruta de red que un cliente, registrar métricas con source=simulator en "
        "Grafana y evitar depender de un servicio de pruebas externo."
    )
    if "servicio de pruebas externo" not in xml:
        xml = replace_once(
            xml,
            "lo que permite diferenciarlas en Grafana.</w:t>",
            "lo que permite diferenciarlas en Grafana." + esc(why_sim) + "</w:t>",
            "simulator why",
        )

    versions_para = (
        "Versiones fijadas en el despliegue Docker de referencia: "
        + "; ".join(f"{a} {b}" for a, b in VERSIONS_TABLE_ROWS)
        + ". En producción no se recomienda usar la etiqueta latest salvo componentes "
        "acotados en laboratorio; conviene validar actualizaciones en un entorno de prueba."
    )
    if "Versiones fijadas en el despliegue" not in xml:
        xml = replace_once(
            xml,
            '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" w14:paraId="14BACEC7"',
            para_text(versions_para)
            + '    <w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" w14:paraId="14BACEC7"',
            "versions before table12",
        )

    xml = replace_all(
        xml,
        "<w:t>Persistencia de datos.</w:t>",
        "<w:t>Persistencia de datos (imagen mysql:8.0).</w:t>",
        "tabla13 mysql",
    )
    xml = replace_once(
        xml,
        "<w:t>Ejecución de la aplicación web.</w:t>",
        "<w:t>Ejecución de la aplicación web (PHP 8.2, Apache 2.4 en Dockerfile).</w:t>",
        "tabla13 php",
    )

    add_hyperlink_rel()

    # Fix cover image rels that break Word (missing image1b.png, absolute paths)
    rels_path = UNPACKED / "word" / "_rels" / "document.xml.rels"
    if rels_path.is_file():
        rels_text = rels_path.read_text(encoding="utf-8")
        rels_text = rels_text.replace('Target="/media/image19.png"', 'Target="media/image19.png"')
        rels_text = rels_text.replace('Target="/media/image1b.png"', 'Target="media/image5.png"')
        rels_path.write_text(rels_text, encoding="utf-8")

    xml = xml.replace("</w:drawing><w:t>.</w:t></w:r>", "</w:drawing></w:r>")
    bare_p = (
        '<w:p w:rsidR="00E6580A" w:rsidP="004A512A" w:rsidRDefault="00000000" '
        'w14:paraId="77777777" w14:textId="77777777">'
    )
    xml = xml.replace("<w:p>\n      <w:pPr>", f"{bare_p}\n      <w:pPr>")

    # Clear comments.xml entries
    for name, body in [
        (
            "comments.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
        ),
        (
            "commentsExtended.xml",
            '<?xml version="1.0" encoding="utf-8"?>'
            '<w15:commentsEx xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"/>',
        ),
    ]:
        p = UNPACKED / "word" / name
        if p.is_file():
            p.write_text(body, encoding="utf-8")

    DOC_XML.write_text(xml, encoding="utf-8")
    print(f"Written {DOC_XML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
