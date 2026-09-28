# Synthetic OAuth MCP acceptance fixture

`server.py` serves an auto-consent OAuth authorization server and a protected
Streamable HTTP MCP tool. It exists to verify AutoTask's published-environment
OAuth protocol path; it is **not** an authentication service for real data.
The fixed public resource is `https://docs.autotask.run/examples/oauth-mcp/mcp`,
the issuer is `https://docs.autotask.run/examples/oauth-mcp`, and the registered
client ID is `autotask-plugin-acceptance`. Its only registered callback is
`https://api.autotask.run/api/v1/plugin-lifecycle/oauth/callback`.

The `oauth_echo` MCP tool needs scope `read:demo` and returns only its synthetic
message. Tokens expire after 15 seconds so a managed Agent task exercises the
refresh path. Codes and refresh tokens are one use. Authorization auto-consents
for the fixed client, so the example proves protocol interoperability but not
real user authentication or independent third-party compatibility.

Run tests with `python3 -m unittest discover -s oauth-mcp-example -p 'test_*.py' -v`.
Run locally with `python3 oauth-mcp-example/server.py --host 127.0.0.1 --port 8770`.
