#!/usr/bin/env python3
"""Fetch recent Gmail inbox messages via the Gmail REST API and emit JSON to stdout.

Uses HTTPS(443) via the Gmail API, so it runs inside the cloud routine sandbox
(which blocks raw IMAP sockets). Messages are pulled with format=raw and parsed
with the stdlib email module, so the MIME/encoding handling is identical to a
normal mailbox read.

Credentials: see gmail_common.py (OAuth client id/secret + refresh token).

Usage:
    python fetch_inbox.py [--hours 24] [--label INBOX] [--max 200]

Notes:
- Read-only: only messages.list + messages.get are used; nothing is modified.
- Standard library only; no pip install needed.
- Since QQ and Chalmers mail is forwarded into Gmail, reading the Gmail INBOX
  covers all three accounts. Source can be inferred from `from_addr`.
"""
import argparse
import base64
import datetime as dt
import email
import json
import sys
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser

from gmail_common import api_get, get_access_token, load_dotenv


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML -> text, dropping <script>/<style> content."""

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self._chunks.append(data)

    def text(self):
        return " ".join("".join(self._chunks).split())


def html_to_text(html):
    parser = _HTMLTextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.text()


def decode_mime(value):
    """Decode an RFC 2047 encoded header (handles Chinese / QQ encodings)."""
    if not value:
        return ""
    out = []
    from email.header import decode_header
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", errors="replace"))
            except (LookupError, TypeError):
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _payload_text(part):
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, TypeError):
        return payload.decode("utf-8", errors="replace")


def extract_body(msg, limit=2000):
    """Return a plain-text snippet of the message body, preferring text/plain."""
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if "attachment" in str(part.get("Content-Disposition") or "").lower():
                continue
            if part.get_content_type() == "text/plain":
                text = _payload_text(part)
                if text.strip():
                    break
        if not text.strip():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    text = html_to_text(_payload_text(part))
                    if text.strip():
                        break
    else:
        if msg.get_content_type() == "text/html":
            text = html_to_text(_payload_text(msg))
        else:
            text = _payload_text(msg)
    return " ".join(text.split())[:limit]


def list_message_ids(token, after_epoch, label, limit):
    """Return up to `limit` message ids newer than after_epoch, newest first."""
    ids = []
    params = {"q": "after:{}".format(after_epoch), "maxResults": 100}
    if label:
        params["labelIds"] = label
    page_token = None
    while len(ids) < limit:
        if page_token:
            params["pageToken"] = page_token
        resp = api_get("/users/me/messages", token, params)
        for m in resp.get("messages", []):
            ids.append(m["id"])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids[:limit]


def get_raw_message(token, msg_id):
    """Fetch one message as raw RFC822 bytes and parse it with the email module."""
    resp = api_get("/users/me/messages/{}".format(msg_id), token, {"format": "raw"})
    raw = resp.get("raw", "")
    raw += "=" * (-len(raw) % 4)  # restore base64url padding Gmail strips
    return email.message_from_bytes(base64.urlsafe_b64decode(raw))


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Fetch recent Gmail inbox messages as JSON.")
    ap.add_argument("--hours", type=int, default=24, help="look back this many hours (default 24)")
    ap.add_argument("--label", "--folder", dest="label", default="INBOX",
                    help="Gmail label to read (default INBOX)")
    ap.add_argument("--max", type=int, default=200, help="cap number of messages (default 200)")
    args = ap.parse_args()

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=args.hours)
    # Gmail `after:` is coarse; query a bit wider, then filter precisely below.
    after_epoch = int((cutoff - dt.timedelta(hours=1)).timestamp())

    token = get_access_token()
    label = args.label.upper() if args.label else None
    ids = list_message_ids(token, after_epoch, label, args.max)

    messages = []
    for msg_id in ids:  # Gmail returns newest first
        msg = get_raw_message(token, msg_id)

        msg_dt = None
        date_hdr = msg.get("Date")
        if date_hdr:
            try:
                msg_dt = parsedate_to_datetime(date_hdr)
                if msg_dt.tzinfo is None:
                    msg_dt = msg_dt.replace(tzinfo=dt.timezone.utc)
            except (TypeError, ValueError):
                msg_dt = None
        if msg_dt is not None and msg_dt < cutoff:
            continue

        _, from_addr = parseaddr(decode_mime(msg.get("From")))
        messages.append({
            "from": decode_mime(msg.get("From")),
            "from_addr": from_addr.lower(),
            "to": decode_mime(msg.get("To")),
            "date": msg_dt.isoformat() if msg_dt else (date_hdr or ""),
            "subject": decode_mime(msg.get("Subject")),
            "snippet": extract_body(msg, limit=2000),
        })

    print(json.dumps(messages, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
