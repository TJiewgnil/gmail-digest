# Plan: Generalize the Gmail digest assistant into a public, reusable GitHub project

## Context

We built a working personal "daily email digest" in `D:\email-agent` (private repo
`TJiewgnil/daily-email-routine`): mail from several providers is forwarded into one Gmail,
a script reads it via the **Gmail API over HTTPS** (IMAP/SMTP are blocked in sandboxes),
an LLM summarizes it per `ROUTINE.md`, and the digest is delivered (currently via email to a
`+digest` alias + a Gmail label + phone notification).

The user wants a **public, general-purpose** version for anyone to use, with:
- **Minimal manual setup** — automate everything except the irreducible Google OAuth console steps.
- **Any source provider** (QQ, Outlook/Office365, Yahoo, 163, iCloud, university, …) that all
  **forward into Gmail**; the tool always reads Gmail.
- A **clear, explicit pipeline** and **detailed, actionable, bilingual (中文 + English) docs**.

**Decisions (confirmed with user):**
1. **New public repo** — keep the personal `daily-email-routine` deployment running untouched.
2. Support **all three deployments**: GitHub Actions + Anthropic API (primary), Claude Code routine, local cron/Task Scheduler.
3. Self-contained summarizer default model: **`claude-haiku-4-5`** (configurable).

## Core design

**The pipeline is always 3 stages:** `fetch → summarize → deliver`.
Only the *trigger* and *who summarizes* differ per deployment:

| Deployment | Trigger | Summarizer | Needs |
|---|---|---|---|
| GitHub Actions (primary) | cron in workflow | `summarize.py` (Anthropic API) | `ANTHROPIC_API_KEY` + GH secrets |
| Claude Code routine | `/schedule` | Claude Code agent (no API key) | Claude Code / claude.ai |
| Local (cron / Task Scheduler) | OS scheduler | `summarize.py` (or local `claude` CLI) | machine on + API key |

**Zero-dependency principle is kept:** all scripts are **Python standard library only** (no pip).
`summarize.py` calls the Anthropic **Messages API** (`POST https://api.anthropic.com/v1/messages`,
headers `x-api-key` + `anthropic-version: 2023-06-01`) via `urllib`, mirroring `gmail_common.py`'s
HTTPS pattern. This makes one script set run identically in CI, locally, and in sandboxes with no
`pip install`. (Alternative considered: the official `anthropic` SDK — rejected to preserve the
no-install portability that is the project's defining property.)

## New repo layout (suggested name: `gmail-digest`)

```
gmail-digest/
  gmail_common.py        # REUSE from D:\email-agent — OAuth refresh + HTTPS helpers (stdlib)
  fetch_inbox.py         # REUSE — Gmail API read → JSON (add optional --query passthrough)
  summarize.py           # NEW — inbox JSON + rules.md → digest via Anthropic Messages API (urllib)
  send_digest.py         # REUSE — parameterize recipient (DIGEST_TO / derived +digest alias)
  setup.py               # NEW — one-command setup wizard (absorbs gmail_oauth_setup.py)
  gmail_oauth_setup.py   # REUSE — OAuth loopback helper (kept standalone; setup.py calls it)
  rules.md               # GENERALIZED ROUTINE.md — user-editable filtering/summary rules
  run_local.ps1          # GENERALIZE — fetch → summarize.py → send
  run_local.sh           # NEW — bash equivalent for macOS/Linux
  .github/workflows/daily-digest.yml   # NEW — scheduled CI pipeline
  .env.example           # GENERALIZE — all config vars, placeholders only
  .gitignore             # .env, *.env, client_secret_*.json, token.json, inbox.json, digest.md, __pycache__
  LICENSE                # NEW — MIT
  README.md              # NEW (English) + language switcher link
  README.zh-CN.md        # NEW (中文)
  docs/
    SETUP.md / SETUP.zh-CN.md
    FORWARDING.md / FORWARDING.zh-CN.md
    NOTIFICATIONS.md / NOTIFICATIONS.zh-CN.md
```

Reusable files come from `D:\email-agent` (scrubbed of personal values). Build the new project in a
fresh directory (e.g. `D:\gmail-digest`) so the personal repo/deployment is never touched.

## Components

### 1. `summarize.py` (NEW — the only new logic)
- Reads `rules.md` + the inbox JSON (stdin or a path arg), calls the Messages API via `urllib`,
  writes the Chinese/English digest to stdout (and optionally `digest.md`).
- Env: `ANTHROPIC_API_KEY` (required), `ANTHROPIC_MODEL` (default `claude-haiku-4-5`).
- Request: `{model, max_tokens: ~4000, messages:[{role:"user", content: rules + "\n\n" + inbox_json}]}`.
  No `effort`/`thinking` params (Haiku rejects `effort`; keep it a plain single call). Parse
  `content[0].text`. Clear error on 401/429/5xx (reuse `gmail_common` error-handling style).
- Mirror `gmail_common.load_dotenv()` + UTF-8 stdout reconfigure so Windows consoles don't break.

### 2. Generalize existing scripts
- **`send_digest.py`**: recipient precedence `--to` → `DIGEST_TO` env → derive `<local>+digest@<domain>`
  from `GMAIL_USER`. Remove any hardcoded personal `+digest` address.
- **`fetch_inbox.py`**: keep `--hours/--label/--max`; add optional `--query` for advanced Gmail search.
  Already generic (reads via Gmail API, no personal data).
- **`gmail_common.py`**: `SCOPES` stays read + send (send needed for email delivery). No personal data.
- **`rules.md`** (from `ROUTINE.md`): replace QQ/Chalmers-specific source rules with **generic,
  user-editable** categories (🔴 action-needed / 👤 real people / 🗂 bulk) and a commented example of
  domain→source mapping users fill in. Keep the output-format template. Provide the digest-language
  as a rules knob (default follows the user's edit).

### 3. `setup.py` (NEW — the automation that minimizes manual steps)
One command after the Google console steps. It:
1. Auto-detects `client_secret_*.json` in the folder → extracts `client_id`/`client_secret`
   (no copy-paste). Falls back to prompting if absent.
2. Runs the OAuth loopback flow (reuse `gmail_oauth_setup.py` logic) → refresh token.
3. Writes `.env` from `.env.example` with all values filled.
4. **Self-test**: fetch last 24h (read) + send a test digest to the `+digest` alias; report OK/fail.
5. If `gh` is installed and the user picks GitHub Actions: offer to `gh secret set` the 5 secrets
   (`GMAIL_CLIENT_ID/SECRET/REFRESH_TOKEN`, `GMAIL_USER`, `ANTHROPIC_API_KEY`) automatically.
6. Prints deployment-specific next steps.

### 4. Deployment artifacts
- **`.github/workflows/daily-digest.yml`**: `on: schedule (cron UTC) + workflow_dispatch`; steps =
  checkout → setup-python → `python fetch_inbox.py --hours 24 > inbox.json` →
  `python summarize.py inbox.json > digest.md` → `python send_digest.py digest.md`. Secrets injected
  as env (scripts already prefer real env vars over `.env`). Document the UTC/DST cron caveat.
- **`run_local.ps1` / `run_local.sh`**: same 3-stage pipeline locally; UTF-8 handling already solved
  for PS 5.1 (BOM + `[Console]::OutputEncoding`). Document Windows Task Scheduler / cron entries.
- **Claude Code routine**: documented in SETUP — `/schedule` with a prompt pointing at `rules.md`;
  no `summarize.py`/API key (Claude Code is the summarizer). Reuses the exact fetch/send scripts.

### 5. Bilingual docs (every doc has `.md` EN + `.zh-CN.md`, cross-linked at top)
- **SETUP**: (0) prereqs → (1) **Google Cloud OAuth** — the one irreducible manual part, with exact
  clicks and the two gotchas we hit: **add yourself as an OAuth "Test user"** (fixes `403 access_denied`),
  and **leave the "used by an AI-powered agent" box unchecked**. → (2) run `python setup.py` → (3) pick a
  deployment (3a GH Actions, 3b Claude Code routine, 3c local) → (4) phone notifications → (5) edit `rules.md`.
- **FORWARDING**: how to forward each provider into Gmail — Gmail, **Outlook/Office365**, **QQ/Foxmail**,
  **163/126**, **Yahoo**, **iCloud**, and **generic IMAP via Gmail "Check mail from other accounts" (POP)**.
  State the principle: all providers forward into one Gmail; the tool only ever reads Gmail.
- **NOTIFICATIONS**: the phone-notification recipe and the lesson we learned —
  "skip-inbox + label" does **not** get real-time push on Android; the working setup is
  **keep in inbox + apply a label** (+ optional per-label notification), plus battery/sync notes.

### 6. Public-release hygiene
- `LICENSE` (MIT). `.gitignore` excludes every secret/runtime artifact (incl. `client_secret_*.json`, `token.json`).
- **No personal data anywhere** — all placeholders `you@gmail.com`; no routine/environment IDs; no real tokens.
- `.env.example` is the single source of config truth; short `SECURITY` note on revoking OAuth at
  `myaccount.google.com/permissions`.

## Reuse map (don't rewrite)
- `D:\email-agent\gmail_common.py`, `fetch_inbox.py`, `send_digest.py`, `gmail_oauth_setup.py`,
  `run_local.ps1`, `ROUTINE.md` → copy into the new repo and generalize as above. They are already
  stdlib-only and (except the `+digest` hardcode and ROUTINE's QQ/Chalmers rules) free of personal data.

## Verification (end-to-end, per deployment)
1. **Static**: `python -m py_compile` all scripts; `python fetch_inbox.py --help` / `summarize.py --help`.
2. **Local self-test**: in the fresh repo, run `python setup.py` with a throwaway test Gmail +
   OAuth client → confirm it writes `.env`, fetches N messages, and the `+digest` test email arrives.
3. **`summarize.py` isolation**: pipe a saved `inbox.json` sample → confirm a well-formed digest and
   that `ANTHROPIC_MODEL` override works; confirm clean error on a bad API key (no traceback).
4. **GitHub Actions**: push, set secrets (via `setup.py`'s `gh` path or manually), trigger
   `workflow_dispatch` → confirm the digest email arrives and the run is green.
5. **Local scheduler**: `run_local.ps1` / `run_local.sh` one-shot → digest arrives.
6. **Claude Code routine**: `/schedule` a run-now against the repo → digest produced.

## Notes / caveats
- **Repo creation & first push are user-run.** In this environment the harness blocks `gh repo create
  --push` to a new remote (cross-trust-boundary). The implementation will prepare everything and hand
  the user the exact `gh repo create ... --public` / `git push` commands (or they create the repo in
  the web UI). See memory `harness-blocks-outward-actions`.
- **Model default** `claude-haiku-4-5` is configurable via `ANTHROPIC_MODEL`; docs note the
  cost/quality knob (Sonnet/Opus) and that daily cost is a few cents at most.
- **DST**: scheduled crons are UTC; docs explain the ±1h noon drift and how to adjust.
- Keep the digest-as-routine-output option for the Claude Code path (visible in routine records),
  and email delivery for the API paths.
