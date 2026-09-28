from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class ReadingNoteManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "manifest.template.json").read_text(encoding="utf-8"))
        self.capability = self.manifest["capabilities"]["note_types"][0]

    def test_manifest_is_metadata_only_and_bounded(self) -> None:
        self.assertEqual(self.manifest["classification"]["plugin_kind"], "note_type")
        self.assertEqual(self.manifest["classification"]["source_kind"], "native")
        self.assertEqual(self.manifest["classification"]["runtime_kinds"], ["external"])
        self.assertEqual(self.manifest["runtimes"], [{
            "runtime_id": "metadata",
            "kind": "external",
            "protocol": "metadata_only",
        }])
        self.assertEqual(self.capability["runtime_kind"], "external")
        self.assertEqual(self.capability["support_level"], "metadata_only")
        self.assertEqual(self.capability["type_key"], "reading_note")
        self.assertEqual(
            {field["key"] for field in self.capability["fields"]},
            {"author", "rating", "finished", "read_date", "status"},
        )
        self.assertEqual(
            {field["type"] for field in self.capability["fields"]},
            {"text", "number", "boolean", "date", "select"},
        )
        status = next(field for field in self.capability["fields"] if field["key"] == "status")
        self.assertEqual(status["options"], [
            {"value": "reading", "label": "在读"},
            {"value": "finished", "label": "读完"},
        ])
        self.assertNotIn("configuration", self.manifest)
        self.assertNotIn("distribution", self.manifest)
        self.assertNotIn("bindings", self.manifest)
        for field in self.capability["fields"]:
            self.assertNotIn("command", field)
            self.assertNotIn("url", field)
            self.assertNotIn("script", field)

    def test_prepare_uses_private_owner_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "prepare.py"),
                    "--author-id",
                    "42",
                    "--author-name",
                    'A "quoted" author',
                    "--out",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["identity"]["plugin_id"], "private-42/reading-note")
            self.assertEqual(manifest["identity"]["author"]["name"], 'A "quoted" author')
            self.assertNotIn("__AUTHOR_", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
