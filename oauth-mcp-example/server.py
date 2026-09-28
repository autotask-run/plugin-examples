"""Synthetic OAuth authorization server and protected MCP tool for acceptance.

Auto-consent is deliberate: this fixture tests the protocol, not user login.
Never use it to protect real data.
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

BASE = "https://docs.autotask.run/examples/oauth-mcp"
RESOURCE = BASE + "/mcp"
CALLBACK = "https://app.autotask.run/api/v1/plugin-lifecycle/oauth/callback"
CLIENT_ID = "autotask-plugin-acceptance"
SCOPE = "read:demo"
PROTOCOLS = ("2025-06-18", "2025-03-26")
LOCK = threading.Lock()
CODES = {}
ACCESS = {}
REFRESH = {}


def one(values, key):
    return values.get(key, [""])[0]


def issue_token(client_id, resource, scope):
    access = secrets.token_urlsafe(32)
    refresh = secrets.token_urlsafe(32)
    with LOCK:
        ACCESS[access] = (client_id, resource, scope, time.time() + 15)
        REFRESH[refresh] = (client_id, resource, scope)
    return {"access_token": access, "refresh_token": refresh, "token_type": "Bearer", "expires_in": 15, "scope": scope}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def respond(self, status, value=None, headers=None):
        body = json.dumps(value).encode() if value is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/.well-known/oauth-protected-resource/examples/oauth-mcp/mcp":
            return self.respond(200, {"resource": RESOURCE, "authorization_servers": [BASE]})
        if parsed.path == "/.well-known/oauth-authorization-server/examples/oauth-mcp":
            return self.respond(200, {"issuer": BASE, "authorization_endpoint": BASE + "/authorize", "token_endpoint": BASE + "/token", "code_challenge_methods_supported": ["S256"], "response_types_supported": ["code"], "grant_types_supported": ["authorization_code", "refresh_token"]})
        if parsed.path != "/examples/oauth-mcp/authorize":
            return self.respond(404)
        query = parse_qs(parsed.query)
        state = one(query, "state")
        challenge = one(query, "code_challenge")
        if (one(query, "response_type") != "code" or one(query, "client_id") != CLIENT_ID
                or one(query, "redirect_uri") != CALLBACK or one(query, "resource") != RESOURCE
                or one(query, "scope") != SCOPE or one(query, "code_challenge_method") != "S256"
                or not state or len(challenge) < 40):
            return self.respond(400, {"error": "invalid_request"})
        code = secrets.token_urlsafe(32)
        with LOCK:
            CODES[code] = (CLIENT_ID, RESOURCE, SCOPE, challenge, time.time() + 120)
        location = CALLBACK + "?" + urlencode({"code": code, "state": state})
        return self.respond(302, headers={"Location": location})

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/examples/oauth-mcp/token", "/examples/oauth-mcp/mcp"):
            return self.respond(404)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536 or self.headers.get("Transfer-Encoding"):
                return self.respond(413)
            payload = self.rfile.read(size)
        except (ValueError, UnicodeDecodeError):
            return self.respond(400)
        if path.endswith("/token"):
            return self.token(payload)
        return self.mcp(payload)

    def token(self, payload):
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            return self.respond(415)
        form = parse_qs(payload.decode())
        if one(form, "client_id") != CLIENT_ID or one(form, "resource") != RESOURCE:
            return self.respond(400, {"error": "invalid_client_or_resource"})
        grant = one(form, "grant_type")
        if grant == "authorization_code":
            code = one(form, "code")
            with LOCK:
                record = CODES.pop(code, None)
            if not record or one(form, "redirect_uri") != CALLBACK or record[4] < time.time():
                return self.respond(400, {"error": "invalid_grant"})
            expected = base64.urlsafe_b64encode(hashlib.sha256(one(form, "code_verifier").encode()).digest()).rstrip(b"=").decode()
            if not hmac.compare_digest(record[3], expected):
                return self.respond(400, {"error": "invalid_grant"})
            return self.respond(200, issue_token(*record[:3]))
        if grant == "refresh_token":
            refresh = one(form, "refresh_token")
            with LOCK:
                record = REFRESH.pop(refresh, None)
            if not record or record[:2] != (CLIENT_ID, RESOURCE):
                return self.respond(400, {"error": "invalid_grant"})
            return self.respond(200, issue_token(*record))
        return self.respond(400, {"error": "unsupported_grant_type"})

    def mcp(self, payload):
        if self.headers.get_content_type() != "application/json":
            return self.respond(415)
        bearer = self.headers.get("Authorization", "")
        token = bearer[7:] if bearer.startswith("Bearer ") else ""
        with LOCK:
            record = ACCESS.get(token)
        if not record or record[1] != RESOURCE or record[2] != SCOPE or record[3] < time.time():
            return self.respond(401, {"error": "unauthorized"}, {"WWW-Authenticate": f'Bearer resource_metadata="https://docs.autotask.run/.well-known/oauth-protected-resource/examples/oauth-mcp/mcp"'})
        if self.headers.get("MCP-Protocol-Version", PROTOCOLS[0]) not in PROTOCOLS:
            return self.respond(400)
        try:
            message = json.loads(payload)
            if not isinstance(message, dict):
                raise ValueError("object required")
        except (ValueError, UnicodeDecodeError):
            return self.respond(400)
        if "id" not in message:
            return self.respond(202)
        method = message.get("method")
        params = message.get("params", {})
        if method == "initialize":
            result = {"protocolVersion": params.get("protocolVersion") if params.get("protocolVersion") in PROTOCOLS else PROTOCOLS[0], "capabilities": {"tools": {}}, "serverInfo": {"name": "autotask-example-oauth-mcp", "version": "1.0.0"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "oauth_echo", "description": "Confirm a scoped OAuth MCP invocation using synthetic data.", "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"], "additionalProperties": False}}]}
        elif method == "tools/call" and params.get("name") == "oauth_echo" and isinstance(params.get("arguments", {}).get("message"), str):
            value = {"authorized": True, "message": params["arguments"]["message"], "scope": SCOPE}
            result = {"content": [{"type": "text", "text": json.dumps(value)}], "structuredContent": value, "isError": False}
        elif method == "ping":
            result = {}
        else:
            return self.respond(200, {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32602, "message": "unknown tool or arguments"}})
        return self.respond(200, {"jsonrpc": "2.0", "id": message["id"], "result": result})

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
