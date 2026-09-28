import base64
import hashlib
import http.client
import json
import threading
import unittest
from urllib.parse import parse_qs, urlencode, urlparse

import server


class OAuthMCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), json.loads(data) if data else None
        conn.close()
        return result

    def test_discovery_code_pkce_mcp_and_refresh(self):
        status, _, metadata = self.request("GET", "/.well-known/oauth-protected-resource/examples/oauth-mcp/mcp")
        self.assertEqual(status, 200)
        self.assertEqual(metadata["resource"], server.RESOURCE)
        status, _, metadata = self.request("GET", "/.well-known/oauth-authorization-server/examples/oauth-mcp")
        self.assertEqual(status, 200)
        self.assertIn("S256", metadata["code_challenge_methods_supported"])
        verifier = "fixture-verifier-" + "a" * 42
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        query = urlencode({"response_type": "code", "client_id": server.CLIENT_ID, "redirect_uri": server.CALLBACK,
                           "resource": server.RESOURCE, "scope": server.SCOPE, "state": "fixture-state",
                           "code_challenge": challenge, "code_challenge_method": "S256"})
        status, headers, _ = self.request("GET", "/examples/oauth-mcp/authorize?" + query)
        self.assertEqual(status, 302)
        code = parse_qs(urlparse(headers["Location"]).query)["code"][0]
        form = urlencode({"grant_type": "authorization_code", "client_id": server.CLIENT_ID,
                          "resource": server.RESOURCE, "redirect_uri": server.CALLBACK,
                          "code": code, "code_verifier": verifier})
        status, _, token = self.request("POST", "/examples/oauth-mcp/token", form,
                                        {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 200)
        self.assertEqual(token["token_type"], "Bearer")
        status, _, _ = self.request("POST", "/examples/oauth-mcp/token", form,
                                    {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 400)
        message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "oauth_echo", "arguments": {"message": "ready"}}})
        status, _, _ = self.request("POST", "/examples/oauth-mcp/mcp", message, {"Content-Type": "application/json"})
        self.assertEqual(status, 401)
        status, _, result = self.request("POST", "/examples/oauth-mcp/mcp", message,
                                         {"Content-Type": "application/json", "Authorization": "Bearer " + token["access_token"]})
        self.assertEqual(status, 200)
        self.assertEqual(result["result"]["structuredContent"], {"authorized": True, "message": "ready", "scope": server.SCOPE})
        form = urlencode({"grant_type": "refresh_token", "client_id": server.CLIENT_ID,
                          "resource": server.RESOURCE, "refresh_token": token["refresh_token"]})
        status, _, refreshed = self.request("POST", "/examples/oauth-mcp/token", form,
                                            {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 200)
        self.assertNotEqual(refreshed["access_token"], token["access_token"])
        status, _, _ = self.request("POST", "/examples/oauth-mcp/token", form,
                                    {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
