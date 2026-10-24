import html
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
import scraper


def page(stations):
    return '<div data-menu="' + html.escape(json.dumps({
        "subLocations": stations
    }), quote=True) + '"></div>'


class ScraperTests(unittest.TestCase):
    def test_empty_list_is_a_valid_menu(self):
        self.assertEqual(scraper.extract_menu(page([]))["subLocations"], {})

    def test_missing_or_invalid_menu_remains_an_error(self):
        for content in ("<html></html>", page(None), page(["invalid"])):
            self.assertIsNone(scraper.extract_menu(content))

    def test_closed_hall_clears_old_menu_and_recovers(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            scraper, "DATA_FOLDER", Path(folder)
        ), patch.object(scraper.requests, "get") as get:
            path = Path(folder) / "southern-kitchen.json"
            path.write_text('{"stations": {"old": {}}}', encoding="utf-8")
            get.return_value = Mock(text=page([]))
            scraper.update_hall("southern-kitchen", scraper.DINING_HALLS["southern-kitchen"])
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["stations"], {})
            self.assertEqual(data["status"], "no_menu")
            get.return_value = Mock(text=page({"grill": {"mealPeriods": {}}}))
            scraper.update_hall("southern-kitchen", scraper.DINING_HALLS["southern-kitchen"])
            self.assertEqual(json.loads(path.read_text())["status"], "available")

    def test_failure_does_not_stop_other_halls_or_overwrite_old_data(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            scraper, "DATA_FOLDER", Path(folder)
        ), patch.object(scraper.requests, "get") as get:
            path = Path(folder) / "stokely.json"
            path.write_text("previous menu", encoding="utf-8")
            get.side_effect = [requests.Timeout("timeout"), Mock(text=page({})), Mock(text=page([]))]
            with self.assertRaises(SystemExit):
                scraper.main()
            self.assertEqual(path.read_text(), "previous menu")
            self.assertTrue((Path(folder) / "rocky-top.json").exists())
            self.assertTrue((Path(folder) / "southern-kitchen.json").exists())


if __name__ == "__main__":
    unittest.main()
