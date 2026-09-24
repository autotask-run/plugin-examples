# AutoTask plugin examples

A runnable starting point for third-party AutoTask plugin authors.

Start with [remote-mcp](remote-mcp): a dependency-free Python MCP server that counts supplied text. It does not access files, call other services or retain input. It runs without credentials by default and can optionally require an installer-provided API key.

```sh
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 remote-mcp/server.py
```

Requires Python 3.10+. The local endpoint is `http://127.0.0.1:8765/mcp`. The template's `https://mcp.example.com/mcp` is a placeholder. Host your instance behind HTTPS before submitting.

To try the API-key variant locally, start the server with `MCP_API_KEY=example-secret python3 remote-mcp/server.py`. Requests then need `Authorization: Bearer example-secret`. Generate its manifest with `python3 remote-mcp/prepare.py --author-id 42 --url https://your-mcp.example.com/mcp --auth api-key`; the key itself stays in the server environment and each installer's private AutoTask connection. Use `--auth oauth --oauth-scope read:data` to generate an OAuth declaration for a *separately hosted OAuth-capable* MCP service. The included text-stats server does not implement OAuth.

Read [AUTHORING.md](AUTHORING.md) for the complete author → platform reviewer → consumer workflow, or the [AutoTask developer guide](https://docs.autotask.run/?section=plugin-development).

| File | Purpose |
|---|---|
| [server.py](remote-mcp/server.py) | Stateless Streamable HTTP server and `text_stats` tool |
| [test_server.py](remote-mcp/test_server.py) | Real HTTP protocol and boundary tests |
| [manifest.template.json](remote-mcp/manifest.template.json) | Complete AutoTask remote MCP manifest |
| [prepare.py](remote-mcp/prepare.py) | Fill in your author ID and hosted endpoint |
| [submission.schema.json](remote-mcp/submission.schema.json) | Editor validation for the public submission subset |

The submission workflow requires an AutoTask build exposing `/api/v1/plugin-submissions`, and CLI **0.1.1 or later** with `plugin submit` / `plugin submissions`. The MCP example itself runs independently of AutoTask. A [public demo endpoint](https://docs.autotask.run/examples/text-stats/mcp) is available for client testing; actual submissions should use an HTTPS endpoint operated by the author.

Supported submission scope: remote HTTPS MCP tools with no auth, installer-provided API key, or MCP OAuth authorization code. Platform review and publication remain separate from submission, installation, authorization, profile binding and actual tool invocation. Executable packages are not part of this example.

The server uses the MCP [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and [tools protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). It returns JSON responses and does not provide a server-initiated SSE stream. Unknown browser Origins are rejected by default. Use an HTTPS proxy with rate/request-size limits for a public deployment; this is a small instructional server, not a production hosting stack.

License: [MIT](LICENSE).
