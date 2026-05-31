# Simulador de tráfico con Apache JMeter (referencia técnica)

En la memoria del proyecto, esta capacidad se describe como **pruebas de carga con Apache JMeter**. En Docker Compose el perfil y los servicios son `traffic`, `traffic-simulator` (worker) y `traffic-simulator-ui` (interfaz web). El worker ejecuta **JMeter en modo CLI (sin GUI)** y vuelca resultados al mismo formato de logs que consume la aplicación para Prometheus (`logs/metrics.log`, `logs/response_time.log`).

> **Nuevos operadores:** sigue la guía paso a paso con el propósito de cada control de la interfaz en **[GUIA_JMETER_USUARIO.md](GUIA_JMETER_USUARIO.md)**. Este documento cubre arranque mínimo, checklist de métricas, API interna, CLI y diagnóstico.

---

## Arranque mínimo

| Entorno | Comando | URL UI |
|---------|---------|--------|
| Windows | `.\scripts\start-jmeter-ui.ps1` | http://localhost:8890 |
| Linux/macOS | `docker compose --profile traffic up -d` (tras `.env` desde `.env.example`) | `TRAFFIC_SIMULATOR_UI_HOST_PORT` |
| AWS EC2 | Tras [`scripts/deploy_aws_docker.sh`](../scripts/deploy_aws_docker.sh) | `TRAFFIC_SIMULATOR_UI_HOST_PORT` (8890 por defecto) |

Salud: `curl -sS http://localhost:8890/health.php` → `"status":"ok"`.

Sin el perfil `traffic` no se levantan worker ni UI: usa **`docker compose --profile traffic ...`**.

### Variables típicas en `.env`

```env
SIMULATOR_CONTROL_TOKEN=tu_token_largo_seguro
SIM_BASE_URL=http://web
TRAFFIC_SIMULATOR_UI_HOST_PORT=8890
MONITORING_UI_HOST_BIND=0.0.0.0
SIM_UI_DEFAULT_BASE_URL=http://web
JMETER_VERSION=5.6.3
SIM_JMETER_HEAP="-Xms128m -Xmx256m -XX:MaxMetaspaceSize=128m"
SIM_JMETER_WORK_DIR=/var/www/html/logs/jmeter
SIM_JMETER_HTML_REPORT=true
PROMETHEUS_EXTERNAL_URL=http://localhost:9090
GRAFANA_EXTERNAL_URL=http://localhost:3000
```

Tabla completa de variables para operadores: [GUIA_JMETER_USUARIO.md § Variables](GUIA_JMETER_USUARIO.md#5-variables-de-configuración-env).

### CLI opcional (operador de confianza)

```bash
docker compose run --rm traffic-simulator \
  php scripts/run_jmeter_traffic.php --users=3 --duration=30 --profile=normal --base-url=http://web
```

---

## Comprobar que las métricas reflejan una web “real”

Para que Prometheus y Grafana muestren el mismo tipo de series que con usuarios reales, hace falta la cadena completa de observabilidad:

- [ ] `docker compose ps` incluye `web`, `traffic-simulator`, `traffic-simulator-ui` y, para gráficos en Grafana, **Prometheus y Grafana** (perfil `monitoring`).
- [ ] Los tres servicios anteriores montan el **mismo** volumen `./logs` en `/var/www/html/logs` (si `web` no monta `./logs`, `metrics.php` no verá las líneas que escribe JMeter).
- [ ] Durante una prueba, aumentan líneas con `source=simulator` en `logs/metrics.log` (o `grep -c source=simulator` dentro del contenedor `traffic-simulator`).
- [ ] `curl` a `/metrics.php` en la app (o el target de Prometheus) muestra contadores con etiqueta `source="simulator"`.
- [ ] En Grafana, el dashboard principal muestra actividad en la fila **Simulador** y en los paneles dedicados a JMeter (18–20), filtrando por `source="simulator"`.

---

## Referencia técnica

### Dónde está el control

- **`traffic-simulator`**: API HTTP interna en **:8085**; genera un plan JMX temporal, ejecuta JMeter y convierte `results.jtl` a logs. Solo debe ser alcanzable desde la red Docker.
- **`traffic-simulator-ui`**: interfaz en el puerto publicado del host (por defecto **8890**). Definición compartida en [`compose/traffic-services.yml`](../compose/traffic-services.yml) (local y AWS); variables `TRAFFIC_SIMULATOR_UI_HOST_PORT` y `MONITORING_UI_HOST_BIND`. El token `SIMULATOR_CONTROL_TOKEN` solo existe en el servidor; [`docker/traffic-simulator-ui/public/api.php`](../docker/traffic-simulator-ui/public/api.php) reenvía las peticiones con el token. La UI muestra estadísticas y vista previa **filtradas a `source=simulator`** (alineado con la fila Simulador en Grafana).

JMeter se instala en la imagen del worker en el build (Java 17; versión `JMETER_VERSION`, por defecto **5.6.3**).

### Artefactos por ejecución (bajo `SIM_JMETER_WORK_DIR`)

- `traffic-test.jmx`, `routes.csv`, `results.jtl`, `jmeter.log`, `stdout.log`.
- Comando equivalente: `jmeter -n -t traffic-test.jmx -l results.jtl -j jmeter.log`.
- Importación a `logs/metrics.log` (`GET 200 /ruta target_host=host run_id=… source=simulator`) y `logs/response_time.log` (tiempos con `run_id` y `source`).
- `SIM_JMETER_HEAP` y `TRAFFIC_SIMULATOR_MEM_LIMIT` deben subirse a la par si aumentas carga.
- `SIM_JMETER_HTML_REPORT=true`: informe en `html-report`; CSS opcional vía `SIM_JMETER_REPORT_CSS_SOURCE`.

### Webs externas (uso responsable)

- Solo **http** / **https**.
- IPs RFC1918 / loopback / reservadas rechazadas salvo **`SIM_ALLOW_PRIVATE_TARGETS=true`** (laboratorio).
- Hosts no listados en `SIM_INTERNAL_HOSTS`: confirmación en UI (`confirm_external` en API).
- **`SIM_EXTERNAL_TARGETS_ENABLED=false`**: solo objetivos “internos”.
- **`SIM_SSL_VERIFY=true`**: verificación TLS por defecto.

CLI (`run_jmeter_traffic.php`, `simulate_traffic.php`): operador confiable; misma política de IPs y externos.

### API de control (`:8085`)

| Método | Ruta      | Auth |
|--------|-----------|------|
| GET    | `/health` | No   |
| GET    | `/status` | `X-Simulator-Token` o `Bearer` |
| POST   | `/start`  | Igual; JSON: `users`, `duration`, `profile`, `base_url`, `confirm_external`, opcional `routes_file` |
| POST   | `/stop`   | Igual |

La UI expone **`/api.php`** con acciones `probe`, `start`, `stop`, `reset`.

### Métricas y Grafana

- App: `source=app` (véase `includes/metrics_logger.php`).
- JMeter: `source=simulator` tras importar el JTL.
- Exporter: [`monitoring/php-exporter/metrics.php`](../monitoring/php-exporter/metrics.php) → `app_http_requests_total{method,status,source}`.
- La UI devuelve además `success_requests`, `error_requests`, `recent_success`, `recent_errors`, `recent_window`, `statuses`.

### Si la simulación corre pero Grafana no muestra nada

1. Mismo volumen `./logs` en `web`, `traffic-simulator` y `traffic-simulator-ui`.
2. `SIM_LOG_DIR=/var/www/html/logs` en la UI; evita rutas relativas fuera del árbol de la app.
3. `docker compose exec traffic-simulator tail -80 /tmp/traffic_simulator.log` y GET `/status` para rutas de `results.jtl` y `jmeter.log`.
4. Tras cambios en `metrics.php`: `docker compose build web`.

Más causas habituales para operadores: [GUIA_JMETER_USUARIO.md § Errores frecuentes](GUIA_JMETER_USUARIO.md#6-buenas-prácticas-y-errores-frecuentes).

### Tests y smoke

```bash
docker run --rm -v "%cd%:/app" -w /app php:8.2-cli php tests/test_traffic_simulator_lib.php
```

```bash
docker compose build web traffic-simulator traffic-simulator-ui
```

```bash
docker compose --profile traffic up -d web mysql traffic-simulator traffic-simulator-ui
TOKEN="${SIMULATOR_CONTROL_TOKEN:-changeme_traffic_sim_secret}"
docker compose exec -T traffic-simulator sh -lc \
  'curl -sf -H "Content-Type: application/json" -H "X-Simulator-Token: '"$TOKEN"'" \
  --data "{\"users\":1,\"duration\":5,\"profile\":\"burst\",\"base_url\":\"http://web\",\"confirm_external\":true}" \
  http://127.0.0.1:8085/start'
docker compose exec -T traffic-simulator sh -lc 'tail -20 "${SIM_LOG_DIR:-/var/www/html/logs}/metrics.log"'
```

Tras desplegar en EC2, el script `deploy_aws_docker.sh` ejecuta un smoke similar cuando el perfil `traffic` está activo (omisible con `SKIP_TRAFFIC_SMOKE=1`). Al final del despliegue y en el *user data* de EC2 se imprime también la guía operativa vía `scripts/print-jmeter-usage.sh` (enlaza [GUIA_JMETER_USUARIO.md](GUIA_JMETER_USUARIO.md)).
