#!/usr/bin/env python3
"""Minimal stdio-json-v1 local tool plugin."""

from __future__ import annotations

import json
import sys
from typing import Any


TOOL_NAME = "plugin.text_stats"


def result(status: str, **fields: Any) -> int:
    payload = {"status": status, **fields}
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


def main() -> int:
    line = sys.stdin.readline()
    if not line:
        return result("error", message="a JSON request is required")
    try:
        request = json.loads(line)
    except json.JSONDecodeError:
        return result("error", message="request must be one JSON object")
    if not isinstance(request, dict):
        return result("error", message="request must be an object")
    if request.get("tool_name") != TOOL_NAME:
        return result("denied", message=f"unsupported tool: {request.get('tool_name')!r}")
    if request.get("sandbox_mode") != "read-only":
        return result("denied", message="text statistics requires read-only sandbox")
    input_payload = request.get("input")
    if not isinstance(input_payload, dict) or not isinstance(input_payload.get("text"), str):
        return result("error", message="input.text must be a string")
    text = input_payload["text"]
    return result(
        "ok",
        characters=len(text),
        words=len(text.split()),
        lines=len(text.splitlines()),
    )


if __name__ == "__main__":
    raise SystemExit(main())
