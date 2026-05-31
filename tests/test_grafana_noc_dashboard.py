#!/usr/bin/env python3
"""Tests for NOC panels in taller-mecanico Grafana dashboard."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "monitoring" / "grafana" / "dashboards" / "taller-mecanico-dashboard.json"
NOC_STAT_IDS = (1, 21, 14, 216, 217)
TABLE_IDS = (17, 22, 214)


def panel_by_id(data: dict, pid: int) -> dict:
    for p in data.get("panels", []):
        if p.get("id") == pid:
            return p
    raise KeyError(f"panel id {pid}")


def noc_stat_panels(data: dict) -> list[dict]:
    y = panel_by_id(data, 1)["gridPos"]["y"]
    return [
        panel_by_id(data, pid)
        for pid in NOC_STAT_IDS
        if panel_by_id(data, pid)["gridPos"]["y"] == y
    ]


class GrafanaNocDashboardTest(unittest.TestCase):
    """Asserts on the committed dashboard JSON (regenerate with tools/patch_grafana_noc_dashboard.py)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DASH.read_text(encoding="utf-8"))

    def test_critical_count_stat_shows_zero_not_no_data(self) -> None:
        p = panel_by_id(self.data, 21)
        expr = p["targets"][0]["expr"]
        self.assertIn("or vector(0)", expr)
        self.assertEqual(p.get("options", {}).get("noValue"), "0")
        self.assertEqual(p["title"], "Avisos críticos")

    def test_critical_tables_have_readable_height(self) -> None:
        for pid in (17, 22):
            h = panel_by_id(self.data, pid)["gridPos"]["h"]
            self.assertGreaterEqual(h, 8)

    def test_critical_detail_panel_describes_empty_state(self) -> None:
        desc = panel_by_id(self.data, 17).get("description", "")
        self.assertIn("Sin alertas críticas", desc)

    def test_noc_stat_row_fits_grid(self) -> None:
        panels = noc_stat_panels(self.data)
        self.assertEqual(len(panels), len(NOC_STAT_IDS))
        total_w = sum(p["gridPos"]["w"] for p in panels)
        self.assertLessEqual(total_w, 24)
        occupied: list[tuple[int, int]] = []
        for p in sorted(panels, key=lambda x: x["gridPos"]["x"]):
            x, w = p["gridPos"]["x"], p["gridPos"]["w"]
            end = x + w
            for start, other_end in occupied:
                self.assertTrue(end <= start or x >= other_end, f"overlap panel {p['id']}")
            occupied.append((x, end))

    def test_legend_is_native_table(self) -> None:
        p = panel_by_id(self.data, 200)
        self.assertEqual(p["type"], "table")
        self.assertEqual(p["datasource"]["uid"], "testdata")
        self.assertEqual(p["targets"][0]["scenarioId"], "csv_content")
        self.assertIn("Sección,Qué muestra", p["targets"][0]["csvContent"])

    def test_legend_note_panel_below_table(self) -> None:
        legend = panel_by_id(self.data, 200)
        note = panel_by_id(self.data, 203)
        self.assertEqual(note["type"], "text")
        self.assertEqual(note["gridPos"]["y"], legend["gridPos"]["h"])
        self.assertIn("JMeter", note["options"]["content"])

    def test_all_tables_have_wrap_and_cell_height(self) -> None:
        for pid in TABLE_IDS:
            p = panel_by_id(self.data, pid)
            self.assertEqual(p["type"], "table")
            custom = p["fieldConfig"]["defaults"]["custom"]
            self.assertTrue(custom.get("wrapText"))
            self.assertEqual(p["options"].get("cellHeight"), "lg")


if __name__ == "__main__":
    unittest.main()
