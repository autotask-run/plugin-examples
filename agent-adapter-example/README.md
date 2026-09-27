# Agent Adapter example

This is a runnable, dependency-free example of the AutoTask **Agent
configuration adapter** contract. It translates one AutoTask setup request into
a JSON file for a fictional `Example Agent`; it does not execute an Agent or
replace the AutoTask Worker.

The adapter is a trusted local child process. It receives the existing target
file as `original_content`, so it must preserve settings it does not own. The
CLI owns path checks, JSON validation, atomic writes, dry-run output and
rollback. The adapter never receives a token value. It emits an environment
variable reference for the remote transport and an `autotask mcp serve`
command for stdio.

## Run the protocol tests

```bash
python3 -m unittest discover -s agent-adapter-example -v
```

## Try it with the real CLI

Generate a local manifest. `prepare.py` pins the current Python interpreter
and the example script, so the result is intentionally machine-local:

```bash
python3 agent-adapter-example/prepare.py --out /tmp/example.agent-adapter.json
autotask config adapters \
  --adapter-manifest /tmp/example.agent-adapter.json
autotask config setup example.agent \
  --adapter-manifest /tmp/example.agent-adapter.json \
  --server https://app.autotask.run \
  --model example-model \
  --transport remote \
  --token-env AUTOTASK_TOKEN \
  --dry-run --json
```

The dry-run reports the file under `$HOME/.config/example-agent/config.json`
and never writes it. To test an actual apply without touching your normal
configuration, set `HOME` to a temporary directory and repeat the command
without `--dry-run`:

```bash
tmp_home="$(mktemp -d)"
HOME="$tmp_home" XDG_CONFIG_HOME="$tmp_home/.config" \
  autotask config setup example.agent \
    --adapter-manifest /tmp/example.agent-adapter.json \
    --server https://app.autotask.run \
    --model example-model \
    --transport remote \
    --token-env AUTOTASK_TOKEN \
    --json
cat "$tmp_home/.config/example-agent/config.json"
```

For a signed Plugin Store package, the manifest embedded in the package uses a
package-relative command and the platform's Ed25519 integrity record. Follow
the trust-key and `--plugin-id ...#sha256:<manifest-hash>` flow in the [Agent
adapter architecture](https://docs.autotask.run/design/agent-adapter-architecture.md).
Signatures authenticate the package; this v1 contract is not a sandbox. Only
install adapters whose code you trust.

The local manifest path is deliberately separate from public `plugin submit`:
ordinary public submissions currently do not accept executable Agent adapters.
