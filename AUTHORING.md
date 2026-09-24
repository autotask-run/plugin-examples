# Develop and submit an MCP plugin

Public listing means **third-party submission → platform review and publication → installation by other workspaces**. An ordinary author account is sufficient to submit; administrators alone approve and publish.

Public submissions support remote HTTPS MCP tools and personal memory providers using Streamable HTTP. Authors host the service; AutoTask distributes reviewed connection metadata. API keys and OAuth are declared in the manifest and connected by each installer, never embedded as shared secrets. Local executables, built-in Go extensions, hooks, skills and UI extensions remain outside this author submission release. This document follows the `remote-mcp` tool example; for memory follow [memory-mcp](memory-mcp/README.md).

[Runnable examples](https://github.com/autotask-run/plugin-examples) · [Chinese guide](https://docs.autotask.run/docs/plugin-development.md) · [Manifest schema](remote-mcp/submission.schema.json)

## Run the example

```bash
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 remote-mcp/server.py
```

Requires Python 3.10+, no packages. The stateless `/mcp` endpoint listens on `127.0.0.1:8765`. It exposes `text_stats`, which counts supplied text without storage, filesystem access or outgoing requests. Deploy behind your own HTTPS reverse proxy before submission. The Worker's container must be able to reach that endpoint; localhost points at the container itself.

The example text `你好 AutoTask\nPlugins work` returns 24 characters, 4 whitespace-separated words and 2 lines. Tests exercise initialize, tools/list, tools/call, invalid inputs and Origin checks. Configure proxy request/rate limits for a public deployment. Unknown browser Origins are rejected; explicitly set MCP_ALLOWED_ORIGINS only for intended browser clients.

## Prepare and submit

Use AutoTask CLI **0.1.1 or later** and a server exposing `/api/v1/plugin-submissions`. If the API returns 404, the server has not been upgraded. This capability is independent from older `plugin publish` commands.

If you do not have an account, [register as an ordinary user](https://app.autotask.run/register) first. Submission does not require administrator access.

```bash
autotask login
autotask plugin submissions --json
```

The response includes your authenticated namespace, for example `user-42/`. Use your own numeric user ID:

```bash
python3 remote-mcp/prepare.py --author-id 42 --url https://your-mcp.example.com/mcp
autotask plugin submit --manifest ./autotask-plugin.json --dry-run
autotask plugin submit --manifest ./autotask-plugin.json --draft-only --json
```

Edit author, description and repository fields in the resulting manifest. The template hostname is a placeholder, not a hosted demo. Dry-run checks only arguments and JSON; the server validates the submission contract. Use the returned submission_id:

```bash
autotask plugin submit --submission-id 123 --note "Verified initialize/list/call; no input retention" --json
autotask plugin submissions --id 123 --json
```

Omit `--draft-only` to create and submit in one command. If submission fails after saving, retry using the saved ID reported by the CLI.

## Manifest contract

- schema_version: autotask.plugin.v1; identity.plugin_id: user-<user_id>/<lowercase-slug>; version: major.minor.patch.
- classification: plugin_kind=mcp_server, source_kind=native, runtime_kinds=[mcp].
- runtimes: runtime_id, kind=mcp, protocol=mcp.
- capabilities: tools only. Each tool declares name, description, object input_schema, runtime_id, runtime_kind=mcp, support_level=executable_existing_runtime, risk_level and permissions.
- metadata.mcp_tool_name equals the tool name. metadata.mcp_server contains name and config; config contains only url and transport=streamable-http.
- Both manifest and tool declare network:<endpoint-hostname>.
- HTTPS only; no URL credentials, query or fragment. No headers, env, commands, configuration, distribution or bindings. Maximum manifest size: 256 KiB.

No plugin package is necessary for this remote service: only the connection manifest is distributed. The repository includes the complete template and preparation script.

## Review and revision

Drafts are editable; reviewing, approved and published snapshots are frozen. Repeating submission while a review is pending returns that review. Inspect reviews for rejection reasons.

```bash
autotask plugin submit --submission-id 123 --manifest ./autotask-plugin.json --note "Addressed review feedback" --json
```

Editing a draft retains its ID. Revising rejected content creates a new draft ID, retaining the original snapshot and review. Track the new returned ID. Published releases are immutable: increment identity.version and create a new submission.

Administrators verify endpoint access, source/license, tool schemas, permissions, error handling and data retention, and actually run initialize/list/call. Approval alone does not publish. In [Platform → Asset Governance](https://platform.autotask.run/admin/asset-governance), select the plugin asset to review and publish it. Administrator CLI commands are an alternative:

```bash
autotask plugin review approve --asset-id user-42/text-stats --review-id 456 --reason "Protocol and permissions verified"
autotask plugin review publish --asset-id user-42/text-stats --version draft-<governance-version> --reason "Publish 1.0.0"
```

The version argument is the draft-... governance version in the submission response, not the manifest's 1.0.0. Review covers metadata and observed endpoint behavior; independently hosted code is not immutable platform-hosted code.

## Install from another workspace

Sign in as the consumer and select the consumer workspace. Find and install the published plugin in the plugin market. If the workspace has no Agent Profile yet, [create a workspace profile in Agent Studio](https://app.autotask.run/agent-studio/profiles/new) and note its ID. Confirm that the workspace model provider passes its connection test before starting an Agent task; an invalid model key stops the task before the plugin can run. Bind the plugin to the profile. CLI equivalent:

```bash
autotask plugin catalog show --plugin-id user-42/text-stats --json
autotask plugin enable --plugin-id user-42/text-stats --capability text_stats --scope workspace --target-type agent_profile --target-id <PROFILE_ID>
```

Enable means install and bind. Start an **Agent task session** with that profile; ordinary chat sessions do not currently load third-party MCP tools. For a reproducible check, ask the Agent to call `text_stats` exactly once with `{"text":"你好 AutoTask\nPlugins work"}`. The tool call should contain both lines with no trailing newline and return `{"characters":24,"words":4,"lines":2}`. A text-only task may then ask for a code repository; choose **Continue without repository**. Check the actual tool-call event and result, not just installed status or MCP downlink. Remove bindings before uninstalling through plugin management.

## REST alternative

Send Authorization: Bearer <account-token>. Ownership comes from authentication, never a client-supplied owner. Never commit tokens or include them in manifests.

| Request | Result |
|---|---|
| GET /api/v1/plugin-submissions?offset=0 | Own entries and namespace, at most 50 per page |
| POST /api/v1/plugin-submissions | Create draft; body: {"manifest": {...}, "note": "..."} |
| GET /api/v1/plugin-submissions/:id | submission and reviews |
| PUT /api/v1/plugin-submissions/:id | Revise using the same body; rejected versions return a new ID |
| POST /api/v1/plugin-submissions/:id/submit | Submit; body: {"note": "..."} |

Responses use a data envelope. 401: login needed; 404: missing or not yours; 409: frozen state; 400: invalid manifest; 413: request too large.

```bash
python3 -c 'import json; print(json.dumps({"manifest":json.load(open("autotask-plugin.json")),"note":"MCP protocol verified"}))' > submission.json
curl -X POST "$AUTOTASK_SERVER/api/v1/plugin-submissions" -H "Authorization: Bearer $AUTOTASK_TOKEN" -H 'Content-Type: application/json' --data-binary @submission.json
```

If approved but not discoverable, ask the reviewer to publish. If installed but unavailable, check profile binding, Worker connectivity, certificate and /mcp path, then session tool errors. A model-provider 401 before the tool call requires a working workspace provider and a new task; retrying an old session may keep its original model. Private workspace publication via plugin publish --scope workspace remains a separate workflow.
