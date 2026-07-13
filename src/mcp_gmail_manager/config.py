"""Configuration loader.

Reads from a JSON file at $GMAIL_MCP_CONFIG_DIR/config.json (default: $XDG_CONFIG_HOME/mcp-gmail-manager).
Missing or partial files fall back to defaults — the MCP runs out of the box.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_config_dir() -> Path:
    env = os.environ.get("GMAIL_MCP_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "mcp-gmail-manager"


# Default deny patterns block obvious credential / secret locations from being
# attached (source path) or overwritten (destination path). Users can add or
# opt out via config.attachments.
DEFAULT_ATTACHMENT_DENY_PATTERNS: list[str] = [
    r"/\.ssh/",
    r"/\.aws/",
    r"/\.gnupg/",
    r"/\.docker/config\.json$",
    r"/\.kube/",
    r"/\.env$",
    r"/\.env\.",
    r"/credentials\.json$",
    r"/token\.json$",
    r"/id_(?:rsa|ed25519|ecdsa|dsa)$",
    r"/\.git-credentials$",
    r"/\.netrc$",
    r"/wallet\.dat$",
    r"/\.bash_history$",
    r"/\.zsh_history$",
    r"/\.mozilla/.*/logins\.json$",
    r"/authorized_keys$",
    r"/known_hosts$",
]


@dataclass
class AllowlistConfig:
    enabled: bool = False
    domains: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)


@dataclass
class AuditConfig:
    enabled: bool = True
    include_reads: bool = False
    path: str | None = None  # None = derived from config_dir / audit.jsonl
    max_size_bytes: int = 10 * 1024 * 1024  # 10 MB before rotate
    max_backups: int = 5  # keep audit.jsonl.1 .. audit.jsonl.N
    verify_on_startup: bool = False  # walk the chain on server start


@dataclass
class AttachmentConfig:
    max_total_bytes: int = 20 * 1024 * 1024
    allowed_paths: list[str] = field(default_factory=list)
    deny_patterns: list[str] = field(default_factory=list)
    use_default_deny_patterns: bool = True

    def effective_deny_patterns(self) -> list[str]:
        base = list(DEFAULT_ATTACHMENT_DENY_PATTERNS) if self.use_default_deny_patterns else []
        return base + list(self.deny_patterns)


@dataclass
class RateLimitConfig:
    enabled: bool = False
    sends_per_hour: int = 60  # only used when enabled


@dataclass
class Config:
    config_dir: Path = field(default_factory=_default_config_dir)
    allowlist: AllowlistConfig = field(default_factory=AllowlistConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    attachments: AttachmentConfig = field(default_factory=AttachmentConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    @property
    def credentials_path(self) -> Path:
        env = os.environ.get("GMAIL_MCP_CREDENTIALS")
        return Path(env).expanduser() if env else self.config_dir / "credentials.json"

    @property
    def token_path(self) -> Path:
        env = os.environ.get("GMAIL_MCP_TOKEN")
        return Path(env).expanduser() if env else self.config_dir / "token.json"

    @property
    def audit_log_path(self) -> Path:
        if self.audit.path:
            return Path(self.audit.path).expanduser()
        return self.config_dir / "audit.jsonl"

    @property
    def config_file_path(self) -> Path:
        return self.config_dir / "config.json"


def load_config() -> Config:
    """Load config from disk, returning a Config with defaults filled in for missing keys."""
    cfg = Config()
    f = cfg.config_file_path
    if not f.is_file():
        return cfg
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Erro ao ler {f}: {e}") from e

    if isinstance(data.get("allowlist"), dict):
        a = data["allowlist"]
        cfg.allowlist = AllowlistConfig(
            enabled=bool(a.get("enabled", False)),
            domains=[str(d).lower() for d in (a.get("domains") or [])],
            emails=[str(e).lower() for e in (a.get("emails") or [])],
        )
    if isinstance(data.get("audit_log"), dict):
        au = data["audit_log"]
        cfg.audit = AuditConfig(
            enabled=bool(au.get("enabled", True)),
            include_reads=bool(au.get("include_reads", False)),
            path=au.get("path"),
            max_size_bytes=int(au.get("max_size_bytes", AuditConfig.max_size_bytes)),
            max_backups=int(au.get("max_backups", AuditConfig.max_backups)),
            verify_on_startup=bool(au.get("verify_on_startup", False)),
        )
    if isinstance(data.get("attachments"), dict):
        at = data["attachments"]
        cfg.attachments = AttachmentConfig(
            max_total_bytes=int(at.get("max_total_bytes", AttachmentConfig.max_total_bytes)),
            allowed_paths=[str(p) for p in (at.get("allowed_paths") or [])],
            deny_patterns=[str(p) for p in (at.get("deny_patterns") or [])],
            use_default_deny_patterns=bool(at.get("use_default_deny_patterns", True)),
        )
    if isinstance(data.get("rate_limit"), dict):
        rl = data["rate_limit"]
        cfg.rate_limit = RateLimitConfig(
            enabled=bool(rl.get("enabled", False)),
            sends_per_hour=int(rl.get("sends_per_hour", RateLimitConfig.sends_per_hour)),
        )
    return cfg
