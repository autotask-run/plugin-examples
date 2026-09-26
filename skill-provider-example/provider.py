"""JSON-lines reference adapter for the AutoTask Skill Provider contract.

The adapter is intentionally deterministic and network-free. A real provider
would replace the inline catalog with a source-specific connector while keeping
the request/response shapes and server-owned validation boundary.
"""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Any

MAX_ITEMS = 100
MAX_BYTES = 256 * 1024
REVISION = "example-catalog-v1"

DEFAULT_CATALOG: list[dict[str, Any]] = [
    {
        "external_id": "example/release-checklist",
        "name": "release-checklist",
        "description": "Check release evidence, versioning and rollback notes.",
        "version": "1.0.0",
        "author": {"name": "Example catalog"},
        "tags": ["release", "review"],
        "readme_content": "---\nname: example/release-checklist\ndescription: Check release evidence.\nversion: 1.0.0\nauthor: Example catalog\ntags:\n  - release\ntools:\n  - file_read\n---\n\n# Release checklist\n",
        "manifest_json": '{"id":"example/release-checklist","version":"1.0.0"}',
        "files": [{"path": "references/release.md", "content": "Confirm version, evidence, rollback and owner."}],
    },
    {
        "external_id": "example/incident-summary",
        "name": "incident-summary",
        "description": "Turn incident evidence into a concise follow-up artifact.",
        "version": "1.0.0",
        "author": {"name": "Example catalog"},
        "tags": ["incident", "artifact-producer"],
        "readme_content": "---\nname: example/incident-summary\ndescription: Summarize incident evidence.\nversion: 1.0.0\nauthor: Example catalog\ntags:\n  - incident\ntools:\n  - file_read\n---\n\n# Incident summary\n",
        "manifest_json": '{"id":"example/incident-summary","version":"1.0.0"}',
        "files": [{"path": "references/incident.md", "content": "Record impact, timeline, root cause and next action."}],
    },
]


class ProviderError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _catalog(config: Any) -> list[dict[str, Any]]:
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ProviderError("invalid_config", "config must be an object")
    catalog = config.get("catalog", DEFAULT_CATALOG)
    if not isinstance(catalog, list) or len(catalog) > MAX_ITEMS:
        raise ProviderError("invalid_config", f"catalog must be a list with at most {MAX_ITEMS} records")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(catalog):
        if not isinstance(raw, dict):
            raise ProviderError("invalid_config", f"catalog[{index}] must be an object")
        required = ("external_id", "name", "description", "version", "readme_content", "manifest_json")
        if any(not isinstance(raw.get(key), str) or not raw[key].strip() for key in required):
            raise ProviderError("invalid_config", f"catalog[{index}] is missing a required string field")
        external_id = raw["external_id"].strip()
        if external_id in seen:
            raise ProviderError("invalid_config", f"duplicate external_id: {external_id}")
        seen.add(external_id)
        files = raw.get("files", [])
        if not isinstance(files, list) or len(files) > 50:
            raise ProviderError("invalid_config", f"catalog[{index}].files must contain at most 50 files")
        safe_files = []
        for file in files:
            if not isinstance(file, dict) or not isinstance(file.get("path"), str) or not isinstance(file.get("content"), str):
                raise ProviderError("invalid_config", f"catalog[{index}].files contains an invalid file")
            path = file["path"]
            if path.startswith("/") or ".." in path.split("/"):
                raise ProviderError("invalid_config", f"catalog[{index}] contains an unsafe file path")
            safe_files.append({"path": path, "content": file["content"]})
        normalized.append({
            "external_id": external_id,
            "name": raw["name"].strip(),
            "description": raw["description"].strip(),
            "version": raw["version"].strip(),
            "author": raw.get("author", {"name": "Example catalog"}),
            "tags": raw.get("tags", []),
            "readme_content": raw["readme_content"],
            "manifest_json": raw["manifest_json"],
            "files": safe_files,
        })
    return normalized


def _source_id(source: Any) -> int | None:
    if not isinstance(source, dict):
        return None
    value = source.get("id")
    return value if isinstance(value, int) and value > 0 else None


def validate_config(request: dict[str, Any]) -> dict[str, Any]:
    config = request.get("config", {})
    catalog = _catalog(config)
    return {
        "valid": True,
        "normalized_config": {"catalog": catalog},
        "warnings": [],
    }


def _content_hash(item: dict[str, Any]) -> str:
    payload = item["readme_content"] + "\n" + item["manifest_json"] + json.dumps(item["files"], sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_ref(item: dict[str, Any], source_id: int | None) -> dict[str, Any]:
    return {
        "provider_id": "example_catalog",
        "source_id": source_id,
        "repository": "example-inline-catalog",
        "path": item["external_id"],
        "ref": "main",
        "revision": REVISION,
        "url": "https://example.invalid/catalog/" + item["external_id"],
    }


def sync(request: dict[str, Any]) -> dict[str, Any]:
    source = request.get("source", {})
    config = source.get("config", {}) if isinstance(source, dict) else {}
    items = _catalog(config)
    limits = request.get("limits", {})
    max_items = limits.get("max_items", MAX_ITEMS) if isinstance(limits, dict) else MAX_ITEMS
    if not isinstance(max_items, int) or max_items < 1:
        raise ProviderError("invalid_request", "limits.max_items must be a positive integer")
    max_items = min(max_items, MAX_ITEMS)
    complete = len(items) <= max_items
    records = []
    for item in items[:max_items]:
        records.append({
            "external_id": item["external_id"],
            "name": item["name"],
            "description": item["description"],
            "version": item["version"],
            "author": item["author"],
            "tags": item["tags"],
            "source_ref": _source_ref(item, _source_id(source)),
            "readme_content": item["readme_content"],
            "manifest_json": item["manifest_json"],
            "content_hash": _content_hash(item),
            "available": True,
        })
    warnings = [] if complete else ["catalog page is partial; absent records must remain available"]
    return {
        "records": records,
        "removed_external_ids": [],
        "cursor": {"revision": REVISION, "offset": len(records)},
        "complete": complete,
        "diagnostics": {"items_seen": len(records), "warnings": warnings},
    }


def _find_item(request: dict[str, Any]) -> dict[str, Any]:
    source = request.get("source", {})
    config = source.get("config", {}) if isinstance(source, dict) else {}
    items = _catalog(config)
    source_ref = request.get("source_ref", {})
    external_id = source_ref.get("path") if isinstance(source_ref, dict) else None
    skill_id = request.get("skill_id")
    wanted = skill_id or external_id
    for item in items:
        if item["external_id"] == wanted:
            return item
    raise ProviderError("not_found", f"skill not found: {wanted}")


def get_content(request: dict[str, Any]) -> dict[str, Any]:
    item = _find_item(request)
    return {
        "readme_content": item["readme_content"],
        "manifest_json": item["manifest_json"],
        "files": [{"path": file["path"], "content": file["content"], "sha256": hashlib.sha256(file["content"].encode("utf-8")).hexdigest()} for file in item["files"]],
        "revision": REVISION,
        "content_hash": _content_hash(item),
    }


def get_file(request: dict[str, Any]) -> dict[str, Any]:
    item = _find_item(request)
    wanted = request.get("file_path")
    for file in item["files"]:
        if file["path"] == wanted:
            return {"path": wanted, "content": file["content"], "revision": REVISION}
    raise ProviderError("not_found", f"file not found: {wanted}")


OPERATIONS = {"validate_config": validate_config, "sync": sync, "get_content": get_content, "get_file": get_file}


def process(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ProviderError("invalid_request", "request must be an object")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise ProviderError("unknown_operation", f"unsupported operation: {operation}")
    return OPERATIONS[operation](request)


def _write_response(response: dict[str, Any]) -> None:
    encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_BYTES:
        raise ProviderError("response_too_large", "provider response exceeds the bounded output limit")
    sys.stdout.write(encoded + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            result = process(json.loads(line))
            _write_response({"ok": True, "result": result})
        except (json.JSONDecodeError, ProviderError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, ProviderError) else "invalid_json"
            _write_response({"ok": False, "error": {"code": code, "message": str(exc)}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
