# Obsidian-style note template MCP plugin

This is a complete, dependency-free Node.js example for AutoTask's note editor
extension path. It follows the safe part of the Obsidian Templater experience:
the plugin receives only the current selection and returns a
`replace_selection.v1` proposal. AutoTask shows the preview and writes it only
after the user confirms.

It deliberately does not evaluate template JavaScript, read an Obsidian Vault,
read the rest of a note, create todo objects, or store the selection. The two
commands are optimized for Chinese note editing:

| Command | Chinese aliases | Result |
| --- | --- | --- |
| `daily-note-template` | `每日模板`, `今日笔记`, `日记模板` | A dated Markdown daily-note template |
| `selection-checklist` | `整理待办`, `待办清单` | One unchecked Markdown task per selected line |

## Run and test locally

Node.js 18 or newer is required; Node 22 is used by the sample image. No npm
package install is needed.

```bash
python3 -m unittest discover -s obsidian-note-template -p 'test_manifest.py' -v
node --test obsidian-note-template/server.integration.test.mjs
node obsidian-note-template/server.mjs
```

The local service listens at `http://127.0.0.1:8765/mcp` and exposes
`GET /health`. Set `NOTE_TEMPLATE_TIME_ZONE` explicitly in deployment; it
defaults to `Asia/Shanghai`.

## Build a public manifest

The template uses an author namespace and an author-hosted HTTPS URL. Generate
a submission manifest after deploying the service behind HTTPS:

```bash
python3 obsidian-note-template/prepare.py \
  --author-id 42 \
  --author-name "Example author" \
  --author-handle example-author \
  --url https://notes.example.com/mcp \
  --out /tmp/autotask-note-template.json
autotask plugin submit --manifest /tmp/autotask-note-template.json --dry-run
autotask plugin submit --manifest /tmp/autotask-note-template.json --json
```

Replace the URL with the exact public endpoint you operate. The manifest has
two `tools` and two `slash_commands`; each command is visible only in
`note_editor`, and each command's `metadata.tool_ref` must point to a tool in
the same version. After platform review and publication, install it in a
personal workspace and bind the desired commands. In a note, type `/` and
choose `每日模板` or `整理待办`; inspect and confirm the proposal.

The official first-party version uses the same contract and is available from
the AutoTask Plugin Market as **Obsidian 风格笔记模板**. This sample is for
authors who want to host and publish their own compatible version.

## Container deployment

The Dockerfile runs as a non-root user with a read-only-friendly filesystem and
contains only Node built-ins and the two source modules:

```bash
docker build -t autotask-note-template:1.0.0 obsidian-note-template
docker run --rm --read-only --user 10001:10001 \
  -e NOTE_TEMPLATE_TIME_ZONE=Asia/Shanghai \
  -p 8765:8765 autotask-note-template:1.0.0
```

Put an HTTPS reverse proxy and request limits in front of the service before
submitting it. Do not put API keys, GitHub tokens, Vault paths, or credentials
in the manifest.
