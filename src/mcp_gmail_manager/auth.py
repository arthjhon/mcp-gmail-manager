"""One-shot OAuth flow. Run via `mcp-gmail-manager-auth` to obtain the refresh token.

Listens on localhost:8765 for the OAuth callback. On a headless server, forward the port
over SSH first:

    ssh -L 8765:localhost:8765 user@your-server

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
OAUTH_PORT = 8765


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

    flow = InstalledAppFlow.from_client_secrets_file(str(cfg.credentials_path), SCOPES)
    creds = flow.run_local_server(
        host="localhost",
        port=OAUTH_PORT,
        open_browser=False,
        bind_addr="127.0.0.1",
    )

    cfg.token_path.write_text(creds.to_json())
    os.chmod(cfg.token_path, 0o600)
    print(f"Token salvo em {cfg.token_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
