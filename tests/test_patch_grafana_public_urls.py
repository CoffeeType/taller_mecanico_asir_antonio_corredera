#!/usr/bin/env python3
"""Tests for tools/patch_grafana_public_urls.py — public browser URLs in dashboard JSON."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from patch_grafana_public_urls import patch_dashboard  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "grafana_dashboard_urls_minimal.json"
HOST = "203.0.113.1"
APP = f"http://{HOST}"
PROM = f"http://{HOST}:9090"
AM = f"http://{HOST}:9093"
SIM = f"http://{HOST}:8890"


class PatchGrafanaPublicUrlsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.dash_path = Path(self.tmp) / "dashboard.json"
        shutil.copy(FIXTURE, self.dash_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _load(self) -> dict:
        return json.loads(self.dash_path.read_text(encoding="utf-8"))

    def test_patch_sets_four_url_variables_hidden(self) -> None:
        data = self._load()
        self.assertTrue(
            patch_dashboard(
                data,
                app_base=APP,
                prom_base=PROM,
                alertmanager_base=AM,
                traffic_simulator_base=SIM,
            )
        )
        by_name = {v["name"]: v for v in data["templating"]["list"]}
        self.assertEqual(by_name["prometheus_base"]["query"], PROM)
        self.assertEqual(by_name["taller_app_base"]["query"], APP)
        self.assertEqual(by_name["alertmanager_base"]["query"], AM)
        self.assertEqual(by_name["traffic_simulator_base"]["query"], SIM)
        for name in ("prometheus_base", "taller_app_base", "alertmanager_base", "traffic_simulator_base"):
            self.assertEqual(by_name[name]["hide"], 2)

    def test_patch_adds_alertmanager_and_simulator_links(self) -> None:
        data = self._load()
        patch_dashboard(
            data,
            app_base=APP,
            prom_base=PROM,
            alertmanager_base=AM,
            traffic_simulator_base=SIM,
        )
        titles = [lnk["title"] for lnk in data["links"]]
        self.assertIn("Alertmanager", titles)
        self.assertIn("Simulador de tráfico", titles)
        by_title = {lnk["title"]: lnk["url"] for lnk in data["links"]}
        self.assertEqual(by_title["Alertmanager"], "${alertmanager_base}")
        self.assertEqual(by_title["Simulador de tráfico"], "${traffic_simulator_base}")
        self.assertEqual(
            by_title["Test Email (Alertas)"],
            "${taller_app_base}/admin/test-alert-email.php",
        )


if __name__ == "__main__":
    unittest.main()
