"""

Manifiesto único de diapositivas para la defensa PFC (COPIAPFC §7.4 Tabla 16).

Consumido por generate_defense_pptx.py y como referencia para index.html.

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Literal



Layout = Literal[

    "title",

    "content",

    "table",

    "picture",

    "two_picture",

    "timeline",

]



VisualPattern = Literal[

    "title_slide",

    "timeline",

    "content_accent",

    "table_styled",

    "diagram_stack",

    "dual_images",

    "data_highlight",

    "closing_statement",

]



COPIAPFC_NAME = "COPIAPFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_con_diagramas.docx"

OUTPUT_PPTX = "PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.pptx"
OUTPUT_PPTX_FROM_HTML = (
    "PFC_Defensa_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells_html.pptx"
)



TITLE_MAIN = (

    "Implantación y monitorización de un sistema web\n"

    "para la gestión de un taller mecánico"

)



COVER_SUBTITLE = [

    "Proyecto final de ciclo — CFGS Administración de Sistemas Informáticos en Red",

    "Autor: Antonio Corredera Cubells",

    "Curso académico: 2025/2026",

    "Centro docente: IES Camp de Morvedre",

    "Tutor/a individual: Hueso Pastor, Francisco Alfonso",

]



KEY_IMAGES = (

    "image1.png",

    "image2.png",

    "image3.png",

    "image4.png",

    "image19.png",

    "image20.png",

)





@dataclass

class DefenseSlide:

    id: str

    layout: Layout

    title: str

    visual_pattern: VisualPattern = "content_accent"

    bullets: list[str] = field(default_factory=list)

    notes: str = ""

    image: str | None = None

    image_right: str | None = None

    table_headers: list[str] = field(default_factory=list)

    table_rows: list[list[str]] = field(default_factory=list)

    picture_width_in: float = 12.0

    picture_left_in: float = 0.45

    picture_top_in: float = 1.25

    html_class: str = ""





SLIDES: list[DefenseSlide] = [

    DefenseSlide(

        id="cover",

        layout="picture",

        visual_pattern="title_slide",

        title=TITLE_MAIN,

        image="portada-presentacion-qr.png",

        bullets=COVER_SUBTITLE,

        notes=(

            "0:00–0:30. Saludo, nombre y título. Una frase: aplicación web LAMP, contenedores, "

            "despliegue AWS y observabilidad Prometheus/Grafana. No leer la portada."

        ),

        html_class="title-slide title-slide--cover-image",

    ),

    DefenseSlide(

        id="timeline",

        layout="timeline",

        visual_pattern="timeline",

        title="Mapa de la exposición (30 min) — Tabla 16",

        table_headers=["Minutos", "Contenido", "Evidencia"],

        table_rows=[

            ["0–5", "Contexto, objetivos y módulos ASIR", "Portada, intro, tabla módulos"],

            ["5–12", "App: login, citas, noticias, administración", "Navegador — flujos principales"],

            ["12–18", "Docker, BD, volúmenes y redes", "docker compose ps, esquema"],

            ["18–24", "Prometheus, Grafana y simulador", "Dashboards y carga sintética"],

            ["24–28", "AWS, seguridad y presupuesto", "Diagrama despliegue y costes"],

            ["28–30", "Conclusiones, mejoras y preguntas", "Tabla objetivos y cierre"],

        ],

        notes=(

            "0:30–1:15. Anuncia el guion completo (memoria §7.4). Indica demos en navegador, "

            "terminal y Grafana. Reserva margen final para preguntas (rúbrica: exposición oral)."

        ),

    ),

    DefenseSlide(

        id="problem",

        layout="content",

        title="Contexto: digitalización de PYMEs",

        image="image3.png",

        bullets=[

            "PYME de servicios (taller mecánico): citas en papel o WhatsApp, duplicados y poca trazabilidad.",

            "Digitalizar no es solo una web: ordenar datos, roles y operación con infraestructura reproducible.",

            "Este PFC usa el taller como caso acotado para demostrar competencias ASIR (despliegue, red, cloud, métricas).",

            "Siguiente paso: objetivos medibles — app operativa, Docker, AWS y observabilidad con Grafana.",

        ],

        notes=(

            "1:15–2:00. Contexto PYME y caso taller acotado. Conecta con introducción de la memoria."

        ),

    ),

    DefenseSlide(

        id="objectives",

        layout="content",

        title="Objetivos del PFC",

        bullets=[

            "Diseñar e implantar una aplicación web funcional para la gestión básica de un taller mecánico.",

            "Base de datos relacional (usuarios, citas, noticias, consejos) con integridad referencial.",

            "Publicar con Docker para despliegue reproducible en local y en cloud.",

            "Monitorización: salud del sistema, uso de la aplicación, BD y métricas de negocio.",

            "Documentar despliegue en AWS con costes, seguridad perimetral y mantenimiento.",

        ],

        notes="2:00–3:00. Lista corta; no leer palabra por palabra. Subraya integración del ciclo completo.",

    ),

    DefenseSlide(

        id="asir_modules",

        layout="content",

        title="Stack tecnológico del PFC",

        bullets=[

            "PHP + Apache (25 %): capa web LAMP y panel de gestión.",

            "MySQL 8 y Docker/Compose (20 % cada uno): datos y despliegue reproducible.",

            "AWS EC2 (15 %), Linux (10 %), Prometheus/Grafana (10 %), GitHub (5 %).",

        ],

        notes=(

            "3:00–4:15. Gráfico de barras del stack (pesos relativos). La Tabla 1 detallada va en la diapositiva siguiente."

        ),

    ),

    DefenseSlide(

        id="asir_modules_2",

        layout="table",

        visual_pattern="table_styled",

        title="Mapa de competencias ASIR (Tabla 1)",

        table_headers=["Módulo", "Contenidos aplicados en el PFC"],

        table_rows=[

            [

                "Implantación de Aplicaciones Web",

                "PHP, Apache, sesiones, formularios, panel admin, API de citas.",

            ],

            [

                "Gestión de Bases de Datos",

                "MySQL 8, relaciones, índices, unicidad en citas y usuarios.",

            ],

            [

                "Administración de SGBD",

                "Inicialización SQL, usuarios de aplicación, backups, migración futura a RDS.",

            ],

            [

                "Servicios de Red e Internet",

                "HTTP, puertos, redes Docker, monitorización.",

            ],

            [

                "Administración de Sistemas Operativos",

                "Contenedores, volúmenes, logs, healthchecks, scripts de despliegue.",

            ],

            [

                "Seguridad y Alta Disponibilidad",

                "Roles, contraseñas cifradas, CSRF, consultas preparadas, alertas.",

            ],

            [

                "Planificación y Administración de Redes",

                "Docker Compose, redes, volúmenes, Security Groups en AWS.",

            ],

            [

                "LMSGI",

                "HTML/CSS/JS, Markdown, YAML Compose, JSON de dashboards Grafana.",

            ],

            [

                "Empresa e Iniciativa Emprendedora",

                "Digitalización del taller, presupuesto y costes de explotación.",

            ],

            [

                "Proyecto de administración de sistemas",

                "Planificación, documentación, despliegue EC2, observabilidad y pruebas.",

            ],

        ],

        notes=(

            "4:15–5:00. Tabla 1 de competencias ASIR. Cierra el mapa antes de arquitectura y demo."

        ),

    ),

    DefenseSlide(

        id="architecture",

        layout="picture",

        visual_pattern="diagram_stack",

        title="Arquitectura general (Fig. 1)",

        image="image1.png",

        bullets=[

            "Capa web (Apache/PHP) y persistencia MySQL.",

            "Stack Prometheus / Grafana / Alertmanager y exportadores.",

            "Simulador de carga opcional para evidencia en defensa.",

        ],

        notes="5:00–5:45. Señala flujo de datos y fronteras. Diagrama en memoria Fig. 1.",

        picture_width_in=11.2,

        picture_left_in=0.9,

        picture_top_in=1.2,

        html_class="diagram-slide",

    ),

    DefenseSlide(

        id="profiles",

        layout="table",

        visual_pattern="table_styled",

        title="Aplicación web — perfiles y funciones (Tabla 2)",

        image="image3.png",

        table_headers=["Perfil", "Funciones (resumen)"],

        table_rows=[

            [

                "Visitante",

                "Inicio, noticias, registro, login, citación como invitado.",

            ],

            [

                "Usuario registrado",

                "Reservas, citas propias, perfil y contraseña.",

            ],

            [

                "Administrador",

                "Usuarios, citas, noticias, consejos, estadísticas y monitorización.",

            ],

            [

                "Operador técnico",

                "Despliegue, logs, métricas, healthchecks, simulador y backups.",

            ],

        ],

        notes=(

            "5:45–12:00. DEMO navegador: login, citación, panel admin. La demo posterior cubre "

            "operador técnico. Alineado con Tabla 16 (5–12 min)."

        ),

    ),

    DefenseSlide(

        id="data_model",

        layout="two_picture",

        visual_pattern="dual_images",

        title="Modelo de datos y flujo de reserva (Fig. 2 y 3)",

        image="image2.png",

        image_right="image3.png",

        notes=(

            "Tras la demo (≈12:00–12:30 si encaja) o antes de Docker: entidades clave y flujo "

            "usuario→cita. No detallar cada columna SQL."

        ),

    ),

    DefenseSlide(

        id="docker",

        layout="table",

        visual_pattern="table_styled",

        title="Implantación con Docker Compose (Tabla 6)",

        table_headers=["Servicio", "Función en el stack"],

        table_rows=[

            ["web", "Apache/PHP — espera healthcheck de MySQL en el arranque."],

            ["mysql", "Persistencia — sin publicar puertos al host en producción."],

            ["prometheus + alertmanager", "Scraping, reglas de alerta y notificaciones."],

            ["grafana", "Dashboards preprovisionados desde monitoring/grafana/."],

            ["exportadores", "Node, MySQL, blackbox, cAdvisor, Telegraf."],

            ["simulador (perfil traffic)", "JMeter worker + UI para carga controlada."],

        ],

        notes=(

            "12:00–18:00. DEMO: docker compose ps. Explica por qué no exponer MySQL. Tabla 16 (12–18 min)."

        ),

    ),

    DefenseSlide(

        id="traffic_source",

        layout="picture",

        title="Originalidad: fuente de tráfico en métricas",

        image="image19.png",

        bullets=[

            "Métricas HTTP etiquetadas: source=app (tráfico real) vs source=simulator (JMeter).",

            "Pipeline por logs: un solo camino de observabilidad sin instrumentar cada ruta PHP.",

            "Permite demostrar carga sintética sin confundirla con uso real del taller.",

        ],

        notes=(

            "18:00–18:30. Puente hacia monitorización. Vocabulario del dominio: Fuente de tráfico, "

            "Tráfico simulado (CONTEXT.md)."

        ),

        html_class="diagram-slide",

    ),

    DefenseSlide(

        id="monitoring",

        layout="picture",

        title="Monitorización y observabilidad",

        image="image1.png",

        bullets=[

            "Prometheus: contenedores, MySQL, Node, blackbox y endpoint PHP (métricas de aplicación).",

            "Métricas RED: rate (req/s), errors (ratio) y duration (latencia) por Fuente de tráfico.",

            "Grafana: dashboards preprovisionados (JSON en monitoring/grafana/).",

            "Alertmanager: notificaciones SMTP/SES según configuración.",

        ],

        notes=(

            "18:30–20:00. La observabilidad alimenta operación y defensa del diseño. Prepara demo Grafana."

        ),

        html_class="diagram-slide",

    ),

    DefenseSlide(

        id="evidence",

        layout="two_picture",

        visual_pattern="dual_images",

        title="Evidencias: monitorización y contenedores (Fig. 22 y 20)",

        image="image19.png",

        image_right="image20.png",

        notes=(

            "18:00–24:00. DEMO: targets Prometheus, dashboard Grafana en vivo, carga breve JMeter/UI. "

            "Comenta tráfico real vs simulado (Tabla 16, 18–24 min). No proyectar credenciales."

        ),

    ),

    DefenseSlide(

        id="security",

        layout="content",

        title="Seguridad de aplicación e infraestructura",

        bullets=[

            "Aplicación: sesiones PHP, validación, roles admin/usuario, CSRF en formularios críticos.",

            "API de citas: rate limiting para reducir spam de reservas (§5.2).",

            "Red: Security Groups; acceso restringido a Prometheus, Grafana, Alertmanager y MySQL.",

            "Simulador: token de control, límites de URLs y TLS si se expone la UI.",

        ],

        notes=(

            "24:00–25:30. Riesgos y mitigaciones (§5.2). Pregunta probable del tribunal: "

            "¿por qué MySQL no está expuesto al host?"

        ),

    ),

    DefenseSlide(

        id="aws",

        layout="picture",

        visual_pattern="diagram_stack",

        title="Despliegue en AWS (EC2 + Docker Compose)",

        image="image4.png",

        bullets=[

            "Packer → AMI base con Docker Engine; EC2 con user-data bootstrap idempotente.",

            "Reglas de entrada mínimas para HTTP/HTTPS y UIs de laboratorio.",

            "Guías y costes documentados en memoria y en docs/ del repositorio.",

        ],

        notes="25:30–26:30. Diagrama Fig. 4. Opcional: consola EC2 en vivo si hay tiempo.",

        picture_width_in=11.5,

        picture_left_in=0.65,

        html_class="diagram-slide",

    ),

    DefenseSlide(

        id="validation",

        layout="content",

        title="Validación y pruebas",

        bullets=[

            "Funcionales (§7.1): registro, login, citaciones, noticias, consejos y administración.",

            "Despliegue y monitorización (§7.2): arranque Docker, healthchecks, targets y dashboards.",

            "Simulador: carga breve con diferenciación source=app vs source=simulator.",

            "Matriz de pruebas (§7.3): trazabilidad requisito → evidencia.",

        ],

        notes="26:30–27:00. Tres frases por bloque; el detalle queda en la memoria.",

    ),

    DefenseSlide(

        id="budget",

        layout="table",

        visual_pattern="data_highlight",

        title="Presupuesto anual orientativo (Tabla 14)",

        table_headers=["Concepto", "Coste anual"],

        table_rows=[

            ["EC2 t3.small 24/7", "300 EUR"],

            ["EBS gp3 cifrado 50 GiB", "60 EUR"],

            ["Dominio propio", "12 EUR"],

            ["Backups / snapshots", "60 EUR"],

            ["Correo SMTP alertas", "60 EUR"],

            ["Implantación + mantenimiento", "550 EUR"],

            ["Contingencia 10 %", "104 EUR"],

            ["Total orientativo", "1.146 EUR/año"],

        ],

        notes=(

            "27:00–27:30. Una cifra memorable. Orientativo según región y tráfico. Tabla 16 (24–28 min)."

        ),

    ),

    DefenseSlide(

        id="conclusions",

        layout="content",

        title="Conclusiones y mejoras futuras",

        bullets=[

            "Consecución: web operativa, BD normalizada, Docker local/AWS, monitorización activa.",

            "Límites del tiempo de proyecto (HTTPS definitivo, endurecimiento adicional).",

            "Mejoras: RDS, CI/CD, backups en S3, políticas RGPD.",

        ],

        notes=(

            "27:30–28:00. Honestidad y visión profesional. La slide siguiente resume Tabla 17."

        ),

    ),

    DefenseSlide(

        id="objectives_grade",

        layout="table",

        visual_pattern="table_styled",

        title="Grado de consecución de objetivos (Tabla 17)",

        table_headers=["Objetivo", "Grado", "Observaciones"],

        table_rows=[

            [

                "Aplicación web funcional",

                "Alto",

                "Registro, login, citas, noticias, consejos y admin.",

            ],

            [

                "Modelo de datos relacional",

                "Alto",

                "Tablas normalizadas, FK, índices y datos iniciales.",

            ],

            [

                "Despliegue reproducible",

                "Alto",

                "Compose local, AWS/Coolify/Dokploy y documentación.",

            ],

            [

                "Monitorización integrada",

                "Alto",

                "Prometheus, Grafana, Alertmanager y exportadores.",

            ],

            [

                "Simulación de tráfico",

                "Medio-Alto",

                "Worker + UI; requiere Docker y token seguro.",

            ],

            [

                "Preparación para producción",

                "Medio",

                "Falta dominio real, TLS definitivo y backups S3 automáticos.",

            ],

        ],

        notes="28:00–28:30. Refuerza criterio de resolución de la rúbrica (50 %).",

    ),

    DefenseSlide(

        id="closing",

        layout="content",

        visual_pattern="closing_statement",

        title="Demostración, preguntas y cierre",

        bullets=[

            "Checklist demo (operador técnico): app → docker compose ps → Grafana/Prometheus → carga breve.",

            "Reserva ≥5 min para preguntas del tribunal (rúbrica: exposición oral 30 %).",

            "Agradecimiento al tribunal y al tutor. ¿Preguntas?",

        ],

        notes=(

            "28:30–30:00+. Prioriza margen para preguntas. Preguntas probables: Security Groups y puertos; "

            "MySQL no expuesto; diferencia source=app vs source=simulator; por qué logs y no solo métricas in-app."

        ),

    ),

]


