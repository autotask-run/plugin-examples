# Knowledge Source Provider example

This dependency-free example implements the public `autotask.knowledge-source.v1`
contract from the [AutoTask authoring guide](https://docs.autotask.run/docs/plugin-development.md).
It exposes `validate_config` and `sync_documents` through Streamable HTTP MCP,
returns two bounded text documents, and never follows a provider-supplied URL.

```sh
python3 -m unittest discover -s knowledge-provider-example -v
KNOWLEDGE_PROVIDER_API_KEY=test-key python3 knowledge-provider-example/server.py
```

The public sync response contains `documents`, `removed_external_ids`, `cursor`
and `complete`. Each document has a stable `external_id`, `revision`, title,
text and display-only `source_url`. AutoTask owns the Knowledge Base, indexing,
conflict handling and retrieval. The API key is configured by the installer and
never belongs in the manifest.

Run `prepare.py` with your author ID and a public HTTPS endpoint to generate a
submission manifest. The template endpoint is a placeholder and the local HTTP
server is for contract tests only.
