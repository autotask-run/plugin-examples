# Local Tool plugin example

This directory is a copyable, dependency-free **local CLI plugin**. It is
loaded by `autotask run-local` as a host process over `stdio-json-v1`; it does
not expose an HTTP service, enter the public `plugin submit` review queue, or
run in a web chat session.

The example exposes one read-only tool, `plugin.text_stats`, which counts
Unicode characters, whitespace-separated words, and lines. The plugin checks
the request tool name and sandbox before reading the input. It has no file,
network, process, or environment side effects.

## Run the offline tests

From the repository root:

```bash
python3 -m unittest discover -s local-tool-example -v
```

The tests invoke the plugin process with the same one-request/one-JSON-result
wire shape used by the CLI. They cover a successful call, a wrong tool name,
and a sandbox that is broader than this read-only plugin allows.

## Run it with AutoTask CLI

Build or install an AutoTask CLI that supports `run-local`, then run it from
this directory:

```bash
autotask doctor --strict --local-plugin ./autotask-plugin.json
autotask run-local "Use plugin.text_stats once for the supplied text" \
  --local-plugin ./autotask-plugin.json \
  --local-tools plugin.text_stats \
  --sandbox read-only \
  --non-interactive --json
```

The CLI starts `./local_tool.py` with the manifest directory as its working
directory. On Windows, use the included `autotask-plugin.windows.json`, which
launches `local_tool.cmd` and then `py -3`. The platform-specific launchers
keep the executable path visible to trust review instead of hiding it behind a
PATH-resolved interpreter.

The task prompt must supply an object with a `text` string. A successful
plugin result includes `status: "ok"` and the three count fields. The CLI
validates that result against `output_schema` before returning it to the
Worker.

## Manifest and safety boundary

`autotask-plugin.json` is a canonical `autotask.plugin.v1` manifest with one
`cli_stdio_json` runtime and one `capabilities.tools` entry. The manifest
declares `read-only`, `low` risk, and no approval requirement because the
operation is pure computation. A plugin with writes, shell commands, browser
control, credentials, or external requests must declare a stricter sandbox and
approval policy and enforce the same boundary inside its process.

The CLI validates the manifest, tool schemas, runtime, and result status, but
the plugin remains responsible for refusing unsafe inputs. Follow the
[Local Plugin Security Contract](https://github.com/autotask-run/autotask/blob/main/packages/cli/docs/local-plugin-security.md)
when adding side effects. Do not put API keys, tokens, or passwords in the
manifest `env` field.

This example is intentionally local-only. To distribute a plugin to other
workspaces, use the separately documented reviewed remote MCP, Provider,
Memory Provider, or static Skill Pack paths; a local executable is not accepted
by the public submission validator.
