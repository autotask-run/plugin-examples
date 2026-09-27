"""Deterministic provider logic kept separate for focused contract tests."""
import re


class ProviderError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


DOCUMENTS = [
    {
        "external_id": "guide/intro",
        "revision": "example-docs-v1",
        "title": "Introduction",
        "text": "AutoTask plugins are reviewed before another workspace can install them.",
        "source_url": "https://docs.example.com/guide/intro",
    },
    {
        "external_id": "guide/security",
        "revision": "example-docs-v1",
        "title": "Security",
        "text": "Credentials are connected per installation and never embedded in a manifest.",
        "source_url": "https://docs.example.com/guide/security",
    },
]


def process(request):
    operation = request.get("operation")
    if operation == "validate_config":
        config = request.get("config", {})
        if not isinstance(config, dict):
            raise ProviderError("invalid_config", "config must be an object")
        collection = config.get("collection", "docs")
        if not isinstance(collection, str) or not re.fullmatch(r"[a-z0-9_-]{1,64}", collection):
            raise ProviderError("invalid_config", "collection must be a bounded lowercase name")
        return {"valid": True, "normalized_config": {"collection": collection}, "warnings": []}
    if operation != "sync_documents":
        raise ProviderError("unknown_operation", "unsupported provider operation")
    cursor = request.get("cursor", "")
    if cursor not in ("", "example-docs-v1"):
        raise ProviderError("invalid_cursor", "cursor is not recognized")
    limits = request.get("limits", {})
    max_items = limits.get("max_items", 100) if isinstance(limits, dict) else 100
    if not isinstance(max_items, int) or max_items < 1 or max_items > 100:
        raise ProviderError("invalid_limits", "max_items must be 1..100")
    documents = DOCUMENTS[:max_items]
    return {"documents": documents, "removed_external_ids": [], "cursor": "example-docs-v1", "complete": True}
