# mcp-gmail-manager

> 🌐 **[Leia em português (pt-BR) →](README.pt-BR.md)**

[![PyPI version](https://img.shields.io/pypi/v/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-blueviolet.svg)](https://modelcontextprotocol.io)

A comprehensive Gmail [Model Context Protocol](https://modelcontextprotocol.io) server: **35 tools** covering send/preview/confirm, reply, forward, drafts, search, read, attachments, trash, labels, filters, signature, and vacation responder.

Defence-in-depth features that distinguish it from other Gmail MCPs:

- **Tamper-evident audit log** (on by default) — every write/send/modify/download appends a JSON line to `audit.jsonl`, chained by SHA-256 so partial tampering is detectable. Includes log rotation, startup chain verification, optional read auditing, and a `mcp-gmail-manager-verify-log` CLI.
- **Recipient allowlist** (off by default) — when enabled, every outbound operation (`send_email`, `create_draft`, `reply_to_message`, `forward_message`, `create_filter` with a `forward` action, plus embedded addresses in signature and vacation body) checks recipients against configured domains and explicit addresses.
- **Attachment path allowlist + denylist** (denylist on by default) — the MCP refuses to attach or overwrite obvious credential files (`~/.ssh/`, `~/.aws/`, `id_rsa`, `.env`, `token.json`, etc.), closing the "LLM exfils SSH key as attachment" attack. See [Security notes](#security-notes) for the full default deny set.
- **Prompt-injection tainted-content markers** — read tools (`get_message`, `get_thread`, `search_threads`, `list_drafts`) wrap message bodies and snippets in `<untrusted-email-content>...</untrusted-email-content>` tags. Tool descriptions instruct the LLM to treat wrapped content as data, not instructions.
- **Outbound content scanning** (off by default) — regex-based detection of secrets in the subject/body/signature/vacation content (AWS access keys, Stripe/OpenAI/Anthropic/GitHub/GitLab/Google/Twilio tokens, PEM private keys, JWTs, credentials embedded in URLs). Blocks the send before it hits Gmail if a pattern matches.
- **Preview + confirm send flow** (off by default) — `preview_send_email` runs every guardrail and stores the payload; `confirm_send_email(preview_id)` delivers it. When `send_confirmation.required=true`, direct `send_email` is disabled so a compromised LLM cannot "preview X, then send Y".
- **Rate limiting** (off by default) — cap outbound sends per hour to stop runaway agent loops from burning Gmail quota.
- **Least-privilege OAuth scopes** — requests `gmail.modify` + `gmail.settings.basic` only. Does NOT request `mail.google.com`, so permanent delete is intentionally unavailable.

See [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) for an institutional-mode configuration.

## Tools (33)

| Group | Tools |
|---|---|
| Send / reply / forward | `send_email`, `preview_send_email`, `confirm_send_email`, `reply_to_message`, `forward_message` |
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

> 📖 **Prefer a step-by-step tutorial with screenshots for every stage of the Google Cloud setup?** See the [**Installation Guide**](docs/INSTALLATION.md). The section below covers only the package install; the full guide walks through GCP, credentials, OAuth, VM setup, and Claude Code registration.

Supported on Linux, macOS, and Windows. Recommended path is [pipx](https://pipx.pypa.io/), which installs the CLI into an isolated venv and exposes the entry points on `$PATH`.

### Linux (Debian / Ubuntu / Mint / Fedora / Arch)

```bash
sudo apt install pipx        # Debian / Ubuntu / Mint
sudo dnf install pipx        # Fedora
sudo pacman -S python-pipx   # Arch
pipx ensurepath              # adds ~/.local/bin to PATH
# reopen shell or: source ~/.bashrc

pipx install mcp-gmail-manager
```

### macOS

```bash
brew install pipx            # or: python3 -m pip install --user pipx
pipx ensurepath              # adds ~/.local/bin to PATH
# reopen shell or: source ~/.zshrc

pipx install mcp-gmail-manager
```

### Windows (PowerShell)

```powershell
# If you don't have Python yet:  winget install --id Python.Python.3.12
python -m pip install --user pipx
python -m pipx ensurepath
# close and reopen PowerShell

pipx install mcp-gmail-manager
```

Windows caveats — everything works, with three notes:

- **Token file permissions.** On Linux/macOS the MCP writes `token.json` with `chmod 0o600`. On Windows there is no POSIX chmod, so the file inherits your `%USERPROFILE%` ACL — protected against other user accounts, but any process running as *your* user can read it. Same effective posture as most Windows CLI tools that store OAuth tokens.
- **Attachment path deny list works.** As of v0.3.2 the deny/allow-list matching normalises paths to forward-slash form via `Path.as_posix()`, so a Windows path like `C:\Users\me\.ssh\id_rsa` is correctly caught by the default `~/.ssh/` deny pattern. Confirmed by the smoke suite on both platforms.
- **Port 8765 may be reserved by Windows.** Hyper-V, WSL2, and Docker Desktop reserve dynamic port ranges that sometimes include 8765, giving `bind [127.0.0.1]:8765: Permission denied` on the local end of an SSH `-L` forward. Check with `netsh interface ipv4 show excludedportrange protocol=tcp`. If 8765 is reserved, set `GMAIL_MCP_AUTH_PORT` to a free port on both ends (v0.3.3+): `set GMAIL_MCP_AUTH_PORT=18765` on the server before running `mcp-gmail-manager-auth`, and forward that same port: `ssh -L 18765:localhost:18765 user@server`.

### Alternative on any OS — manual venv

```bash
python3 -m venv ~/.venv-mcp-gmail
~/.venv-mcp-gmail/bin/pip install mcp-gmail-manager
# Windows: python -m venv %USERPROFILE%\.venv-mcp-gmail
# Use the absolute path when registering with Claude Code (see below)
```

**Why not plain `pip install` system-wide?** On modern Debian-based distros and Homebrew Python it fails with `error: externally-managed-environment` ([PEP 668](https://peps.python.org/pep-0668/)) — the OS protects its Python. The pipx and venv methods above are the canonical workarounds.

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

- [`examples/config.example.json`](examples/config.example.json) — **hardened defaults** (recommended starting point). Every guardrail on; allowlist enabled but empty, so the startup warning will point you at what to configure first.
- [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) — fully-populated institutional example with placeholder domains.
- [`examples/config.permissive.json`](examples/config.permissive.json) — **explicit opt-out** for users who want no guardrails (allowlist off, content scan off, rate limit off, no send confirmation). Consider this only if you understand the blast radius.

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
    "include_reads": false,
    "path": null
  },
  "attachments": {
    "max_total_bytes": 20971520,
    "allowed_paths": [],
    "deny_patterns": [],
    "use_default_deny_patterns": true
  }
}
```

| Field | Default | Meaning |
|---|---|---|
| `allowlist.enabled` | `false` | When `false`, any recipient is accepted. Enable explicitly for institutional use. |
| `allowlist.domains` | `[]` | Lower-case domain suffixes accepted as recipients. |
| `allowlist.emails` | `[]` | Explicit lower-case email addresses accepted regardless of domain. |
| `audit_log.enabled` | `true` | Append every write/send/modify to JSONL. |
| `audit_log.include_reads` | `false` | Also log read operations (`get_message`, `search_threads`, `get_thread`, `list_drafts`, `get_message_attachments`). Useful for detecting silent reconnaissance. |
| `audit_log.path` | `null` | `null` → `<config_dir>/audit.jsonl`. Override to centralise logs. |
| `audit_log.max_size_bytes` | `10485760` (10 MB) | Rotate to `audit.jsonl.1..N` when the current file exceeds this size. Chain resets across rotations; verify each file separately with the CLI. |
| `audit_log.max_backups` | `5` | Number of rotated backups to keep. Older ones are overwritten. |
| `audit_log.verify_on_startup` | `false` | Walk the chain on server start and emit a stderr warning if broken. Cheap for logs up to a few MB. |
| `attachments.max_total_bytes` | `20971520` (20 MB) | Combined size cap per send. Gmail's hard limit is 25 MB raw. |
| `attachments.allowed_paths` | `[]` | When populated, attach/download sources and destinations MUST be under one of these bases. Empty = only deny patterns apply. |
| `attachments.deny_patterns` | `[]` | Extra regex patterns to reject (matched against absolute path). Added on top of defaults. |
| `attachments.use_default_deny_patterns` | `true` | Include the built-in deny set (`~/.ssh/`, `~/.aws/`, `id_rsa`, `.env`, `token.json`, credential files, browser stores). |
| `rate_limit.enabled` | `false` | When `true`, cap outbound sends per hour per running instance. In-memory sliding window — resets on server restart. |
| `rate_limit.sends_per_hour` | `60` | Applied to `send_email`, `reply_to_message`, `forward_message`, and `send_draft` combined. |
| `content_scan.enabled` | `false` | When `true`, scan outbound subjects, bodies, signatures, and vacation content for secret patterns. Matches block the operation before it reaches Gmail. |
| `content_scan.use_default_patterns` | `true` | Include the built-in secret regexes (AWS access keys, Stripe/OpenAI/Anthropic/GitHub/GitLab/Google/Twilio tokens, PEM private keys, JWTs, URL-embedded credentials). |
| `content_scan.patterns` | `[]` | Additional user-defined patterns. Each entry: `{"name": "...", "regex": "..."}`. Names surface in error messages for debugging. |
| `content_scan.scan_subject` / `scan_body` / `scan_signature` / `scan_vacation` | `true` | Per-scope toggles. Useful for disabling one location while keeping others active. |
| `send_confirmation.required` | `false` | When `true`, direct `send_email` is disabled — must go through `preview_send_email` → `confirm_send_email(preview_id)`. |
| `send_confirmation.preview_ttl_seconds` | `300` | How long a preview stays valid before it must be re-issued. |

### Verifying the audit log

Run `mcp-gmail-manager-verify-log` to walk the hash chain and confirm no entry has been edited or removed:

```bash
mcp-gmail-manager-verify-log                       # verify the active log
mcp-gmail-manager-verify-log ~/.config/.../audit.jsonl.1   # verify a rotated backup
```

Exit codes: `0` OK, `1` log not found, `2` malformed JSON, `3` chain broken.

### Environment variable overrides

| Variable | Default |
|---|---|
| `GMAIL_MCP_CONFIG_DIR` | `$XDG_CONFIG_HOME/mcp-gmail-manager` or `~/.config/mcp-gmail-manager` |
| `GMAIL_MCP_CREDENTIALS` | `<config_dir>/credentials.json` |
| `GMAIL_MCP_TOKEN` | `<config_dir>/token.json` |

## Security notes

- **Threat model**: this MCP is primarily hardened against a **misbehaving LLM** — prompt injection, hallucinated recipients, tricked-into-exfil scenarios. It is NOT a substitute for host security; an attacker with local access can read `token.json` and call Gmail directly, bypassing every guardrail here.
- **Token storage**: `token.json` is written `chmod 600`. Treat it as a password.
- **No remote attestation**: this server runs entirely on your machine. No telemetry, no third-party calls beyond `googleapis.com`.
- **OAuth scope is deliberately narrow-ish**: `gmail.modify` covers send/read/label/trash/drafts. It does NOT request `mail.google.com`, so permanent delete is unavailable — deletes go to Trash and can be undone with `untrash_*`. If you only need to send, fork and replace the scope with `gmail.send`.
- **Recipient guardrails cover forward-in-filters**: `create_filter` with an `action.forward` targeting a non-allowlisted address is rejected. Filters were a common bypass of send-only allowlists.
- **Read tools mark content as untrusted**: bodies and snippets are wrapped in `<untrusted-email-content>...</untrusted-email-content>`. Tool descriptions instruct downstream LLMs to treat wrapped content as data. Any occurrence of the closing tag inside a message body is escaped to prevent break-out.
- **Default attachment deny set** (source and destination) covers common credential / secret paths:
  `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.docker/config.json`, `~/.kube/`, `.env`, `.env.*`, `credentials.json`, `token.json`, `id_rsa`/`id_ed25519`/`id_ecdsa`/`id_dsa`, `.git-credentials`, `.netrc`, `wallet.dat`, `.bash_history`, `.zsh_history`, `~/.mozilla/*/logins.json`, `authorized_keys`, `known_hosts`. Extend via `attachments.deny_patterns` or narrow further via `attachments.allowed_paths`.
- **Audit log is tamper-evident, not tamper-proof**: each entry includes `prev_hash = sha256(previous line)`. Partial modification breaks the chain and is detectable. A full log rewrite by an attacker with file-write is NOT prevented — pair with off-host log shipping (roadmap) for stronger guarantees.
- **What is NOT mitigated**: rate limiting (a compromised agent can burn Gmail quota fast), outbound content pattern scanning (no secret regex on bodies), signature/vacation phishing (allowlist doesn't cover their content), full log rewrite by a local attacker. See [SECURITY.md](SECURITY.md) for the current threat model and roadmap.

## Limitations

- OAuth "Production" verification for `gmail.modify` requires a paid Google security assessment. Stay in "Internal" (Workspace, no expiration) or "Testing" (≤ 100 users, **7-day refresh token rotation** — see [Token expiration](#token-expiration)) to avoid this.
- HTML email body composition is not exposed as a first-class field. Send via `create_draft` + manual HTML editing in the Gmail UI, or extend `_build_mime` in a fork.
- Push notifications (Pub/Sub `watch`/`stop`) not implemented — out of scope.

## Contributing

Issues and PRs welcome. Keep changes scoped, document any new tool with a schema example, and add an audit-log entry for anything that mutates state.

## License

MIT — see [LICENSE](LICENSE).
