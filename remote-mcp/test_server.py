import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from server import Handler


class MCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/mcp"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def call(self, method, params=None, request_id=1, headers=None):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if request_id is not None:
            body["id"] = request_id
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers={
            "Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})})
        with urllib.request.urlopen(req, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def test_complete_protocol_and_unicode(self):
        _, initialized = self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "example-test", "version": "1"}})
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(self.call("notifications/initialized", request_id=None), (202, None))
        _, tools = self.call("tools/list")
        self.assertEqual(tools["result"]["tools"][0]["name"], "text_stats")
        _, result = self.call("tools/call", {"name": "text_stats", "arguments": {"text": "你好 AutoTask\nPlugins work"}})
        self.assertEqual(result["result"]["structuredContent"], {"characters": 24, "words": 4, "lines": 2})
        self.assertFalse(result["result"]["isError"])

    def test_bad_arguments_and_unknown_tool(self):
        _, result = self.call("tools/call", {"name": "text_stats", "arguments": {"text": 1}})
        self.assertTrue(result["result"]["isError"])
        _, result = self.call("tools/call", {"name": "missing"})
        self.assertEqual(result["error"]["code"], -32602)

    def test_origin_and_protocol_boundaries(self):
        for headers, expected in [({"Origin": "https://untrusted.example"}, 403), ({"MCP-Protocol-Version": "invalid"}, 400)]:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.call("ping", headers=headers)
            self.assertEqual(error.exception.code, expected)
            error.exception.close()

    def test_optional_api_key(self):
        with patch.dict("os.environ", {"MCP_API_KEY": "example-secret", "MCP_API_KEY_HEADER": "Authorization", "MCP_API_KEY_PREFIX": "Bearer "}):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.call("tools/list")
            self.assertEqual(error.exception.code, 401)
            error.exception.close()
            _, tools = self.call("tools/list", headers={"Authorization": "Bearer example-secret"})
            self.assertEqual(tools["result"]["tools"][0]["name"], "text_stats")


if __name__ == "__main__":
    unittest.main()
