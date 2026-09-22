"""Generate an author-specific manifest; no credentials are read or written."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument("--author-id", type=int, required=True, help="Numeric ID from your AutoTask user namespace")
parser.add_argument("--url", required=True, help="Public HTTPS MCP endpoint")
parser.add_argument("--out", default="autotask-plugin.json")
args = parser.parse_args()
url = urlparse(args.url)
if args.author_id <= 0 or url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
    parser.error("Use a positive author ID and an HTTPS URL without credentials, query or fragment")
manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
manifest["identity"]["plugin_id"] = f"user-{args.author_id}/text-stats"
permission = f"network:{url.hostname}"
manifest["permissions"][0]["permission"] = permission
tool = manifest["capabilities"]["tools"][0]
tool["permissions"] = [permission]
tool["metadata"]["mcp_server"]["name"] = f"user-{args.author_id}-text-stats"
tool["metadata"]["mcp_server"]["config"]["url"] = args.url
Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {args.out}; publish the endpoint before submitting this manifest for review.")
