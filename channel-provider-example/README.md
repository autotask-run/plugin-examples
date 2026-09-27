# Channel Provider source template

This directory is a **source-integration template** for AutoTask Channels. It
shows the canonical `channels` manifest and the Go registration shape for a
Provider plus Runtime Driver. It is intentionally a loopback fixture: it does
not connect to Feishu, Telegram or another external service, and it does not
run as a standalone Python/Go service.

AutoTask currently loads Channel Providers from Go code compiled into the Server
at startup. A manifest in this directory is useful for catalog metadata and
review, but `plugin submit` rejects `channel_provider`, and installing this
manifest does not load `register.go`. To make a real source integration:

1. Copy the Go files into an AutoTask Server checkout under
   `server/internal/plugins/...`.
2. Replace the loopback message/Send logic with a platform adapter. Keep
   platform verification, tenant identity and credentials inside that adapter.
3. Call `Register(plugins)` from the Server startup registry.
4. Create a Channel in the Channels module, bind an Agent Profile, and run the
   host-side Channel tests before enabling a live platform account.

The complete contract and security boundary are documented in the [Channel
Provider authoring guide](https://docs.autotask.run/guides/channel-provider-authoring.en.md).
The AutoTask repository's `server/internal/plugins/builtin/channeltest` package
contains the real Runtime/Gateway database harness; this folder does not claim
to replace that evidence.

The manifest must contain a non-empty `channel_id`, `provider`, and unique
`events`. `support_level` describes the declaration only. A capability is
executable only when the matching Provider and Driver are registered in the
running Server.
