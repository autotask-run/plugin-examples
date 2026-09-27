"""Dependency-free AutoTask Knowledge Source Provider example."""
import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from provider import ProviderError, process

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26")
TOOLS = [
    {"name": "knowledge_validate_config", "description": "Validate a Knowledge Source configuration.", "inputSchema": {"type": "object"}},
    {"name": "knowledge_sync_documents", "description": "Return a bounded document snapshot.", "inputSchema": {"type": "object"}},
]


def provider_key_valid(headers):
    secret = os.environ.get("KNOWLEDGE_PROVIDER_API_KEY", "")
    return bool(secret) and hmac.compare_digest(headers.get("Authorization", ""), "Bearer " + secret)


def call_provider(name, arguments):
    if name == "knowledge_validate_config":
        return process({"operation": "validate_config", "config": arguments.get("config", {})})
    if name == "knowledge_sync_documents":
        return process({
            "operation": "sync_documents",
            "source_id": arguments.get("source_id"),
            "config": arguments.get("config", {}),
            "cursor": arguments.get("cursor", ""),
            "limits": arguments.get("limits", {}),
        })
    raise ProviderError("unknown_operation", "unsupported MCP tool")


def dispatch(message):
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})

    def error(code, text):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": text}}

    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return error(-32600, "Invalid Request")
    if "id" not in message:
        return None
    if not isinstance(params, dict):
        return error(-32602, "params must be an object")
    if method == "initialize":
        requested = params.get("protocolVersion")
        result = {"protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0], "capabilities": {"tools": {}}, "serverInfo": {"name": "autotask-example-knowledge-provider", "version": "1.0.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name not in {tool["name"] for tool in TOOLS} or not isinstance(arguments, dict):
            return error(-32602, "unknown Knowledge Source tool or invalid arguments")
        try:
            value = call_provider(name, arguments)
        except ProviderError as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
        result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "structuredContent": value, "isError": False}
    else:
        return error(-32601, "Method not found")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status, value=None):
        body = json.dumps(value, ensure_ascii=False).encode() if value is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/provider-mcp":
            return self.respond(404)
        if not provider_key_valid(self.headers):
            self.close_connection = True
            return self.respond(401, {"error": "Unauthorized"})
        allowed_origins = {value.strip() for value in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if value.strip()}
        if self.headers.get("Origin") and self.headers.get("Origin") not in allowed_origins:
            self.close_connection = True
            return self.respond(403, {"error": "Origin not allowed"})
        if self.headers.get("MCP-Protocol-Version", PROTOCOL_VERSIONS[0]) not in PROTOCOL_VERSIONS:
            self.close_connection = True
            return self.respond(400, {"error": "Unsupported MCP protocol version"})
        if self.headers.get_content_type() != "application/json":
            return self.respond(415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536 or self.headers.get("Transfer-Encoding"):
                return self.respond(413)
            message = json.loads(self.rfile.read(length))
            if not isinstance(message, dict):
                raise ValueError("object required")
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
        response = dispatch(message)
        return self.respond(202 if response is None else 200, response)

    def do_GET(self):
        return self.respond(405)

    do_DELETE = do_GET

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8769)
    args = parser.parse_args()
    if not os.environ.get("KNOWLEDGE_PROVIDER_API_KEY"):
        parser.error("set KNOWLEDGE_PROVIDER_API_KEY before starting")
    service = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Knowledge Source Provider example listening on {args.host}:{args.port}/provider-mcp", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.server_close()
