from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
MANIFEST = ROOT / "autotask-plugin.json"


class HookExampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_declares_workspace_prompt_hook(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "autotask.plugin.v1")
        self.assertEqual(self.manifest["classification"]["source_kind"], "workspace")
        self.assertEqual(self.manifest["classification"]["runtime_kinds"], ["system_hook"])
        capability = self.manifest["capabilities"]["hooks"][0]
        self.assertEqual(capability["schema_version"], "autotask.hook.v1")
        self.assertEqual(capability["event"], "TaskCompleted")
        self.assertEqual(capability["handlers"][0]["type"], "prompt")

    def test_prompt_hook_has_a_bounded_delivery_review_effect(self) -> None:
        capability = self.manifest["capabilities"]["hooks"][0]
        handler = capability["handlers"][0]
        self.assertLessEqual(len(handler["template"].encode("utf-8")), 24000)
        self.assertEqual(handler["effect"]["type"], "session.message.create")
        self.assertEqual(capability["supported_binding_targets"], ["agent_profile"])

    def test_example_does_not_claim_public_submission_support(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("not accepted", readme)
        self.assertIn("plugin submit", readme)


if __name__ == "__main__":
    unittest.main()
