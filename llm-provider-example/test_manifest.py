import json
import unittest
from pathlib import Path


class LLMProviderManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((Path(__file__).parent / "manifest.template.json").read_text())
        self.capability = self.manifest["capabilities"]["llm_providers"][0]
        self.metadata = self.capability["metadata"]

    def test_fixed_gateway_descriptor(self):
        self.assertEqual(self.manifest["classification"]["plugin_kind"], "llm_provider")
        self.assertEqual(self.manifest["runtimes"][0]["protocol"], "autotask.llm-provider.v1")
        self.assertEqual(self.metadata["protocol"], "openai-compatible-v1")
        self.assertEqual(self.metadata["default_api_format"], "openai")

    def test_static_model_list_and_default(self):
        models = self.metadata["models"]
        self.assertGreaterEqual(len(models), 1)
        self.assertLessEqual(len(models), 32)
        self.assertEqual(len(models), len(set(models)))
        self.assertIn(self.metadata["default_model"], models)

    def test_manifest_has_no_credentials_or_dynamic_discovery(self):
        encoded = json.dumps(self.manifest).lower()
        for forbidden in ("api_key_value", "client_secret", "models_url", "sync_models", "proxy_url"):
            self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
