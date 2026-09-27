# Remote Channel Bridge example

This is a dependency-free Python MCP adapter for a **workspace-private** AutoTask
Channel. It demonstrates `autotask.channel.v1`:

- `bridge_poll` returns bounded normalized text events and an opaque cursor.
- `bridge_send` accepts a `delivery_id` and rejects reuse with a different payload.
- AutoTask persists the cursor and inbound/outbound state; the adapter must still
  persist its own upstream cursor and make delivery IDs idempotent in production.

It is not a public `plugin submit` example in this release. The public authoring
allowlist still excludes Channel Bridge until the platform completes independent
review of identity mapping, recovery, and platform-specific adapter behavior.

Run the offline HTTP tests:

```sh
python3 -m unittest discover -s remote-channel-example -v
python3 remote-channel-example/server.py
```

Prepare a workspace-private manifest after hosting the service behind HTTPS:

```sh
python3 remote-channel-example/prepare.py \
  --author-id 42 \
  --url https://bridge.example.com/mcp \
  --out /tmp/autotask-remote-channel.json
```

Install the plugin in a workspace, configure the `remote_bridge` capability with a
channel name and optional non-secret `channel_config`, then connect the declared
API Key/OAuth authorization through the plugin installation authorization UI/API.
Never put a token in `channel_config` or in the manifest. The platform sends the
server-generated `instance_key`, bounded cursor, and stable delivery IDs to the
adapter; it derives workspace and user identity through the installed Channel
binding and never trusts adapter-provided workspace IDs.
