# Public declarative Agent Studio UI panel example

This example is a complete public `ui_extension` submission for the fixed
native Agent Studio panel runtime. It renders a repository review form inside
AutoTask, then asks the platform to create an ordinary interactive task. The
plugin does not ship JavaScript, HTML, CSS, an iframe, a webhook, or a remote
server: the platform owns the renderer, validation, profile selection,
idempotency and audit event.

The public contract is intentionally small. A manifest has one hosted runtime
(`autotask.ui-panel.v1`), one `ui_extensions` capability, bounded text/select/
toggle components, and one `create_task` action. Templates may reference only
declared component IDs. This example is workspace-installable after platform
review; it is not a personal `plugin publish --scope personal` package.

## Validate and prepare

The checks use only Python 3.10+ standard-library modules:

```bash
python3 -m unittest discover -s ui-panel-example -v
python3 ui-panel-example/prepare.py \
  --author-id 42 \
  --author-name "Example author" \
  --author-handle example-author \
  --out /tmp/autotask-ui-panel.json
autotask plugin submit --manifest /tmp/autotask-ui-panel.json --dry-run
```

Replace the author values with the authenticated AutoTask user. The prepared
manifest uses the reviewed `user-<id>/` namespace. Do not add URLs, code or
credentials to the panel metadata. After publication, install it in a
workspace, bind an Agent Profile, open the plugin's Agent Studio subpage and
create a task from the form.
