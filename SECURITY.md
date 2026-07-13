# Security Policy

## Reporting a vulnerability

Please open a **private security advisory** at
https://github.com/arthjhon/mcp-gmail-manager/security/advisories/new
rather than a public issue. If you cannot use GitHub's advisory flow,
email the maintainer at the address listed in `pyproject.toml`.

Include:

- The affected version (`mcp-gmail-manager --version` or the tag/commit).
- A minimal reproduction (config, input to the tool, observed behaviour).
- The concrete impact (what can an attacker do?).

I aim to acknowledge within 5 business days and to ship a fix or a
mitigation within 30 days for confirmed high/critical issues. Please do
not disclose publicly until a fix is out.

## Supported versions

| Version | Supported |
|---|---|
| 0.2.1   | ✅ |
| 0.2.0   | ⚠ (upgrade to 0.2.1 recommended) |
| 0.1.x   | ❌ (upgrade to 0.2.x) |

## Threat model

This project is designed to reduce the blast radius of a **misbehaving
or manipulated LLM agent** that has been given access to a Gmail account
via MCP. It is **not** a defence against a compromised host.

### What we defend against

| Threat | Mitigation |
|---|---|
| LLM tricked into sending to attacker via `send_email` | Recipient allowlist (opt-in) |
| Same, via `create_draft` / `reply_to_message` / `forward_message` | Same allowlist |
| Same, via `create_filter` with a `forward` action | Same allowlist (extended in 0.2.0) |
| LLM tricked into attaching `~/.ssh/id_rsa` (or other secrets) | Attachment path deny list (default on) + optional `allowed_paths` whitelist |
| LLM tricked into overwriting `~/.ssh/authorized_keys` via `download_attachment` | Same deny list applies to destination paths |
| Prompt injection in incoming email body / snippet | `<untrusted-email-content>` markers on read tools + tool descriptions |
| Silent inbox reconnaissance | `audit_log.include_reads = true` (opt-in) |
| Partial audit-log tampering (hide one entry) | Per-entry `prev_hash = sha256(previous line)` chain |
| Permanent deletion of evidence | `mail.google.com` scope NOT requested; deletes go to Trash |

### What we do NOT defend against

Explicitly out of scope for the MCP layer:

- **Host compromise** — an attacker with local file access can read `token.json` and call Gmail directly, bypassing every check here. Protect the host.
- **Last-line audit tampering** — the hash chain detects modification of any entry that has a successor. An attacker who modifies only the tip entry (or truncates the log to the tip) is not caught because there is no downstream entry to verify against. Off-host log shipping (roadmap) closes this.
- **Full audit-log rewrite** — same reasoning at the file level. If an attacker can rewrite the entire file, they can recompute the whole chain. Off-host shipping is the fix.
- **Content pattern scanning** — outbound body/subject/attachments are not scanned for secret patterns (API keys, PII). Add server-side DLP if this matters for you.
- **Signature and vacation responder abuse** — `update_signature` and `set_vacation_responder` accept arbitrary content. A tricked LLM could plant phishing text there. Allowlist does not cover this content (only recipients).
- **Google account phishing** — this MCP inherits Google's own 2FA and phishing protections; nothing at the MCP layer helps if the underlying Google account is compromised.
- **Supply chain of transitive dependencies** — we pin our direct deps with upper bounds and run `pip-audit` in CI, but transitive dep vulnerabilities can still land. Watch releases.
- **Multi-tenant abuse** — this MCP is designed for single-user OAuth. Do not run one instance for multiple end users.

## Roadmap (short list, subject to change)

- Optional off-host audit-log shipping (HTTPS POST to a configured endpoint) — closes the full-rewrite gap
- Optional content pattern deny list (regex on outbound bodies) — closes the "LLM leaks a secret in the body" gap
- `preview_send_email` tool for confirm-before-send workflows
- Signed configuration file (HMAC) to detect config tampering
- Extension of allowlist checks to `update_signature` and `set_vacation_responder` bodies

Delivered in 0.2.1:

- ✅ Rate limiting (`rate_limit.sends_per_hour`)
- ✅ Log rotation (`audit_log.max_size_bytes`, `max_backups`)
- ✅ Startup misconfiguration warnings (permissive perms on token/config, empty allowlist, `allowed_paths` = `$HOME`)
- ✅ Startup chain verification (`audit_log.verify_on_startup`)
- ✅ CLI `mcp-gmail-manager-verify-log` for on-demand chain integrity check

Contributions in any of the open directions are welcome.
