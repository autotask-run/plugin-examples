#!/usr/bin/env python3
"""Create a submission manifest with an author-owned namespace."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", required=True, type=int)
    parser.add_argument("--output", default="manifest.json")
    args = parser.parse_args()
    if args.author_id <= 0:
        parser.error("author id must be positive")

    root = Path(__file__).parent
    manifest = json.loads((root / "manifest.template.json").read_text())
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/example-llm"
    Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
