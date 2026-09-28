"""Generate an author-specific Obsidian-style note plugin manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", type=int, required=True)
    parser.add_argument("--author-name", default="AutoTask plugin author")
    parser.add_argument("--author-handle", default="autotask-run")
    parser.add_argument("--url", required=True, help="Author-hosted public HTTPS MCP endpoint")
    parser.add_argument("--out", default="autotask-plugin.json")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if args.author_id <= 0:
        parser.error("--author-id must be positive")
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("--url must be HTTPS without credentials, query or fragment")

    root = Path(__file__).parent
    manifest = json.loads((root / "manifest.template.json").read_text(encoding="utf-8"))
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/obsidian-note-template"
    manifest["identity"]["author"]["name"] = args.author_name
    manifest["identity"]["author"]["url"] = f"https://github.com/{args.author_handle}"
    permission = f"network:{parsed.hostname}"
    for entry in manifest["permissions"]:
        if entry["permission"].startswith("network:"):
            entry["permission"] = permission
    for tool in manifest["capabilities"]["tools"]:
        tool["permissions"] = [permission]
        tool["metadata"]["mcp_server"]["config"]["url"] = args.url
        tool["metadata"]["mcp_server"]["name"] = f"user-{args.author_id}-obsidian-note-template"
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}; host the endpoint before submitting it for review.")


if __name__ == "__main__":
    main()
