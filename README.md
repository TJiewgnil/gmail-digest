# gmail-digest

**English** · [中文](README.zh-CN.md)

A reusable, self-setup **daily email digest**. Forward any mailbox
(Outlook/Office 365, QQ/Foxmail, 163/126, Yahoo, iCloud, university, …) into one
Gmail, and get a filtered, LLM-summarized digest delivered on a schedule.

- Reads Gmail over the **Gmail API (HTTPS)** — so it runs anywhere, including
  sandboxes and CI that block IMAP/SMTP.
- **Python standard library only** — no `pip install`, ever.
- Three ways to run it, same three-stage pipeline each time.

## How it works

```
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
        │ fetch_inbox │ --> │  summarize   │ --> │ send_digest  │
        │  (Gmail API)│     │ (LLM rules)  │     │  (Gmail API) │
        └─────────────┘     └──────────────┘     └──────────────┘
           inbox.json          digest.md            your inbox
```

The pipeline is always **fetch → summarize → deliver**. Only the *trigger* and
*who summarizes* differ per deployment:

| Deployment | Trigger | Summarizer | Needs |
|---|---|---|---|
| **GitHub Actions + Anthropic API** (primary) | cron in the workflow | `summarize.py` | `ANTHROPIC_API_KEY` + GitHub secrets |
| **Claude Code routine** | `/schedule` | Claude Code (no API key) | Claude Code / claude.ai |
| **Local cron / Task Scheduler** | your OS scheduler | `summarize.py` | the machine on + API key |

## Quick start

1. **Google Cloud (the one irreducible manual part).** Enable the Gmail API,
   configure the OAuth consent screen (add yourself as a **Test user**), and
   create a **Desktop app** OAuth client. Full click-by-click steps, including
   the two gotchas, are in **[docs/SETUP.md](docs/SETUP.md)**.
2. **Run the wizard:**
   ```bash
   python setup.py
   ```
   It auto-detects your `client_secret_*.json`, runs the OAuth flow, writes
   `.env`, self-tests (fetch + send), and can push your GitHub Actions secrets.
3. **Pick a deployment** (GitHub Actions / Claude Code routine / local) — see
   [docs/SETUP.md](docs/SETUP.md) section 3.
4. **Forward your other mailboxes into Gmail** —
   [docs/FORWARDING.md](docs/FORWARDING.md).
5. **Set up a phone notification** for the digest —
   [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md).
6. **Customize `ROUTINE.md`** — your filtering/summary rules and output format.

## Files

| File | What it does |
|---|---|
| `fetch_inbox.py` | Read recent Gmail via the Gmail API → JSON (`--hours/--label/--max/--query`) |
| `summarize.py` | inbox JSON + `ROUTINE.md` → digest via the Anthropic Messages API |
| `send_digest.py` | Email the digest via the Gmail API (`--to` / `DIGEST_TO` / `+digest` alias) |
| `gmail_common.py` | OAuth refresh + HTTPS helpers (stdlib) |
| `gmail_oauth_setup.py` | One-time local OAuth helper → refresh token |
| `setup.py` | One-command setup wizard |
| `ROUTINE.md` | Customizable filtering/summary rules (also the Claude Code routine prompt) |
| `run_local.sh` / `run_local.ps1` | Local end-to-end runner (macOS/Linux / Windows) |
| `.github/workflows/daily-digest.yml` | Scheduled CI pipeline |
| `.env.example` | Config template (placeholders only) |

## Configuration

All config is environment variables (set as `.env` locally, or as GitHub
Actions secrets/variables). See [`.env.example`](.env.example):

- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_USER` — Gmail access.
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (default `claude-haiku-4-5`) — the summarizer.
- `DIGEST_TO` (optional), `DIGEST_HOURS` (default `24`) — delivery.

## Cost

Summarizing one day of mail with `claude-haiku-4-5` costs a few cents at most.
For higher-quality summaries set `ANTHROPIC_MODEL=claude-sonnet-4-5`.

## Security

- `.env`, `client_secret_*.json`, `token.json`, `inbox.json`, `digest.md` are all
  git-ignored. Never commit secrets.
- Revoke the app's Gmail access any time at
  <https://myaccount.google.com/permissions>.

## License

[MIT](LICENSE).
