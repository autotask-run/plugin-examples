"""A dependency-free, stateless Streamable HTTP MCP example (Python 3.10+).

Only text supplied in a tool call is processed. No filesystem, network calls
or persistent storage. Optional MCP_API_KEY protects the endpoint; keep it in
the server environment, never in a plugin manifest or repository.
"""
import argparse
import json
import os
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26")
TOOL = {
    "name": "text_stats",
    "description": "Count Unicode characters, whitespace-separated words and lines in supplied text.",
    "inputSchema": {
        "type": "object",
        "properties": {"text": {"type": "string", "maxLength": 10000}},
        "required": ["text"],
        "additionalProperties": False,
    },
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
}


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
        result = {
            "protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "autotask-example-text-stats", "version": "1.0.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [TOOL]}
    elif method == "tools/call":
        if params.get("name") != "text_stats":
            return error(-32602, "Unknown tool")
        arguments = params.get("arguments", {})
        text = arguments.get("text") if isinstance(arguments, dict) else None
        if not isinstance(text, str) or len(text) > 10000 or set(arguments) != {"text"}:
            result = {"content": [{"type": "text", "text": "Provide only a text string of at most 10000 characters."}], "isError": True}
        else:
            stats = {"characters": len(text), "words": len(text.split()), "lines": len(text.splitlines())}
            result = {"content": [{"type": "text", "text": json.dumps(stats)}], "structuredContent": stats, "isError": False}
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

    def valid_origin(self):
        origin = self.headers.get("Origin")
        allowed = {v.strip() for v in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if v.strip()}
        return origin is None or origin in allowed

    def do_POST(self):
        if self.path != "/mcp":
            self.respond(404)
            return
        if not self.valid_origin():
            self.close_connection = True
            self.respond(403, {"error": "Origin not allowed"})
            return
        configured_key = os.environ.get("MCP_API_KEY")
        if configured_key:
            header = os.environ.get("MCP_API_KEY_HEADER", "Authorization")
            prefix = os.environ.get("MCP_API_KEY_PREFIX", "Bearer ")
            supplied = self.headers.get(header, "")
            if not hmac.compare_digest(supplied, prefix + configured_key):
                self.close_connection = True
                self.respond(401, {"error": "API key required"})
                return
        if self.headers.get("MCP-Protocol-Version", PROTOCOL_VERSIONS[0]) not in PROTOCOL_VERSIONS:
            self.close_connection = True
            self.respond(400, {"error": "Unsupported MCP protocol version"})
            return
        if self.headers.get_content_type() != "application/json":
            self.close_connection = True
            self.respond(415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not 0 < length <= 65536 or self.headers.get("Transfer-Encoding"):
            self.close_connection = True
            self.respond(413)
            return
        try:
            message = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            return
        if not isinstance(message, dict):
            self.respond(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
            return
        response = dispatch(message)
        self.respond(202 if response is None else 200, response)

    def do_GET(self):
        # This stateless server does not offer an SSE stream.
        self.respond(403 if not self.valid_origin() else 405)

    do_DELETE = do_GET

    def log_message(self, *_):
        # Never record user text, request bodies, or headers.
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"MCP example listening on {args.host}:{args.port}/mcp", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
