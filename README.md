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

**Recommended — [pipx](https://pipx.pypa.io/)** (installs in an isolated venv, exposes the entry points on `$PATH`):

```bash
pipx install mcp-gmail-manager
```

If `pipx` is missing:

```bash
sudo apt install pipx        # Debian / Ubuntu / Mint
brew install pipx            # macOS
pipx ensurepath              # makes ~/.local/bin available, may need shell restart
```

**Alternative — manual venv:**

```bash
python3 -m venv ~/.venv-mcp-gmail
~/.venv-mcp-gmail/bin/pip install mcp-gmail-manager
# Use the absolute path when registering with Claude Code (see below)
```

**Why not plain `pip install` system-wide?** On modern Debian-based distros it fails with `error: externally-managed-environment` ([PEP 668](https://peps.python.org/pep-0668/)) — the OS protects its Python. The two methods above are the canonical workarounds.

**From source:**

```bash
git clone https://github.com/arthjhon/mcp-gmail-manager.git
cd mcp-gmail-manager
pipx install .
```

## Google Cloud setup (one-time, ~10 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project (or pick an existing one).
2. Enable the **Gmail API** (not "Gmail MCP API" — that's Google's own remote MCP; not what we want).
3. Configure the **OAuth consent screen**:
   - User type: **Internal** if your account is part of a Google Workspace (no token expiration); otherwise **External** in Testing mode (up to 100 users, refresh tokens **expire every 7 days** — see [Token expiration](#token-expiration) below).
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

## Token expiration

The refresh token's lifetime depends on how the OAuth consent screen is configured:

| Setup | Refresh token lifetime | Re-auth required? |
|---|---|---|
| **Internal** (Google Workspace) | No expiration | Never (until user revokes) |
| **External + Testing** | **7 days** (Google's policy for unverified apps) | **Yes — weekly** |
| **External + Production verified** | No expiration | Never, but verification requires a paid Google security assessment |

When the refresh token expires in Testing mode you'll see `invalid_grant` or `Token has been expired or revoked` errors. To recover:

```bash
rm ~/.config/mcp-gmail-manager/token.json
mcp-gmail-manager-auth
```

Takes ~30 seconds. Your `credentials.json` is **not** affected — only the user's token.

### How to avoid the weekly rotation

- **Workspace users**: configure the consent screen as **Internal** instead of External. Token never expires.
- **Personal Gmail users**: weekly re-auth is the only practical option today. Production verification for `gmail.modify` requires a Google security assessment (paid, weeks of process) — not feasible for most personal projects.
- **Set a calendar reminder** or a cron job to nudge you weekly. A future release may add proactive in-tool warnings before expiry.

## Register with Claude Code

If installed via `pipx`:

```bash
claude mcp add gmail-manager -- mcp-gmail-manager
```

If installed in a manual venv that isn't on `$PATH`:

```bash
claude mcp add gmail-manager -- ~/.venv-mcp-gmail/bin/mcp-gmail-manager
```

Restart your Claude Code session so the new tool schemas load.

## Multiple Gmail accounts

Each MCP instance handles **one** Gmail account. To use several accounts from the same Claude Code session (e.g. personal + work), register the MCP **once per account** with a distinct `GMAIL_MCP_CONFIG_DIR`. Each instance gets its own credentials, token, audit log, and config — fully isolated.

### Setup per account

```bash
# 1. Dedicated config directory
mkdir -p ~/.config/mcp-gmail-<name> && chmod 700 ~/.config/mcp-gmail-<name>

# 2. Reuse the same OAuth client (one credentials.json works for any user in the same GCP project)
cp ~/.config/mcp-gmail-<other>/credentials.json ~/.config/mcp-gmail-<name>/
chmod 600 ~/.config/mcp-gmail-<name>/credentials.json

# 3. Authenticate with the target Gmail account
GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-<name> mcp-gmail-manager-auth

# 4. Register with the env override
claude mcp add gmail-<name> -s user \
  -e GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-<name> \
  -- mcp-gmail-manager
```

Restart Claude Code. The tools appear under separate namespaces:

- `mcp__gmail-personal__send_email` → sends from the personal account
- `mcp__gmail-work__send_email` → sends from the work account

You can prompt Claude with "send via gmail-work" and it picks the right namespace.

### Per-account configuration

Each `<config_dir>/config.json` is independent. Useful patterns:

```json
// ~/.config/mcp-gmail-work/config.json — strict allowlist
{
  "allowlist": {
    "enabled": true,
    "domains": ["yourcompany.com"]
  }
}
```

```json
// ~/.config/mcp-gmail-personal/config.json — silence the audit log
{
  "audit_log": { "enabled": false }
}
```

Compromise of one account's token does not leak the other — each lives in a separate directory with `chmod 600`.

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

- OAuth "Production" verification for `gmail.modify` requires a paid Google security assessment. Stay in "Internal" (Workspace, no expiration) or "Testing" (≤ 100 users, **7-day refresh token rotation** — see [Token expiration](#token-expiration)) to avoid this.
- HTML email body composition is not exposed as a first-class field. Send via `create_draft` + manual HTML editing in the Gmail UI, or extend `_build_mime` in a fork.
- Push notifications (Pub/Sub `watch`/`stop`) not implemented — out of scope.

## Contributing

Issues and PRs welcome. Keep changes scoped, document any new tool with a schema example, and add an audit-log entry for anything that mutates state.

## License

MIT — see [LICENSE](LICENSE).
