# AutoTask plugin examples

A runnable starting point for third-party AutoTask plugin authors.

Start with [remote-mcp](remote-mcp): a dependency-free Python MCP server that counts supplied text. It does not access files, call other services, retain input or require credentials.

```sh
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 remote-mcp/server.py
```

Requires Python 3.10+. The local endpoint is `http://127.0.0.1:8765/mcp`. The template's `https://mcp.example.com/mcp` is a placeholder. Host your instance behind HTTPS before submitting.

Read [AUTHORING.md](AUTHORING.md) for the complete author → platform reviewer → consumer workflow, or the [AutoTask developer guide](https://docs.autotask.run/?section=plugin-development).

| File | Purpose |
|---|---|
| [server.py](remote-mcp/server.py) | Stateless Streamable HTTP server and `text_stats` tool |
| [test_server.py](remote-mcp/test_server.py) | Real HTTP protocol and boundary tests |
| [manifest.template.json](remote-mcp/manifest.template.json) | Complete AutoTask remote MCP manifest |
| [prepare.py](remote-mcp/prepare.py) | Fill in your author ID and hosted endpoint |
| [submission.schema.json](remote-mcp/submission.schema.json) | Editor validation for the public submission subset |

The submission workflow requires an AutoTask build exposing `/api/v1/plugin-submissions`, and CLI **0.1.1 or later** with `plugin submit` / `plugin submissions`. The MCP example itself runs independently of AutoTask. A [public demo endpoint](https://docs.autotask.run/examples/text-stats/mcp) is available for client testing; actual submissions should use an HTTPS endpoint operated by the author.

First supported submission scope: remote HTTPS MCP tools without shared credentials. Platform review and publication remain separate from submission, installation, profile binding and actual tool invocation. Executable packages, OAuth and authenticated remote providers are not part of this example.

The server uses the MCP [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and [tools protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). It returns JSON responses and does not provide a server-initiated SSE stream. Unknown browser Origins are rejected by default. Use an HTTPS proxy with rate/request-size limits for a public deployment; this is a small instructional server, not a production hosting stack.

License: [MIT](LICENSE).
