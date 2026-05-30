# mcp-gmail-manager

> 🌐 **[Leia em português (pt-BR) →](README.pt-BR.md)**

[![PyPI version](https://img.shields.io/pypi/v/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-blueviolet.svg)](https://modelcontextprotocol.io)

A comprehensive Gmail [Model Context Protocol](https://modelcontextprotocol.io) server: **33 tools** covering send, reply, forward, drafts, search, read, attachments, trash, labels, filters, signature, and vacation responder.

Two optional features that distinguish it from other Gmail MCPs:

- **Local audit log** (on by default) — every write/send/modify/download appends a JSON line to `audit.jsonl`. Metadata only (no body content). Compliance trail without third-party services.
- **Recipient allowlist** (off by default) — when enabled, every outbound operation (`send_email`, `create_draft`, `reply_to_message`, `forward_message`) checks recipients against configured domains and explicit addresses. Useful for institutional / compliance contexts. See [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) to enable.

## Tools (33)

| Group | Tools |
|---|---|
| Send / reply / forward | `send_email`, `reply_to_message`, `forward_message` |
| Drafts | `create_draft`, `list_drafts`, `send_draft`, `update_draft`, `delete_draft` |
| Read / profile | `get_profile`, `get_message`, `search_threads`, `get_thread` |
| Attachments | `get_message_attachments`, `download_attachment` |
| Trash | `trash_message`, `untrash_message`, `trash_thread`, `untrash_thread` |
| Labels | `list_labels`, `create_label`, `update_label`, `delete_label`, `label_message`, `unlabel_message`, `label_thread`, `unlabel_thread` |
| Filters | `list_filters`, `create_filter`, `delete_filter` |
| Signature | `get_signature`, `update_signature` |
| Vacation responder | `get_vacation_responder`, `set_vacation_responder` |

OAuth scopes requested: `gmail.modify` + `gmail.settings.basic`. Does **not** request the `https://mail.google.com/` superuser scope — permanent delete is intentionally unsupported.

## Requirements

- Python ≥ 3.10
- A Google Cloud project with the Gmail API enabled and an OAuth 2.0 client (Desktop type)
- A way to forward `localhost:8765` to your auth host (typically `ssh -L 8765:localhost:8765 user@host`)

## Install

```bash
pip install mcp-gmail-manager
```

Or from source:

```bash
git clone https://github.com/arthjhon/mcp-gmail-manager.git
cd mcp-gmail-manager
pip install .
```

## Google Cloud setup (one-time, ~10 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project (or pick an existing one).
2. Enable the **Gmail API** (not "Gmail MCP API" — that's Google's own remote MCP; not what we want).
3. Configure the **OAuth consent screen**:
   - User type: **Internal** if your account is part of a Google Workspace; otherwise **External** in Testing mode (limited to 100 users, tokens expire every 7 days — fine for individuals).
   - Scopes: add `https://www.googleapis.com/auth/gmail.modify` and `https://www.googleapis.com/auth/gmail.settings.basic`. **Do not** add anything else.
   - Test users (External only): add the Gmail address you'll authenticate with.
4. Create an **OAuth Client ID**:
   - Application type: **Desktop app**
   - Download the JSON. Save it as `credentials.json`.

## First-time auth

Move your credentials into the config directory (default `~/.config/mcp-gmail-manager/`):

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/Downloads/client_secret_*.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

Run the auth flow:

```bash
mcp-gmail-manager-auth
```

This binds to `localhost:8765` and prints a Google authorisation URL. Open it in a browser **on a machine that can reach `localhost:8765` on the auth host**:

- **Local desktop**: the printed URL works directly.
- **Remote / headless server**: forward the port from your laptop first:
  ```bash
  ssh -L 8765:localhost:8765 user@your-server
  ```
  Then run `mcp-gmail-manager-auth` inside that SSH session.

Authorise with the Google account that will own outbound mail. On success the script writes `token.json` and exits.

## Register with Claude Code

```bash
claude mcp add gmail-manager -- mcp-gmail-manager
```

Or, if you installed inside a virtualenv that isn't on `$PATH`:

```bash
claude mcp add gmail-manager -- /path/to/venv/bin/mcp-gmail-manager
```

Restart your Claude Code session so the new tool schemas load.

## Configuration

`~/.config/mcp-gmail-manager/config.json` is optional — if it doesn't exist, sensible defaults apply (no allowlist, audit log enabled). Two ready-to-copy examples are provided:

- [`examples/config.example.json`](examples/config.example.json) — minimal, no allowlist (default behaviour). Use this if you want the MCP to send to any address.
- [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) — institutional setup with allowlist enforced.

Schema reference:

```json
{
  "allowlist": {
    "enabled": false,
    "domains": [],
    "emails": []
  },
  "audit_log": {
    "enabled": true,
    "path": null
  },
  "attachments": {
    "max_total_bytes": 20971520
  }
}
```

| Field | Default | Meaning |
|---|---|---|
| `allowlist.enabled` | `false` | When `false`, any recipient is accepted. Enable explicitly for institutional use. |
| `allowlist.domains` | `[]` | Lower-case domain suffixes accepted as recipients. |
| `allowlist.emails` | `[]` | Explicit lower-case email addresses accepted regardless of domain. |
| `audit_log.enabled` | `true` | Append every write/modify/send to JSONL. |
| `audit_log.path` | `null` | `null` → `<config_dir>/audit.jsonl`. Override to centralise logs. |
| `attachments.max_total_bytes` | `20971520` (20 MB) | Combined size cap per send. Gmail's hard limit is 25 MB raw. |

### Environment variable overrides

| Variable | Default |
|---|---|
| `GMAIL_MCP_CONFIG_DIR` | `$XDG_CONFIG_HOME/mcp-gmail-manager` or `~/.config/mcp-gmail-manager` |
| `GMAIL_MCP_CREDENTIALS` | `<config_dir>/credentials.json` |
| `GMAIL_MCP_TOKEN` | `<config_dir>/token.json` |

## Security notes

- **Token storage**: `token.json` is written `chmod 600`. Treat it as a password — anyone with read access can act as your Gmail account.
- **No remote attestation**: this server runs entirely on your machine. No telemetry, no third-party calls beyond `googleapis.com`.
- **Allowlist is defence in depth, not perimeter security**: an attacker who compromises your machine can read `token.json` and call the Gmail API directly, bypassing the MCP entirely. The allowlist defends against the LLM being tricked or hallucinating malicious recipients, not against host compromise.
- **OAuth scope is broad**: `gmail.modify` covers everything except permanent delete. If you only need to send, fork and replace the scope with `gmail.send`.
- **Permanent delete intentionally unsupported**: we don't request `https://mail.google.com/`. Deletes go to Trash and can be undone with `untrash_*`.

## Limitations

- OAuth "Production" verification for `gmail.modify` requires a Google security assessment (paid, weeks of process). Stay in "Internal" (Workspace) or "Testing" (≤ 100 users, 7-day token refresh) modes to avoid this.
- HTML email body composition is not exposed as a first-class field. Send via `create_draft` + manual HTML editing in the Gmail UI, or extend `_build_mime` in a fork.
- Push notifications (Pub/Sub `watch`/`stop`) not implemented — out of scope.

## Contributing

Issues and PRs welcome. Keep changes scoped, document any new tool with a schema example, and add an audit-log entry for anything that mutates state.

## License

MIT — see [LICENSE](LICENSE).
