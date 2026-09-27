"""Generate an author-specific remote Tool Provider manifest."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def public_https(value):
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("use an HTTPS URL without credentials, query or fragment")
    return parsed


parser = argparse.ArgumentParser()
parser.add_argument("--author-id", type=int, required=True)
parser.add_argument("--url", required=True, help="Public HTTPS provider endpoint, normally /provider-mcp")
parser.add_argument("--item-url", required=True, help="Public HTTPS no-credential MCP item endpoint")
parser.add_argument("--out", default="autotask-tool-provider.json")
args = parser.parse_args()
if args.author_id <= 0:
    parser.error("author ID must be positive")
try:
    provider_url = public_https(args.url)
    item_url = public_https(args.item_url)
except ValueError as error:
    parser.error(str(error))

manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
manifest["identity"]["plugin_id"] = f"user-{args.author_id}/remote-tool-catalog"
permission = f"network:{provider_url.hostname}"
manifest["permissions"][0]["permission"] = permission
capability = manifest["capabilities"]["tool_providers"][0]
capability["permissions"] = [permission]
capability["metadata"]["mcp_server"]["name"] = f"user-{args.author_id}-remote-tool-catalog"
capability["metadata"]["mcp_server"]["config"]["url"] = args.url
capability["metadata"]["mcp_server"]["config"]["item_url"] = args.item_url
# item_url is runtime data, not part of the provider metadata contract. Keep it
# in the author output only as a comment-free local reminder instead.
capability["metadata"]["mcp_server"]["config"].pop("item_url", None)
Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {args.out}; verify the provider and returned item endpoint over HTTPS before submitting.")
