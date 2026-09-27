# Remote Channel Bridge example

This is a dependency-free Python MCP adapter fixture for the
`autotask.channel.v1` contract. It demonstrates the adapter side of a
**workspace-private** Remote Channel Bridge:

- `bridge_poll` returns bounded normalized text events and an opaque cursor.
- `bridge_send` accepts a `delivery_id` and rejects reuse with a different payload.
- AutoTask persists the cursor, inbox, outbox, lease claims and retry state for
  an installed workspace Channel. The adapter remains responsible for its
  upstream cursor and delivery-id storage and must tolerate at-least-once
  retries.

It can be installed only through a workspace-private catalog entry. It is still
rejected by `plugin submit`; public distribution needs independent review of
identity mapping, tenant isolation, durable recovery and platform-specific
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

Publish the generated manifest with `plugin publish --scope workspace`, then
install and configure its `remote_bridge` capability. The platform generates
the `instance_key`, owns the bounded cursor and delivery IDs, and derives
workspace/user identity from the installed Channel binding rather than trusting
adapter-provided workspace IDs. Configure only non-secret values such as a
tenant or queue; connect API Key/OAuth through the installation authorization
flow, never in `channel_config` or the manifest.

The platform configuration request has this shape:

```sh
curl -X PATCH "$AUTOTASK_SERVER/api/v1/plugin-lifecycle/installations/$INSTALLATION_ID/configure" \
  -H "Authorization: Bearer $AUTOTASK_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"config":{"capability_name":"remote_bridge","channel_name":"Support inbox","channel_config":{"tenant":"acme"}}}'
```
