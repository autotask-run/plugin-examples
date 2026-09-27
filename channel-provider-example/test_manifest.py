import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent


class ChannelManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "autotask-plugin.json").read_text())

    def test_manifest_is_source_integrated_and_not_public_mcp(self):
        classification = self.manifest["classification"]
        self.assertEqual(classification["plugin_kind"], "channel_provider")
        self.assertEqual(classification["runtime_kinds"], ["go_builtin"])
        self.assertEqual(classification["source_kind"], "workspace")

    def test_channel_identity_and_events_are_explicit(self):
        capability = self.manifest["capabilities"]["channels"][0]
        self.assertEqual(capability["channel_id"], "loopback")
        self.assertEqual(capability["provider"], "loopback")
        events = capability["events"]
        self.assertEqual(len(events), len(set(events)))
        self.assertTrue(all(event.strip() for event in events))

    def test_no_credentials_or_remote_entrypoint(self):
        self.assertEqual(self.manifest["permissions"], [])
        self.assertNotIn("url", self.manifest["runtimes"][0].get("entrypoint", {}))


if __name__ == "__main__":
    unittest.main()
