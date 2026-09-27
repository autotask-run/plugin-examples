from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLUGIN = ROOT / "local_tool.py"
MANIFEST = ROOT / "autotask-plugin.json"


def invoke(request: dict) -> dict:
    completed = subprocess.run(
        [sys.executable, str(PLUGIN)],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


class LocalToolExampleTests(unittest.TestCase):
    def test_manifest_declares_canonical_read_only_runtime(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "autotask.plugin.v1")
        self.assertEqual(manifest["classification"]["runtime_kinds"], ["cli_stdio_json"])
        runtime = manifest["runtimes"][0]
        self.assertEqual(runtime["protocol"], "stdio-json-v1")
        self.assertEqual(runtime["isolation"]["default_sandbox"], "read-only")

    def test_counts_unicode_text(self) -> None:
        self.assertEqual(
            invoke(
                {
                    "contract_version": "local-tools.v1",
                    "runtime": "stdio-json-v1",
                    "tool_name": "plugin.text_stats",
                    "sandbox_mode": "read-only",
                    "input": {"text": "你好 AutoTask\nPlugins work"},
                }
            ),
            {"status": "ok", "characters": 24, "words": 4, "lines": 2},
        )

    def test_rejects_wrong_tool_and_broader_sandbox(self) -> None:
        wrong_tool = invoke(
            {
                "tool_name": "plugin.other",
                "sandbox_mode": "read-only",
                "input": {"text": "safe"},
            }
        )
        self.assertEqual(wrong_tool["status"], "denied")

        broad_sandbox = invoke(
            {
                "tool_name": "plugin.text_stats",
                "sandbox_mode": "workspace-write",
                "input": {"text": "safe"},
            }
        )
        self.assertEqual(broad_sandbox["status"], "denied")


if __name__ == "__main__":
    unittest.main()
