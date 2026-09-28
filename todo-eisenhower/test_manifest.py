from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class EisenhowerManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "manifest.template.json").read_text(encoding="utf-8"))
        self.capability = self.manifest["capabilities"]["ui_extensions"][0]

    def test_manifest_matches_public_todo_view_schema(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "autotask.plugin.v1")
        self.assertEqual(self.manifest["classification"]["plugin_kind"], "ui_extension")
        self.assertEqual(self.manifest["classification"]["source_kind"], "native")
        self.assertEqual(self.manifest["classification"]["categories"], ["todos", "productivity"])
        runtime = self.manifest["runtimes"][0]
        self.assertEqual(runtime, {
            "runtime_id": "hosted",
            "kind": "hosted",
            "protocol": "autotask.todo-view.v1",
        })
        self.assertEqual(self.manifest["permissions"], [
            {"permission": "todo:read", "risk_level": "low"},
            {"permission": "todo:write", "risk_level": "low"},
        ])
        self.assertEqual(self.capability["name"], "eisenhower")
        self.assertEqual(self.capability["runtime_kind"], "hosted")
        self.assertEqual(self.capability["support_level"], "executable_existing_runtime")
        self.assertEqual(self.capability["permissions"], ["todo:read", "todo:write"])
        self.assertEqual(self.capability["surface"], "personal_todos")
        self.assertEqual(self.capability["entrypoint"], "eisenhower")
        self.assertEqual(self.capability["metadata"], {
            "protocol": "autotask.todo-view.v1",
            "view": "eisenhower",
            "rules": {
                "importance": "priority_high",
                "urgency": "planned_date_on_or_before_local_date",
            },
            "actions": ["complete", "set_priority", "set_planned_date"],
        })
        self.assertNotIn("configuration", self.manifest)
        self.assertNotIn("distribution", self.manifest)
        self.assertNotIn("bindings", self.manifest)
        self.assertEqual(set(self.capability["metadata"]), {"protocol", "view", "rules", "actions"})

    def test_prepare_rewrites_identity_without_runtime_code(self) -> None:
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
                    "--out",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["identity"]["plugin_id"], "user-42/eisenhower-quadrants")
            self.assertEqual(manifest["identity"]["author"]["name"], 'A "quoted" author')
            self.assertNotIn("__AUTHOR_", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
