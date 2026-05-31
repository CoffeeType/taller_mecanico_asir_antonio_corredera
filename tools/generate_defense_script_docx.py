from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from defense_slides_manifest import COVER_SUBTITLE, SLIDES, TITLE_MAIN


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Guion_Defensa_PFC_Taller_Mecanico_ASIR_Antonio_Corredera_Cubells.docx"


@dataclass(frozen=True)
class SlideScript:
    timebox: str
    objective: str
    speech: list[str]
    demo: list[str]
    transition: str


SCRIPT_BY_ID: dict[str, SlideScript] = {
    "cover": SlideScript(
        timebox="0:00-0:30",
        objective="Abrir con seguridad, identificar el proyecto y situar el alcance técnico.",
        speech=[
            "Buenos dias. Soy Antonio Corredera Cubells y voy a presentar mi Proyecto Final de Ciclo: implantacion y monitorizacion de un sistema web para la gestion de un taller mecanico.",
            "El proyecto toma un caso de PYME muy concreto, un taller mecanico, y lo utiliza para demostrar un ciclo completo de administracion de sistemas: una aplicacion web LAMP, una base de datos relacional, despliegue reproducible con Docker, despliegue documentado en AWS y observabilidad con Prometheus y Grafana.",
            "La idea principal no es solo mostrar una web, sino defender como se prepara un servicio para operar, medirse y mantenerse.",
        ],
        demo=["No leer la portada. Mirar al tribunal, indicar nombre y titulo, y avanzar rapido."],
        transition="Empiezo con el mapa de la exposicion para que se vea donde encajan las demos.",
    ),
    "timeline": SlideScript(
        timebox="0:30-1:15",
        objective="Explicar la estructura de 30 minutos y anticipar las evidencias.",
        speech=[
            "La defensa esta organizada en seis bloques. Primero presentare el contexto, los objetivos y la relacion con los modulos de ASIR. Despues pasare a la aplicacion: login, citaciones, noticias y administracion.",
            "A continuacion defendere la parte de implantacion: Docker Compose, base de datos, volumenes y redes. El cuarto bloque es la monitorizacion, con Prometheus, Grafana y el simulador de trafico.",
            "Finalmente explicare AWS, seguridad, presupuesto, validacion y conclusiones. He reservado margen para preguntas, porque varias decisiones tecnicas son defendibles desde el punto de vista de operacion.",
        ],
        demo=[
            "Avisar de que habra demo en navegador, terminal y Grafana.",
            "No detenerse en cada fila de la tabla; usarla como contrato de tiempo.",
        ],
        transition="Con ese recorrido, el primer punto es explicar por que este caso de taller es util para un PFC de ASIR.",
    ),
    "problem": SlideScript(
        timebox="1:15-2:00",
        objective="Conectar el problema de negocio con el alcance ASIR.",
        speech=[
            "El punto de partida es una situacion habitual en una pequena empresa de servicios: citas gestionadas por telefono, papel o WhatsApp, informacion duplicada y poca trazabilidad.",
            "Digitalizar aqui no significa crear una pagina informativa y ya esta. Significa ordenar datos, separar roles, controlar el acceso, desplegar de forma repetible y observar si el sistema funciona.",
            "Por eso el taller es un caso acotado: tiene citas, usuarios, administracion y contenido publico, pero permite demostrar infraestructura, red, seguridad, cloud y metricas sin convertir el proyecto en un producto comercial enorme.",
        ],
        demo=["Enfatizar la expresion caso_taller: negocio acotado, alcance ASIR amplio."],
        transition="A partir de ese contexto, los objetivos se pueden medir de forma bastante directa.",
    ),
    "objectives": SlideScript(
        timebox="2:00-3:00",
        objective="Presentar objetivos verificables y no solo funcionales.",
        speech=[
            "Los objetivos se agrupan en cinco lineas. La primera es disenar una aplicacion web funcional para la gestion basica del taller: registro, login, citaciones, noticias, consejos y administracion.",
            "La segunda es sostener esa aplicacion con una base de datos relacional, con tablas para usuarios, citas y contenido, y con integridad referencial para evitar inconsistencias.",
            "La tercera es publicar el sistema con Docker para que el despliegue sea reproducible en local y en cloud. La cuarta es incorporar monitorizacion: salud del sistema, uso de la aplicacion, base de datos y metricas de negocio.",
            "Y la quinta es documentar una implantacion en AWS, incluyendo costes orientativos, seguridad perimetral y tareas de mantenimiento.",
        ],
        demo=["No leer literalmente las cinco viñetas; convertirlas en cinco compromisos verificables."],
        transition="Para cubrir esos objetivos he combinado tecnologias de desarrollo web, sistemas, red y observabilidad.",
    ),
    "asir_modules": SlideScript(
        timebox="3:00-4:15",
        objective="Defender que el proyecto integra competencias del ciclo, no una unica asignatura.",
        speech=[
            "El stack tecnologico combina un enfoque clasico LAMP con herramientas actuales de operacion. En la capa web se usa Apache y PHP; en persistencia, MySQL; en infraestructura, Docker y Docker Compose.",
            "Sobre esa base se anade Prometheus para recopilar metricas, Grafana para visualizarlas, Alertmanager para alertas y JMeter para generar carga controlada.",
            "Esta mezcla es importante para ASIR porque obliga a trabajar con servicios, puertos, volumenes, variables de entorno, logs, backups, seguridad y despliegue. La aplicacion es el hilo conductor, pero el valor academico esta en operar el sistema completo.",
        ],
        demo=["Señalar el grafico de barras como reparto aproximado de peso tecnico."],
        transition="La siguiente diapositiva traduce ese stack a modulos concretos del ciclo.",
    ),
    "asir_modules_2": SlideScript(
        timebox="4:15-5:00",
        objective="Vincular evidencias concretas con modulos ASIR.",
        speech=[
            "Esta tabla resume la correspondencia con los modulos. En Implantacion de Aplicaciones Web aparecen PHP, Apache, formularios, sesiones y el panel de administracion.",
            "En Bases de Datos y Administracion de SGBD se trabaja con MySQL, relaciones, indices, inicializacion SQL y usuarios de aplicacion. En Sistemas, Redes y Seguridad entran Docker Compose, volumenes, healthchecks, roles, contrasenas cifradas, CSRF y Security Groups.",
            "Tambien hay documentacion tecnica en Markdown, YAML y JSON de dashboards. Por tanto, no es una entrega aislada: cada bloque deja una evidencia concreta del ciclo.",
        ],
        demo=["Elegir 3 o 4 filas representativas; no leer la tabla completa."],
        transition="Una vez situado el mapa de competencias, paso a la arquitectura general.",
    ),
    "architecture": SlideScript(
        timebox="5:00-5:45",
        objective="Explicar fronteras entre aplicacion, datos, monitorizacion y simulador.",
        speech=[
            "La arquitectura separa tres areas. La primera es la aplicacion web, servida por Apache y PHP. La segunda es la persistencia, con MySQL como base de datos relacional.",
            "La tercera es la observabilidad: Prometheus recoge metricas de la aplicacion, de MySQL, del nodo y de contenedores; Grafana las muestra; Alertmanager permite convertir reglas en notificaciones.",
            "El simulador de carga queda como un componente opcional de laboratorio. No forma parte del uso normal del taller, pero sirve para demostrar comportamiento bajo trafico y generar evidencias durante la defensa.",
        ],
        demo=["Señalar en el diagrama que MySQL no se expone como servicio publico."],
        transition="Con esa arquitectura en mente, enseño ahora que puede hacer cada perfil dentro de la aplicacion.",
    ),
    "profiles": SlideScript(
        timebox="5:45-12:00",
        objective="Demostrar la aplicacion desde el punto de vista del usuario y del administrador.",
        speech=[
            "La aplicacion distingue cuatro perfiles. El visitante puede consultar informacion publica, noticias y consejos, registrarse, iniciar sesion y solicitar una citacion como invitado si no tiene cuenta.",
            "El usuario registrado puede reservar citas, consultar sus citas propias, revisar su perfil y cambiar la contrasena. En el dominio del proyecto, la citacion es la accion de reservar; si se confirma, se crea una cita persistida en base de datos.",
            "El administrador gestiona usuarios, citas, noticias, consejos, estadisticas y accesos a monitorizacion. Y el operador tecnico no es un rol de negocio de la web, sino la persona que despliega, revisa logs, comprueba healthchecks, lanza simulaciones y valida backups.",
            "En la demo voy a recorrer el flujo principal: acceso a la aplicacion, login, solicitud de cita y panel de administracion. La idea es mostrar que el sistema no es una maqueta estatica, sino una aplicacion con roles y datos persistentes.",
        ],
        demo=[
            "Abrir navegador en la aplicacion.",
            "Mostrar pagina publica, noticias/consejos y acceso a citaciones.",
            "Iniciar sesion con un usuario de prueba o administrador.",
            "Crear o revisar una cita sin mostrar credenciales sensibles.",
            "Entrar en panel admin y enseñar usuarios, citas, noticias o consejos.",
        ],
        transition="Despues de ver el flujo funcional, conviene enseñar que datos quedan detras y como se relacionan.",
    ),
    "data_model": SlideScript(
        timebox="12:00-12:30",
        objective="Resumir entidades y flujo de reserva sin entrar en cada columna SQL.",
        speech=[
            "El modelo de datos recoge las entidades necesarias para el alcance del taller: usuarios, citas y contenidos como noticias o consejos.",
            "La parte clave es que la reserva no queda como texto suelto. Se valida una fecha y una franja horaria, se registran los datos necesarios y se crea una cita vinculada a usuario o a datos de invitado.",
            "Esto permite trazabilidad: el administrador puede ver, editar o eliminar la cita desde su panel, mientras que el usuario consulta su historial desde citaciones.",
        ],
        demo=["No explicar cada campo; hablar de relaciones, unicidad y trazabilidad."],
        transition="Una vez visto el modelo, paso a como se implanta todo el stack con Docker Compose.",
    ),
    "docker": SlideScript(
        timebox="12:00-18:00",
        objective="Defender reproducibilidad, redes internas, volumenes y aislamiento de servicios.",
        speech=[
            "Docker Compose permite levantar el sistema como un conjunto de servicios coordinados. El servicio web contiene Apache y PHP, y espera a que MySQL este sano antes de arrancar completamente.",
            "MySQL guarda la persistencia y, en un despliegue serio, no se publica al host. Esto reduce superficie de ataque: la aplicacion habla con la base de datos por la red interna de Docker, no por un puerto abierto hacia fuera.",
            "Prometheus y Alertmanager se encargan de scraping y alertas; Grafana carga dashboards preprovisionados desde la carpeta de monitorizacion; y los exportadores aportan metricas de nodo, MySQL, blackbox, cAdvisor y Telegraf.",
            "El perfil traffic añade JMeter worker y una interfaz para pruebas controladas. Lo separo como perfil porque no es necesario para el uso diario del taller, pero si para validar carga y generar evidencias.",
        ],
        demo=[
            "En terminal, ejecutar o mostrar `docker compose ps`.",
            "Señalar servicios esperados: web, mysql, prometheus, alertmanager, grafana, exportadores y simulador si esta activo.",
            "Explicar puertos publicados y puertos privados.",
            "Si se enseña `.env`, ocultar secretos o usar solo variables no sensibles.",
        ],
        transition="El simulador enlaza directamente con una de las decisiones mas originales del proyecto: distinguir trafico real y trafico sintetico.",
    ),
    "traffic_source": SlideScript(
        timebox="18:00-18:30",
        objective="Explicar la decision de etiquetar fuentes de trafico para no mezclar evidencias.",
        speech=[
            "En monitorizacion era importante no mezclar el uso real de la aplicacion con la carga generada por JMeter. Por eso las metricas HTTP incorporan una etiqueta de fuente de trafico.",
            "Las peticiones de la aplicacion quedan como source=app y las importadas desde JMeter como source=simulator. Asi puedo comparar comportamiento sin presentar trafico sintetico como si fuera actividad real del taller.",
            "La decision esta documentada en los ADRs: se reutiliza un pipeline por logs y un unico camino de scraping, evitando instrumentar cada ruta PHP solo para la demo.",
        ],
        demo=["Usar el diagrama para decir que el simulador escribe en el mismo modelo de metricas, pero etiquetado."],
        transition="Con esa etiqueta, Prometheus y Grafana pueden separar claramente que esta ocurriendo.",
    ),
    "monitoring": SlideScript(
        timebox="18:30-20:00",
        objective="Explicar el sistema de observabilidad y las metricas que se defenderan.",
        speech=[
            "Prometheus recoge metricas de la aplicacion PHP mediante metrics.php, de MySQL, del sistema y de probes HTTP con blackbox. El objetivo es cubrir salud de servicio, rendimiento y datos de negocio.",
            "Para la aplicacion uso metricas RED: rate, errors y duration. Es decir, cuantas peticiones llegan, cuantas fallan y que latencia tienen. Al añadir la etiqueta source puedo ver esas metricas para trafico real o simulado.",
            "Grafana consume Prometheus y muestra dashboards preprovisionados. Alertmanager queda preparado para convertir reglas en notificaciones, por ejemplo alertas de caida de metricas, errores 5xx o problemas de probe HTTP.",
        ],
        demo=["Preparar la demo de Grafana: targets, dashboard principal y paneles JMeter/source."],
        transition="Ahora muestro las evidencias: contenedores vivos, targets sanos y paneles con datos.",
    ),
    "evidence": SlideScript(
        timebox="20:00-24:00",
        objective="Mostrar evidencias operativas en vivo sin exponer credenciales.",
        speech=[
            "En esta parte no quiero limitarme a capturas. La defensa debe demostrar que el sistema esta operando: contenedores levantados, Prometheus scrapeando targets y Grafana visualizando series.",
            "Primero reviso Prometheus targets para confirmar que la aplicacion, MySQL y exportadores responden. Despues paso a Grafana y enseño el dashboard principal: estado general, trafico, errores, latencia, base de datos, recursos y metricas de negocio.",
            "Si lanzo una carga breve con JMeter, la lectura importante es que la actividad aparece como source=simulator. Eso permite demostrar carga sin confundirla con usuarios reales.",
            "Tambien puedo enseñar que el endpoint metrics.php centraliza metricas de aplicacion y que blackbox comprueba disponibilidad HTTP desde fuera de la propia aplicacion.",
        ],
        demo=[
            "Abrir Prometheus `/targets` y comprobar targets UP.",
            "Abrir Grafana y seleccionar el dashboard principal.",
            "Mostrar paneles de requests, errores, latencia, MySQL y negocio.",
            "Ejecutar carga breve solo si el entorno esta estable y hay tiempo.",
            "No proyectar credenciales, tokens ni paneles de configuracion sensible.",
        ],
        transition="Tras ver que el sistema funciona, explico las medidas de seguridad y las decisiones de exposicion.",
    ),
    "security": SlideScript(
        timebox="24:00-25:30",
        objective="Defender mitigaciones de aplicacion e infraestructura.",
        speech=[
            "La seguridad se trabaja en dos niveles. En la aplicacion hay sesiones PHP, validacion de entrada, roles de administrador y usuario, CSRF en formularios criticos y consultas preparadas para reducir riesgo de SQL injection.",
            "Las contrasenas no se guardan en texto plano: se cifran con el mecanismo de hash de PHP. En la API de citas se incorpora rate limiting para reducir spam de reservas.",
            "En infraestructura, la decision principal es cerrar lo que no debe ser publico. MySQL no se expone al host; Prometheus, Grafana, Alertmanager y la UI del simulador deben quedar restringidos por Security Groups o por rutas controladas.",
            "El simulador tambien tiene token de control, limites de URL y recomendacion de TLS si se expone la interfaz.",
        ],
        demo=["Preparar respuesta a la pregunta: por que MySQL no esta expuesto al host."],
        transition="Estas medidas se trasladan al despliegue cloud documentado en AWS.",
    ),
    "aws": SlideScript(
        timebox="25:30-26:30",
        objective="Presentar una arquitectura cloud realista para el alcance del PFC.",
        speech=[
            "El despliegue en AWS se plantea con una instancia EC2 y Docker Compose. Para este tamano de proyecto es una solucion razonable: sencilla, economica y suficiente para demostrar operacion.",
            "La guia contempla una AMI base con Docker mediante Packer, o un user-data idempotente que instala Docker, clona el repositorio en `/opt/taller_mecanico_asir` y ejecuta el script de despliegue.",
            "El disco EBS debe ir cifrado, los secretos se rotan en `.env`, y las reglas de entrada se limitan a HTTP/HTTPS y, si hace falta en laboratorio, a las UIs de monitorizacion desde una IP concreta.",
            "Para una fase posterior, una mejora natural seria mover MySQL a RDS y automatizar backups en S3.",
        ],
        demo=["Si se abre consola EC2, mostrar solo arquitectura o estado; evitar enseñar secretos o claves."],
        transition="Despues de arquitectura, queda demostrar como se ha validado el proyecto.",
    ),
    "validation": SlideScript(
        timebox="26:30-27:00",
        objective="Resumir pruebas funcionales, despliegue y trazabilidad requisito-evidencia.",
        speech=[
            "La validacion se organiza en tres grupos. Primero, pruebas funcionales: registro, login, citaciones, noticias, consejos y administracion.",
            "Segundo, pruebas de despliegue y monitorizacion: arranque Docker, healthchecks, targets de Prometheus y dashboards de Grafana.",
            "Tercero, pruebas con simulador: carga breve y diferenciacion entre source=app y source=simulator. La matriz de pruebas enlaza requisito con evidencia, que es lo importante para defender el grado de consecucion.",
        ],
        demo=["Mantener esta diapositiva breve; el detalle ya se habra visto en las demos."],
        transition="Con las pruebas cerradas, presento el coste orientativo de operar esta solucion.",
    ),
    "budget": SlideScript(
        timebox="27:00-27:30",
        objective="Dar una cifra memorable y prudente de coste anual.",
        speech=[
            "El presupuesto anual orientativo ronda los 1.146 euros al ano. Incluye una EC2 t3.small funcionando 24/7, disco EBS cifrado, dominio, backups o snapshots, correo SMTP para alertas, implantacion, mantenimiento y una contingencia del 10 por ciento.",
            "Es una estimacion para tener orden de magnitud. En produccion real dependeria de region, trafico, dominio, politica de backups y si se incorpora un balanceador, RDS u otros servicios gestionados.",
        ],
        demo=["No discutir centimos; defender el coste como estimacion de explotacion."],
        transition="Con coste y alcance claros, cierro con conclusiones y mejoras.",
    ),
    "conclusions": SlideScript(
        timebox="27:30-28:00",
        objective="Cerrar con balance honesto: conseguido, limites y futuro.",
        speech=[
            "Como conclusion, el proyecto alcanza los objetivos principales: aplicacion web operativa, base de datos relacional, despliegue reproducible local y cloud, y monitorizacion activa.",
            "Tambien es importante reconocer limites: queda margen para endurecimiento adicional, TLS definitivo, automatizacion de backups externos y politicas RGPD mas completas.",
            "Las mejoras naturales serian RDS para base de datos gestionada, CI/CD, backups en S3 y una politica formal de continuidad.",
        ],
        demo=["Usar tono honesto: conseguido no significa cerrado para produccion exigente."],
        transition="La ultima tabla resume el grado de consecucion de cada objetivo.",
    ),
    "objectives_grade": SlideScript(
        timebox="28:00-28:30",
        objective="Reforzar la evaluacion por objetivos antes del cierre.",
        speech=[
            "El grado de consecucion es alto en aplicacion web, modelo de datos, despliegue reproducible y monitorizacion integrada.",
            "El simulador queda en medio-alto porque funciona como herramienta de laboratorio, pero requiere Docker y token seguro. La preparacion para produccion queda en medio porque faltan elementos que no eran el nucleo del PFC: dominio real, TLS definitivo y backups S3 automaticos.",
            "Esta tabla es importante porque separa lo que se ha implementado de lo que se propone como evolucion profesional.",
        ],
        demo=["Señalar la fila de preparacion para produccion para mostrar criterio y no sobreprometer."],
        transition="Con esto termino la exposicion y dejo preparado el bloque de preguntas.",
    ),
    "closing": SlideScript(
        timebox="28:30-30:00+",
        objective="Cerrar, agradecer y abrir preguntas con una posicion tecnica clara.",
        speech=[
            "Para cerrar, el proyecto demuestra un recorrido completo: aplicacion, datos, despliegue, observabilidad, seguridad basica, coste y validacion.",
            "Si queda tiempo, puedo repetir una comprobacion rapida de operador tecnico: aplicacion, `docker compose ps`, Prometheus/Grafana y una carga breve. Si no, prefiero dejar margen para preguntas del tribunal.",
            "Muchas gracias por la atencion y al tutor por el seguimiento del proyecto. Quedo a disposicion para preguntas.",
        ],
        demo=[
            "Checklist opcional: app -> docker compose ps -> Grafana/Prometheus -> carga breve.",
            "Priorizar preguntas frente a demos adicionales si el tiempo esta justo.",
        ],
        transition="Fin de exposicion.",
    ),
}


DEFENSE_QA: list[tuple[str, str]] = [
    (
        "Por que no expones MySQL al host o a Internet?",
        "Porque MySQL solo debe ser consumido por la aplicacion dentro de la red Docker. Publicarlo aumentaria la superficie de ataque sin aportar valor al usuario final. Para administracion se usarian canales controlados: shell, backup, tunel o herramientas internas.",
    ),
    (
        "Que diferencia hay entre source=app y source=simulator?",
        "source=app representa trafico real generado por la aplicacion. source=simulator representa peticiones importadas desde JMeter. La separacion evita confundir carga sintetica con uso real y permite comparar latencia, errores y volumen por origen.",
    ),
    (
        "Por que usar logs para metricas HTTP y no instrumentar cada ruta PHP?",
        "El pipeline por logs permite un unico camino de observabilidad para trafico real y simulado, reduce cambios en rutas PHP y encaja con un enfoque ASIR centrado en operacion. La desventaja es que exige formato de log consistente y control de volumen.",
    ),
    (
        "Que aporta Prometheus/Grafana si la aplicacion ya funciona?",
        "Aporta visibilidad operativa. Permite saber si la aplicacion responde, si hay errores 5xx, como evoluciona la latencia, si MySQL tiene problemas y si los contenedores consumen demasiados recursos. Sin observabilidad solo se descubre el fallo cuando el usuario se queja.",
    ),
    (
        "Por que Docker Compose en vez de Kubernetes?",
        "Para el alcance del PFC y una PYME pequena, Compose es mas proporcionado: menos complejidad, despliegue reproducible y suficiente para demostrar servicios, redes, volumenes y monitorizacion. Kubernetes seria justificable con escalado, alta disponibilidad o varios equipos.",
    ),
    (
        "Que faltaria para produccion real?",
        "TLS definitivo, dominio real, politicas RGPD revisadas, backups externos probados, restauracion documentada, rotacion formal de secretos, endurecimiento de UIs de monitorizacion y posiblemente RDS para reducir operacion de base de datos.",
    ),
    (
        "Como validas que una cita no se duplica?",
        "El flujo valida fecha y franja antes de crear el registro y el modelo relacional impone coherencia. En la defensa conviene explicar que la aplicacion no trata la cita como texto libre, sino como registro persistido y administrable.",
    ),
    (
        "Que pasa si Grafana no muestra datos durante la defensa?",
        "Hay un plan de contingencia: revisar Prometheus targets, comprobar `metrics.php`, verificar contenedores con `docker compose ps` y usar capturas/evidencias incluidas en la presentacion si el entorno de demo falla.",
    ),
]


PRACTICE_TIPS = [
    "No leer las diapositivas: usar cada una como apoyo visual y el guion como ensayo previo.",
    "En demos, explicar primero que se va a comprobar y despues mostrarlo. Evitar navegar sin narracion.",
    "No proyectar credenciales, tokens, `.env` completo ni consolas con secretos.",
    "Si una demo falla, convertirlo en procedimiento operativo: revisar contenedores, targets y logs.",
    "Mantener la diferencia entre citacion (accion de reservar) y cita (registro creado).",
    "Cerrar cada bloque con una frase puente para que el tribunal vea continuidad.",
]


SPANISH_PHRASE_REPLACEMENTS = {
    "Buenos dias": "Buenos días",
    "defensa esta organizada": "defensa está organizada",
    "A continuacion": "A continuación",
    "Despues pasare": "Después pasaré",
    "habra demo": "habrá demo",
    "por que este caso": "por qué este caso",
    "situacion habitual": "situación habitual",
    "Digitalizar aqui": "Digitalizar aquí",
    "pagina informativa": "página informativa",
    "contenido publico": "contenido público",
    "expresion caso_taller": "expresión caso_taller",
    "cinco lineas": "cinco líneas",
    "disenar una": "diseñar una",
    "con una base": "con una base",
    "una unica asignatura": "una única asignatura",
    "stack tecnologico": "stack tecnológico",
    "enfoque clasico": "enfoque clásico",
    "se anade": "se añade",
    "valor academico": "valor académico",
    "valor académico esta en": "valor académico está en",
    "grafico de barras": "gráfico de barras",
    "peso tecnico": "peso técnico",
    "modulos concretos": "módulos concretos",
    "Implantacion de Aplicaciones Web": "Implantación de Aplicaciones Web",
    "Administracion de SGBD": "Administración de SGBD",
    "Tambien hay": "También hay",
    "documentacion tecnica": "documentación técnica",
    "tres areas": "tres áreas",
    "servicio publico": "servicio público",
    "que puede hacer": "qué puede hacer",
    "La aplicacion distingue": "La aplicación distingue",
    "informacion publica": "información pública",
    "iniciar sesion": "iniciar sesión",
    "solicitar una citacion": "solicitar una citación",
    "la citacion es la accion": "la citación es la acción",
    "operador tecnico": "operador técnico",
    "maqueta estatica": "maqueta estática",
    "la aplicacion": "la aplicación",
    "Mostrar pagina publica": "Mostrar página pública",
    "Iniciar sesion": "Iniciar sesión",
    "Despues de ver": "Después de ver",
    "que datos quedan detras": "qué datos quedan detrás",
    "paso a como": "paso a cómo",
    "MySQL este sano": "MySQL esté sano",
    "si esta activo": "si está activo",
    "decisiones mas originales": "decisiones más originales",
    "trafico sintetico": "tráfico sintético",
    "La decision esta documentada": "La decisión está documentada",
    "camino de scraping": "camino de scraping",
    "que esta ocurriendo": "qué está ocurriendo",
    "metricas que se defenderan": "métricas que se defenderán",
    "cuantas peticiones": "cuántas peticiones",
    "cuantas fallan": "cuántas fallan",
    "alertas de caida": "alertas de caída",
    "sistema esta operando": "sistema está operando",
    "Despues paso": "Después paso",
    "trafico, errores": "tráfico, errores",
    "Tambien puedo": "También puedo",
    "configuracion sensible": "configuración sensible",
    "decisiones de exposicion": "decisiones de exposición",
    "En la aplicacion": "En la aplicación",
    "formularios criticos": "formularios críticos",
    "La seguridad se trabaja": "La seguridad se trabaja",
    "contrasenas no": "contraseñas no",
    "La decision principal": "La decisión principal",
    "no debe ser publico": "no debe ser público",
    "tambien tiene": "también tiene",
    "limites de URL": "límites de URL",
    "recomendacion de TLS": "recomendación de TLS",
    "por que MySQL": "por qué MySQL",
    "tamano de proyecto": "tamaño de proyecto",
    "solucion razonable": "solución razonable",
    "economica y suficiente": "económica y suficiente",
    "La guia contempla": "La guía contempla",
    "una mejora natural seria": "una mejora natural sería",
    "Despues de arquitectura": "Después de arquitectura",
    "La validacion": "La validación",
    "monitorizacion: arranque": "monitorización: arranque",
    "diferenciacion entre": "diferenciación entre",
    "grado de consecucion": "grado de consecución",
    "se habra visto": "se habrá visto",
    "esta solucion": "esta solución",
    "al ano": "al año",
    "implantacion, mantenimiento": "implantación, mantenimiento",
    "Es una estimacion": "Es una estimación",
    "En produccion real dependeria": "En producción real dependería",
    "de region": "de región",
    "politica de backups": "política de backups",
    "No discutir centimos": "No discutir céntimos",
    "estimacion de explotacion": "estimación de explotación",
    "Como conclusion": "Como conclusión",
    "Tambien es importante": "También es importante",
    "reconocer limites": "reconocer límites",
    "automatizacion de backups": "automatización de backups",
    "politicas RGPD": "políticas RGPD",
    "mas completas": "más completas",
    "mejoras naturales serian": "mejoras naturales serían",
    "politica formal": "política formal",
    "La ultima tabla": "La última tabla",
    "evaluacion por objetivos": "evaluación por objetivos",
    "consecucion es alto": "consecución es alto",
    "preparacion para produccion": "preparación para producción",
    "nucleo del PFC": "núcleo del PFC",
    "automaticos": "automáticos",
    "evolucion profesional": "evolución profesional",
    "termino la exposicion": "termino la exposición",
    "posicion tecnica": "posición técnica",
    "seguridad basica": "seguridad básica",
    "comprobacion rapida": "comprobación rápida",
    "atencion": "atención",
    "disposicion": "disposición",
    "exposicion.": "exposición.",
    "donde encajan": "dónde encajan",
    "entorno esta estable": "entorno está estable",
    "no esta expuesto": "no está expuesto",
    "tiempo esta justo": "tiempo está justo",
    "Por que no expones": "¿Por qué no expones",
    "Que diferencia hay": "¿Qué diferencia hay",
    "Por que usar logs": "¿Por qué usar logs",
    "Que aporta Prometheus": "¿Qué aporta Prometheus",
    "Por que Docker Compose": "¿Por qué Docker Compose",
    "Que faltaria": "¿Qué faltaría",
    "Como validas": "¿Cómo validas",
    "Que pasa si Grafana": "¿Qué pasa si Grafana",
    "aplicacion dentro": "aplicación dentro",
    "aumentaria": "aumentaría",
    "administracion se usarian": "administración se usarían",
    "trafico real": "tráfico real",
    "La separacion evita": "La separación evita",
    "carga sintetica": "carga sintética",
    "metricas HTTP": "métricas HTTP",
    "un unico camino": "un único camino",
    "operacion. La desventaja": "operación. La desventaja",
    "la aplicacion responde": "la aplicación responde",
    "como evoluciona": "cómo evoluciona",
    "PYME pequena": "PYME pequeña",
    "es mas proporcionado": "es más proporcionado",
    "seria justificable": "sería justificable",
    "produccion real": "producción real",
    "politicas RGPD": "políticas RGPD",
    "restauracion documentada": "restauración documentada",
    "rotacion formal": "rotación formal",
    "monitorizacion y posiblemente": "monitorización y posiblemente",
    "El flujo valida": "El flujo valida",
    "la aplicacion no trata": "la aplicación no trata",
    "presentacion si": "presentación si",
    "guion como ensayo": "guión como ensayo",
    "despues mostrarlo": "después mostrarlo",
    "sin narracion": "sin narración",
    "citacion (accion": "citación (acción",
    "Indice operativo": "Índice operativo",
    "Transicion:": "Transición:",
    "desviacion de tiempo": "desviación de tiempo",
    "separacion source": "separación source",
}


SPANISH_WORD_REPLACEMENTS = {
    "implantacion": "implantación",
    "monitorizacion": "monitorización",
    "gestion": "gestión",
    "mecanico": "mecánico",
    "administracion": "administración",
    "aplicacion": "aplicación",
    "titulo": "título",
    "rapido": "rápido",
    "exposicion": "exposición",
    "presentare": "presentaré",
    "relacion": "relación",
    "modulos": "módulos",
    "defendere": "defenderé",
    "volumenes": "volúmenes",
    "trafico": "tráfico",
    "validacion": "validación",
    "tecnicas": "técnicas",
    "operacion": "operación",
    "util": "útil",
    "pequena": "pequeña",
    "telefono": "teléfono",
    "informacion": "información",
    "administracion": "administración",
    "publico": "público",
    "metricas": "métricas",
    "basica": "básica",
    "tecnologias": "tecnologías",
    "unica": "única",
    "tecnologico": "tecnológico",
    "clasico": "clásico",
    "tecnico": "técnico",
    "indices": "índices",
    "inicializacion": "inicialización",
    "contrasenas": "contraseñas",
    "areas": "áreas",
    "sesion": "sesión",
    "citacion": "citación",
    "accion": "acción",
    "contrasena": "contraseña",
    "estadisticas": "estadísticas",
    "detras": "detrás",
    "sintetico": "sintético",
    "decision": "decisión",
    "caida": "caída",
    "configuracion": "configuración",
    "exposicion": "exposición",
    "criticos": "críticos",
    "guia": "guía",
    "tamano": "tamaño",
    "solucion": "solución",
    "economica": "económica",
    "seria": "sería",
    "consecucion": "consecución",
    "estimacion": "estimación",
    "produccion": "producción",
    "dependeria": "dependería",
    "region": "región",
    "politica": "política",
    "centimos": "céntimos",
    "explotacion": "explotación",
    "conclusion": "conclusión",
    "limites": "límites",
    "automatizacion": "automatización",
    "politicas": "políticas",
    "serian": "serían",
    "ultima": "última",
    "evaluacion": "evaluación",
    "preparacion": "preparación",
    "nucleo": "núcleo",
    "evolucion": "evolución",
    "posicion": "posición",
    "comprobacion": "comprobación",
    "rapida": "rápida",
    "atencion": "atención",
    "disposicion": "disposición",
    "tunel": "túnel",
    "unico": "único",
    "pequeno": "pequeño",
    "faltaria": "faltaría",
    "restauracion": "restauración",
    "rotacion": "rotación",
    "guion": "guión",
    "narracion": "narración",
}


def normalize_spanish_text(value: str) -> str:
    """Restores Spanish spelling before serializing document text to OOXML."""
    normalized = value
    for source, target in SPANISH_PHRASE_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    for source, target in SPANISH_WORD_REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
        normalized = re.sub(
            rf"\b{re.escape(source.capitalize())}\b",
            target.capitalize(),
            normalized,
        )
    return normalized


def xml_text(value: str) -> str:
    return escape(normalize_spanish_text(value), {"\"": "&quot;"})



def run(text: str, *, bold: bool = False, italic: bool = False) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    prop_xml = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    space = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f"<w:r>{prop_xml}<w:t{space}>{xml_text(text)}</w:t></w:r>"


def para(
    text: str = "",
    *,
    style: str | None = None,
    bold: bool = False,
    italic: bool = False,
    num_id: int | None = None,
    keep_next: bool = False,
) -> str:
    p_props = []
    if style:
        p_props.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        p_props.append("<w:keepNext/>")
    if num_id is not None:
        p_props.append(f"<w:numPr><w:ilvl w:val=\"0\"/><w:numId w:val=\"{num_id}\"/></w:numPr>")
    ppr = f"<w:pPr>{''.join(p_props)}</w:pPr>" if p_props else ""
    return f"<w:p>{ppr}{run(text, bold=bold, italic=italic)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(rows: Iterable[Iterable[str]]) -> str:
    cells_xml = []
    for row in rows:
        row_xml = []
        for cell in row:
            row_xml.append(
                "<w:tc>"
                '<w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr>'
                f"{para(cell)}"
                "</w:tc>"
            )
        cells_xml.append(f"<w:tr>{''.join(row_xml)}</w:tr>")
    return (
        "<w:tbl>"
        "<w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"D9D9D9\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"D9D9D9\"/>"
        "</w:tblBorders></w:tblPr>"
        f"{''.join(cells_xml)}"
        "</w:tbl>"
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="260"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="34"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/><w:color w:val="666666"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="360" w:after="200"/><w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="30"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="260" w:after="140"/><w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Quote">
    <w:name w:val="Quote"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:ind w:left="360"/><w:spacing w:before="80" w:after="160"/></w:pPr>
    <w:rPr><w:i/><w:color w:val="444444"/></w:rPr>
  </w:style>
</w:styles>
"""


def numbering_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="1">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="•"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:abstractNum w:abstractNumId="2">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1."/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
  <w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>
"""


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>
"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Guion defensa PFC Taller Mecanico ASIR</dc:title>
  <dc:creator>Claude</dc:creator>
  <cp:lastModifiedBy>Claude</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>
"""


def app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Cursor</Application>
</Properties>
"""


def build_document_xml() -> str:
    body: list[str] = []
    body.append(para(TITLE_MAIN.replace("\n", " "), style="Title"))
    for line in COVER_SUBTITLE:
        body.append(para(line, style="Subtitle"))
    body.append(para("Guion oral completo para defensa de 30 minutos", style="Subtitle", italic=True))
    body.append(page_break())

    body.append(para("Indice operativo", style="Heading1"))
    timeline = next(slide for slide in SLIDES if slide.id == "timeline")
    body.append(table([timeline.table_headers, *timeline.table_rows]))
    body.append(para("Uso recomendado", style="Heading2"))
    for tip in PRACTICE_TIPS:
        body.append(para(tip, num_id=1))
    body.append(page_break())

    body.append(para("Guion por diapositiva", style="Heading1"))
    for index, slide in enumerate(SLIDES, start=1):
        script = SCRIPT_BY_ID[slide.id]
        body.append(para(f"{index:02d}. {slide.title}", style="Heading2", keep_next=True))
        body.append(para(f"Tiempo estimado: {script.timebox}", bold=True))
        body.append(para(f"Objetivo comunicativo: {script.objective}", italic=True))
        body.append(para("Texto oral sugerido", bold=True))
        for paragraph in script.speech:
            body.append(para(paragraph))
        body.append(para("Indicaciones de demo o énfasis", bold=True))
        for item in script.demo:
            body.append(para(item, num_id=1))
        body.append(para(f"Transicion: {script.transition}", style="Quote"))

    body.append(page_break())
    body.append(para("Preguntas probables del tribunal", style="Heading1"))
    for question, answer in DEFENSE_QA:
        body.append(para(question, style="Heading2"))
        body.append(para(answer))

    body.append(para("Cierre de ensayo", style="Heading1"))
    body.append(
        para(
            "Si hay desviacion de tiempo, recortar antes las tablas y conservar las evidencias: app, Docker, Grafana y separacion source=app/source=simulator. La defensa debe transmitir criterio operativo, no solo enumerar herramientas."
        )
    )

    sect = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>'
        "</w:sectPr>"
    )
    body.append(sect)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14">'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )


def write_docx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types_xml())
        docx.writestr("_rels/.rels", root_rels_xml())
        docx.writestr("docProps/core.xml", core_xml())
        docx.writestr("docProps/app.xml", app_xml())
        docx.writestr("word/document.xml", build_document_xml())
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("word/numbering.xml", numbering_xml())
        docx.writestr("word/_rels/document.xml.rels", document_rels_xml())


if __name__ == "__main__":
    write_docx(OUTPUT)
    print(OUTPUT)
