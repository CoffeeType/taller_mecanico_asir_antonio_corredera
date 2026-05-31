#!/usr/bin/env python3
"""Patch Grafana dashboard templating URLs and dashboard links for public browser access."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

URL_VAR_SPECS = (
    ("prometheus_base", "Prometheus (URL base)"),
    ("taller_app_base", "App PHP (URL base)"),
    ("alertmanager_base", "Alertmanager (URL base)"),
    ("traffic_simulator_base", "Simulador de tráfico (URL base)"),
)

LINK_SPECS = (
    {
        "title": "Prometheus",
        "url": "${prometheus_base}",
        "tooltip": "Ir a Prometheus",
        "icon": "external link",
    },
    {
        "title": "Alertmanager",
        "url": "${alertmanager_base}",
        "tooltip": "Ir a Alertmanager",
        "icon": "external link",
    },
    {
        "title": "Test Email (Alertas)",
        "url": "${taller_app_base}/admin/test-alert-email.php",
        "tooltip": (
            "Abre el panel admin de prueba de alertas. Debes iniciar sesión como administrador "
            "en la app; si no, verás el login y luego esta página."
        ),
        "icon": "external link",
    },
    {
        "title": "Simulador de tráfico",
        "url": "${traffic_simulator_base}",
        "tooltip": "Ir a la UI del simulador JMeter",
        "icon": "external link",
    },
)


def _textbox_var(name: str, label: str, value: str) -> dict[str, Any]:
    return {
        "current": {"selected": True, "text": value, "value": value},
        "hide": 2,
        "label": label,
        "name": name,
        "query": value,
        "skipUrlSync": False,
        "type": "textbox",
    }


def _link_entry(spec: dict[str, str]) -> dict[str, Any]:
    return {
        "asDropdown": False,
        "icon": spec.get("icon", "external link"),
        "includeVars": False,
        "keepTime": False,
        "tags": [],
        "targetBlank": True,
        "title": spec["title"],
        "tooltip": spec.get("tooltip", ""),
        "type": "link",
        "url": spec["url"],
    }


def patch_dashboard(
    data: dict[str, Any],
    *,
    app_base: str,
    prom_base: str,
    alertmanager_base: str,
    traffic_simulator_base: str,
) -> bool:
    values = {
        "prometheus_base": prom_base,
        "taller_app_base": app_base,
        "alertmanager_base": alertmanager_base,
        "traffic_simulator_base": traffic_simulator_base,
    }
    labels = {name: label for name, label in URL_VAR_SPECS}

    templating = data.setdefault("templating", {})
    var_list: list[dict[str, Any]] = list(templating.get("list") or [])
    by_name = {v.get("name"): i for i, v in enumerate(var_list) if v.get("name")}

    changed = False
    for name, label in URL_VAR_SPECS:
        new_var = _textbox_var(name, label, values[name])
        if name in by_name:
            idx = by_name[name]
            if var_list[idx] != new_var:
                var_list[idx] = new_var
                changed = True
        else:
            var_list.append(new_var)
            changed = True

    templating["list"] = var_list

    managed_titles = {s["title"] for s in LINK_SPECS}
    existing_links: list[dict[str, Any]] = list(data.get("links") or [])
    preserved = [lnk for lnk in existing_links if lnk.get("title") not in managed_titles]
    new_links = [_link_entry(s) for s in LINK_SPECS]
    doc_links = [lnk for lnk in existing_links if lnk.get("title") == "Documentación"]
    if not doc_links:
        doc_links = [
            _link_entry(
                {
                    "title": "Documentación",
                    "url": "https://github.com/CoffeeType/taller_mecanico_asir/blob/main/docs/MONITORING_SETUP_GUIDE.md",
                    "tooltip": "Guía de monitoreo",
                    "icon": "doc",
                }
            )
        ]
    merged_links = new_links + doc_links + [
        lnk for lnk in preserved if lnk.get("title") != "Documentación"
    ]
    if data.get("links") != merged_links:
        data["links"] = merged_links
        changed = True

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Grafana dashboard public URLs.")
    parser.add_argument("dashboard", type=Path, help="Path to dashboard JSON")
    parser.add_argument("--app-base", required=True)
    parser.add_argument("--prom-base", required=True)
    parser.add_argument("--alertmanager-base", required=True)
    parser.add_argument("--traffic-simulator-base", required=True)
    args = parser.parse_args()

    path = args.dashboard
    if not path.is_file():
        print(f"ERROR: dashboard not found: {path}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    changed = patch_dashboard(
        data,
        app_base=args.app_base.rstrip("/"),
        prom_base=args.prom_base.rstrip("/"),
        alertmanager_base=args.alertmanager_base.rstrip("/"),
        traffic_simulator_base=args.traffic_simulator_base.rstrip("/"),
    )

    if not changed:
        return 0

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
