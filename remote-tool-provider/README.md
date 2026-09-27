# Remote MCP Tool Provider example

This dependency-free Python 3.10 example implements the public
`autotask.tool-provider.v1` contract. It exposes an authenticated provider
endpoint with `validate_config` and paged `sync_catalog` operations. The
catalog returns no-credential Streamable HTTP MCP descriptors that can be
installed separately and called by an Agent.

Run the tests:

```sh
python3 -m unittest discover -s remote-tool-provider -v
```

Run the service locally:

```sh
TOOL_PROVIDER_API_KEY=local-provider-key \
  python3 remote-tool-provider/server.py
```

The provider listens on `/provider-mcp`; returned `weather` items use the
unauthenticated `/items/weather/mcp` endpoint. Put both paths behind the
author's HTTPS reverse proxy before submitting. The local URLs are only test
fixtures and must not be used in a public manifest.

`prepare.py` fills the author namespace and provider URL in
`manifest.template.json`:

```sh
python3 remote-tool-provider/prepare.py \
  --author-id 42 \
  --url https://catalog.example.com/provider-mcp \
  --item-url https://catalog.example.com/items/weather/mcp \
  --out autotask-tool-provider.json
```

The provider key is never written to the manifest. An AutoTask installer
connects the key to the provider plugin installation; the key is not copied to
the returned MCP item installation.
