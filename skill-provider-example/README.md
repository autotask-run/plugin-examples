# Skill Provider example

This dependency-free provider demonstrates the provider operation contract from
[`pluginized-skill-provider.md`](https://github.com/autotask-run/autotask/blob/vibe/docs/design/pluginized-skill-provider.md):
`validate_config`, `sync`, `get_content`, and the optional `get_file` operation.
It uses a deterministic inline catalog, emits one JSON response for each JSON
request on stdin, and never calls a network or writes a database.

```sh
python3 -m unittest discover -s skill-provider-example -v
printf '%s\n' '{"operation":"sync","source":{"id":123,"config":{}}}' | python3 skill-provider-example/provider.py
```

The response uses the design's `records`, `source_ref`, `readme_content`,
`manifest_json`, server-computed-looking `content_hash`, cursor and diagnostics
fields. The real AutoTask service still validates provider output, computes the
stored hash, applies scope/ownership rules, and snapshots content before a
Worker sees it.

`manifest.template.json` is a reference for a workspace/private provider and is
marked `projected_read_only`. The public `plugin submit` endpoint currently
accepts remote HTTPS MCP tools and personal memory providers; it does not accept
`skill_provider` submissions or execute arbitrary JSON-lines commands. Treat
this sample as a contract fixture until a governed provider runtime is opened.
