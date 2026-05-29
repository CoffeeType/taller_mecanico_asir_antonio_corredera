#!/usr/bin/env python3
"""Add target_host variable and filter simulator panels in Grafana dashboard."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "monitoring" / "grafana" / "dashboards" / "taller-mecanico-dashboard.json"

# 215 = latencia (summary sin label target_host en el exporter)
SIM_PANEL_IDS = {18, 19, 20, 210, 211, 212, 213, 214}


def main() -> None:
    data = json.loads(DASH.read_text(encoding="utf-8"))
    data["version"] = data.get("version", 5) + 1

    var = {
        "allValue": ".*",
        "current": {"selected": True, "text": "All", "value": "$__all"},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "definition": 'label_values(app_http_requests_total{source="simulator"}, target_host)',
        "hide": 0,
        "includeAll": True,
        "label": "Host simulador",
        "multi": False,
        "name": "target_host",
        "options": [],
        "query": {
            "query": 'label_values(app_http_requests_total{source="simulator"}, target_host)',
            "refId": "StandardVariableQuery",
        },
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "type": "query",
    }
    names = [v.get("name") for v in data["templating"]["list"]]
    if "target_host" not in names:
        data["templating"]["list"].insert(1, var)

    for panel in data["panels"]:
        pid = panel.get("id")
        if pid not in SIM_PANEL_IDS:
            continue
        for target in panel.get("targets", []):
            expr = target.get("expr", "")
            if "source=\"simulator\"" not in expr and "source=\\\"simulator\\\"" not in expr:
                continue
            if "target_host" in expr:
                continue
            expr = expr.replace(
                'source="simulator"',
                'source="simulator",target_host=~"$target_host"',
            )
            target["expr"] = expr

    DASH.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched {DASH}")


if __name__ == "__main__":
    main()
