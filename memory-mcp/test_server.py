import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

spec = importlib.util.spec_from_file_location("memory_server", Path(__file__).with_name("server.py"))
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)


class MemoryMCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ["MEMORY_DB"] = str(Path(cls.temp.name) / "records.sqlite3")
        os.environ["MEMORY_API_KEY"] = "local-example-key"
        os.environ["MEMORY_USER_ID"] = "7"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/mcp"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()
        os.environ.pop("MEMORY_DB", None)
        os.environ.pop("MEMORY_API_KEY", None)
        os.environ.pop("MEMORY_USER_ID", None)

    def call(self, method, params=None, authenticated=True, request_id=1):
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if authenticated:
            headers["Authorization"] = "Bearer local-example-key"
        request = urllib.request.Request(self.url, json.dumps(payload).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def tool(self, name, arguments):
        response = self.call("tools/call", {"name": "memory_" + name, "arguments": arguments})[1]["result"]
        self.assertFalse(response["isError"], response)
        return response["structuredContent"]

    def test_four_operations_and_namespace_isolation(self):
        self.assertEqual(self.call("initialize", {"protocolVersion": "2025-06-18"})[1]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(len(self.call("tools/list")[1]["result"]["tools"]), 4)
        namespace = {"user_id": "7", "profile_id": "21", "workspace_id": "4", "project_id": "9", "session_id": "a"}
        entry = {"scope": "user", "category": "preference", "content": "Prefer Go", "source": "user", "trust": 0.8, "recall_mode": "associative"}
        record_id = self.tool("store", {"namespace": namespace, "entry": entry})["id"]
        self.assertEqual(self.tool("recall", {"namespace": {"user_id": "7", "profile_id": "21", "session_id": "b"}, "query": "Go", "limit": 10})["items"][0]["id"], record_id)
        denied_user = self.call("tools/call", {"name": "memory_recall", "arguments": {"namespace": {"user_id": "8", "profile_id": "21"}, "query": "", "limit": 10}})[1]["result"]
        self.assertTrue(denied_user["isError"])
        entry["content"] = "Prefer Rust"
        self.assertEqual(self.tool("update", {"namespace": namespace, "id": record_id, "entry": entry})["id"], record_id)
        self.assertEqual(self.tool("recall", {"namespace": namespace, "id": record_id, "limit": 1})["items"][0]["content"], "Prefer Rust")
        denied = self.call("tools/call", {"name": "memory_delete", "arguments": {"namespace": {"user_id": "8", "profile_id": "21"}, "id": record_id}})[1]["result"]
        self.assertTrue(denied["isError"])
        self.assertEqual(self.tool("delete", {"namespace": namespace, "id": record_id}), {"deleted": True})
        self.assertEqual(self.tool("recall", {"namespace": namespace, "id": record_id, "limit": 1})["items"], [])

    def test_authentication_required(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call("tools/list", authenticated=False)
        self.assertEqual(error.exception.code, 401)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
