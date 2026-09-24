"""Small persistent MCP memory provider for the AutoTask memory.v1 contract.

Run one instance per customer behind HTTPS. The API key is supplied at install
time; the manifest never contains it. SQLite is used only for this example.
"""
import argparse
import hmac
import json
import os
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "2025-06-18"
TOOLS = [
    {"name": "memory_" + action, "description": action.title() + " a scoped memory record.",
     "inputSchema": {"type": "object"}}
    for action in ("recall", "store", "update", "delete")
]


def database():
    connection = sqlite3.connect(os.environ.get("MEMORY_DB", "/tmp/autotask-memory-example.sqlite3"))
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL, profile_id TEXT NOT NULL,
        scope TEXT NOT NULL, workspace_id TEXT NOT NULL, project_id TEXT NOT NULL,
        session_id TEXT NOT NULL, entry TEXT NOT NULL)""")
    return connection


def namespace_of(arguments):
    namespace = arguments.get("namespace")
    if not isinstance(namespace, dict):
        raise ValueError("namespace is required")
    user_id, profile_id = namespace.get("user_id"), namespace.get("profile_id")
    if not all(isinstance(value, str) and value for value in (user_id, profile_id)):
        raise ValueError("user_id and profile_id are required")
    allowed_user = os.environ.get("MEMORY_USER_ID", "")
    if allowed_user and user_id != allowed_user:
        raise ValueError("user is not permitted by this provider instance")
    for key in ("workspace_id", "project_id", "session_id"):
        if not isinstance(namespace.get(key, ""), str):
            raise ValueError(key + " must be a string")
    return namespace


def visible(row, namespace):
    if row["user_id"] != namespace["user_id"] or row["profile_id"] != namespace["profile_id"]:
        return False
    return row["scope"] == "user" or (
        row["scope"] == "workspace" and bool(namespace.get("workspace_id")) and row["workspace_id"] == namespace["workspace_id"]
    ) or (
        row["scope"] == "project" and bool(namespace.get("project_id")) and row["project_id"] == namespace["project_id"]
    ) or (
        row["scope"] == "session" and bool(namespace.get("session_id")) and row["session_id"] == namespace["session_id"]
    )


def checked_entry(arguments):
    entry = arguments.get("entry")
    if not isinstance(entry, dict) or not isinstance(entry.get("content"), str) or not entry["content"].strip() or len(entry["content"]) > 16000:
        raise ValueError("entry.content is required and limited to 16000 characters")
    if entry.get("scope") not in ("user", "workspace", "project", "session"):
        raise ValueError("unsupported scope")
    return {
        "scope": entry["scope"], "category": entry.get("category", "custom"),
        "key": entry.get("key", ""), "content": entry["content"],
        "priority": entry.get("priority", 0), "source": entry.get("source", "user"),
        "trust": entry.get("trust", 0.7), "recall_mode": entry.get("recall_mode", "associative"),
    }


def operate(name, arguments):
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be an object")
    namespace = namespace_of(arguments)
    with database() as db:
        if name == "memory_store":
            entry = checked_entry(arguments)
            scope = entry["scope"]
            required = {"workspace": "workspace_id", "project": "project_id", "session": "session_id"}.get(scope)
            if required and not namespace.get(required):
                raise ValueError(required + " is required for " + scope + " scope")
            record_id = "mem:" + str(uuid.uuid4())
            entry["id"] = record_id
            db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?)", (
                record_id, namespace["user_id"], namespace["profile_id"], scope,
                namespace.get("workspace_id", "") if scope in ("workspace", "project", "session") else "",
                namespace.get("project_id", "") if scope in ("project", "session") else "",
                namespace.get("session_id", "") if scope == "session" else "", json.dumps(entry)))
            return {"id": record_id}
        if name not in ("memory_recall", "memory_update", "memory_delete"):
            raise ValueError("unknown memory operation")
        record_id = arguments.get("id")
        if record_id is not None and (not isinstance(record_id, str) or not record_id or len(record_id) > 1024):
            raise ValueError("invalid record ID")
        if name != "memory_recall" and record_id is None:
            raise ValueError("record ID is required")
        rows = db.execute("SELECT * FROM records WHERE user_id=? AND profile_id=?" + (" AND id=?" if record_id else ""),
                          (namespace["user_id"], namespace["profile_id"], record_id) if record_id else (namespace["user_id"], namespace["profile_id"])).fetchall()
        rows = [row for row in rows if visible(row, namespace)]
        if name == "memory_recall":
            limit = arguments.get("limit", 20)
            if not isinstance(limit, int) or not 1 <= limit <= 50:
                raise ValueError("limit must be 1..50")
            query = arguments.get("query", "")
            if not isinstance(query, str) or len(query) > 1000:
                raise ValueError("query must be at most 1000 characters")
            items = [json.loads(row["entry"]) for row in rows if not query or query.lower() in row["entry"].lower()]
            return {"items": items[:limit]}
        if len(rows) != 1:
            raise ValueError("record not found in namespace")
        if name == "memory_delete":
            db.execute("DELETE FROM records WHERE id=?", (record_id,))
            return {"deleted": True}
        entry = checked_entry(arguments)
        if entry["scope"] != rows[0]["scope"]:
            raise ValueError("scope cannot change during update")
        entry["id"] = record_id
        db.execute("UPDATE records SET entry=? WHERE id=?", (json.dumps(entry), record_id))
        return {"id": record_id}


def dispatch(message):
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})
    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32600, "message": "Invalid Request"}}
    if "id" not in message:
        return None
    try:
        if method == "initialize":
            result = {"protocolVersion": VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "autotask-example-memory", "version": "1.0.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name = params.get("name")
            try:
                value = operate(name, params.get("arguments"))
                result = {"content": [{"type": "text", "text": json.dumps(value)}], "structuredContent": value, "isError": False}
            except (ValueError, TypeError) as error:
                result = {"content": [{"type": "text", "text": str(error)}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
    except (ValueError, TypeError):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid params"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def respond(self, status, value=None):
        body = json.dumps(value).encode() if value is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/mcp":
            return self.respond(404)
        secret = os.environ.get("MEMORY_API_KEY", "")
        if not secret or not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + secret):
            self.close_connection = True
            return self.respond(401, {"error": "Unauthorized"})
        origin = self.headers.get("Origin")
        if origin and origin not in {value.strip() for value in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if value.strip()}:
            self.close_connection = True
            return self.respond(403, {"error": "Origin not allowed"})
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
        pass  # Do not log memory content or authorization headers.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not os.environ.get("MEMORY_API_KEY") or not os.environ.get("MEMORY_USER_ID"):
        parser.error("set MEMORY_API_KEY and MEMORY_USER_ID before starting")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Memory MCP example listening on {args.host}:{args.port}/mcp", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
