"""Dependency-free remote MCP Tool Provider example.

The provider endpoint is authenticated and returns a deterministic two-page
catalog. Returned MCP item endpoints deliberately require no provider
credential, so the example demonstrates the provider/item credential boundary.
"""
import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26")
REVISION = "demo-1"
PROVIDER_TOOLS = [
    {"name": "provider_validate_config", "description": "Validate a Tool Source configuration.", "inputSchema": {"type": "object"}},
    {"name": "provider_sync_catalog", "description": "Synchronize a paged MCP item catalog.", "inputSchema": {"type": "object"}},
]
ITEM_TOOLS = [{
    "name": "weather_lookup",
    "description": "Return deterministic example weather data.",
    "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"], "additionalProperties": False},
}]
TIME_TOOLS = [{"name": "time_now", "description": "Return deterministic example time data.", "inputSchema": {"type": "object"}}]


def catalog_items(item_url):
    time_item_url = item_url.replace("/weather/", "/time/", 1)
    return [
        {
            "external_id": "example.weather",
            "name": "example_weather",
            "title": "Example Weather",
            "description": "A no-credential demo MCP weather tool.",
            "category": "demo",
            "version": "1.0.0",
            "revision": REVISION,
            "source_url": "https://github.com/autotask-run/plugin-examples",
            "package_manifest": {"package_type": "mcp_server", "runtime_kind": "mcp", "url": item_url, "transport": "streamable-http"},
            "tools": ITEM_TOOLS,
            "risk_summary": {"read_only": True, "third_party": True},
            "execution_protocols": ["mcp", "streamable-http"],
            "available": True,
        },
        {
            "external_id": "example.time",
            "name": "example_time",
            "title": "Example Time",
            "description": "A second catalog page used to test cursor continuation.",
            "category": "demo",
            "version": "1.0.0",
            "revision": REVISION,
            "source_url": "https://github.com/autotask-run/plugin-examples",
            "package_manifest": {"package_type": "mcp_server", "runtime_kind": "mcp", "url": time_item_url, "transport": "streamable-http"},
            "tools": [{"name": "time_now", "description": "Return deterministic example time data.", "inputSchema": {"type": "object"}}],
            "risk_summary": {"read_only": True, "third_party": True},
            "execution_protocols": ["mcp", "streamable-http"],
            "available": True,
        },
    ]


def provider_key_valid(headers):
    secret = os.environ.get("TOOL_PROVIDER_API_KEY", "")
    return bool(secret) and hmac.compare_digest(headers.get("Authorization", ""), "Bearer " + secret)


def dispatch(message, path, item_url):
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})

    def error(code, text):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": text}}

    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return error(-32600, "Invalid Request")
    if "id" not in message:
        return None
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion") if params.get("protocolVersion") in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0], "capabilities": {"tools": {}}, "serverInfo": {"name": "autotask-example-tool-provider", "version": "1.0.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": PROVIDER_TOOLS if path == "/provider-mcp" else (TIME_TOOLS if path == "/items/time/mcp" else ITEM_TOOLS)}
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if path == "/provider-mcp":
            if name == "provider_validate_config":
                if not isinstance(arguments, dict) or arguments.get("source_kind") != "remote_catalog":
                    return error(-32602, "source_kind must be remote_catalog")
                result = {"valid": True, "normalized_config": {"catalog_revision": REVISION}, "warnings": []}
            elif name == "provider_sync_catalog":
                if not isinstance(arguments, dict) or arguments.get("source_kind") != "remote_catalog":
                    return error(-32602, "source_kind must be remote_catalog")
                cursor = arguments.get("cursor") or {}
                if not isinstance(cursor, dict):
                    return error(-32602, "cursor must be an object")
                try:
                    offset = int(cursor.get("offset", 0))
                except (TypeError, ValueError):
                    return error(-32602, "cursor.offset must be an integer")
                limit = arguments.get("limits", {}).get("max_items", 1)
                if not isinstance(limit, int) or not 1 <= limit <= 1000:
                    return error(-32602, "limits.max_items must be 1..1000")
                items = catalog_items(item_url)
                page = items[offset:offset + min(limit, 1)]
                end = offset + len(page)
                result = {"items": page, "cursor": {"revision": REVISION, "offset": end}, "complete": end >= len(items), "diagnostics": {"items_seen": len(page), "warnings": []}}
            else:
                return error(-32602, "unknown provider tool")
        elif path.startswith("/items/"):
            if name == "weather_lookup":
                city = arguments.get("city") if isinstance(arguments, dict) else None
                if not isinstance(city, str) or not city.strip():
                    return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": "city is required"}], "isError": True}}
                value = {"city": city, "condition": "sunny", "temperature_c": 22}
            elif name == "time_now":
                value = {"timezone": "UTC", "time": "12:00:00"}
            else:
                return error(-32602, "unknown item tool")
            result = {"content": [{"type": "text", "text": json.dumps(value)}], "structuredContent": value, "isError": False}
        else:
            return error(-32602, "unknown endpoint")
    else:
        return error(-32601, "Method not found")
    if path == "/provider-mcp" and method == "tools/call":
        result = {"content": [{"type": "text", "text": json.dumps(result)}], "structuredContent": result, "isError": False}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    item_url = "https://catalog.example.com/items/weather/mcp"

    def respond(self, status, value=None):
        body = json.dumps(value, ensure_ascii=False).encode() if value is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/provider-mcp", "/items/weather/mcp", "/items/time/mcp"):
            return self.respond(404)
        if self.path == "/provider-mcp" and not provider_key_valid(self.headers):
            self.close_connection = True
            return self.respond(401, {"error": "Unauthorized"})
        if self.headers.get("Origin") and self.headers.get("Origin") not in {v.strip() for v in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if v.strip()}:
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
        response = dispatch(message, self.path, self.item_url)
        return self.respond(202 if response is None else 200, response)

    def do_GET(self):
        return self.respond(405)

    do_DELETE = do_GET

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--item-url", default=Handler.item_url)
    args = parser.parse_args()
    if not os.environ.get("TOOL_PROVIDER_API_KEY"):
        parser.error("set TOOL_PROVIDER_API_KEY before starting")
    Handler.item_url = args.item_url
    service = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Tool Provider example listening on {args.host}:{args.port}/provider-mcp", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.server_close()
