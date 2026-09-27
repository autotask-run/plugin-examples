# Skill Provider example

This dependency-free provider demonstrates the public `autotask.skill-provider.v1`
contract from [the AutoTask guide](https://docs.autotask.run/docs/plugin-development.md).
`server.py` exposes `validate_config`, `sync`, and `get_content` through a
Streamable HTTP MCP endpoint. It uses a deterministic inline catalog and an
installation-scoped API Key; it never writes a database.

```sh
python3 -m unittest discover -s skill-provider-example -v
SKILL_PROVIDER_API_KEY=test-key python3 skill-provider-example/server.py
```

The private `provider.py` JSON-lines adapter remains a small fixture for unit
testing normalization. The public MCP response uses `records`, `source_ref`,
`readme_content`, `manifest_json`, `revision`, `complete=true`, and diagnostics.
AutoTask validates every record, computes the stored hash, applies
scope/ownership rules, and snapshots content before a Worker sees it. Public
sync is a complete bounded snapshot; pagination and `get_file` are not part of
this first contract.

`manifest.template.json` is a public submission template. Replace the example
HTTPS URL and author namespace with `prepare.py`, then run `plugin submit`.
The provider API key is configured by the installer after publication and never
belongs in the manifest.
