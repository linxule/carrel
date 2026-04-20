# Google Workspace CLI Setup Guide

This guide walks a researcher through setting up `gws` (Google Workspace CLI) so Carrel can export Google Docs, Sheets, and Slides directly. **This is a high-friction setup** — expect 15-30 minutes. Only proceed if the researcher actively uses Google Docs for their work.

## Before You Start

The researcher needs:
- A Google account (personal or institutional)
- Access to the Google Cloud Console (console.cloud.google.com)
- Willingness to create a "project" in Google Cloud (free, no billing required for Drive API)

**Important framing for the researcher:** "To let me access your Google Docs, we need to set up a secure connection through Google's system. It's a one-time process — about 15-20 minutes. After that, I can import any of your Google Docs directly."

## Step 1: Install gws

```bash
brew install googleworkspace-cli
```

Verify: `gws --version`

## Step 2: Create a Google Cloud Project

Guide the researcher through this. Use plain language.

1. Open https://console.cloud.google.com
2. Click the project dropdown (top bar) → "New Project"
3. Name it something recognizable: "Carrel Research Tools" or "My Research"
4. Click "Create" — takes a few seconds

**Plain language:** "We're creating a little workspace in Google's system. Think of it like registering an app — except the app is just your personal research tool."

## Step 3: Enable the Google Drive API

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click it → "Enable"

**Why:** This is what allows `gws` to export your documents. Without it, Google blocks the connection.

## Step 4: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (works for all Google accounts)
3. Fill in:
   - App name: "Carrel" (or anything — only you see this)
   - User support email: researcher's email
   - Developer contact: researcher's email
4. Click "Save and Continue"
5. Skip "Scopes" — click "Save and Continue"
6. Under "Test users" → "Add users" → add the researcher's Google email
7. Click "Save and Continue"

**Plain language:** "Google wants to know what this connection is for. We're just telling it 'this is a personal research tool' — nothing gets shared publicly."

## Step 5: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Carrel Desktop" (or anything)
5. Click "Create"
6. **Download the JSON file** — click the download button next to the new credential

**Plain language:** "This file is like a key that lets your computer talk to Google securely. Keep it safe — we'll use it in the next step."

## Step 6: Authenticate gws

```bash
gws auth login --client-id-file ~/Downloads/client_secret_*.json -s drive
```

This opens a browser window. The researcher signs in with their Google account and approves access.

After approval, credentials are stored encrypted at `~/.config/gws/` — the researcher won't need to do this again.

**Verify it worked:**
```bash
gws drive about get --params '{"fields": "user"}'
```

Should show the researcher's Google account name and email.

## Step 7: Test with a Real Document

Ask the researcher for a Google Doc they'd like to import:

1. Get the URL (e.g., `https://docs.google.com/document/d/1abc.../edit`)
2. Run: `carrel google export <url>`
3. Show the result in the vault

**Plain language:** "Let's test it — paste a link to one of your Google Docs and I'll bring it into your vault."

## Troubleshooting

## Windows-specific setup

On Windows, `gws auth setup` cannot find `gcloud.cmd` due to how Rust binaries resolve `.cmd` wrappers. Skip that command and follow these steps instead:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID of type "Desktop app"
3. Download the credentials JSON
4. Place it at `%APPDATA%\gws\credentials.json` (or wherever `gws` expects)
5. Run `gws auth login -s drive` — this reads the manually-placed credentials and completes the browser OAuth flow.

Same one-time setup friction as macOS, different entry point.

**"Access blocked: This app's request is invalid"**
- The OAuth consent screen is in "Testing" mode — make sure the researcher's email is added as a test user (Step 4.6).

**"The caller does not have permission"**
- The Google Drive API might not be enabled. Go back to Step 3.

**"Token expired"**
- Run `gws auth login -s drive` again. Tokens last about 1 hour, but `gws` refreshes automatically in most cases.

**"gws command not found"**
- Reinstall: `brew install googleworkspace-cli`

## What This Enables

Once set up, the researcher can say:
- "Import my Google Doc: [paste URL]"
- "Bring my Google Sheets data into the vault"
- "Convert my Google Slides to notes"

Carrel exports the document via the Drive API, then processes it through the normal conversion pipeline (DOCX → markitdown, PDF → liteparse).

## Scope and Limitations

- **Export only** — Carrel reads from Google Docs but does not write back to them
- **10 MB per file** — Google's export limit
- **Public or researcher-owned** — can't export documents shared read-only by others (unless the owner allows download)
- **No billing required** — the Drive API is free for personal use within Google's quotas

## Source Links (for maintaining this guide)

- **gws CLI repo**: https://github.com/googleworkspace/cli
- **gws auth docs**: https://github.com/googleworkspace/cli#authentication
- **Google Cloud Console**: https://console.cloud.google.com
- **Google Drive API reference**: https://developers.google.com/drive/api/reference/rest/v3
- **Drive export MIME types**: https://developers.google.com/drive/api/guides/ref-export-formats
- **OAuth consent screen setup**: https://developers.google.com/workspace/guides/configure-oauth-consent
- **Create OAuth credentials**: https://developers.google.com/workspace/guides/create-credentials#desktop-app
