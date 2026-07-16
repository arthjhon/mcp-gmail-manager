# Screenshot capture guide

This folder holds the visual assets referenced by [`INSTALLATION.md`](../INSTALLATION.md) and [`INSTALLATION.pt-BR.md`](../INSTALLATION.pt-BR.md).

Screenshots have not been captured yet. Until they land, users will see broken image placeholders in the rendered docs — the text alone is still enough to complete the tutorial, but the visual walkthrough is the target UX.

## Capture guidelines

- **Format**: PNG (lossless, good for UI). Widths around 1200–1600px are ideal.
- **Naming**: keep the exact filenames listed below so the Markdown links resolve.
- **Redact anything sensitive**: project names, personal emails, OAuth client IDs, screenshots of `credentials.json` content. When in doubt, black-out the field before saving.
- **Zoom**: capture at 100% browser zoom. The `.png` files should be crisp on both light and dark GitHub themes.
- **Language of the UI**: doesn't need to match the docs language — GCP has a language toggle at the bottom, and users are used to figuring out mixed-language screenshots. Prefer whichever language you already have your GCP set to.

## Files needed

### GCP OAuth setup (highest priority — this is the section users get stuck in)

| File | What it should show |
|---|---|
| `01-gcp-select-project.png` | GCP Console home page with the project dropdown at the top expanded, or the standalone project picker page. Highlight the "New Project" button. |
| `02-gcp-new-project-form.png` | The "New Project" form. Fields visible: Project name, Location (No organization for personal Gmail), Project ID (auto-generated). Highlight the "Create" button. |
| `03-gcp-api-library.png` | **APIs & Services → Library** with the search bar populated with `Gmail API`. Show the search results including the Gmail API card. |
| `04-gcp-gmail-api-enable.png` | The Gmail API detail page, with the **Enable** button visible and prominent. |
| `05-gcp-oauth-consent-user-type.png` | The OAuth consent screen user type selection: **Internal** vs **External** radio buttons. If you can, show tooltip text explaining the difference. |
| `06-gcp-oauth-consent-app-info.png` | The consent screen "App information" form: App name, User support email, Developer contact information. |
| `07-gcp-oauth-consent-scopes.png` | The Scopes step showing the two required scopes checked / added: `.../auth/gmail.modify` and `.../auth/gmail.settings.basic`. Ideally, show them in the "Sensitive scopes" table with green checkmarks. |
| `08-gcp-oauth-consent-test-users.png` | The Test users step (External-only) with at least one Gmail address added. Use a redacted example like `test.user@gmail.com`. |
| `09-gcp-credentials-create.png` | **APIs & Services → Credentials** page with the **Create Credentials** dropdown expanded, showing the **OAuth Client ID** option. |
| `10-gcp-credentials-desktop-app.png` | The Application type dropdown expanded, showing **Desktop app** selected. |
| `11-gcp-credentials-download.png` | The confirmation modal that appears after creating the client, with the **Download JSON** button visible. Redact the client ID / client secret if they're shown. |

### Auth flow (medium priority)

| File | What it should show |
|---|---|
| `12-auth-cli-output.png` | Terminal output of `mcp-gmail-manager-auth`. Show the `OAuth callback listener on localhost:8765` line and the `Please visit this URL to authorize this application: https://accounts.google.com/...` URL. The URL can be blurred/truncated after the query-string prefix. |
| `13-google-consent-dialog.png` | Google's OAuth consent dialog in the browser. Show the app name, the scopes being requested ("Ver, editar, criar ou mudar seus filtros" etc.), and the **Allow** button. |
| `14-auth-success.png` | Terminal showing the `Token salvo em /Users/.../token.json` success message. |

### Claude Code (nice to have)

| File | What it should show |
|---|---|
| `15-claude-mcp-list.png` | Terminal output of `claude mcp add gmail-manager -s user -- mcp-gmail-manager` followed by `claude mcp list` showing the new server marked `✓ Connected`. |
| `16-claude-tool-in-use.png` | A Claude Code chat panel with a user asking to call `get_profile` on `gmail-manager` and the tool result showing the authenticated email and message/thread counts. |

## After capturing

Commit the images:

```bash
cd docs/images
# add all captured PNGs
git add *.png
git commit -m "docs: add installation-guide screenshots"
git push
```

The Markdown links in `INSTALLATION.md` and `INSTALLATION.pt-BR.md` are already in place, so the images will start rendering automatically once the files land in this folder.
