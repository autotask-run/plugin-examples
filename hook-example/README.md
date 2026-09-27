# Private Prompt Hook example

This example is a workspace-private reference for `autotask.hook.v1`. It
listens for `TaskCompleted` and injects a bounded delivery-review prompt into
the bound Agent Profile. It does not write memory or call an external service;
the Agent must use its normal tools if the review produces a follow-up action.

The current Hook runtime supports `prompt`, guarded `command`, and guarded
`http` handlers. This example intentionally uses only `prompt`. `mcp_tool` is
reserved and is rejected at execution time.

Run the offline manifest checks:

```sh
python3 -m unittest discover -s hook-example -v
```

The manifest is a workspace-private catalog entry. It is not accepted by the
public `plugin submit` endpoint. To use it, publish it to a workspace catalog,
install it, bind `delivery-review` to an Agent Profile, and run a task with
that profile. A completed task should produce a `plugin_hook` session message
and a matching `capability_invoke` audit record.

The server-side path is:

```text
publish --scope workspace
  -> install --scope workspace
  -> bind --target-type agent_profile --target-id <PROFILE_ID>
  -> TaskCompleted dispatch
  -> plugin_hook message + audit
```

The archived platform governance examples contain command and HTTP variants,
but they require platform review and a worker/egress environment. Do not copy
those handlers into a public submission until the platform has approved the
runtime and permissions.
