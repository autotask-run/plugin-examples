# Personal memory MCP example

This independent Python 3.10+ server implements AutoTask's `autotask.memory.v1` contract over MCP Streamable HTTP. It persists records in SQLite and requires an API key. The four tools return MCP `structuredContent`; IDs are opaque `mem:<uuid>` strings. Every operation requires an AutoTask-supplied `namespace` with `user_id` and `profile_id`. User records remain visible across sessions; workspace, project and session records require the matching context.

This is a protocol reference, not a mature memory engine. Existing MCP services such as Mem0 use different argument and result schemas; mapping tool names in the manifest alone is insufficient. A provider-specific bridge and real account test are required.

```sh
export MEMORY_API_KEY='choose-a-long-random-key'
export MEMORY_USER_ID=42  # the AutoTask user who owns this provider instance
export MEMORY_DB=/data/autotask/example-memory.sqlite3
python3 -m unittest discover -s memory-mcp -v
python3 memory-mcp/server.py
```

The local service listens on `127.0.0.1:8766/mcp`. Put it behind your own HTTPS reverse proxy before submitting. This example runs one service instance and one API key per AutoTask user, and checks `MEMORY_USER_ID` on every tool call. A hosted multi-tenant provider needs its own tenant identity and per-user keys, rate limits, backups, encryption and retention policy. Never put `MEMORY_API_KEY` in the manifest or repository.

Get your AutoTask user ID from `autotask plugin submissions --json`, then prepare the manifest:

```sh
python3 memory-mcp/prepare.py --author-id 42 --url https://your-memory.example.com/mcp
autotask plugin submit --manifest ./autotask-memory-plugin.json --dry-run
autotask plugin submit --manifest ./autotask-memory-plugin.json --json
```

The platform reviews and publishes the submitted version. An installer adds the reviewed plugin **personally**, enters the API key in the plugin connection panel, enables long-term memory on a personal Profile, and selects the provider in the Profile memory tab. Switching providers does not migrate existing records. The Profile memory tab then searches, creates, corrects and deletes external user records; session stats count only session extraction writes, not all external records.

The contract sends `{namespace, query, limit}` to recall, or `{namespace, id, limit:1}` for exact recall. Store receives `{namespace, entry}`; update receives `{namespace, id, entry}`; delete receives `{namespace, id}`. Recall returns `{"items":[...]}`, store/update return `{"id":"..."}`, delete returns `{"deleted":true}` in MCP `structuredContent`. A record contains `id`, `scope`, `category`, `key`, `content`, `priority`, `source`, `trust`, and `recall_mode`. All four operations must use the same remote HTTPS MCP endpoint and credential declaration.
