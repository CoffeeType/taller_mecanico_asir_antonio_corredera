#!/usr/bin/env python3
"""Patch taller-mecanico Grafana dashboard: NOC layout, http_source variable, simulator sync."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "monitoring" / "grafana" / "dashboards" / "taller-mecanico-dashboard.json"

DS = {"type": "prometheus", "uid": "prometheus"}


def prom_target(expr: str, legend: str = "", ref: str = "A", instant: bool = False) -> dict:
    t = {
        "datasource": DS,
        "editorMode": "code",
        "expr": expr,
        "legendFormat": legend,
        "range": not instant,
        "refId": ref,
    }
    if instant:
        t["instant"] = True
    return t


def stat_panel(pid: int, title: str, expr: str, x: int, y: int, w: int, h: int = 5, unit: str = "none", desc: str = "") -> dict:
    p = {
        "id": pid,
        "title": title,
        "type": "stat",
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": [prom_target(expr, "__auto", instant=True)],
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "decimals": 2 if unit == "percent" else 0,
                "unit": unit,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 1 if unit == "percent" else 10},
                        {"color": "red", "value": 5 if unit == "percent" else 50},
                    ],
                },
            },
            "overrides": [],
        },
        "options": {
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto",
        },
    }
    if desc:
        p["description"] = desc
    return p


def main() -> None:
    data = json.loads(DASH.read_text(encoding="utf-8"))
    data["refresh"] = "15s"
    data["version"] = data.get("version", 4) + 1

    by_id = {p["id"]: p for p in data["panels"] if "id" in p}

    # Legend
    if 200 in by_id:
        by_id[200]["options"]["content"] = (
            "| Sección | Qué muestra |\n"
            "|---------|---------------|\n"
            "| **NOC / Operaciones** | Disponibilidad (`up`), alertas críticas, RED resumido (`source=app`) |\n"
            "| **HTTP / aplicación** | RED filtrable por variable *Fuente HTTP* (`app`, `simulator`, `all`) |\n"
            "| **Simulador** | Tráfico JMeter (`source=simulator`); ventanas cortas `[1m]` para alinear con la UI |\n"
            "| **Host** | CPU, RAM, disco y red (node_exporter) |\n"
            "| **MySQL** | Conexiones, QPS, consultas lentas |\n"
            "| **Contenedores** | CPU y RAM (cAdvisor) |\n"
            "| **Negocio** | KPIs de la app (usuarios, citas, noticias…) |\n\n"
            "Durante pruebas de carga, cada petición JMeter también genera líneas `source=app` en el log; "
            "use la fila **Simulador** para la prueba y **HTTP** con fuente `app` para tráfico real."
        )

    if 23 in by_id:
        by_id[23]["title"] = "NOC / Operaciones"

    # HTTP panels — source variable
    if 2 in by_id:
        by_id[2]["title"] = "Tráfico HTTP (por fuente)"
        by_id[2]["description"] = "Peticiones/s según variable Fuente HTTP (`$http_source`)."
        by_id[2]["targets"][0]["expr"] = 'sum(rate(app_http_requests_total{source=~"$http_source"}[5m])) by (method)'

    if 3 in by_id:
        by_id[3]["description"] = "Errores 4xx/5xx sobre el total de la fuente seleccionada."
        by_id[3]["targets"][0]["expr"] = (
            'sum(rate(app_http_requests_total{source=~"$http_source",status=~"5.."}[5m])) '
            '/ sum(rate(app_http_requests_total{source=~"$http_source"}[5m])) * 100'
        )
        by_id[3]["targets"][1]["expr"] = (
            'sum(rate(app_http_requests_total{source=~"$http_source",status=~"4.."}[5m])) '
            '/ sum(rate(app_http_requests_total{source=~"$http_source"}[5m])) * 100'
        )

    if 4 in by_id:
        by_id[4]["description"] = "Percentiles desde response_time.log filtrados por fuente en el exporter."
        quantile_map = {
            "0.5": "p50 (Mediana)",
            "0.95": "p95 (95%)",
            "0.99": "p99 (99%)",
        }
        for t in by_id[4]["targets"]:
            for q, _ in quantile_map.items():
                if f'quantile="{q}"' in t.get("expr", ""):
                    t["expr"] = f'app_http_response_time_seconds{{quantile="{q}",source=~"$http_source"}}'
                    break

    # Simulator timeseries — 1m windows
    for pid, legend_a, legend_b in ((18, None, None), (19, "éxitos", "errores"), (20, "% errores", None)):
        if pid not in by_id:
            continue
        for t in by_id[pid]["targets"]:
            t["expr"] = t["expr"].replace("[5m]", "[1m]")

    if 20 in by_id:
        by_id[20]["description"] = (
            "Porcentaje 4xx–5xx del simulador (ventana 1m). Sin tráfico reciente puede quedar vacío."
        )

    # Remove old simulator-only panels if re-adding
    existing_ids = {p["id"] for p in data["panels"]}
    new_panels = []

    if 216 not in existing_ids:
        new_panels.append(
            stat_panel(
                216,
                "NOC: error HTTP app %",
                '100 * sum(rate(app_http_requests_total{source="app",status=~"[45].."}[5m])) / clamp_min(sum(rate(app_http_requests_total{source="app"}[5m])), 0.001)',
                14,
                5,
                5,
                unit="percent",
                desc="RED — errores 4xx–5xx sobre tráfico real (source=app).",
            )
        )
    if 217 not in existing_ids:
        new_panels.append(
            stat_panel(
                217,
                "NOC: req/s app",
                'sum(rate(app_http_requests_total{source="app"}[5m]))',
                19,
                5,
                5,
                unit="reqps",
                desc="RED — tasa de peticiones de aplicación.",
            )
        )

    sim_y_base = 36
    if 210 not in existing_ids:
        new_panels.extend(
            [
                stat_panel(
                    210,
                    "Sim: GET req/s",
                    'sum(rate(app_http_requests_total{source="simulator",method="GET"}[1m]))',
                    0,
                    sim_y_base,
                    6,
                    4,
                    "reqps",
                ),
                stat_panel(
                    211,
                    "Sim: éxitos (2m)",
                    'sum(increase(app_http_requests_total{source="simulator",status=~"[23].."}[2m]))',
                    6,
                    sim_y_base,
                    6,
                    4,
                    "none",
                ),
                stat_panel(
                    212,
                    "Sim: errores (2m)",
                    'sum(increase(app_http_requests_total{source="simulator",status=~"[45].."}[2m]))',
                    12,
                    sim_y_base,
                    6,
                    4,
                    "none",
                ),
                stat_panel(
                    213,
                    "Sim: % error",
                    '100 * sum(rate(app_http_requests_total{source="simulator",status=~"[45].."}[1m])) / clamp_min(sum(rate(app_http_requests_total{source="simulator"}[1m])), 0.001)',
                    18,
                    sim_y_base,
                    6,
                    4,
                    "percent",
                ),
            ]
        )

    if 214 not in existing_ids:
        new_panels.append(
            {
                "id": 214,
                "title": "Simulador: desglose por método y código",
                "description": "Conteo en el rango de tiempo del dashboard (alineado con la UI del simulador).",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 56},
                "datasource": DS,
                "targets": [
                    prom_target(
                        'sum by (method, status) (increase(app_http_requests_total{source="simulator"}[$__range]))',
                        "",
                        instant=True,
                    )
                ],
                "fieldConfig": {"defaults": {}, "overrides": []},
                "options": {"showHeader": True, "sortBy": [{"desc": True, "displayName": "Value"}]},
                "transformations": [
                    {
                        "id": "organize",
                        "options": {
                            "excludeByName": {"Time": True},
                            "renameByName": {
                                "method": "Método",
                                "status": "HTTP",
                                "Value": "Peticiones",
                            },
                        },
                    }
                ],
            }
        )

    if 215 not in existing_ids:
        new_panels.append(
            {
                "id": 215,
                "title": "Simulador: latencia p50 / p95",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 56},
                "datasource": DS,
                "targets": [
                    prom_target(
                        'app_http_response_time_seconds{quantile="0.5",source="simulator"}',
                        "p50",
                        "A",
                    ),
                    prom_target(
                        'app_http_response_time_seconds{quantile="0.95",source="simulator"}',
                        "p95",
                        "B",
                    ),
                ],
                "fieldConfig": {
                    "defaults": {"unit": "s", "custom": {"drawStyle": "line", "lineWidth": 2}},
                    "overrides": [],
                },
                "options": {
                    "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["last", "max"]},
                    "tooltip": {"mode": "multi"},
                },
            }
        )

    data["panels"].extend(new_panels)

    # Layout: reposition major sections (y only)
    layout = {
        200: 0,
        23: 4,
        1: 5,
        21: 5,
        14: 5,
        17: 10,
        216: 5,
        217: 5,
        22: 15,
        24: 20,
        2: 21,
        3: 21,
        4: 29,
        5: 29,
        29: 37,
        201: 38,
        210: 41,
        211: 41,
        212: 41,
        213: 41,
        18: 45,
        19: 45,
        20: 53,
        214: 61,
        215: 61,
        25: 69,
        8: 70,
        9: 70,
        16: 78,
        26: 86,
        6: 87,
        7: 87,
        15: 95,
        28: 103,
        30: 104,
        31: 104,
        27: 112,
        10: 113,
        11: 113,
        12: 113,
        13: 113,
    }

    layout_x = {17: {"x": 0, "w": 24}, 216: {"x": 13, "w": 5}, 217: {"x": 18, "w": 6}}

    for p in data["panels"]:
        pid = p.get("id")
        if pid in layout and "gridPos" in p:
            p["gridPos"]["y"] = layout[pid]
        if pid in layout_x and "gridPos" in p:
            p["gridPos"].update(layout_x[pid])
        if pid == 23:
            p["gridPos"]["y"] = 4
        if pid == 29:
            p["title"] = "Simulador (JMeter)"

    # Templating: http_source
    http_src_var = {
        "current": {"selected": True, "text": "app", "value": "app"},
        "hide": 0,
        "includeAll": False,
        "label": "Fuente HTTP",
        "multi": False,
        "name": "http_source",
        "options": [
            {"selected": True, "text": "app", "value": "app"},
            {"selected": False, "text": "simulator", "value": "simulator"},
            {"selected": False, "text": "all", "value": "app|simulator"},
        ],
        "query": "app,simulator,app|simulator",
        "skipUrlSync": False,
        "type": "custom",
    }
    names = [v["name"] for v in data["templating"]["list"]]
    if "http_source" not in names:
        data["templating"]["list"].insert(0, http_src_var)

    DASH.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {DASH} (version {data['version']})")


if __name__ == "__main__":
    main()
