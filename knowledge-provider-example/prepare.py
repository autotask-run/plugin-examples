"""Generate an author-specific public Knowledge Source manifest."""
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
parser.add_argument("--out", default="autotask-knowledge-provider.json")
args = parser.parse_args()
if args.author_id <= 0:
    parser.error("author ID must be positive")
try:
    endpoint = public_https(args.url)
except ValueError as error:
    parser.error(str(error))
manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
manifest["identity"]["plugin_id"] = f"user-{args.author_id}/docs-source"
permission = f"network:{endpoint.hostname}"
manifest["permissions"][0]["permission"] = permission
capability = manifest["capabilities"]["knowledge_sources"][0]
capability["permissions"] = [permission]
capability["metadata"]["mcp_server"]["name"] = f"user-{args.author_id}-docs-source"
capability["metadata"]["mcp_server"]["config"]["url"] = args.url
Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {args.out}; verify the provider over HTTPS before submitting.")
