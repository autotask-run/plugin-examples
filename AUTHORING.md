# Develop and submit an MCP plugin

Public listing means **third-party submission → platform review and publication → installation by other workspaces**. An ordinary author account is sufficient to submit; administrators alone approve and publish.

The first supported type is a remote HTTPS MCP tool using Streamable HTTP. Authors host the service; AutoTask distributes reviewed connection metadata. The manifest may declare no authentication, an installer-provided API key, or MCP OAuth authorization code. Local executables, built-in Go extensions, hooks, skills, and UI extensions remain outside this author submission release.

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

The [public demo endpoint](https://docs.autotask.run/examples/text-stats/mcp) lets you test client connectivity. AutoTask operates it for learning and tests; a real submission should use an HTTPS endpoint operated by the author.

## Prepare and submit

The minimum CLI version is **0.1.1** (Linux amd64, macOS amd64/arm64, Windows amd64). See the [CLI reference](https://docs.autotask.run/?section=cli-reference) for installation, or run `autotask update --version 0.1.1`. The server must expose `/api/v1/plugin-submissions`; a 404 means the server has not been upgraded. This submission flow is independent from older `plugin publish` commands.

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
- metadata.mcp_tool_name equals the tool name. metadata.mcp_server contains name, config and optional auth; config contains only url and transport=streamable-http.
- Both manifest and tool declare network:<endpoint-hostname>.
- HTTPS only; no URL credentials, query or fragment. No embedded key, token, client secret, headers, env, commands, configuration, distribution or bindings. Every tool must declare the same server and auth. Maximum manifest size: 256 KiB.

For an API-key service, add `"auth":{"type":"api_key","header":"Authorization","prefix":"Bearer "}` to each tool's `metadata.mcp_server`. The optional prefix may only be empty, `Bearer ` or `Token `. The installer supplies the actual key after installation; it never belongs in the manifest or author repository.

For OAuth, use `"auth":{"type":"oauth","scopes":["read:data"]}`. The MCP resource must publish Protected Resource Metadata matching its manifest URL; its authorization server must publish OAuth Authorization Server Metadata and support authorization code, PKCE S256 and refresh tokens. AutoTask discovers the endpoints and includes `resource=<MCP URL>` in authorization and token requests. In this release, the installer registers an OAuth client upstream with redirect URI `<AUTOTASK_PUBLIC_URL>/api/v1/plugin-lifecycle/oauth/callback`, then enters the client ID and optional client secret in AutoTask. Services without this OAuth flow need a separate integration.

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

Sign in as the consumer and select the consumer workspace. Find and install the published plugin in the plugin market. For API-key or OAuth plugins, open **Connect MCP service** in the plugin detail and set the key or complete upstream authorization before running an Agent. The UI shows connection status but never echoes credentials. Agents bound to this workspace/project installation share the authorized upstream identity; use a suitable account and minimum scopes. If the workspace has no Agent Profile yet, [create a workspace profile in Agent Studio](https://app.autotask.run/agent-studio/profiles/new) and note its ID. Before running an Agent task, confirm that the selected workspace model provider passes its connection test; an invalid model key stops the task before any plugin call. Bind the plugin to the profile. CLI equivalent:

```bash
autotask plugin catalog show --plugin-id user-42/text-stats --json
autotask plugin enable --plugin-id user-42/text-stats --capability text_stats --scope workspace --target-type agent_profile --target-id <PROFILE_ID>
```

Enable means install and bind. Start an **Agent task session** with that profile and ask the Worker to call `text_stats`; ordinary chat sessions do not currently load third-party MCP tools. Check the actual `text_stats` call and result, not just installed status or MCP downlink. If this text-only task subsequently asks for a code repository, choose **Continue without repository**; that prompt is separate from the MCP call. Remove bindings before uninstalling through plugin management.

For a reproducible task, write: `Call text_stats once. Use the following JSON as the exact tool arguments. The \n separates two lines; there is no trailing newline or period. Report the tool's JSON result.` Then paste:

```json
{"text":"你好 AutoTask\nPlugins work"}
```

The expected result is `{"characters":24,"words":4,"lines":2}`. Also check that the tool-call event contains both lines in its `text` argument and no trailing newline.

## REST alternative

Send Authorization: Bearer <account-token>. Ownership comes from authentication, never a client-supplied owner. Never commit tokens or include them in manifests.

| Request | Result |
|---|---|
| GET /api/v1/plugin-submissions?offset=0 | Own entries and namespace, at most 50 per page |
| POST /api/v1/plugin-submissions | Create draft; body: {"manifest": {...}, "note": "..."} |
| GET /api/v1/plugin-submissions/:id | submission and reviews |
| PUT /api/v1/plugin-submissions/:id | Revise using the same body; rejected versions return a new ID |
| POST /api/v1/plugin-submissions/:id/submit | Submit; body: {"note": "..."} |

Installer authorization endpoints require the account Bearer token and access to the installation's workspace. GET returns status only:

| Request | Result |
|---|---|
| GET /api/v1/plugin-lifecycle/installations/:id/mcp-authorization | auth_type, status and connected; no credential |
| PUT /api/v1/plugin-lifecycle/installations/:id/mcp-authorization | Set/replace API key: {"api_key":"..."} |
| DELETE /api/v1/plugin-lifecycle/installations/:id/mcp-authorization | Disconnect and delete authorization |
| POST /api/v1/plugin-lifecycle/installations/:id/mcp-authorization/oauth/start | {"client_id":"...","client_secret":"..."}; open the returned authorization_url |

The upstream browser redirects to public `GET /api/v1/plugin-lifecycle/oauth/callback`; one-time state protects the callback.

Responses use a data envelope. 401: login needed; 404: missing or not yours; 409: frozen state; 400: invalid manifest; 413: request too large.

```bash
python3 -c 'import json; print(json.dumps({"manifest":json.load(open("autotask-plugin.json")),"note":"MCP protocol verified"}))' > submission.json
curl -X POST "$AUTOTASK_SERVER/api/v1/plugin-submissions" -H "Authorization: Bearer $AUTOTASK_TOKEN" -H 'Content-Type: application/json' --data-binary @submission.json
```

If approved but not discoverable, ask the reviewer to publish. If installed but unavailable, check connection status, profile binding, Worker connectivity, certificate and /mcp path, then session tool errors. For OAuth failures, verify the registered redirect URI, the resource URL in Protected Resource Metadata, PKCE S256 support, and refresh-token support; restart authorization after it expires. A model-provider 401 before the tool call requires a working workspace provider and a new task; retrying an old session may keep its original model. Private workspace publication via plugin publish --scope workspace remains a separate workflow.
