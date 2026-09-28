# Declarative reading-note type

This public JSON example adds a typed **读书笔记** note type to an owner's
personal knowledge base. It is metadata only: AutoTask validates the field
schema, stores values by installed version, and renders the form. The plugin
does not run a process, load a URL, execute JavaScript, or access note content.

The fields are:

- `author` — text, indexed for search
- `rating` — number
- `finished` — boolean
- `read_date` — date
- `status` — bounded select: `在读` or `读完`

## Validate and install

The checks use only Python 3.10+ standard-library modules:

```bash
python3 -m unittest discover -s readingnote -v
python3 readingnote/prepare.py \
  --author-id 42 \
  --author-name "Example author" \
  --out /tmp/autotask-reading-note.json
autotask plugin publish --scope personal \
  --manifest /tmp/autotask-reading-note.json --dry-run --json
autotask plugin publish --scope personal \
  --manifest /tmp/autotask-reading-note.json --json
```

The current release keeps `note_type` plugins owner-only, so the generated
namespace is `private-<user-id>/`. After installing the version in your
personal workspace, verify it with:

```bash
autotask plugin catalog show \
  --plugin-id private-42/reading-note --json
curl -sS "$API_BASE/knowledge/note-types" \
  -H "Authorization: Bearer <access-token>" \
  -H "X-Workspace-ID: <personal-workspace-id>"
```

When creating a knowledge document, pass the installed note type ID/key and
the bounded field values. Existing values remain readable if the plugin is
disabled or upgraded; writes must match an active installed version.
