import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--auth-type", choices=("none", "api_key", "oauth"), default="none")
    parser.add_argument("--api-key-header", default="Authorization")
    parser.add_argument("--api-key-prefix", default="Bearer ")
    parser.add_argument("--oauth-scope", action="append", default=[])
    parser.add_argument("--out", default="autotask-remote-channel.json")
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).parent / "manifest.template.json").read_text())
    # Workspace-private plugins must not use the reviewed public user-<id>/
    # namespace. This example keeps the author ID only to make a repeatable,
    # collision-resistant local slug.
    manifest["identity"]["plugin_id"] = f"workspace-{args.author_id}/remote-channel-example"
    manifest["identity"]["author"]["name"] = f"User {args.author_id}"
    manifest["capabilities"]["channels"][0]["metadata"]["mcp_server"]["config"]["url"] = args.url
    auth = {"type": args.auth_type}
    if args.auth_type == "api_key":
        auth.update({"header": args.api_key_header, "prefix": args.api_key_prefix})
    elif args.auth_type == "oauth":
        auth["scopes"] = args.oauth_scope
    manifest["capabilities"]["channels"][0]["metadata"]["mcp_server"]["auth"] = auth
    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
