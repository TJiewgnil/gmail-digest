# Setup

**English** · [中文](SETUP.zh-CN.md)

Related: [Forwarding](FORWARDING.md) · [Notifications](NOTIFICATIONS.md)

The only part you *must* do by hand is the Google Cloud OAuth setup (step 1).
Everything after that is automated by `python setup.py`.

---

## 0. Prerequisites

- **Python 3.8+** (standard library only — no `pip install`).
- A **Gmail account** that will receive all your mail (set up forwarding later;
  see [Forwarding](FORWARDING.md)).
- For the GitHub Actions / local paths: an **Anthropic API key**
  (<https://console.anthropic.com/>).
- Optional, for auto-pushing CI secrets: the **GitHub CLI** (`gh`).

---

## 1. Google Cloud OAuth (the one manual part)

Do this once at <https://console.cloud.google.com/>.

1. **Create or pick a project** (top project selector → *New project*).
2. **Enable the Gmail API:** *APIs & Services → Library* → search "Gmail API" →
   **Enable**.
3. **Configure the OAuth consent screen:** *APIs & Services → OAuth consent
   screen*.
   - User type: **External** → *Create*.
   - Fill in the app name and your email where required.
   - **Add yourself as a Test user.** *Audience / Test users → Add users →* your
     Gmail address.
     > ⚠️ **Gotcha #1.** If you skip this, authorization fails with
     > **`403 access_denied`** ("app is being tested"). Adding yourself as a Test
     > user fixes it. (You do **not** need to publish the app or get it verified
     > for personal use.)
4. **Create the OAuth client:** *APIs & Services → Credentials → Create
   credentials → OAuth client ID*.
   - Application type: **Desktop app** (this is what allows the
     `http://localhost` loopback redirect the setup uses).
   - If Google shows a checkbox like **"This app will be used by an AI-powered
     agent"**, **leave it unchecked.**
     > ⚠️ **Gotcha #2.** Checking it changes the client's allowed flows and
     > breaks the desktop loopback used here.
   - Create, then **Download JSON**. Save it into the repo folder as
     `client_secret_*.json` (any name starting with `client_secret`). It is
     git-ignored.

---

## 2. Run the setup wizard

```bash
python setup.py
```

It will:

1. auto-detect `client_secret_*.json` and read the client id/secret,
2. open your browser for Google consent → obtain a **refresh token**,
3. ask for `GMAIL_USER`, `ANTHROPIC_API_KEY`, model, recipient, look-back hours,
4. write `.env` (git-ignored),
5. **self-test**: fetch the last 24h (read) and send a test digest email,
6. optionally run `gh secret set` to push your GitHub Actions secrets,
7. print the next steps for the deployment you choose.

Prefer to do it by hand? Run `python gmail_oauth_setup.py --client-id <id>
--client-secret <secret>`, then copy `.env.example` → `.env` and fill it in.

---

## 3. Pick a deployment

### 3a. GitHub Actions + Anthropic API (primary, recommended)

Runs in the cloud on a schedule — nothing stays on your machine.

1. Push this repo to GitHub.
2. Set these **Actions secrets** (*Settings → Secrets and variables → Actions*),
   or let `setup.py` push them with `gh`:
   `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`,
   `GMAIL_USER`, `ANTHROPIC_API_KEY`.
   Optional **variables** (same screen, "Variables" tab): `ANTHROPIC_MODEL`,
   `DIGEST_TO`, `DIGEST_HOURS`.
3. Edit the cron in `.github/workflows/daily-digest.yml`.
   > ⏰ **Cron is UTC and ignores daylight saving.** A fixed UTC time drifts ±1h
   > across DST in your local clock. Pick the UTC time that matches your desired
   > local time, e.g. `0 7 * * *` = 07:00 UTC = 08:00 CET / 09:00 CEST. Adjust
   > twice a year if you need it pinned to local time.
4. Test it: *Actions → Daily Email Digest → Run workflow*.

### 3b. Claude Code routine (no API key)

Here Claude Code is the summarizer, so you do **not** need `ANTHROPIC_API_KEY`
or `summarize.py`.

1. Open this repo in Claude Code / claude.ai.
2. Use `/schedule` to create a daily routine whose prompt follows `ROUTINE.md`:
   it runs `python fetch_inbox.py --hours 24`, summarizes per the rules, writes
   `digest.md`, and runs `python send_digest.py digest.md`.
3. The digest is also emitted as the routine's own output, so you can review it
   in the routine history.

Store `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`,
`GMAIL_USER` as environment secrets for the routine.

### 3c. Local cron / Task Scheduler

Runs on your own always-on machine. Needs `ANTHROPIC_API_KEY` in `.env`.

- **macOS / Linux:**
  ```bash
  ./run_local.sh          # one-shot test
  ```
  Then add a crontab entry (`crontab -e`):
  ```cron
  0 8 * * *  cd /path/to/gmail-digest && ./run_local.sh >> digest.log 2>&1
  ```
  Local cron uses your machine's local time (no UTC conversion needed).

- **Windows:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\run_local.ps1
  ```
  Then create a **Task Scheduler** Basic Task (daily) with:
  - Program: `powershell.exe`
  - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\gmail-digest\run_local.ps1"`

---

## 4. Phone notifications

Set up a Gmail filter + label so the digest pushes to your phone. The exact
recipe, and the lesson about Android push, is in
**[Notifications](NOTIFICATIONS.md)**.

---

## 5. Customize `ROUTINE.md`

`ROUTINE.md` holds your filtering priorities, source mapping, output format, and
language. Edit it to taste — it's the single place that controls what the digest
looks like, for all three deployments.

---

## Verification checklist

- `python -m py_compile *.py` — all scripts compile.
- `python fetch_inbox.py --hours 24` — prints inbox JSON.
- `python summarize.py inbox.json` — prints a digest (needs `ANTHROPIC_API_KEY`).
- `python send_digest.py digest.md` — the test email arrives at your `+digest`
  alias / `DIGEST_TO`.
- GitHub Actions: `workflow_dispatch` run is green and the digest arrives.

## Troubleshooting

- **`403 access_denied`** → add yourself as a Test user (step 1.3).
- **No `refresh_token` returned** → Google only returns one on first consent.
  Revoke the app at <https://myaccount.google.com/permissions> and re-run.
- **`401` from Anthropic** → check `ANTHROPIC_API_KEY`.
- **`429` from Anthropic** → rate-limited or out of credit; retry later.
- **Chinese/emoji look garbled on Windows** → the scripts force UTF-8; make sure
  you run them via `run_local.ps1` (which sets the console encoding).
