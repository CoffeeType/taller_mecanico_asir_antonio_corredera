#!/usr/bin/env python3
"""Patch taller-mecanico Grafana dashboard: NOC layout, legend table, http_source variable."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "monitoring" / "grafana" / "dashboards" / "taller-mecanico-dashboard.json"

DS = {"type": "prometheus", "uid": "prometheus"}
DS_TEST = {"type": "grafana-testdata-datasource", "uid": "testdata"}

# Legend block: table (h=7) + note text (h=2) => NOC row starts at y=9
LEGEND_TABLE_H = 7
LEGEND_NOTE_H = 2
NOC_ROW_Y = LEGEND_TABLE_H + LEGEND_NOTE_H
NOC_STATS_Y = NOC_ROW_Y + 1
NOC_STATS_H = 5

LEGEND_CSV = (
    "Sección,Qué muestra\n"
    "NOC / Operaciones,\"Disponibilidad (up), alertas críticas, RED resumido (source=app)\"\n"
    "HTTP / aplicación,\"RED filtrable por variable Fuente HTTP (app, simulator, all)\"\n"
    "Simulador,\"Tráfico JMeter (source=simulator); ventanas cortas [1m] para alinear con la UI\"\n"
    "Host,\"CPU, RAM, disco y red (node_exporter)\"\n"
    "MySQL,\"Conexiones, QPS, consultas lentas\"\n"
    "Contenedores,\"CPU y RAM (cAdvisor)\"\n"
    "Negocio,\"KPIs de la app (usuarios, citas, noticias…)\""
)

LEGEND_NOTE = (
    "Durante pruebas de carga, cada petición JMeter también genera líneas `source=app` en el log; "
    "use la fila **Simulador** para la prueba y **HTTP** con fuente `app` para tráfico real."
)

NOC_STAT_LAYOUT = {
    1: {"x": 0, "w": 6},
    21: {"x": 6, "w": 4},
    14: {"x": 10, "w": 4},
    217: {"x": 14, "w": 5},
    216: {"x": 19, "w": 5},
}


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


def table_panel_style() -> tuple[dict, dict]:
    field_config = {
        "defaults": {
            "custom": {
                "align": "left",
                "cellOptions": {"type": "auto"},
                "inspect": False,
                "minWidth": 120,
                "wrapText": True,
            },
        },
        "overrides": [],
    }
    options = {
        "cellHeight": "lg",
        "showHeader": True,
        "footer": {"show": False, "reducer": ["sum"], "countRows": False, "fields": ""},
    }
    return field_config, options


def apply_table_style(panel: dict, column_overrides: list[dict] | None = None) -> None:
    fc, opts = table_panel_style()
    panel.setdefault("fieldConfig", {}).setdefault("defaults", {}).update(fc["defaults"])
    for k, v in fc["defaults"].get("custom", {}).items():
        panel["fieldConfig"]["defaults"].setdefault("custom", {})[k] = v
    if column_overrides:
        panel["fieldConfig"]["overrides"] = column_overrides
    panel["options"] = {**opts, **panel.get("options", {})}
    panel["options"]["cellHeight"] = "lg"
    panel["options"].setdefault("footer", {})["show"] = False


def legend_table_panel() -> dict:
    fc, opts = table_panel_style()
    fc["overrides"] = [
        {
            "matcher": {"id": "byName", "options": "Sección"},
            "properties": [{"id": "custom.width", "value": 220}],
        },
        {
            "matcher": {"id": "byName", "options": "Qué muestra"},
            "properties": [{"id": "custom.width", "value": 480}],
        },
    ]
    return {
        "id": 200,
        "title": "Leyenda de secciones",
        "type": "table",
        "gridPos": {"h": LEGEND_TABLE_H, "w": 24, "x": 0, "y": 0},
        "datasource": DS_TEST,
        "targets": [
            {
                "datasource": DS_TEST,
                "refId": "A",
                "scenarioId": "csv_content",
                "csvContent": LEGEND_CSV,
            }
        ],
        "fieldConfig": fc,
        "options": opts,
    }


def legend_note_panel() -> dict:
    return {
        "id": 203,
        "type": "text",
        "title": "",
        "gridPos": {"h": LEGEND_NOTE_H, "w": 24, "x": 0, "y": LEGEND_TABLE_H},
        "options": {"mode": "markdown", "content": LEGEND_NOTE},
        "transparent": True,
    }


def stat_panel(
    pid: int,
    title: str,
    expr: str,
    x: int,
    y: int,
    w: int,
    h: int = 5,
    unit: str = "none",
    desc: str = "",
) -> dict:
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

    # Legend: native table + note
    legend = legend_table_panel()
    if 200 in by_id:
        by_id[200].clear()
        by_id[200].update(legend)
    else:
        data["panels"].insert(0, legend)

    note = legend_note_panel()
    if 203 in by_id:
        by_id[203].clear()
        by_id[203].update(note)
    else:
        data["panels"].insert(1, note)
        by_id = {p["id"]: p for p in data["panels"] if "id" in p}

    if 23 in by_id:
        by_id[23]["title"] = "NOC / Operaciones"

    if 21 in by_id:
        by_id[21]["title"] = "Avisos críticos"
        by_id[21]["targets"][0]["expr"] = (
            'count(ALERTS{alertstate="firing", severity="critical"}) or vector(0)'
        )
        by_id[21].setdefault("options", {})["noValue"] = "0"
        by_id[21]["options"]["textMode"] = "value"

    if 1 in by_id:
        by_id[1]["options"]["orientation"] = "horizontal"
        by_id[1]["options"]["textMode"] = "value_and_name"

    if 17 in by_id:
        by_id[17]["gridPos"]["h"] = 8
        by_id[17]["description"] = (
            "Alertas críticas activas. Mira primero componente y estado para saber qué servicio requiere "
            "atención. Sin alertas críticas activas la tabla quedará vacía (comportamiento normal)."
        )
        apply_table_style(
            by_id[17],
            [
                {
                    "matcher": {"id": "byName", "options": "Alerta"},
                    "properties": [{"id": "custom.width", "value": 220}],
                },
                {
                    "matcher": {"id": "byName", "options": "Componente"},
                    "properties": [{"id": "custom.width", "value": 160}],
                },
                {
                    "matcher": {"id": "byName", "options": "Severidad"},
                    "properties": [{"id": "custom.width", "value": 110}],
                },
            ],
        )
        for tr in by_id[17].get("transformations", []):
            if tr.get("id") == "organize":
                tr.setdefault("options", {})["indexByName"] = {
                    "alertname": 0,
                    "component": 1,
                    "alertstate": 2,
                    "severity": 3,
                }

    if 22 in by_id:
        by_id[22]["gridPos"]["h"] = 8
        by_id[22]["description"] = (
            "Resumen de alertas críticas por componente. Los valores más altos aparecen arriba."
        )
        apply_table_style(
            by_id[22],
            [
                {
                    "matcher": {"id": "byName", "options": "Componente"},
                    "properties": [{"id": "custom.width", "value": 200}],
                },
                {
                    "matcher": {"id": "byName", "options": "Críticos activos"},
                    "properties": [
                        {"id": "custom.align", "value": "right"},
                        {"id": "custom.width", "value": 140},
                    ],
                },
            ],
        )

    if 214 in by_id:
        apply_table_style(
            by_id[214],
            [
                {
                    "matcher": {"id": "byName", "options": "Método"},
                    "properties": [{"id": "custom.width", "value": 100}],
                },
                {
                    "matcher": {"id": "byName", "options": "HTTP"},
                    "properties": [{"id": "custom.width", "value": 90}],
                },
                {
                    "matcher": {"id": "byName", "options": "Peticiones"},
                    "properties": [
                        {"id": "custom.align", "value": "right"},
                        {"id": "custom.width", "value": 120},
                    ],
                },
            ],
        )

    # HTTP panels — source variable
    if 2 in by_id:
        by_id[2]["title"] = "Tráfico HTTP (por fuente)"
        by_id[2]["description"] = "Peticiones/s según variable Fuente HTTP (`$http_source`)."
        by_id[2]["targets"][0]["expr"] = (
            'sum(rate(app_http_requests_total{source=~"$http_source"}[5m])) by (method)'
        )

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
        by_id[4]["description"] = (
            "Percentiles desde response_time.log filtrados por fuente en el exporter."
        )
        for t in by_id[4]["targets"]:
            for q in ("0.5", "0.95", "0.99"):
                if f'quantile="{q}"' in t.get("expr", ""):
                    t["expr"] = (
                        f'app_http_response_time_seconds{{quantile="{q}",source=~"$http_source"}}'
                    )
                    break

    for pid in (18, 19, 20):
        if pid not in by_id:
            continue
        for t in by_id[pid]["targets"]:
            t["expr"] = t["expr"].replace("[5m]", "[1m]")

    if 20 in by_id:
        by_id[20]["description"] = (
            "Porcentaje 4xx–5xx del simulador (ventana 1m). Sin tráfico reciente puede quedar vacío."
        )

    existing_ids = {p["id"] for p in data["panels"]}
    new_panels = []

    noc_y = NOC_STATS_Y
    if 216 not in existing_ids:
        new_panels.append(
            stat_panel(
                216,
                "NOC: error HTTP app %",
                '100 * sum(rate(app_http_requests_total{source="app",status=~"[45].."}[5m])) '
                '/ clamp_min(sum(rate(app_http_requests_total{source="app"}[5m])), 0.001)',
                19,
                noc_y,
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
                14,
                noc_y,
                5,
                unit="reqps",
                desc="RED — tasa de peticiones de aplicación.",
            )
        )

    sim_y_base = NOC_ROW_Y + 43
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
                    '100 * sum(rate(app_http_requests_total{source="simulator",status=~"[45].."}[1m])) '
                    '/ clamp_min(sum(rate(app_http_requests_total{source="simulator"}[1m])), 0.001)',
                    18,
                    sim_y_base,
                    6,
                    4,
                    "percent",
                ),
            ]
        )

    if 214 not in existing_ids:
        p214 = {
            "id": 214,
            "title": "Simulador: desglose por método y código",
            "description": "Conteo en el rango de tiempo del dashboard (alineado con la UI del simulador).",
            "type": "table",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": sim_y_base + 20},
            "datasource": DS,
            "targets": [
                prom_target(
                    'sum by (method, status) (increase(app_http_requests_total{source="simulator"}[$__range]))',
                    "",
                    instant=True,
                )
            ],
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
        apply_table_style(p214)
        p214["options"]["sortBy"] = [{"desc": True, "displayName": "Peticiones"}]
        new_panels.append(p214)

    if 215 not in existing_ids:
        new_panels.append(
            {
                "id": 215,
                "title": "Simulador: latencia p50 / p95",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": sim_y_base + 20},
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
    by_id = {p["id"]: p for p in data["panels"] if "id" in p}

    noc_table_17_y = NOC_STATS_Y + NOC_STATS_H
    noc_table_22_y = noc_table_17_y + 8
    http_row_y = noc_table_22_y + 8

    layout = {
        200: 0,
        203: LEGEND_TABLE_H,
        23: NOC_ROW_Y,
        1: NOC_STATS_Y,
        21: NOC_STATS_Y,
        14: NOC_STATS_Y,
        216: NOC_STATS_Y,
        217: NOC_STATS_Y,
        17: noc_table_17_y,
        22: noc_table_22_y,
        24: http_row_y,
        2: http_row_y + 1,
        3: http_row_y + 1,
        4: http_row_y + 9,
        5: http_row_y + 9,
        29: http_row_y + 17,
        201: http_row_y + 18,
        210: http_row_y + 21,
        211: http_row_y + 21,
        212: http_row_y + 21,
        213: http_row_y + 21,
        18: http_row_y + 25,
        19: http_row_y + 25,
        20: http_row_y + 33,
        214: http_row_y + 41,
        215: http_row_y + 41,
        25: http_row_y + 49,
        8: http_row_y + 50,
        9: http_row_y + 50,
        16: http_row_y + 58,
        26: http_row_y + 66,
        6: http_row_y + 67,
        7: http_row_y + 67,
        15: http_row_y + 75,
        28: http_row_y + 83,
        30: http_row_y + 84,
        31: http_row_y + 84,
        27: http_row_y + 92,
        10: http_row_y + 93,
        11: http_row_y + 93,
        12: http_row_y + 93,
        13: http_row_y + 93,
    }

    layout_pos = {
        17: {"x": 0, "w": 24},
        22: {"x": 0, "w": 24},
        **{pid: pos for pid, pos in NOC_STAT_LAYOUT.items()},
    }

    for p in data["panels"]:
        pid = p.get("id")
        if pid in layout and "gridPos" in p:
            p["gridPos"]["y"] = layout[pid]
        if pid in layout_pos and "gridPos" in p:
            p["gridPos"].update(layout_pos[pid])
        if pid in (1, 21, 14, 216, 217) and "gridPos" in p:
            p["gridPos"]["h"] = NOC_STATS_H
        if pid == 23:
            p["gridPos"]["y"] = NOC_ROW_Y
        if pid == 29:
            p["title"] = "Simulador (JMeter)"

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
