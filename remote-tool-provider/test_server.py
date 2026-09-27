import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from server import Handler


class ToolProviderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["TOOL_PROVIDER_API_KEY"] = "test-provider-key"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.provider_url = f"http://127.0.0.1:{cls.server.server_port}/provider-mcp"
        cls.item_url = f"http://127.0.0.1:{cls.server.server_port}/items/weather/mcp"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def call(self, url, method, params=None, request_id=1, headers=None):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if request_id is not None:
            body["id"] = request_id
        req = urllib.request.Request(url, json.dumps(body).encode(), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})})
        with urllib.request.urlopen(req, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def test_validate_and_paginated_catalog(self):
        auth = {"Authorization": "Bearer test-provider-key"}
        _, initialized = self.call(self.provider_url, "initialize", {"protocolVersion": "2025-06-18"}, headers=auth)
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        _, validated = self.call(self.provider_url, "tools/call", {"name": "provider_validate_config", "arguments": {"source_kind": "remote_catalog", "config": {}}}, headers=auth)
        self.assertTrue(validated["result"]["structuredContent"]["valid"])
        first = self.call(self.provider_url, "tools/call", {"name": "provider_sync_catalog", "arguments": {"source_kind": "remote_catalog", "cursor": {}, "limits": {"max_items": 1}}}, headers=auth)[1]["result"]["structuredContent"]
        self.assertFalse(first["complete"])
        self.assertEqual(first["items"][0]["external_id"], "example.weather")
        self.assertNotIn("auth", first["items"][0]["package_manifest"])
        second = self.call(self.provider_url, "tools/call", {"name": "provider_sync_catalog", "arguments": {"source_kind": "remote_catalog", "cursor": first["cursor"], "limits": {"max_items": 1}}}, headers=auth)[1]["result"]["structuredContent"]
        self.assertTrue(second["complete"])
        self.assertEqual(second["items"][0]["external_id"], "example.time")

    def test_provider_key_boundary_and_item_is_credential_free(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call(self.provider_url, "ping")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        _, tools = self.call(self.item_url, "tools/list")
        self.assertEqual(tools["result"]["tools"][0]["name"], "weather_lookup")
        _, result = self.call(self.item_url, "tools/call", {"name": "weather_lookup", "arguments": {"city": "Shanghai"}})
        self.assertEqual(result["result"]["structuredContent"]["temperature_c"], 22)


if __name__ == "__main__":
    unittest.main()
