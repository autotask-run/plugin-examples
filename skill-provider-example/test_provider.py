import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class SkillProviderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen(
            [sys.executable, str(ROOT / "provider.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

    @classmethod
    def tearDownClass(cls):
        if cls.process.stdin:
            cls.process.stdin.close()
        cls.process.terminate()
        cls.process.wait(timeout=3)

    @classmethod
    def call(cls, operation, **payload):
        assert cls.process.stdin and cls.process.stdout
        cls.process.stdin.write(json.dumps({"operation": operation, **payload}) + "\n")
        cls.process.stdin.flush()
        line = cls.process.stdout.readline()
        return json.loads(line)

    def test_validate_sync_and_content_contract(self):
        validated = self.call("validate_config", config={})
        self.assertTrue(validated["ok"], validated)
        self.assertTrue(validated["result"]["valid"])

        synced = self.call("sync", source={"id": 123, "config": {}}, limits={"max_items": 1})
        self.assertTrue(synced["ok"], synced)
        self.assertFalse(synced["result"]["complete"])
        self.assertIn("partial", synced["result"]["diagnostics"]["warnings"][0])
        record = synced["result"]["records"][0]
        self.assertEqual(record["source_ref"]["provider_id"], "example_catalog")
        self.assertEqual(record["source_ref"]["source_id"], 123)
        self.assertTrue(record["content_hash"].startswith("sha256:"))

        complete = self.call("sync", source={"id": 123, "config": {}}, limits={"max_items": 100})
        self.assertTrue(complete["ok"], complete)
        self.assertTrue(complete["result"]["complete"])
        self.assertEqual(complete["result"]["diagnostics"]["warnings"], [])

        content = self.call("get_content", source={"id": 123, "config": {}}, skill_id=record["external_id"])
        self.assertTrue(content["ok"], content)
        self.assertIn("readme_content", content["result"])
        self.assertEqual(content["result"]["files"][0]["path"], "references/release.md")

        file_result = self.call("get_file", source={"id": 123, "config": {}}, skill_id=record["external_id"], file_path="references/release.md")
        self.assertTrue(file_result["ok"], file_result)

    def test_rejects_unknown_operation_and_unsafe_catalog_file(self):
        unknown = self.call("nope")
        self.assertFalse(unknown["ok"])
        self.assertEqual(unknown["error"]["code"], "unknown_operation")
        unsafe = self.call("validate_config", config={"catalog": [{
            "external_id": "bad",
            "name": "bad",
            "description": "bad",
            "version": "1.0.0",
            "readme_content": "---\n---",
            "manifest_json": "{}",
            "files": [{"path": "../secret", "content": "no"}],
        }]})
        self.assertFalse(unsafe["ok"])
        self.assertEqual(unsafe["error"]["code"], "invalid_config")


if __name__ == "__main__":
    unittest.main()
