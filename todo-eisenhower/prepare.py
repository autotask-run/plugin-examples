"""Generate an author-specific manifest for the fixed todo view protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", type=int, required=True)
    parser.add_argument("--author-name", default="AutoTask plugin author")
    parser.add_argument("--author-handle", default="autotask-run")
    parser.add_argument("--out", default="autotask-eisenhower.json")
    args = parser.parse_args()
    if args.author_id <= 0:
        parser.error("--author-id must be positive")

    root = Path(__file__).parent
    manifest = json.loads((root / "manifest.template.json").read_text(encoding="utf-8"))
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/eisenhower-quadrants"
    manifest["identity"]["author"]["name"] = args.author_name
    manifest["identity"]["author"]["url"] = f"https://github.com/{args.author_handle}"
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}; submit it for review after replacing the example metadata.")


if __name__ == "__main__":
    main()
