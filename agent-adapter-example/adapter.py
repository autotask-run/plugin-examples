#!/usr/bin/env python3
"""Reference Agent configuration adapter for the AutoTask JSONL contract.

The process handles one request and writes one JSON object to stdout.  It is a
configuration adapter: it does not run an Agent, receive AutoTask credentials,
or make network calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROTOCOL = "autotask.agent-adapter.protocol.v1"
TARGET_RELATIVE_PATH = Path(".config/example-agent/config.json")


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def read_message() -> dict[str, Any]:
    line = sys.stdin.readline()
    if not line:
        fail("expected one JSON request line")
    try:
        message = json.loads(line)
    except json.JSONDecodeError as error:
        fail(f"invalid JSON request: {error}")
    if not isinstance(message, dict):
        fail("request must be a JSON object")
    if message.get("protocol") != PROTOCOL:
        fail("unsupported protocol")
    return message


def target_path(host: dict[str, Any]) -> Path:
    home = host.get("home")
    if not isinstance(home, str) or not home:
        fail("host.home is required")
    return Path(home) / TARGET_RELATIVE_PATH


def discover(payload: dict[str, Any]) -> dict[str, Any]:
    host = payload.get("host")
    if not isinstance(host, dict):
        fail("discover.host is required")
    return {
        "protocol": PROTOCOL,
        "targets": [{"path": str(target_path(host)), "format": "json"}],
        "warnings": [],
    }


def server_config(request: dict[str, Any]) -> dict[str, Any]:
    transport = request.get("transport")
    if transport == "remote":
        token_env = request.get("token_env", "AUTOTASK_TOKEN")
        return {
            "url": request["mcp_url"],
            "transport": "streamable-http",
            # This is an environment reference, never a token value.  A real
            # client may use its own environment interpolation syntax.
            "headers": {"Authorization": f"Bearer ${{{token_env}}}"},
        }
    if transport == "stdio":
        return {
            "command": "autotask",
            "args": ["mcp", "serve", "--server", request["server_url"]],
            "transport": "stdio",
        }
    fail("request.transport must be remote or stdio")


def plan(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    host = payload.get("host")
    targets = payload.get("targets")
    if not isinstance(request, dict) or not isinstance(host, dict):
        fail("plan.request and plan.host are required")
    if not isinstance(targets, list) or len(targets) != 1:
        fail("this example manages exactly one target")

    expected_path = target_path(host)
    target = targets[0]
    if not isinstance(target, dict) or Path(str(target.get("path"))) != expected_path:
        fail("plan target does not match the discovered target")
    if target.get("format") != "json":
        fail("the example target format is json")

    original_content = target.get("original_content")
    if original_content is None:
        document: dict[str, Any] = {}
    else:
        try:
            parsed = json.loads(original_content)
        except (TypeError, json.JSONDecodeError) as error:
            fail(f"existing target is not valid JSON: {error}")
        if not isinstance(parsed, dict):
            fail("existing target must contain a JSON object")
        document = parsed

    servers = document.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        fail("existing mcpServers value must be an object")
    servers["autotask"] = server_config(request)
    model = request.get("model")
    if isinstance(model, str) and model.strip() and "model" not in document:
        # Preserve an explicit client model.  This sample only fills an empty
        # model slot and therefore remains idempotent for repeated setup.
        document["model"] = model.strip()

    return {
        "protocol": PROTOCOL,
        "files": [
            {
                "path": str(expected_path),
                "content": json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                "transport": request["transport"],
                "model_configured": isinstance(model, str) and bool(model.strip()),
            }
        ],
        "warnings": [
            "This example emits an environment reference; it never receives or stores token values."
        ],
    }


def main() -> None:
    message = read_message()
    operation = message.get("operation")
    payload = message.get("payload")
    if not isinstance(payload, dict):
        fail("payload must be an object")
    if operation == "discover":
        response = discover(payload)
    elif operation == "plan":
        response = plan(payload)
    else:
        fail("operation must be discover or plan")
    print(json.dumps(response, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
