# AutoTask plugin examples

A runnable starting point for third-party AutoTask plugin authors.

Start with [remote-mcp](remote-mcp): a dependency-free Python MCP server that counts supplied text. It does not access files, call other services, retain input or require credentials.

For replaceable personal memory, see [memory-mcp](memory-mcp): an independent authenticated MCP server with persistent SQLite storage and a reviewed memory-provider manifest.

For a public remote Tool Provider, see [remote-tool-provider](remote-tool-provider): an authenticated paged catalog whose returned MCP items are installed and invoked without copying the provider credential.

For public static Skill Packs, see [skill-example](skill-example): it embeds `SKILL.md`, `autotask-skill.json`, and bounded text references in the reviewed manifest. For a public remote Skill Provider, see [skill-provider-example](skill-provider-example): it implements the bounded `autotask.skill-provider.v1` MCP catalog contract. The memory example covers all four operations and cross-user namespace isolation.

For a local CLI Tool, see [local-tool-example](local-tool-example): it runs a
read-only `stdio-json-v1` process from `autotask run-local`, includes Linux/macOS
and Windows launch manifests, and demonstrates plugin-side sandbox checks. Local
executables are intentionally outside the public `plugin submit` path.

For workspace-private extensions, see [hook-example](hook-example) for a
`TaskCompleted` prompt Hook and [slash-command-example](slash-command-example)
for a prompt Slash Command. These examples use existing server runtimes and
are intentionally outside the public `plugin submit` allowlist.

```sh
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 -m unittest discover -s memory-mcp -v
python3 -m unittest discover -s remote-tool-provider -v
python3 -m unittest discover -s skill-example -v
python3 -m unittest discover -s skill-provider-example -v
python3 -m unittest discover -s local-tool-example -v
python3 -m unittest discover -s hook-example -v
python3 -m unittest discover -s slash-command-example -v
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
| [remote-tool-provider/](remote-tool-provider) | Public `autotask.tool-provider.v1` provider, paged catalog and no-credential item MCP tests |
| [skill-example/](skill-example) | Public embedded Skill Pack, artifact contract, preparation script and bounded validator |
| [skill-provider-example/](skill-provider-example) | Public `autotask.skill-provider.v1` MCP provider and complete snapshot tests |
| [local-tool-example/](local-tool-example) | Local CLI `stdio-json-v1` tool, platform launch manifests, and sandbox tests |
| [hook-example/](hook-example) | Workspace-private `autotask.hook.v1` prompt Hook and lifecycle steps |
| [slash-command-example/](slash-command-example) | Workspace-private prompt Slash Command, raw args and ambiguity rules |

The submission workflow requires an AutoTask build exposing `/api/v1/plugin-submissions`, and CLI **0.1.1 or later** with `plugin submit` / `plugin submissions`. The MCP example itself runs independently of AutoTask. A [public demo endpoint](https://docs.autotask.run/examples/text-stats/mcp) is available for client testing; actual submissions should use an HTTPS endpoint operated by the author.

Public submissions support remote HTTPS MCP tools, remote `autotask.tool-provider.v1` catalogs, remote `autotask.skill-provider.v1` catalogs, immutable text-only `skill_pack` bundles and personal memory providers. API keys or OAuth are declared in the manifest and connected by each installer; credentials are never embedded in the submission. Platform review and publication remain separate from installation, profile binding and actual invocation. Local executable packages and personal private Skill bundles remain outside the public submission path; use `--local-plugin` or a workspace-private catalog entry for local development.

The server uses the MCP [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and [tools protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). It returns JSON responses and does not provide a server-initiated SSE stream. Unknown browser Origins are rejected by default. Use an HTTPS proxy with rate/request-size limits for a public deployment; this is a small instructional server, not a production hosting stack.

License: [MIT](LICENSE).
