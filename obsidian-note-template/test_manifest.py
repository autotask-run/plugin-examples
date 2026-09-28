from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class ObsidianNoteManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "manifest.template.json").read_text(encoding="utf-8"))

    def test_manifest_declares_note_editor_contract(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "autotask.plugin.v1")
        self.assertEqual(self.manifest["classification"]["plugin_kind"], "mcp_server")
        self.assertEqual(self.manifest["classification"]["categories"], ["notes", "productivity"])
        self.assertEqual(self.manifest["runtimes"][0]["protocol"], "mcp")
        self.assertEqual(len(self.manifest["capabilities"]["tools"]), 2)
        tool_names = {tool["name"] for tool in self.manifest["capabilities"]["tools"]}
        self.assertEqual(tool_names, {"obsidian.note-template.daily", "obsidian.note-template.checklist"})
        commands = self.manifest["capabilities"]["slash_commands"]
        self.assertEqual({command["metadata"]["tool_ref"] for command in commands}, tool_names)
        for command in commands:
            self.assertEqual(command["visible_in"], ["note_editor"])
            self.assertIn("note.read_selection", command["permissions"])
        endpoints = {
            tool["metadata"]["mcp_server"]["config"]["url"]
            for tool in self.manifest["capabilities"]["tools"]
        }
        self.assertEqual(endpoints, {"https://notes.example.com/mcp"})
        self.assertNotIn("configuration", self.manifest)
        self.assertNotIn("distribution", self.manifest)
        self.assertNotIn("bindings", self.manifest)
        for tool in self.manifest["capabilities"]["tools"]:
            self.assertNotIn("auth", tool["metadata"]["mcp_server"])

    def test_prepare_rewrites_author_and_endpoint_without_credentials(self) -> None:
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
                    "--author-handle",
                    "example-author",
                    "--url",
                    "https://notes.example.test/mcp",
                    "--out",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["identity"]["plugin_id"], "user-42/obsidian-note-template")
            self.assertEqual(manifest["identity"]["author"]["name"], 'A "quoted" author')
            self.assertEqual(manifest["permissions"][1]["permission"], "network:notes.example.test")
            for tool in manifest["capabilities"]["tools"]:
                self.assertEqual(tool["permissions"], ["network:notes.example.test"])
                self.assertEqual(tool["metadata"]["mcp_server"]["config"]["url"], "https://notes.example.test/mcp")


if __name__ == "__main__":
    unittest.main()
