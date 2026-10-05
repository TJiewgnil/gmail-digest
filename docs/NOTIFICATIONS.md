# Phone notifications

**English** · [中文](NOTIFICATIONS.zh-CN.md)

Related: [Setup](SETUP.md) · [Forwarding](FORWARDING.md)

Goal: when the daily digest lands, your phone pings you — and *only* for the
digest, not for every marketing email.

## The key lesson (read this first)

> ⚠️ **On Android, a filter that "Skip the Inbox (Archive it)" does NOT produce a
> real-time push notification.** The Gmail app only reliably pushes for mail that
> **stays in the Inbox**.
>
> **The working setup is: keep the digest in the Inbox *and* apply a label** —
> then (optionally) turn on per-label notifications. Do **not** archive it.

We learned this the hard way: archiving-with-a-label looked tidy but silently
killed the phone push. Keeping it in the inbox is what makes the notification
fire.

## Recommended recipe

### 1. Deliver the digest to a dedicated address

`send_digest.py` defaults to the `<local>+digest@<domain>` alias of your
`GMAIL_USER` (e.g. `you+digest@gmail.com`). Gmail delivers `+suffix` aliases to
the same inbox, which gives you a clean thing to filter on. (Or set `DIGEST_TO`.)

### 2. Create a Gmail filter

*Gmail → Settings → Filters and Blocked Addresses → Create a new filter.*

- **To:** `you+digest@gmail.com` (or your `DIGEST_TO`), or **From:**
  `you@gmail.com` with Subject containing `Email Digest`.
- Click **Create filter**, then tick:
  - ✅ **Apply the label:** create one, e.g. `Digest`.
  - ✅ (optional) **Mark as important** / **Star it** / **Always mark as
    important**.
  - ❌ **Do NOT** tick "Skip the Inbox (Archive it)" — leaving it in the inbox is
    what enables the phone push.

### 3. Turn on Gmail app notifications

**Android (Gmail app):**
1. *Settings → (your account) → Manage labels → Digest → Label notifications →
   On.*
2. *Settings → (your account) → Notifications → All new mail* (or at least allow
   the `Digest` label).
3. Pick a distinct sound/vibration for the `Digest` label if you like.

**iOS (Gmail app):** *Settings → (account) → Notifications → All new mail*, and
enable notifications for the Gmail app in iOS *Settings → Notifications → Gmail*.
(iOS is less sensitive to the archive issue, but keeping the digest in the inbox
is still the safe choice.)

### 4. Make sure the push can actually arrive

- **Battery optimization:** exempt Gmail from aggressive battery saving
  (*Android Settings → Apps → Gmail → Battery → Unrestricted*). OEM skins
  (Xiaomi/MIUI, Samsung, Huawei, OnePlus, Oppo/Vivo) are the usual culprits for
  "notifications arrive late or only when I open the app".
- **Account sync:** ensure Gmail sync is on for the account
  (*Settings → (account) → Data usage → Sync Gmail*).
- **Do Not Disturb / schedules:** make sure the digest's arrival time isn't
  inside a DND window, or allow the `Digest` label through DND.

## Quick test

Run `python send_digest.py digest.md` (or trigger your deployment) and confirm:
1. the message appears **in the Inbox** with the `Digest` label, and
2. your phone shows a notification within a minute or two.

If no push arrives, re-check: inbox (not archived) → label notifications on →
battery unrestricted → sync on.
