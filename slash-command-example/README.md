# Private prompt Slash Command example

This example is a workspace-private reference for an installed
`slash_commands` capability. It registers `/delivery-review` with the existing
prompt handler. The handler appends the raw argument string to the installed
prompt and sends it to the current Agent Session.

Run the offline manifest checks:

```sh
python3 -m unittest discover -s slash-command-example -v
```

The capability is not part of the public `plugin submit` allowlist yet. Use a
workspace catalog publication, then install it. After installation it appears
in the workspace command registry. Invoke `/delivery-review release checklist`;
the session prompt contains the installed version's prompt followed by
`User request: release checklist`.

`requires_approval` must remain `false` in this example. The platform stores
approval declarations, but does not yet run an approval gate for third-party
prompt Slash Commands. Execution rejects a declaration of `true` instead of
silently ignoring it.

Command arguments are a single raw string. `arguments_schema` is used for
discovery/help text; it is not a claim that the server parses arbitrary JSON
arguments.

If two installed plugins expose the same command name, an unqualified
`provider=plugin` execution is rejected as ambiguous. A client that needs an
exact choice can send `provider=plugin:<plugin-id>`.
