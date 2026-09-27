import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from server import Handler


class KnowledgeProviderMCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["KNOWLEDGE_PROVIDER_API_KEY"] = "test-key"
        cls.service = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.service.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.service.server_port}/provider-mcp"

    @classmethod
    def tearDownClass(cls):
        cls.service.shutdown()
        cls.service.server_close()
        cls.thread.join()
        os.environ.pop("KNOWLEDGE_PROVIDER_API_KEY", None)

    def call(self, method, params=None, authenticated=True, request_id=1):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if request_id is not None:
            body["id"] = request_id
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if authenticated:
            headers["Authorization"] = "Bearer test-key"
        request = urllib.request.Request(self.url, json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def tool(self, name, arguments):
        result = self.call("tools/call", {"name": "knowledge_" + name, "arguments": arguments})[1]["result"]
        self.assertFalse(result["isError"], result)
        return result["structuredContent"]

    def test_initialize_validate_and_idempotent_sync(self):
        self.assertEqual(self.call("initialize", {"protocolVersion": "2025-06-18"})[1]["result"]["serverInfo"]["name"], "autotask-example-knowledge-provider")
        self.assertEqual({item["name"] for item in self.call("tools/list")[1]["result"]["tools"]}, {"knowledge_validate_config", "knowledge_sync_documents"})
        self.assertEqual(self.tool("validate_config", {"config": {"collection": "docs"}})["normalized_config"], {"collection": "docs"})
        first = self.tool("sync_documents", {"source_id": 7, "config": {"collection": "docs"}, "limits": {"max_items": 100}})
        second = self.tool("sync_documents", {"source_id": 7, "cursor": first["cursor"], "config": {"collection": "docs"}, "limits": {"max_items": 100}})
        self.assertTrue(first["complete"])
        self.assertEqual(first, second)
        self.assertEqual([item["external_id"] for item in first["documents"]], ["guide/intro", "guide/security"])
        self.assertTrue(all(item["text"] and item["revision"] for item in first["documents"]))

    def test_authentication_required(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call("tools/list", authenticated=False)
        self.assertEqual(error.exception.code, 401)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
