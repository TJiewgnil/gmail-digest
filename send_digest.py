#!/usr/bin/env python3
"""Email a digest file back to yourself via the Gmail REST API (HTTPS).

Uses HTTPS(443) so it works inside the cloud routine sandbox, which blocks raw
SMTP sockets. Credentials: see gmail_common.py.

Usage:
    python send_digest.py digest.md [--subject "..."] [--to someone@example.com]

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


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Email a digest file to yourself via the Gmail API.")
    ap.add_argument("digest_file", help="path to the digest text/markdown file")
    ap.add_argument("--subject", default=None, help="override the email subject")
    ap.add_argument("--to", default=None, help="recipient (default: GMAIL_USER)")
    args = ap.parse_args()

    user = os.environ.get("GMAIL_USER")
    if not user:
        sys.stderr.write("ERROR: set GMAIL_USER (your gmail address)\n")
        sys.exit(2)

    to_addr = args.to or user
    subject = args.subject or "每日邮件摘要 {}".format(dt.date.today().isoformat())

    try:
        with open(args.digest_file, "r", encoding="utf-8-sig") as f:
            body = f.read()
    except OSError as e:
        sys.stderr.write("ERROR: cannot read {}: {}\n".format(args.digest_file, e))
        sys.exit(1)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Claude 邮件助手", user))
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    token = get_access_token()
    api_post("/users/me/messages/send", token, {"raw": raw})

    print("OK: sent '{}' to {}".format(subject, to_addr))


if __name__ == "__main__":
    main()
