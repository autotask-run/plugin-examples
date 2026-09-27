# Develop and submit an MCP plugin

Public listing means **third-party submission → platform review and publication → installation by other workspaces**. An ordinary author account is sufficient to submit; administrators alone approve and publish.

Public submissions support remote HTTPS MCP tools, the remote `autotask.tool-provider.v1` and `autotask.skill-provider.v1` catalog contracts, immutable text-only `skill_pack` bundles, fixed OpenAI-compatible LLM Provider descriptors, personal memory providers using Streamable HTTP, and declarative Agent Studio UI panels. Authors host remote services; AutoTask stores reviewed Skill content and distributes reviewed connection metadata. API keys and OAuth are declared in the manifest and connected by each installer, never embedded as shared secrets. Local executables, built-in Go extensions, hooks and source-integrated/public Channels remain outside this author submission release. This document follows the `remote-mcp` tool example; see [remote-tool-provider](remote-tool-provider/README.md), [skill-provider-example](skill-provider-example/README.md), [skill-example](skill-example/README.md), [llm-provider-example](llm-provider-example/README.md), [memory-mcp](memory-mcp/README.md), [ui-panel-example](ui-panel-example/README.md), [local-tool-example](local-tool-example/README.md), [hook-example](hook-example/README.md), [slash-command-example](slash-command-example/README.md), [channel-provider-example](channel-provider-example/README.md), [remote-channel-example](remote-channel-example/README.md) and [agent-adapter-example](agent-adapter-example/README.md) for provider and private extension contracts.

## Agent configuration adapters

The [agent-adapter-example](agent-adapter-example/README.md) is a complete
local example for `autotask config setup`. An adapter is a trusted child
process that reads one JSONL request and returns one setup plan; it configures a
third-party client's MCP/Gateway file and does not execute an Agent. The CLI
owns home-directory path checks, format validation, atomic writes and
credentials. The adapter receives existing configuration content, which may
contain client secrets, so install only code you trust.

Run its standard-library tests, then generate a machine-local manifest with
`prepare.py` and use `autotask config setup example.agent --dry-run`. Signed
Plugin Store packages use the same protocol after Ed25519 integrity and local
trust-key verification. Executable adapters are not ordinary public
`plugin submit` entries in this release.

[Runnable examples](https://github.com/autotask-run/plugin-examples) · [Chinese guide](https://docs.autotask.run/docs/plugin-development.md) · [Manifest schema](remote-mcp/submission.schema.json)

## Run the example

```bash
git clone https://github.com/autotask-run/plugin-examples.git
cd plugin-examples
python3 -m unittest discover -s remote-mcp -v
python3 -m unittest discover -s memory-mcp -v
python3 -m unittest discover -s remote-tool-provider -v
python3 -m unittest discover -s skill-example -v
python3 -m unittest discover -s skill-provider-example -v
python3 -m unittest discover -s llm-provider-example -v
python3 -m unittest discover -s local-tool-example -v
python3 -m unittest discover -s hook-example -v
python3 -m unittest discover -s slash-command-example -v
python3 -m unittest discover -s channel-provider-example -v
python3 -m unittest discover -s remote-channel-example -v
python3 -m unittest discover -s ui-panel-example -v
python3 -m unittest discover -s executor-plugin-example -v
python3 -m unittest discover -s agent-adapter-example -v
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

## Memory and Skill Provider examples

The [`memory-mcp`](memory-mcp/README.md) example follows the public `autotask.memory.v1` contract. It is submitted with `plugin_kind=memory_provider`, then an installer supplies API Key/OAuth credentials and verifies create, search, correct and delete on a personal Profile.

[`skill-example`](skill-example/README.md) documents the public embedded `skill_pack` path. It carries `SKILL.md`, `autotask-skill.json` and bounded UTF-8 reference files in the reviewed version; use its `prepare.py` to set your `user-<ID>/` namespace before `plugin submit`. [`skill-provider-example`](skill-provider-example/README.md) is different: it is a public remote MCP provider. It declares `plugin_kind=skill_provider`, exactly one `capabilities.skill_providers` entry, and the three bounded operations `validate_config`, `sync`, and `get_content`. The provider returns a complete snapshot with a revision; AutoTask validates and atomically applies it before a consumer explicitly installs and binds a Skill.

Prepare the public Skill Provider manifest with:

```sh
python3 skill-provider-example/prepare.py \
  --author-id 42 \
  --url https://skills.example.com/provider-mcp
autotask plugin submit --manifest ./autotask-skill-provider.json --dry-run
autotask plugin submit --manifest ./autotask-skill-provider.json --json
```

The provider API key is configured by each installer after publication. Pagination,
incremental deletion, arbitrary files and private upstream credentials are outside
the first public Skill Provider contract.

The [`llm-provider-example`](llm-provider-example/README.md) is a fixed Gateway
descriptor rather than a remote tool server. It declares one reviewed HTTPS
OpenAI-compatible base URL, up to 32 static model IDs and bounded configuration
fields. The author does not ship code, a model-discovery endpoint, prices,
proxy settings or credentials. Installers enter the API key in the encrypted
plugin connection form; changing the model list requires a reviewed version.

## Declarative Agent Studio UI panel

[`ui-panel-example`](ui-panel-example/README.md) is the public UI extension path.
It declares one hosted `autotask.ui-panel.v1` runtime and a fixed
`capabilities.ui_extensions` descriptor. The current host supports text,
textarea, select and toggle fields and one `create_task` action. Templates can
reference only declared component IDs; the server validates the manifest again
at installation and invocation, enforces `task:create`, records an audit event,
and treats a repeated request ID as an idempotent retry.

The panel is rendered by the AutoTask Agent Studio host. An author cannot ship
arbitrary JavaScript, HTML, CSS, iframe content, REST callbacks or credentials
inside this contract. Prepare and submit it with:

```sh
python3 ui-panel-example/prepare.py --author-id 42 --out /tmp/autotask-ui-panel.json
autotask plugin submit --manifest /tmp/autotask-ui-panel.json --dry-run
```

After publication, a consumer installs the plugin in a workspace, binds an
Agent Profile, opens its Agent Studio subpage and creates a task from the form.
Personal scope does not accept UI panels in this release.

## Worker executor plugins

[`executor-plugin-example`](executor-plugin-example/README.md) documents a
different trust boundary. `capabilities.executors[]` is consumed by the Rust
Worker's generic `headless_stdio_v1` driver and is registered through the
administrator-only `/api/v1/admin/executor-plugins` API. It is not accepted by
`plugin submit`, because selecting an executor changes task dispatch and may
run a host-supplied binary inside the full-runtime container.

The administrator must validate the manifest, upload a matching content-
addressed artifact when needed, and push the enabled definition to Workers.
The Worker verifies protocol, paths, checksum and optional signature before it
binds the executor. A rejected definition is not used for dispatch. Public
third-party authors should use a remote MCP or declarative UI panel instead of
requesting executor access.

## Local CLI Tool example

[`local-tool-example`](local-tool-example/README.md) is the reference path for
an author who wants to develop and use a plugin on their own computer without
listing it in the public market. It uses the canonical `autotask.plugin.v1`
manifest with one `cli_stdio_json` runtime and the `stdio-json-v1` stdin/stdout
protocol. The CLI starts the declared process in the manifest directory for the
current `run-local` task; the process reads one JSON request and writes one JSON
result.

Run the offline protocol tests and inspect the manifest before connecting it to
an AutoTask server:

```sh
python3 -m unittest discover -s local-tool-example -v
autotask doctor --local-plugin ./local-tool-example/autotask-plugin.json
autotask run-local "Use plugin.text_stats once" \
  --local-plugin ./local-tool-example/autotask-plugin.json \
  --local-tools plugin.text_stats \
  --sandbox read-only --non-interactive --json
```

The example's tool is pure computation and therefore declares `low` risk,
`read-only`, and `requires_approval=false`. A plugin that writes files,
executes commands, controls a browser, reads credentials, or calls another
service must declare the narrowest matching sandbox and approval policy and
must enforce those checks inside its own process. The CLI validates the
manifest, input/output schema, result status, timeout and trust boundary, but
it cannot make an arbitrary host process safe by itself.

The local path accepts a manifest file or a previously published workspace
catalog entry. It is intentionally separate from public `plugin submit`: local
executables are not copied into the reviewed remote MCP/Skill submission and
are not started by web chat sessions. Use the public remote MCP, Provider,
Memory Provider or static Skill Pack contracts when other workspaces must
install the capability.

## Remote Tool Provider contract

The [`remote-tool-provider`](remote-tool-provider/README.md) example
implements the public `autotask.tool-provider.v1` contract. It declares
`plugin_kind=tool_provider`, exactly one `capabilities.tool_providers` entry,
and one public HTTPS Streamable HTTP provider endpoint. The endpoint exposes
exactly two MCP operations: `validate_config` and `sync_catalog`.

`sync_catalog` receives the Tool Source identity, normalized config, opaque
cursor, page limit and execution context. It returns bounded catalog items, an
advancing cursor and `complete`. Each item has a unique `external_id`, bounded
tool schemas, both `mcp` and `streamable-http` execution protocols, and a
package manifest containing only a public HTTPS Streamable HTTP MCP endpoint.
The item descriptor must not contain an API key, OAuth token, header,
environment variable or command.

The provider installation owns authorization for the provider endpoint. A
consumer connects that installation with API Key/OAuth, creates a Tool Source
and syncs the catalog. Sync creates read-only Tool Store rows; it does not
install or bind returned items. The consumer explicitly installs a catalog
item, enables it on an Agent Profile, and verifies a real Agent MCP call. The
returned item endpoint receives no provider credential and therefore needs its
own public access policy or a separate declared installation flow.

Cursor state resumes only when provider plugin/version and normalized config
match. A provider or config change starts from an empty cursor; concurrent
stale pages, duplicate IDs, non-advancing incomplete cursors and
`not_modified` responses carrying payload changes are rejected. Catalog data
is third-party metadata and cannot grant official status or execution
authorization.

Prepare and submit the example with:

```sh
python3 remote-tool-provider/prepare.py \\
  --author-id 42 \\
  --url https://catalog.example.com/provider-mcp \\
  --item-url https://catalog.example.com/items/weather/mcp
autotask plugin submit --manifest ./autotask-tool-provider.json --dry-run
autotask plugin submit --manifest ./autotask-tool-provider.json --json
```

## Remote MCP manifest contract

The following contract describes the `remote-mcp` example. The public memory-provider contract is documented in [memory-mcp](memory-mcp/README.md).

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

## Channel Provider source integration

[`channel-provider-example`](channel-provider-example) is deliberately different
from the public MCP examples. It contains a canonical `channel_provider`
manifest and a Go Provider/Runtime Driver skeleton for a loopback fixture. The
imports target AutoTask's `internal` packages, so the files must be copied into
an AutoTask Server checkout and registered during startup; they are not a
standalone SDK or service.

Run its metadata checks with:

```bash
python3 -m unittest discover -s channel-provider-example -v
```

The host-side proof comes from the AutoTask repository's registry, Channel
service, gateway and `server/internal/plugins/builtin/channeltest` runtime
harness. A real adapter must normalize `ChannelMessage`, preserve channel-scoped
external identity, suppress duplicate platform events, use the supplied
`ChannelReply`, and keep secrets out of events and logs. Create/configure the
Channel through the Channels module and bind an Agent Profile after the Go
Provider and Driver are registered.

The manifest is not accepted by `plugin submit`; `webhook_schema` does not open
a public callback. The Remote Channel Bridge below is a workspace-private
runtime. Public marketplace distribution still needs a separate review of
credentials, replay protection, tenant isolation and idempotency.

## Workspace-private Remote Channel Bridge

[`remote-channel-example`](remote-channel-example) is a runnable adapter for an
author who wants to use the private channel contract without adding Go code to
the AutoTask Server. It implements the bounded
`autotask.channel.v1` contract over Streamable HTTP MCP:

- `bridge_poll` receives the server-generated `instance_key`, an opaque cursor,
  a bounded page size and non-secret `adapter_config`; it returns normalized text
  events and the next cursor.
- `bridge_send` receives a stable `delivery_id`; the example rejects reuse with a
  different payload so retries cannot duplicate a reply.
- AutoTask persists the cursor, inbox, outbox, claims and retry schedule for an
  installed workspace Channel. The adapter still owns its upstream cursor and
  must retry an immutable delivery ID at least once.

Run its offline protocol tests with:

```bash
python3 -m unittest discover -s remote-channel-example -v
```

Prepare the illustrative workspace-private manifest after hosting the endpoint
behind HTTPS:

```bash
python3 remote-channel-example/prepare.py \
  --author-id 42 \
  --url https://bridge.example.com/mcp \
  --out /tmp/autotask-remote-channel.json
```

Publish it with `plugin publish --scope workspace`, then install and configure
the `remote_bridge` capability. The protocol carries text turns only and does
not expose Slash Commands, cards, attachments or a public webhook.
`plugin submit` still rejects `channel_provider` until the platform separately
reviews identity mapping, durable recovery and platform-specific behavior.
Connect API Key/OAuth through installation authorization; never put credentials
in the manifest or adapter config.

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
