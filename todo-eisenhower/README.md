# Eisenhower quadrants todo-view plugin

This is a complete declarative example for AutoTask's fixed
`autotask.todo-view.v1` protocol. It groups open personal todos into four
host-rendered quadrants using two deterministic rules:

- important: `priority_high`
- urgent: `planned_date_on_or_before_local_date`

The host owns rendering, workspace scoping, data reads, audit events and all
mutations. The manifest does not ship JavaScript, HTML, CSS, an iframe, a
webhook, or a remote UI service. It declares only the view and the actions
`complete`, `set_priority`, and `set_planned_date`.

## Validate and prepare

The checks use only Python 3.10+ standard-library modules:

```bash
python3 -m unittest discover -s todo-eisenhower-example -v
python3 todo-eisenhower-example/prepare.py \
  --author-id 42 \
  --author-name "Example author" \
  --author-handle example-author \
  --out /tmp/autotask-eisenhower.json
autotask plugin submit --manifest /tmp/autotask-eisenhower.json --dry-run
autotask plugin submit --manifest /tmp/autotask-eisenhower.json --json
```

After platform review and publication, install it in a personal workspace and
open the todo page's **Quadrants** entry. The platform will render the view and
invoke the existing personal todo APIs for the three declared actions. A
third-party view cannot read another workspace or execute browser code.

The official first-party version is available from the AutoTask Plugin Market
as **艾森豪威尔四象限**. This sample is the public authoring shape for a
compatible reviewed version; its name and version must be unique in your
`user-<id>/` namespace.

The protocol intentionally supports this one safe view in the current release.
An arbitrary custom todo board, calendar sync, or enterprise WeCom integration
needs a separately reviewed capability contract and should not be represented
by extra manifest fields.
