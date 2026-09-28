"""Generate an owner-only manifest for the declarative reading-note type."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", type=int, required=True)
    parser.add_argument("--author-name", default="AutoTask plugin author")
    parser.add_argument("--out", default="autotask-reading-note.json")
    args = parser.parse_args()
    if args.author_id <= 0:
        parser.error("--author-id must be positive")

    root = Path(__file__).parent
    manifest = json.loads((root / "manifest.template.json").read_text(encoding="utf-8"))
    manifest["identity"]["plugin_id"] = f"private-{args.author_id}/reading-note"
    manifest["identity"]["author"]["name"] = args.author_name
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}; this declarative note type is owner-only in the current release.")


if __name__ == "__main__":
    main()
