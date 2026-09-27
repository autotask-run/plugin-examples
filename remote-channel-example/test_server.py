import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from server import Handler, SENT


class RemoteChannelTest(unittest.TestCase):
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

    def call(self, name, arguments=None):
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments or {}}}
        request = urllib.request.Request(self.url, json.dumps(body).encode(), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.loads(response.read())

    def test_poll_cursor_and_send_idempotency(self):
        first = self.call("bridge_poll", {"instance_key": "instance-1", "cursor": "", "limit": 100})
        page = first["result"].get("structuredContent", first["result"])
        self.assertEqual(page["events"][0]["event_id"], "example-event-1")
        self.assertEqual(page["next_cursor"], "cursor-1")

    def test_send_reuses_delivery_id(self):
        arguments = {"instance_key": "instance-1", "delivery_id": "delivery-test", "conversation_id": "conversation-1", "text": "hello", "reply_kind": "final"}
        first = self.call("bridge_send", arguments)
        second = self.call("bridge_send", arguments)
        self.assertEqual(first, second)
        self.assertIn("delivery-test", SENT)


if __name__ == "__main__":
    unittest.main()
