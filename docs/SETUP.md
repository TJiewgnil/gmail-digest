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
- A **Claude Code** account with access to cloud routines
  (<https://claude.ai/code>), and a **GitHub** account to host this repo.

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
3. ask for `GMAIL_USER` and an optional recipient override,
4. write `.env` (git-ignored),
5. **self-test**: fetch the last 24h (read) and send a test digest email,
6. print the next steps for creating the cloud routine.

Prefer to do it by hand? Run `python gmail_oauth_setup.py --client-id <id>
--client-secret <secret>`, then copy `.env.example` → `.env` and fill it in.

---

## 3. Create the Claude Code cloud routine

Claude is the summarizer, so there is no API key and no summarizer script — the
routine just follows `ROUTINE.md`.

1. **Push this repo to GitHub** (a private repo is fine) and connect it to
   Claude Code on the web (<https://claude.ai/code>).
2. **Create a cloud environment** for the routine and add these as environment
   secrets (values are in the `.env` the wizard wrote):
   `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`,
   `GMAIL_USER`, and optionally `DIGEST_TO`.
3. **Create a daily routine** (run `/schedule` in Claude Code, or use the
   routines page on claude.ai) on this repo + environment, with a prompt like:
   > Follow the instructions in ROUTINE.md.

   Per `ROUTINE.md`, each run executes `python fetch_inbox.py --hours 24`,
   summarizes the mail, writes `digest.md`, runs
   `python send_digest.py digest.md`, and also prints the digest as the
   routine's own output so you can review it in the routine history.
   `.claude/settings.json` pre-approves running `python` so the unattended run
   never stalls on a permission prompt.
   > ⏰ **The routine's cron is UTC and ignores daylight saving.** A fixed UTC
   > time drifts ±1h in your local clock across DST, e.g. `0 10 * * *` is 12:00
   > CEST in summer but 11:00 CET in winter. Adjust twice a year if you want it
   > pinned to local time.
4. **Test it:** trigger a manual run of the routine and check that the digest
   arrives.

---

## 4. Phone notifications

Set up a Gmail filter + label so the digest pushes to your phone. The exact
recipe, and the lesson about Android push, is in
**[Notifications](NOTIFICATIONS.md)**.

---

## 5. Customize `ROUTINE.md`

`ROUTINE.md` holds your filtering priorities, source mapping, output format, and
language. Edit it to taste — it's the single place that controls what the digest
looks like.

---

## Verification checklist

- `python -m py_compile *.py` — all scripts compile.
- `python fetch_inbox.py --hours 24` — prints inbox JSON.
- `python send_digest.py digest.md` — the test email arrives at your `+digest`
  alias / `DIGEST_TO`.
- A manual run of the routine finishes and the digest arrives.

## Troubleshooting

- **`403 access_denied`** → add yourself as a Test user (step 1.3).
- **No `refresh_token` returned** → Google only returns one on first consent.
  Revoke the app at <https://myaccount.google.com/permissions> and re-run.
- **Routine run says `GMAIL_CLIENT_ID is not set`** → the secrets are missing
  from the routine's cloud environment (step 3.2).
- **Chinese/emoji look garbled on Windows** (local runs only) → set
  `PYTHONUTF8=1` before running the scripts.
