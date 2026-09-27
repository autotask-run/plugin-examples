"""Dependency-free private Remote Channel Bridge MCP example.

The adapter exposes a bounded polling inbox and an idempotent send operation.
It keeps only demo messages in memory; production adapters should persist the
upstream cursor and deduplicate delivery_id before acknowledging a send.
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26")
EVENTS = [{"event_id": "example-event-1", "user_id": "example-user", "conversation_id": "example-conversation", "text": "Hello from the private bridge"}]
SENT = {}

POLL_TOOL = {
    "name": "bridge_poll",
    "description": "Return bounded channel events after an opaque cursor.",
    "inputSchema": {"type": "object", "additionalProperties": False, "properties": {"instance_key": {"type": "string", "maxLength": 128}, "cursor": {"type": "string", "maxLength": 16384}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}, "adapter_config": {"type": "object"}}},
}
SEND_TOOL = {
    "name": "bridge_send",
    "description": "Accept one idempotent channel delivery.",
    "inputSchema": {"type": "object", "required": ["instance_key", "delivery_id", "conversation_id", "text", "reply_kind"], "additionalProperties": False, "properties": {"instance_key": {"type": "string", "maxLength": 128}, "delivery_id": {"type": "string", "maxLength": 200}, "conversation_id": {"type": "string", "maxLength": 200}, "reply_to_message_id": {"type": "string", "maxLength": 200}, "text": {"type": "string", "maxLength": 16384}, "reply_kind": {"type": "string", "maxLength": 40}, "metadata": {"type": "object"}, "adapter_config": {"type": "object"}}},
}


def result(value, request_id):
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def error(message, request_id, code=-32602):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def dispatch(message):
    request_id = message.get("id")
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return error("Invalid Request", request_id, -32600)
    if "id" not in message:
        return None
    params = message.get("params", {})
    if not isinstance(params, dict):
        return error("params must be an object", request_id)
    method = message["method"]
    if method == "initialize":
        requested = params.get("protocolVersion")
        return result({"protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0], "capabilities": {"tools": {}}, "serverInfo": {"name": "autotask-private-remote-channel", "version": "0.1.0"}}, request_id)
    if method == "ping":
        return result({}, request_id)
    if method == "tools/list":
        return result({"tools": [POLL_TOOL, SEND_TOOL]}, request_id)
    if method != "tools/call":
        return error("Method not found", request_id, -32601)
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not isinstance(arguments, dict):
        return error("arguments must be an object", request_id)
    if name == "bridge_poll":
        cursor = arguments.get("cursor", "")
        if not isinstance(cursor, str) or len(cursor.encode()) > 16384:
            return error("cursor is invalid", request_id)
        events = EVENTS if cursor == "" else []
        return result({"events": events, "next_cursor": "cursor-1", "poll_after_ms": 1000}, request_id)
    if name == "bridge_send":
        required = ("instance_key", "delivery_id", "conversation_id", "text", "reply_kind")
        if any(not isinstance(arguments.get(key), str) or not arguments[key].strip() for key in required):
            return error("send payload is incomplete", request_id)
        delivery_id = arguments["delivery_id"]
        previous = SENT.get(delivery_id)
        payload = {key: arguments.get(key) for key in ("conversation_id", "reply_to_message_id", "text", "reply_kind")}
        if previous is not None and previous != payload:
            return error("delivery_id was reused with different payload", request_id)
        SENT[delivery_id] = payload
        return result({"accepted": True, "external_message_id": "example-delivery-" + delivery_id}, request_id)
    return error("Unknown tool", request_id)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def respond(self, status, value=None):
        body = json.dumps(value, ensure_ascii=False).encode() if value is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/mcp":
            self.respond(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not 0 < length <= 131072 or self.headers.get("Transfer-Encoding"):
            self.respond(413)
            return
        try:
            message = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self.respond(400, error("Parse error", None, -32700))
            return
        response = dispatch(message) if isinstance(message, dict) else error("Invalid Request", None, -32600)
        self.respond(202 if response is None else 200, response)

    def do_GET(self):
        self.respond(405)

    do_DELETE = do_GET

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Remote Channel MCP example listening on {args.host}:{args.port}/mcp", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
