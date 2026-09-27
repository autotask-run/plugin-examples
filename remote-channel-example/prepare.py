import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", default="autotask-remote-channel.json")
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).parent / "manifest.template.json").read_text())
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/remote-channel-example"
    manifest["identity"]["author"]["name"] = f"User {args.author_id}"
    manifest["capabilities"]["channels"][0]["metadata"]["mcp_server"]["config"]["url"] = args.url
    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
