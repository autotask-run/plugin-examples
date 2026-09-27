import json
import tempfile
import unittest
from pathlib import Path

import prepare


ROOT = Path(__file__).parent


class UIPanelManifestTest(unittest.TestCase):
    def load_template(self):
        return json.loads((ROOT / "manifest.template.json").read_text())

    def test_template_is_fixed_and_declarative(self):
        manifest = self.load_template()
        self.assertEqual(manifest["classification"]["plugin_kind"], "ui_extension")
        self.assertEqual(manifest["classification"]["runtime_kinds"], ["hosted"])
        runtime = manifest["runtimes"][0]
        self.assertEqual(runtime["protocol"], "autotask.ui-panel.v1")
        capability = manifest["capabilities"]["ui_extensions"][0]
        self.assertEqual(capability["entrypoint"], "declarative")
        self.assertEqual(capability["permissions"], ["task:create"])
        panel = capability["metadata"]["panel"]
        self.assertEqual([action["type"] for action in panel["actions"]], ["create_task"])
        self.assertEqual({component["id"] for component in panel["components"]}, {"repository", "mode", "include_tests"})
        self.assertNotIn("url", panel)
        self.assertNotIn("script", panel)

    def test_prepare_replaces_author_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            import sys

            original = sys.argv
            try:
                sys.argv = ["prepare.py", "--author-id", "42", "--author-name", "A", "--author-handle", "a", "--out", str(output)]
                prepare.main()
            finally:
                sys.argv = original
            manifest = json.loads(output.read_text())
            self.assertEqual(manifest["identity"]["plugin_id"], "user-42/repository-review-panel")
            self.assertEqual(manifest["identity"]["author"]["name"], "A")
            self.assertNotIn("__AUTHOR_", output.read_text())


if __name__ == "__main__":
    unittest.main()
