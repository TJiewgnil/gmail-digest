# Forwarding mail into Gmail

**English** · [中文](FORWARDING.zh-CN.md)

Related: [Setup](SETUP.md) · [Notifications](NOTIFICATIONS.md)

## The principle

> **All your providers forward into one Gmail. The tool only ever reads Gmail.**

This keeps the tool simple and portable: it speaks the Gmail API (HTTPS) and
nothing else. You can add or remove source mailboxes any time without touching
the code — just set up (or stop) forwarding at the source.

Two ways to get mail into Gmail:

- **Push (forwarding rule at the source)** — the source provider auto-forwards
  every new message to your Gmail. Near-instant. Preferred when available.
- **Pull (Gmail fetches via POP)** — Gmail logs into the other account and pulls
  new mail periodically (*Gmail → Settings → Accounts and Import → Check mail
  from other accounts*). Use this when the source can't forward (e.g. no
  forwarding option, or you don't want to touch its settings). Polling is
  slower (tens of minutes).

> Tip: After forwarding is set up, you can tell which Gmail message came from
> which source by its `from_addr` — `ROUTINE.md` uses that for source labels.

---

## Gmail → Gmail

*Settings (gear) → See all settings → Forwarding and POP/IMAP → Add a
forwarding address.* Confirm via the verification email, then choose **Forward a
copy of incoming mail to** your main Gmail. Optionally create a filter to forward
only some mail.

## Outlook.com / Office 365

- **Outlook.com:** *Settings → Mail → Forwarding → Enable forwarding →* your
  Gmail → Save. (Keep "Keep a copy" on if you still want it in Outlook.)
- **Office 365 (work/school):** *Outlook on the web → Settings → Mail →
  Forwarding.* If your admin disabled it, use an **Inbox rule** (*Rules → Add
  new rule → Redirect/Forward to*) or ask the admin, or fall back to Gmail POP
  pull.

## QQ Mail / Foxmail

QQ Mail web → *设置 (Settings) → 收信规则 / 自动转发 (Auto-forward)* → add your
Gmail as the forwarding target and verify. You may need to enable the service
first under *设置 → 账户*. (Foxmail shares the QQ Mail backend; configure it in
the QQ Mail web UI.)

## 163 / 126 (NetEase)

163/126 web → *设置 (Settings) → POP3/SMTP/IMAP* and *设置 → 自动回复/转发 (Auto
forward)*. Enable auto-forward to your Gmail and verify. NetEase often requires
an **authorization code** (客户端授权密码) rather than your login password if you
instead choose the Gmail POP-pull route.

## Yahoo Mail

Automatic forwarding may require Yahoo Mail Plus on some accounts. If available:
*Settings → More Settings → Mailboxes → (your account) → Forwarding →* add your
Gmail and verify. Otherwise use **Gmail POP pull** with a Yahoo **app password**
(Yahoo *Account Security → Generate app password*), since Yahoo blocks plain
password logins.

## iCloud Mail

*iCloud Mail (web) → Settings (gear) → Rules*, or *Preferences → General →
Forward my email to* → your Gmail. iCloud supports native forwarding without a
paid add-on.

## Generic IMAP/POP (university, custom domains, anything else)

If the source offers no forwarding, let **Gmail pull it via POP**:

1. *Gmail → Settings → Accounts and Import → Check mail from other accounts →
   Add a mail account.*
2. Enter the address, then the POP server, port, username and password (use an
   **app password** / **authorization code** if the provider requires one).
3. Gmail will poll and import new mail automatically.

This works for virtually any mailbox that exposes POP, including most university
and custom-domain accounts.

---

## After forwarding

- Send yourself a test message to each source and confirm it lands in Gmail.
- If a source lands in Gmail's **Spam** or **Promotions**, create a Gmail filter
  (*Filter messages like these → Never send to Spam / Categorize as Primary*) so
  the digest sees it.
- Re-run `python fetch_inbox.py --hours 24` to confirm the tool now sees mail
  from every source (check the `from_addr` values).
