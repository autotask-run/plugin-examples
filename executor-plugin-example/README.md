# Worker executor plugin example

This is an **administrator-managed worker executor** example, not an ordinary
public `plugin submit` manifest. It demonstrates the generic
`capabilities.executors[]` contract used by the Rust Worker:

- protocol `headless_stdio_v1` and the `job` surface;
- an argv task placeholder (`{task}`), with no shell interpolation;
- a stderr progress marker and a bounded process timeout;
- optional content-addressed `binary` metadata for an uploaded file or
  `dir_tar` artifact.

The Worker uses one generic driver for this protocol. It does not load plugin
code into the Worker process. An administrator first registers the manifest at
`/api/v1/admin/executor-plugins`, uploads a matching binary artifact when the
runtime is not already in the full-runtime image, then pushes the enabled set
to connected Workers. The Worker verifies the manifest and (when present) the
artifact checksum/signature before binding the executor. A missing or invalid
definition stays unbound and dispatch fails closed.

The example has no executable payload, so its offline tests only check the
manifest contract. Replace `example-executor` with a real headless program and
upload its artifact before selecting `example_executor` for a task.

## Validate and register

```bash
python3 -m unittest discover -s executor-plugin-example -v

# Admin-only API; use an administrator token and the server URL for your
# environment. The endpoint accepts the manifest JSON as the request body.
curl -X POST "$SERVER/api/v1/admin/executor-plugins" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  --data-binary @executor-plugin-example/autotask-plugin.json
```

If an artifact is required, upload it before the manifest's `binary` reference
is enabled. The server computes the SHA-256 digest; the reference must match
the uploaded executor ID, version, OS, architecture and size. Use the worker
push endpoint only after the manifest and artifact are ready.

This path is intentionally separate from third-party public review. Public
authors should use the remote MCP, memory, Skill Provider, Knowledge Source or
declarative Agent Studio examples instead.
