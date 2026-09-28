import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from server import Handler


class PublicSkillProviderMCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SKILL_PROVIDER_API_KEY"] = "test-key"
        cls.service = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.service.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.service.server_port}/provider-mcp"

    @classmethod
    def tearDownClass(cls):
        cls.service.shutdown()
        cls.service.server_close()
        cls.thread.join()

    def call(self, method, params=None, request_id=1, headers=None):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if request_id is not None:
            body["id"] = request_id
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers={
            "Authorization": "Bearer test-key", "Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})})
        with urllib.request.urlopen(req, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def test_tools_and_full_snapshot(self):
        _, initialized = self.call("initialize", {"protocolVersion": "2025-06-18"})
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "autotask-example-skill-provider")
        _, tools = self.call("tools/list")
        self.assertEqual({item["name"] for item in tools["result"]["tools"]}, {"skill_validate_config", "skill_sync", "skill_get_content"})
        _, synced = self.call("tools/call", {"name": "skill_sync", "arguments": {"source_id": 7, "source_kind": "skill_catalog", "config": {}, "limits": {"max_items": 100}}})
        value = synced["result"]["structuredContent"]
        self.assertTrue(value["complete"])
        self.assertEqual(value["revision"], "example-catalog-v2")
        self.assertEqual(len(value["records"]), 2)
        self.assertNotIn("cursor", value)
        self.assertNotIn("removed_external_ids", value)
        _, content = self.call("tools/call", {"name": "skill_get_content", "arguments": {"external_id": "example/release-checklist", "source_ref": {"revision": "example-catalog-v2"}}})
        content_value = content["result"]["structuredContent"]
        self.assertEqual(content_value["revision"], "example-catalog-v2")
        self.assertIn("Confirm the release version", content_value["readme_content"])
        self.assertIn("Record the test results", content_value["readme_content"])
        self.assertIn("Write down the rollback artifact", content_value["readme_content"])
        self.assertNotIn("content_hash", content_value)

    def test_auth_boundary(self):
        req = urllib.request.Request(self.url, b"{}", headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(req, timeout=3)
        self.assertEqual(error.exception.code, 401)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
