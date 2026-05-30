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


@dataclass
class AllowlistConfig:
    enabled: bool = False
    domains: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)


@dataclass
class AuditConfig:
    enabled: bool = True
    path: str | None = None  # None = derived from config_dir / audit.jsonl


@dataclass
class AttachmentConfig:
    max_total_bytes: int = 20 * 1024 * 1024


@dataclass
class Config:
    config_dir: Path = field(default_factory=_default_config_dir)
    allowlist: AllowlistConfig = field(default_factory=AllowlistConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    attachments: AttachmentConfig = field(default_factory=AttachmentConfig)

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
            path=au.get("path"),
        )
    if isinstance(data.get("attachments"), dict):
        at = data["attachments"]
        cfg.attachments = AttachmentConfig(
            max_total_bytes=int(at.get("max_total_bytes", AttachmentConfig.max_total_bytes)),
        )
    return cfg
