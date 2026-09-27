# Remote Channel Bridge example

This is a dependency-free Python MCP adapter fixture for the proposed
`autotask.channel.v1` contract. It demonstrates the adapter side of a
**workspace-private** Remote Channel Bridge:

- `bridge_poll` returns bounded normalized text events and an opaque cursor.
- `bridge_send` accepts a `delivery_id` and rejects reuse with a different payload.
- The current AutoTask Server does not yet run this generic Bridge or persist
  its cursor/inbox/outbox state. The example therefore tests only the adapter
  protocol; a production integration still needs the platform state machine,
  identity binding and crash-recovery work.

It is not installable or accepted by `plugin submit` in this release. The public
authoring allowlist excludes Channel Bridge until the platform completes
independent review of identity mapping, durable recovery and platform-specific
adapter behavior.

Run the offline HTTP tests:

```sh
python3 -m unittest discover -s remote-channel-example -v
python3 remote-channel-example/server.py
```

Prepare a workspace-private manifest after hosting the service behind HTTPS.
The generated `workspace-<author_id>/` namespace is a local example namespace;
choose your own workspace-owned slug for a real installation:

```sh
python3 remote-channel-example/prepare.py \
  --author-id 42 \
  --url https://bridge.example.com/mcp \
  --out /tmp/autotask-remote-channel.json
```

For an installer-provided API key, use `--auth-type api_key --api-key-header
X-Bridge-Key --api-key-prefix 'Bearer '`. For OAuth, use
`--auth-type oauth --oauth-scope messages:read --oauth-scope messages:write`.
These flags declare the authorization shape only; they never add a credential.

The generated manifest documents the future workspace-private shape. Do not
publish or install it against the current server. Never put a token in
`channel_config` or in the manifest. When the platform Bridge is implemented,
it must generate the `instance_key`, own the bounded cursor and delivery IDs,
and derive workspace/user identity from the installed Channel binding rather
than trusting adapter-provided workspace IDs.
