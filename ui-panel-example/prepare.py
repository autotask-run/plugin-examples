"""Fill the public UI panel manifest with an AutoTask author identity."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", type=int, required=True)
    parser.add_argument("--author-name", default="AutoTask plugin author")
    parser.add_argument("--author-handle", default="autotask-run")
    parser.add_argument("--out", default="autotask-ui-panel.json")
    args = parser.parse_args()
    if args.author_id < 1:
        parser.error("--author-id must be positive")
    manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/repository-review-panel"
    manifest["identity"]["author"]["name"] = args.author_name
    manifest["identity"]["author"]["url"] = f"https://github.com/{args.author_handle}"
    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
