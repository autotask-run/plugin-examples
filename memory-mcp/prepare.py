"""Fill the public submission manifest with your AutoTask user ID and HTTPS URL."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", type=int, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", default="autotask-memory-plugin.json")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if args.author_id < 1 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        parser.error("provide a positive author ID and public HTTPS URL without credentials, query or fragment")
    manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
    manifest["identity"]["plugin_id"] = f"user-{args.author_id}/personal-memory"
    manifest["capabilities"]["memory_providers"][0]["metadata"]["mcp_server"]["config"]["url"] = args.url
    permission = "network:" + parsed.hostname
    manifest["permissions"][0]["permission"] = permission
    manifest["capabilities"]["memory_providers"][0]["permissions"] = [permission]
    Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
