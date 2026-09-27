from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
MANIFEST = ROOT / "autotask-plugin.json"


class SlashCommandExampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.capability = self.manifest["capabilities"]["slash_commands"][0]

    def test_manifest_declares_prompt_command(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "autotask.plugin.v1")
        self.assertEqual(self.manifest["classification"]["plugin_kind"], "slash_command")
        self.assertEqual(self.capability["handler"], "prompt")
        self.assertEqual(self.capability["visible_in"], ["ui", "cli"])
        self.assertFalse(self.capability["requires_approval"])

    def test_prompt_is_bounded_and_arguments_are_raw_text(self) -> None:
        prompt = self.capability["metadata"]["prompt"]
        self.assertTrue(prompt.strip())
        self.assertLessEqual(len(prompt.encode("utf-8")), 24000)
        self.assertEqual(self.capability["arguments_schema"]["type"], "object")
        self.assertEqual(self.capability["arguments_schema"]["properties"]["request"]["type"], "string")

    def test_readme_documents_private_and_ambiguous_boundaries(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("plugin submit", readme)
        self.assertIn("plugin:<plugin-id>", readme)
        self.assertIn("raw argument string", readme)


if __name__ == "__main__":
    unittest.main()
