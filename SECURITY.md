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
| 0.3.1   | ✅ |
| 0.3.0   | ⚠ (upgrade to 0.3.1 — closes F1/F2/F4 from the external audit) |
| 0.2.x   | ⚠ (upgrade to 0.3.1 recommended) |
| 0.1.x   | ❌ (upgrade to 0.3.1) |

## External review

v0.3.0 was externally reviewed by [Haider Ali](https://github.com/shadowhunter-92) of
[AgentBridge](https://github.com/shadowhunter-92/agentbridge) on 2026-07-14 (static + design review against
the OWASP Top-10 for Agentic Applications 2026). The review confirmed the primary controls
close the attack paths they were designed to close, and produced 0 Critical / 0 High / 2 Medium
/ 2 Low findings. **v0.3.1 fixes F1, F2, and F4**; F3 is documented as an accepted-risk policy
decision (see below). Full report: [`audits/v0.3.0-external-audit.md`](audits/v0.3.0-external-audit.md).

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
- **High-recall PII / arbitrary secrets** — the content scan is high-precision (specific well-known prefixes like `AKIA`, `sk_live_`, `ghp_`). It will not catch every possible sensitive value (e.g., passwords, generic 32-char hex strings, personal data). Consider a dedicated DLP if you need broader coverage.
- **Google account phishing** — this MCP inherits Google's own 2FA and phishing protections; nothing at the MCP layer helps if the underlying Google account is compromised.
- **Supply chain of transitive dependencies** — we pin our direct deps with upper bounds and run `pip-audit` in CI, but transitive dep vulnerabilities can still land. Watch releases.
- **Multi-tenant abuse** — this MCP is designed for single-user OAuth. Do not run one instance for multiple end users.

## Roadmap (short list, subject to change)

- Optional off-host audit-log shipping (HTTPS POST to a configured endpoint) — closes the full-rewrite gap
- Signed configuration file (HMAC) to detect config tampering
- Optional 2FA gating on the send flow (require a passcode via an out-of-band channel)

Delivered in 0.3.1 (external audit response):

- ✅ **F1**: `_wrap_untrusted` extended to `subject`, `from`, `to`, `cc` on `get_message`/`get_thread`/`list_drafts` and to attachment `filename` on `get_message_attachments`. Attacker-controlled header fields and attachment filenames now carry the same `<untrusted-email-content>` markers as bodies and snippets, and tool descriptions reflect the extended coverage.
- ✅ **F2**: `config.example.json` — the file new users are most likely to copy — now ships with every guardrail **on** by default (allowlist, content scan, rate limit, send-confirmation, verify-on-startup). A new `config.permissive.json` documents the opt-out mode for users who explicitly want fewer restrictions. `config.with-allowlist.json` remains as a fully-populated institutional example.
- ✅ **F4**: `send_draft` now fetches the draft's actual Gmail-side content and re-runs the recipient allowlist and content scan at send time. A draft edited via the Gmail web UI (or created before the current guardrails were configured) is validated at send time instead of trusted based on write-time checks.
- ⚠ **F3** (accepted risk): `pip-audit` in CI remains `continue-on-error: true`. Transitive dependency CVEs surface faster than we can pin them, so gating the build would either force noisy releases or tempt us to ignore the signal. The workflow's own comment documents this rationale. A future refinement — gating only on Critical/High severity — is a candidate for the roadmap.

Delivered in 0.3.0:

- ✅ Outbound content scanning (`content_scan.enabled`) with default regexes for AWS, Stripe, OpenAI, Anthropic, GitHub, GitLab, Google API, Slack, Twilio, PEM private keys, JWTs, and URL-embedded credentials. Per-scope toggles for subject/body/signature/vacation.
- ✅ Embedded-address allowlist check on `update_signature` and `set_vacation_responder` bodies — blocks the LLM from planting phishing addresses in the auto-appended signature or vacation autoreply.
- ✅ Preview + confirm send flow (`preview_send_email` + `confirm_send_email`) with hard `send_confirmation.required` mode that disables direct `send_email`. Preview payload is stored server-side keyed by an opaque `preview_id`, so confirmation always sends the previewed content — the LLM cannot preview X then send Y.

Delivered in 0.2.1:

- ✅ Rate limiting (`rate_limit.sends_per_hour`)
- ✅ Log rotation (`audit_log.max_size_bytes`, `max_backups`)
- ✅ Startup misconfiguration warnings (permissive perms on token/config, empty allowlist, `allowed_paths` = `$HOME`)
- ✅ Startup chain verification (`audit_log.verify_on_startup`)
- ✅ CLI `mcp-gmail-manager-verify-log` for on-demand chain integrity check

Contributions in any of the open directions are welcome.
