#!/usr/bin/env python3
"""Email a digest file via the Gmail REST API (HTTPS).

Uses HTTPS(443) so it works inside sandboxes / CI that block raw SMTP sockets.
Credentials: see gmail_common.py.

Recipient precedence (first match wins):
    1. --to <addr>                explicit command-line recipient
    2. DIGEST_TO env var          configured recipient
    3. derived "+digest" alias    <local>+digest@<domain> from GMAIL_USER
       (Gmail delivers +suffix aliases to the same inbox, which makes it easy to
        filter/label the digest and get a separate phone notification for it)

Usage:
    python send_digest.py digest.md
    python send_digest.py digest.md --to you@example.com --subject "..."

Standard library only.
"""
import argparse
import base64
import datetime as dt
import os
import sys
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

from gmail_common import api_post, get_access_token, load_dotenv


def derive_digest_alias(user):
    """Turn user@domain into user+digest@domain; return user unchanged if malformed."""
    local, sep, domain = user.partition("@")
    if not sep or not domain:
        return user
    if "+" in local:  # already has a +suffix; don't double it
        return user
    return "{}+digest@{}".format(local, domain)


def resolve_recipient(cli_to, user):
    if cli_to:
        return cli_to
    env_to = os.environ.get("DIGEST_TO")
    if env_to:
        return env_to.strip()
    return derive_digest_alias(user)


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Email a digest file via the Gmail API.")
    ap.add_argument("digest_file", help="path to the digest text/markdown file")
    ap.add_argument("--subject", default=None, help="override the email subject")
    ap.add_argument("--to", default=None,
                    help="recipient (default: DIGEST_TO env, else <user>+digest@<domain>)")
    args = ap.parse_args()

    user = os.environ.get("GMAIL_USER")
    if not user:
        sys.stderr.write("ERROR: set GMAIL_USER (your gmail address)\n")
        sys.exit(2)

    to_addr = resolve_recipient(args.to, user)
    subject = args.subject or "Email Digest · {}".format(dt.date.today().isoformat())

    try:
        with open(args.digest_file, "r", encoding="utf-8-sig") as f:
            body = f.read()
    except OSError as e:
        sys.stderr.write("ERROR: cannot read {}: {}\n".format(args.digest_file, e))
        sys.exit(1)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Gmail Digest", user))
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    token = get_access_token()
    api_post("/users/me/messages/send", token, {"raw": raw})

    print("OK: sent '{}' to {}".format(subject, to_addr))


if __name__ == "__main__":
    main()
