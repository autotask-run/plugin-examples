# AutoTask plugin examples

A runnable starting point for third-party AutoTask plugin authors.

Start with [remote-mcp](remote-mcp): a dependency-free Python MCP server that counts supplied text. It does not access files, call other services, retain input or require credentials.

For replaceable personal memory, see [memory-mcp](memory-mcp): an independent authenticated MCP server with persistent SQLite storage and a reviewed memory-provider manifest.

For the next capability families, see [skill-example](skill-example) for a local Skill bundle and [skill-provider-example](skill-provider-example) for a deterministic Skill Provider contract fixture. These two are private/workspace reference examples; they are not public submission formats yet. The memory example covers all four operations and cross-user namespace isolation.

```sh
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 -m unittest discover -s memory-mcp -v
python3 -m unittest discover -s skill-example -v
python3 -m unittest discover -s skill-provider-example -v
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
| [memory-mcp/](memory-mcp) | Personal `autotask.memory.v1` MCP provider and persistence tests |
| [skill-example/](skill-example) | Private Skill bundle, artifact contract and bounded validator |
| [skill-provider-example/](skill-provider-example) | JSON-lines Skill Provider operation contract fixture |

The submission workflow requires an AutoTask build exposing `/api/v1/plugin-submissions`, and CLI **0.1.1 or later** with `plugin submit` / `plugin submissions`. The MCP example itself runs independently of AutoTask. A [public demo endpoint](https://docs.autotask.run/examples/text-stats/mcp) is available for client testing; actual submissions should use an HTTPS endpoint operated by the author.

Public submissions support remote HTTPS MCP tools and personal memory providers. API keys or OAuth are declared in the manifest and connected by each installer; credentials are never embedded in the submission. Platform review and publication remain separate from installation, profile binding and actual invocation. Executable packages remain outside this example.

The server uses the MCP [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and [tools protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). It returns JSON responses and does not provide a server-initiated SSE stream. Unknown browser Origins are rejected by default. Use an HTTPS proxy with rate/request-size limits for a public deployment; this is a small instructional server, not a production hosting stack.

License: [MIT](LICENSE).
