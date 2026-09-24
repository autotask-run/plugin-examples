"""Generate an author-specific manifest; no credentials are read or written."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument("--author-id", type=int, required=True, help="Numeric ID from your AutoTask user namespace")
parser.add_argument("--url", required=True, help="Public HTTPS MCP endpoint")
parser.add_argument("--out", default="autotask-plugin.json")
parser.add_argument("--auth", choices=("none", "api-key", "oauth"), default="none", help="Public manifest auth declaration; never a credential")
parser.add_argument("--api-key-header", default="Authorization")
parser.add_argument("--api-key-prefix", choices=("", "Bearer ", "Token "), default="Bearer ")
parser.add_argument("--oauth-scope", action="append", default=[], help="Repeat for each required OAuth scope")
args = parser.parse_args()
url = urlparse(args.url)
if args.author_id <= 0 or url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
    parser.error("Use a positive author ID and an HTTPS URL without credentials, query or fragment")
if args.auth == "api-key" and (not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,63}", args.api_key_header) or args.api_key_header.lower() in {"host", "cookie", "content-type", "connection", "proxy-authorization"}):
    parser.error("Use a safe API-key header name")
if args.auth == "oauth" and (len(args.oauth_scope) > 20 or len(set(args.oauth_scope)) != len(args.oauth_scope) or any(not re.fullmatch(r"[A-Za-z0-9._:/-]{1,128}", scope) for scope in args.oauth_scope)):
    parser.error("OAuth scopes must be distinct safe strings (at most 20)")
manifest = json.loads(Path(__file__).with_name("manifest.template.json").read_text())
manifest["identity"]["plugin_id"] = f"user-{args.author_id}/text-stats"
permission = f"network:{url.hostname}"
manifest["permissions"][0]["permission"] = permission
tool = manifest["capabilities"]["tools"][0]
tool["permissions"] = [permission]
tool["metadata"]["mcp_server"]["name"] = f"user-{args.author_id}-text-stats"
tool["metadata"]["mcp_server"]["config"]["url"] = args.url
if args.auth == "api-key":
    manifest["identity"]["description"] += " Requires an installer-provided API key."
    tool["metadata"]["mcp_server"]["auth"] = {"type": "api_key", "header": args.api_key_header, "prefix": args.api_key_prefix}
elif args.auth == "oauth":
    manifest["identity"]["description"] += " Requires installer OAuth authorization."
    tool["metadata"]["mcp_server"]["auth"] = {"type": "oauth", "scopes": args.oauth_scope}
Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {args.out}; publish the endpoint before submitting this manifest for review.")
if args.auth == "oauth":
    print("The included text-stats server does not implement OAuth. Deploy an MCP resource with Protected Resource Metadata and a PKCE-capable authorization server before submitting.")
