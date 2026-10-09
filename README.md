# gmail-digest

**English** · [中文](README.zh-CN.md)

A reusable, self-setup **daily email digest**. Forward any mailbox
(Outlook/Office 365, QQ/Foxmail, 163/126, Yahoo, iCloud, university, …) into one
Gmail, and a **Claude Code cloud routine** sends you a filtered, summarized
digest every day.

- Reads Gmail over the **Gmail API (HTTPS)** — so it runs in the routine's cloud
  sandbox, which blocks IMAP/SMTP.
- **No API key needed** — Claude itself is the summarizer.
- **Python standard library only** — no `pip install`, ever.

## How it works

```
   QQ / Outlook / school … ──forward──> Gmail inbox
                                          │  daily, Claude Code cloud routine
                                          ▼
   fetch_inbox.py ──Gmail API──> last 24h of mail (JSON)
                                          ▼
   Claude filters + summarizes per ROUTINE.md ──> digest.md
                                          ▼
   send_digest.py ──Gmail API──> you+digest@gmail.com ──> phone notification
```

The digest is also the routine's own output, so you can review past runs in the
routine history on claude.ai.

## Quick start

1. **Google Cloud (the one irreducible manual part).** Enable the Gmail API,
   configure the OAuth consent screen (add yourself as a **Test user**), and
   create a **Desktop app** OAuth client. Full click-by-click steps, including
   the two gotchas, are in **[docs/SETUP.md](docs/SETUP.md)**.
2. **Run the wizard** on your own machine:
   ```bash
   python setup.py
   ```
   It auto-detects your `client_secret_*.json`, runs the OAuth flow, writes
   `.env`, and self-tests (fetch + send).
3. **Create the cloud routine** — [docs/SETUP.md](docs/SETUP.md) section 3.
4. **Forward your other mailboxes into Gmail** —
   [docs/FORWARDING.md](docs/FORWARDING.md).
5. **Set up a phone notification** for the digest —
   [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md).
6. **Customize `ROUTINE.md`** — your filtering/summary rules and output format.

## Files

| File | What it does |
|---|---|
| `ROUTINE.md` | The routine's prompt: filtering/summary rules and output format (customize this) |
| `fetch_inbox.py` | Read recent Gmail via the Gmail API → JSON (`--hours/--label/--max/--query`) |
| `send_digest.py` | Email the digest via the Gmail API (`--to` / `DIGEST_TO` / `+digest` alias) |
| `gmail_common.py` | OAuth refresh + HTTPS helpers (stdlib) |
| `gmail_oauth_setup.py` | One-time local OAuth helper → refresh token |
| `setup.py` | One-command setup wizard |
| `.claude/settings.json` | Lets the routine run the scripts without permission prompts |
| `.env.example` | Config template (placeholders only) |

## Configuration

All config is environment variables — secrets on the routine's cloud
environment, or `.env` when running locally. See [`.env.example`](.env.example):

- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_USER` — Gmail access.
- `DIGEST_TO` (optional) — recipient override; default is your `+digest` alias.

The look-back window is the `--hours` value in `ROUTINE.md`.

## Security

- `.env`, `client_secret_*.json`, `token.json`, `inbox.json`, `digest.md` are all
  git-ignored. Never commit secrets.
- Revoke the app's Gmail access any time at
  <https://myaccount.google.com/permissions>.

## License

[MIT](LICENSE).
