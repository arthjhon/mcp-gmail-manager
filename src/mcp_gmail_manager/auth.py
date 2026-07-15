"""One-shot OAuth flow. Run via `mcp-gmail-manager-auth` to obtain the refresh token.

Listens on localhost:<port> for the OAuth callback. The port defaults to 8765; override
with the environment variable ``GMAIL_MCP_AUTH_PORT`` (useful on Windows when 8765 falls
inside a reserved dynamic-port range and returns ``Permission denied`` on bind).

On a headless server, forward the port over SSH first:

    ssh -L 8765:localhost:8765 user@your-server           # default
    ssh -L 18765:localhost:18765 user@your-server          # with GMAIL_MCP_AUTH_PORT=18765

Then run this script remotely and paste the printed URL into the browser on your laptop.
"""
from __future__ import annotations

import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from .config import load_config

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
DEFAULT_OAUTH_PORT = 8765


def _resolve_port() -> int:
    raw = os.environ.get("GMAIL_MCP_AUTH_PORT")
    if not raw:
        return DEFAULT_OAUTH_PORT
    try:
        port = int(raw)
    except ValueError:
        print(
            f"GMAIL_MCP_AUTH_PORT={raw!r} nao eh um inteiro valido; "
            f"usando default {DEFAULT_OAUTH_PORT}.",
            file=sys.stderr,
        )
        return DEFAULT_OAUTH_PORT
    if not (1 <= port <= 65535):
        print(
            f"GMAIL_MCP_AUTH_PORT={port} fora do range 1-65535; "
            f"usando default {DEFAULT_OAUTH_PORT}.",
            file=sys.stderr,
        )
        return DEFAULT_OAUTH_PORT
    return port


def run() -> int:
    cfg = load_config()
    cfg.config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    if not cfg.credentials_path.is_file():
        print(
            f"credentials.json nao encontrado em {cfg.credentials_path}.\n"
            f"Crie um OAuth Client (Desktop) no Google Cloud Console, baixe o JSON, e salve "
            f"no caminho acima (chmod 600).\n",
            file=sys.stderr,
        )
        return 1

    port = _resolve_port()
    print(f"OAuth callback listener on localhost:{port}", file=sys.stderr)

    flow = InstalledAppFlow.from_client_secrets_file(str(cfg.credentials_path), SCOPES)
    creds = flow.run_local_server(
        host="localhost",
        port=port,
        open_browser=False,
        bind_addr="127.0.0.1",
    )

    cfg.token_path.write_text(creds.to_json())
    os.chmod(cfg.token_path, 0o600)
    print(f"Token salvo em {cfg.token_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
