# Installation Guide

> 🌐 **[Leia em português (pt-BR) →](INSTALLATION.pt-BR.md)**

Step-by-step tutorial for installing and configuring **mcp-gmail-manager** — from Google Cloud OAuth setup to a working MCP integration in Claude Code.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Choose your installation path](#choose-your-installation-path)
3. [Step 1 — Install the package](#step-1--install-the-package)
4. [Step 2 — Set up Google Cloud (one-time)](#step-2--set-up-google-cloud-one-time)
5. [Step 3 — Deploy credentials.json](#step-3--deploy-credentialsjson)
6. [Step 4 — Run the OAuth flow](#step-4--run-the-oauth-flow)
7. [Step 5 — Register with Claude Code](#step-5--register-with-claude-code)
8. [Step 6 — Verify the installation](#step-6--verify-the-installation)
9. [Optional — Hardening](#optional--hardening)
10. [Multiple accounts and multiple VMs](#multiple-accounts-and-multiple-vms)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.10 or newer
- A Gmail account (personal `@gmail.com` or Google Workspace)
- Claude Code installed and working (`claude --version`)
- **For desktop install**: a browser on the same machine
- **For headless VM install** (Contabo, DigitalOcean, Hetzner, EC2, etc.): SSH access and a way to forward ports

---

## Choose your installation path

| Scenario | Auth complexity | Token lifetime |
|---|---|---|
| **Desktop (macOS / Linux with browser / Windows)** | Simple — browser and auth server on same machine | Depends on OAuth mode below |
| **Headless VM** | Medium — requires SSH port forwarding | Same |
| **Personal `@gmail.com` account** | Same install steps | **7-day rotation** (Google Testing mode) |
| **Google Workspace account (Internal)** | Same install steps | **No expiration** |

Pick your combination and follow the sections below.

---

## Step 1 — Install the package

### macOS

```bash
brew install pipx           # skip if already installed
pipx ensurepath             # adds ~/.local/bin to PATH
# close and reopen terminal, or: source ~/.zshrc

pipx install mcp-gmail-manager
```

### Linux (Debian / Ubuntu / Mint / Fedora / Arch)

```bash
sudo apt install pipx        # Debian / Ubuntu / Mint
sudo dnf install pipx        # Fedora / Rocky / Alma
sudo pacman -S python-pipx   # Arch
pipx ensurepath              # adds ~/.local/bin to PATH
# reopen shell, or: source ~/.bashrc

pipx install mcp-gmail-manager
```

### Windows (PowerShell)

```powershell
# If Python isn't installed:
winget install --id Python.Python.3.12

python -m pip install --user pipx
python -m pipx ensurepath
# close and reopen PowerShell

pipx install mcp-gmail-manager
```

### Verify

```bash
python3 -c "import mcp_gmail_manager; print(mcp_gmail_manager.__version__)"
# Expected: 0.3.3 (or newer)
```

---

## Step 2 — Set up Google Cloud (one-time)

This section is where most installers get stuck. Screenshots make it painless — refer to the images alongside the text.

### 2.1 Create (or select) a Google Cloud project

Open the [Google Cloud Console](https://console.cloud.google.com/).

![GCP Console home — click the project dropdown at the top](images/01-gcp-select-project.png)

Click **New Project**, give it a name (e.g. `mcp-gmail-manager`), leave the Organization at "No organization" if you're using a personal Gmail account, then **Create**.

![New project form with name field](images/02-gcp-new-project-form.png)

### 2.2 Enable the Gmail API

Navigate to **APIs & Services → Library** and search for `Gmail API`.

![APIs & Services Library — search bar with "Gmail API"](images/03-gcp-api-library.png)

Click the "Gmail API" result and press **Enable**.

![Gmail API page with the Enable button prominent](images/04-gcp-gmail-api-enable.png)

> ⚠ **Important**: enable the **Gmail API**, not the "Gmail MCP API" — the latter is Google's own remote MCP service and is **not** what this project uses.

### 2.3 Configure the OAuth consent screen

Navigate to **APIs & Services → OAuth consent screen** (in the newer console it may be under "Google Auth Platform → Branding / Audience / Data access").

Pick the user type:

- **Internal** — only available if you're a Google Workspace admin/user. Any user in your Workspace org can authenticate; refresh tokens do **not** expire.
- **External** — required for personal `@gmail.com` accounts. Refresh tokens rotate every **7 days** while the app stays in "Testing" mode.

![Consent screen user type selection — Internal vs External](images/05-gcp-oauth-consent-user-type.png)

Fill in the app info:

- **App name**: `mcp-gmail-manager` (or your choice)
- **User support email**: your email
- **Developer contact email**: your email

![Consent screen app info form](images/06-gcp-oauth-consent-app-info.png)

Add scopes — **only these two**, nothing else:

- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/gmail.settings.basic`

![Consent screen scope selection with the two required scopes](images/07-gcp-oauth-consent-scopes.png)

**External + Testing users only**: add the Gmail addresses that will authenticate as test users (up to 100). Skip this if you selected Internal.

![Test users list with an added Gmail address](images/08-gcp-oauth-consent-test-users.png)

Save the consent screen.

### 2.4 Create the OAuth Client ID

Navigate to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**.

![Credentials page with Create Credentials button](images/09-gcp-credentials-create.png)

Choose **Application type: Desktop app** and give it a name (`mcp-gmail-manager-desktop` is fine).

![Application type selection — Desktop app option](images/10-gcp-credentials-desktop-app.png)

Click **Create** and **Download JSON** on the confirmation dialog. Save the file as `credentials.json`.

![Confirmation dialog with Download JSON button](images/11-gcp-credentials-download.png)

---

## Step 3 — Deploy credentials.json

### macOS / Linux (desktop or VM)

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/Downloads/credentials.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.config\mcp-gmail-manager" | Out-Null
Move-Item "$HOME\Downloads\credentials.json" "$HOME\.config\mcp-gmail-manager\credentials.json"
```

### Deploying to a headless VM

If Google Cloud lives on your desktop but the MCP runs on a VM, transfer the file via `scp`:

```bash
scp ~/Downloads/credentials.json user@vm-ip:~/credentials.json
```

Then on the VM:

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/credentials.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

---

## Step 4 — Run the OAuth flow

### 4a — Desktop / local (browser on the same machine)

```bash
mcp-gmail-manager-auth
```

Copy the printed URL into your browser, sign in with the Google account you added, and click **Allow**.

![Terminal output showing the printed OAuth URL](images/12-auth-cli-output.png)

![Google consent dialog asking to authorize the app](images/13-google-consent-dialog.png)

You'll see confirmation:

```
Token salvo em /Users/you/.config/mcp-gmail-manager/token.json
```

![Terminal showing "Token salvo em ..." success message](images/14-auth-success.png)

### 4b — Headless VM (browser on a different machine)

The auth listener binds to `localhost:8765` **on the VM**. Google will redirect **your browser** (on your laptop) to `http://localhost:8765/`. You need an SSH tunnel between the two.

**From your local machine, in a new terminal:**

```bash
ssh -L 8765:localhost:8765 user@vm-ip
```

Leave this session open — it keeps the tunnel alive.

**Inside that same SSH session, on the VM:**

```bash
mcp-gmail-manager-auth
```

Copy the printed URL into your local browser, sign in, click **Allow**. The callback travels through the SSH tunnel and is captured on the VM.

#### If port 8765 is already in use on the VM

Check with `ss -tlnp | grep 8765`. If something's there, pick a free port (e.g., `18765`) and use the `GMAIL_MCP_AUTH_PORT` environment variable (v0.3.3+):

```bash
# On the VM
export GMAIL_MCP_AUTH_PORT=18765
mcp-gmail-manager-auth
```

```bash
# On the local machine — match the port
ssh -L 18765:localhost:18765 user@vm-ip
```

#### Windows-specific note

Some Windows setups block `ssh -L` from binding local loopback ports with `bind [127.0.0.1]:8765: Permission denied` — often Windows Defender or an EDR agent. Workarounds:

- Try `ssh -4 -L 18765:localhost:18765 user@vm-ip` (force IPv4)
- Run PowerShell as Administrator
- Use `GMAIL_MCP_AUTH_PORT=45123` (any high port outside `netsh interface ipv4 show excludedportrange protocol=tcp`)

If nothing works, run the auth on a Linux/macOS machine and `scp` the resulting `token.json` to the VM.

---

## Step 5 — Register with Claude Code

```bash
claude mcp add gmail-manager -s user -- mcp-gmail-manager
```

The `-s user` flag makes the MCP available in **every project** you open with Claude Code, not just the current directory.

![Terminal showing successful claude mcp add and claude mcp list output](images/15-claude-mcp-list.png)

Now **restart your Claude Code session** (close and reopen the chat, or run `/exit` and `claude`) so it loads the new tool schemas.

---

## Step 6 — Verify the installation

In a fresh Claude Code session, ask:

> "Call `get_profile` on gmail-manager."

The MCP should return your Gmail address and message/thread counts.

![Claude Code chat showing get_profile being called and its output](images/16-claude-tool-in-use.png)

If you see your email and stats, you're done. If you see an error like `Token nao encontrado`, revisit **Step 4**.

---

## Optional — Hardening

The default configuration is permissive — no allowlist, no content scanning, no rate limit. Great for testing, not ideal for production. To enable the security-first defaults:

```bash
curl -o ~/.config/mcp-gmail-manager/config.json \
  https://raw.githubusercontent.com/arthjhon/mcp-gmail-manager/main/examples/config.example.json
```

Then edit `~/.config/mcp-gmail-manager/config.json` and set `allowlist.domains` to the domains you actually want to send to. The startup warning will remind you if you leave it empty.

For the full explanation of each config field, see the [Configuration section of the README](../README.md#configuration).

---

## Multiple accounts and multiple VMs

You can run several instances of `mcp-gmail-manager` in parallel — one per Gmail account, each with its own config directory:

```bash
# 1. Create dedicated config dir
mkdir -p ~/.config/mcp-gmail-work && chmod 700 ~/.config/mcp-gmail-work

# 2. Reuse the same credentials.json (same OAuth Client works for any authorised user)
cp ~/.config/mcp-gmail-manager/credentials.json ~/.config/mcp-gmail-work/
chmod 600 ~/.config/mcp-gmail-work/credentials.json

# 3. Authenticate with the second account
GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-work mcp-gmail-manager-auth

# 4. Register a second MCP with the env override
claude mcp add gmail-work -s user \
  -e GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-work \
  -- mcp-gmail-manager
```

Tools appear under separate namespaces: `mcp__gmail-manager__send_email`, `mcp__gmail-work__send_email`, etc.

---

## Troubleshooting

### `credentials.json nao encontrado`

You skipped or misfiled Step 3. Verify:

```bash
ls -la ~/.config/mcp-gmail-manager/credentials.json
# Expected: -rw------- (chmod 600) and non-zero size
```

### `Token nao encontrado. Rode mcp-gmail-manager-auth primeiro.`

You haven't completed Step 4 for this config dir, or the token expired (7-day rotation in Testing mode). Rerun the auth flow.

### `Address already in use` on the auth port

Another process is holding the port on the VM. Diagnose with `ss -tlnp | grep <port>` and either kill it or use `GMAIL_MCP_AUTH_PORT` to pick a different port.

### `bind [127.0.0.1]:8765: Permission denied` (Windows SSH client)

See the Windows-specific note in [Step 4b](#4b--headless-vm-browser-on-a-different-machine).

### The Google consent screen says "This app is restricted to a specific organization"

Your consent screen is set to **Internal** but you're trying to authenticate with a Gmail account outside that Google Workspace organization. Either:

- Switch the consent screen to **External + Testing** and add the Gmail address as a test user, or
- Authenticate with a Google account inside the same Workspace organization

### Claude Code says my tool doesn't exist

You forgot to restart Claude Code after `claude mcp add`. Run `/exit` and `claude`, or reload the VSCode window (`Developer: Reload Window` from the command palette).

### Nothing else on this list fits

Open an issue at https://github.com/arthjhon/mcp-gmail-manager/issues with:

- The command you ran
- The full error output
- Your OS, Python version (`python3 --version`), and mcp-gmail-manager version (`python3 -c "import mcp_gmail_manager; print(mcp_gmail_manager.__version__)"`)

---

## Where to next

- **[README](../README.md)** — feature overview, tool reference, security notes
- **[SECURITY.md](../SECURITY.md)** — threat model and known limitations
- **[examples/](../examples/)** — three ready-to-copy config presets
- **[audits/](../audits/)** — external security review reports
